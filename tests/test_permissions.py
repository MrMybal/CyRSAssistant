import copy
import unittest
from unittest.mock import Mock, patch
from companion.permissions import PermissionClient, PermissionDenied
from companion.chat import respond

STATE = {"session":"s", "runtime":1, "generation":1, "revision":1,
         "prompt":{"id":2,"pending":True,"text":"Regle le rendu"},
         "parameters":[], "techniques":[], "permissions":{"mode":1,"epoch":1,"request":None}}
PAYLOAD = {"session":"s", "runtime":1,"generation":1,"revision":1,"prompt_id":2,"changes":[]}


class PermissionTests(unittest.TestCase):
    def setUp(self):
        self.raw = Mock()
        self.raw.state.return_value = copy.deepcopy(STATE)
        self.client = PermissionClient(self.raw, 1, STATE, timeout=1)

    def test_automatic_grant_attached_to_exact_payload(self):
        self.raw.call.side_effect = [{"permission":{"id":7,"status":"approved"}}, {"ok":True}]
        self.client.call("apply_patch", **PAYLOAD)
        first = self.raw.call.call_args_list[0]
        self.assertEqual(first.kwargs["payload"], PAYLOAD)
        self.raw.call.assert_called_with("apply_patch", **PAYLOAD, permission_id=7)

    def test_waits_until_approved_before_write(self):
        pending = {"id":7,"epoch":1,"status":"pending"}
        approved = {**pending,"status":"approved"}
        self.raw.call.side_effect = [{"permission":pending},{"ok":True}]
        waiting = {**STATE,"permissions":{"mode":1,"request":pending}}
        ready = {**STATE,"permissions":{"mode":1,"request":approved}}
        self.raw.state.side_effect = [STATE, waiting, ready]
        with patch("companion.permissions.time.sleep") as sleep:
            self.client.call("apply_patch", **PAYLOAD)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual([c.args[0] for c in self.raw.call.call_args_list], ["request_action_permission","apply_patch"])

    def test_refusal_never_writes(self):
        self.raw.call.return_value = {"permission":{"id":7,"status":"denied"}}
        with self.assertRaises(PermissionDenied):
            self.client.call("apply_patch", **PAYLOAD)
        self.assertEqual(self.raw.call.call_count, 1)

    def test_cancelled_prompt_does_not_request_permission(self):
        self.raw.state.return_value["prompt"]["pending"] = False
        with self.assertRaises(PermissionDenied):
            self.client.call("apply_patch", **PAYLOAD)
        self.raw.call.assert_not_called()

    def test_source_refusal_is_before_source_or_disassembly_access(self):
        self.raw.call.return_value = {"permission":{"id":7,"status":"denied"}}
        with self.assertRaises(PermissionDenied):
            self.client.call("inspect_game_shader", runtime=1, hash="test")
        self.assertEqual([c.args[0] for c in self.raw.call.call_args_list], ["request_action_permission"])

    def test_stale_values_are_not_offered_for_approval(self):
        self.raw.state.return_value["revision"] = 5
        with self.assertRaises(ValueError):
            self.client.call("apply_patch", **PAYLOAD)
        self.raw.call.assert_not_called()

    def test_full_mode_allows_sequential_render_operations(self):
        state = copy.deepcopy(STATE); state["permissions"]["mode"] = 2
        self.raw.state.return_value = state
        provider = Mock()
        provider.complete.side_effect = [{"message":"Undo", "action":"undo"}, {"message":"Restore", "action":"restore_game_shaders"}, {"message":"Termine", "action":"reply"}]
        with patch("companion.chat.with_permissions", return_value=self.raw):
            self.assertEqual(respond(self.raw,1,provider,state), "Termine")
        self.assertEqual([c.args[0] for c in self.raw.call.call_args_list if c.args[0] != "assistant_progress"], ["undo","restore_game_shaders"])
