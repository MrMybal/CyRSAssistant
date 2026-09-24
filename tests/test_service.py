import json
import subprocess
import unittest
from unittest.mock import patch

from companion.service import CliProvider, connect
from companion.provider import Provider


class ServiceTests(unittest.TestCase):
    def test_codex_missing_login_is_not_ready(self):
        with patch("companion.service.cli_path", return_value="codex.exe"), patch("companion.service.run_cli", return_value=subprocess.CompletedProcess([], 1, "", "secret")):
            with self.assertRaisesRegex(ValueError, "codex session missing"):
                connect({"provider": 0})

    def test_claude_requires_logged_in_flag(self):
        with patch("companion.service.cli_path", return_value="claude.exe"), patch("companion.service.run_cli", return_value=subprocess.CompletedProcess([], 0, '{"loggedIn": false}', "")):
            with self.assertRaisesRegex(ValueError, "claude session missing"):
                connect({"provider": 1})

    def test_local_cli_auth_is_not_claimed_as_remote_test(self):
        with patch("companion.service.cli_path", return_value="codex.exe"), patch("companion.service.run_cli", return_value=subprocess.CompletedProcess([], 0, "", "")):
            provider, status = connect({"provider": 0})
            self.assertIsInstance(provider, CliProvider)
            self.assertIn("first message", status)

    def test_api_requires_model_response(self):
        config = {"provider": 2, "endpoint": "http://127.0.0.1/chat/completions", "model": "test"}
        with patch.object(Provider, "complete", return_value={"connected": False}):
            with self.assertRaises(ValueError):
                connect(config)
        with patch.object(Provider, "complete", return_value={"connected": True}):
            self.assertIn("responded", connect(config)[1])

    def test_compact_inventory_keeps_original_ids(self):
        state = {"parameters": [{"id": 0, "readonly": True}, {"id": 1, "name": "Exposure", "effect": "test.fx", "type": "float", "readonly": False, "value": [0.0], "effect_description": "x" * 200000}], "techniques": []}
        provider = Provider({"endpoint": "http://localhost/test", "model": "test"})
        result = {"message": "ok", "changes": [{"kind": "parameter", "id": 1, "value": [0.2]}]}
        with patch.object(provider, "complete", return_value=result) as call:
            self.assertEqual(provider.plan("request", state), result)
            payload = json.loads(call.call_args.args[1])
            self.assertEqual(payload["parameters"][0]["id"], 1)
            self.assertNotIn("effect_description", payload["parameters"][0])


if __name__ == "__main__":
    unittest.main()
