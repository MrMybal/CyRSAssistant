import copy
import unittest
from unittest.mock import Mock
from companion.generation import checked_response, fresh_request, generate_effect

STATE = {"session": "s", "runtime": 1, "generation": 2, "revision": 3,
         "prompt": {"id": 4, "pending": True, "text": "Grayscale"}}


class GenerationTests(unittest.TestCase):
    def test_cancelled_request_never_compiles(self):
        client = Mock()
        current = copy.deepcopy(STATE)
        current["prompt"]["pending"] = False
        client.state.return_value = current
        provider = Mock()
        provider.complete.return_value = {"message": "ok", "body": "return color;"}
        with self.assertRaisesRegex(RuntimeError, "cancelled"):
            generate_effect(client, 1, provider, STATE)
        client.call.assert_not_called()

    def test_changed_session_never_mutates(self):
        client = Mock()
        client.state.return_value = {**STATE, "session": "other"}
        with self.assertRaises(RuntimeError):
            fresh_request(client, 1, STATE)

    def test_invalid_source_response_rejected(self):
        for response in ({"message": "ok", "body": []}, {"message": 7, "body": ""}, {"message": "ok", "body": "x" * 16385}):
            with self.assertRaises(ValueError):
                checked_response(response, "body", 16384)

    def test_native_compile_error_repaired_once_and_real_ready_required(self):
        client = Mock()
        client.state.side_effect = [STATE, STATE, {**STATE, "generated": {"file": "generated.fx", "phase": "ready"}}]
        client.call.side_effect = [RuntimeError("error X3000: syntax error"), {"generated": {"file": "generated.fx"}}]
        provider = Mock()
        provider.complete.side_effect = [{"message": "test", "body": "bad"}, {"message": "fixed", "body": "return color;"}]
        result = generate_effect(client, 1, provider, STATE)
        self.assertIn("compiled and activated", result)
        self.assertIn("compiler_error", provider.complete.call_args.args[1])
        self.assertEqual(client.call.call_count, 2)

    def test_native_fx_failure_never_reported_as_applied(self):
        client = Mock()
        client.state.side_effect = [STATE, {**STATE, "generated": {"file": "generated.fx", "phase": "error", "message": "FX compiler failure"}}]
        client.call.return_value = {"generated": {"file": "generated.fx"}}
        provider = Mock()
        provider.complete.return_value = {"message": "ok", "body": "return color;"}
        with self.assertRaisesRegex(RuntimeError, "FX compiler failure"):
            generate_effect(client, 1, provider, STATE)
