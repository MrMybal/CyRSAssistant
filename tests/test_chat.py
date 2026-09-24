import copy
import json
import unittest
from unittest.mock import Mock, patch
from companion.chat import respond
from companion.service import answer

STATE = {"session": "s", "runtime": 1, "generation": 0, "revision": 0,
         "parameters": [], "techniques": [], "loading": True,
         "prompt": {"id": 1, "pending": True, "mode": 3, "text": "Bonjour", "shader_hash": ""}}


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.client, self.provider = Mock(), Mock()
        self.state = copy.deepcopy(STATE)
        self.client.state.return_value = self.state

    def test_greeting_works_without_effects_selection_or_finished_loading(self):
        self.provider.complete.return_value = {"message": "Bonjour !", "action": "reply"}
        self.assertEqual(respond(self.client, 1, self.provider, self.state), "Bonjour !")
        self.client.call.assert_not_called()

    def test_followup_receives_history_without_private_runtime_paths(self):
        self.state["conversation"] = [{"role": "user", "content": "Je prefere un rendu froid"},
                                      {"role": "assistant", "content": "D'accord"}]
        self.state["base_path"] = "private-game-path"
        self.provider.complete.return_value = {"message": "Oui", "action": "reply"}
        respond(self.client, 1, self.provider, self.state)
        payload = self.provider.complete.call_args.args[1]
        self.assertIn("rendu froid", payload)
        self.assertNotIn("private-game-path", payload)

    def test_missing_target_is_reported_without_mutation(self):
        self.state["loading"] = False
        self.provider.complete.side_effect = [{"message": "ok", "action": "replace_effect", "request": "replace bloom", "arguments": {"effect": "absent.fx"}}, {"message": "Quel bloom remplacer ?", "action": "reply"}]
        self.assertIn("Quel bloom", respond(self.client, 1, self.provider, self.state))
        self.assertTrue(all(c.args[0] == "assistant_progress" for c in self.client.call.call_args_list))

    def test_generation_dispatches_then_model_reads_tool_result(self):
        self.state["loading"] = False
        self.provider.complete.side_effect = [{"message": "ok", "action": "generate_effect", "request": "Create warm colors"}, {"message": "Effet compile", "action": "reply"}]
        with patch("companion.chat.generate_effect", return_value="compiled") as generate:
            self.assertEqual(respond(self.client, 1, self.provider, self.state), "Effet compile")
            self.assertEqual(generate.call_args.args[3]["prompt"]["text"], "Create warm colors")
        self.assertIn("compiled", self.provider.complete.call_args.args[1])

    def test_cancelled_action_never_runs(self):
        current = copy.deepcopy(self.state)
        current["prompt"]["pending"] = False
        self.client.state.return_value = current
        self.provider.complete.return_value = {"message": "ok", "action": "reload_effects"}
        with self.assertRaisesRegex(RuntimeError, "cancelled"):
            respond(self.client, 1, self.provider, self.state)
        self.assertTrue(all(c.args[0] == "assistant_progress" for c in self.client.call.call_args_list))

    def test_reads_real_parameter_values_then_answers(self):
        self.state["parameters"] = [{"id": 0, "effect": "Bloom.fx", "name": "Threshold", "label": "Seuil", "type": "float", "value": [1.2], "min": 0, "max": 4, "readonly": False}]
        self.provider.complete.side_effect = [{"message": "Je lis le seuil", "action": "get_parameters", "arguments": {"effect": "Bloom.fx"}}, {"message": "Le seuil vaut 1.2, plage 0 a 4.", "action": "reply"}]
        self.assertIn("1.2", respond(self.client, 1, self.provider, self.state))
        context = json.loads(self.provider.complete.call_args.args[1])
        self.assertEqual(context["tool_results"][0]["result"]["items"][0]["name"], "Threshold")
        self.assertEqual(context["tool_results"][0]["result"]["items"][0]["value"], [1.2])

    def test_replacement_cannot_be_silently_added(self):
        self.state["loading"] = False
        self.state["prompt"]["text"] = "Remplace le bloom"
        self.provider.complete.side_effect = [{"message": "ok", "action": "generate_effect", "request": "Add bloom"}, {"message": "Quel effet remplacer ?", "action": "reply"}]
        with patch("companion.chat.generate_effect") as generate:
            respond(self.client, 1, self.provider, self.state)
            generate.assert_not_called()

    def test_unknown_tool_is_rejected(self):
        self.provider.complete.return_value = {"message": "ok", "action": "shell"}
        with self.assertRaises(ValueError):
            respond(self.client, 1, self.provider, self.state)
        self.client.call.assert_not_called()

    def test_provider_failure_does_not_lock_next_send(self):
        self.provider.complete.side_effect = RuntimeError("temporary failure")
        phase, _ = answer(self.client, 1, self.provider, self.state)
        self.assertEqual(phase, "ready")
        self.assertIn("Request failed", self.client.call.call_args.kwargs["message"])

    def test_utf8_response_respects_native_byte_limit(self):
        with patch("companion.service.respond", return_value="é" * 16000):
            answer(self.client, 1, self.provider, self.state)
        message = self.client.call.call_args.kwargs["message"]
        self.assertLessEqual(len(message.encode("utf-8")), 16000)

    def test_agent_reads_source_tool_then_uses_result(self):
        self.provider.complete.side_effect = [{"message": "Lecture", "action": "read_effect_source", "arguments": {"file": "Bloom.fx"}}, {"message": "Le seuil est utilise dans le code.", "action": "reply"}]
        with patch("companion.chat.read_source", return_value={"file": "Bloom.fx", "source": "return max(color-threshold,0);", "next_offset": None}) as source:
            result = respond(self.client, 1, self.provider, self.state)
            source.assert_called_once_with(self.state, "Bloom.fx", 0)
        self.assertIn("seuil", result)
        self.assertIn("return max(color-threshold,0);", self.provider.complete.call_args.args[1])
