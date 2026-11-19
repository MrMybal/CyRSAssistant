import json
import subprocess
import sys
import unittest
from unittest.mock import patch
from companion.mcp import Server


class MCPTests(unittest.TestCase):
    def test_stdio_initialization_and_read_only_tools(self):
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "cyrs_apply_patch", "arguments": {}}},
        ]
        process = subprocess.Popen([sys.executable, "-m", "companion.mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        try:
            responses = []
            for message in messages:
                process.stdin.write(json.dumps(message)+"\n"); process.stdin.flush()
                if "id" in message: responses.append(json.loads(process.stdout.readline()))
            self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-06-18")
            available = {t["name"] for t in responses[1]["result"]["tools"]}
            self.assertTrue({"cyrs_get_state", "cyrs_get_parameters", "cyrs_get_effects"}.issubset(available))
            self.assertTrue(responses[2]["result"]["isError"])
            self.assertIn("AccessDenied", responses[2]["result"]["content"][0]["text"])
        finally:
            process.stdin.close(); process.wait(timeout=10)
            process.stdout.close(); process.stderr.close()

    def test_write_tool_preserves_stale_version_for_native_validation(self):
        server = Server("\\\\.\\pipe\\CyRSAssistant-123", allow_write=True)
        server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        arguments = {"session": "s", "runtime": 1, "generation": 2, "revision": 3,
                     "changes": [{"kind": "technique", "id": 0, "value": True}]}
        with patch("companion.mcp.Client") as client:
            client.return_value.call.return_value = {"ok": True}
            response = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "cyrs_apply_patch", "arguments": arguments}})
            client.return_value.call.assert_called_once_with("apply_patch", **arguments)
            self.assertFalse(response["result"]["isError"])

    def test_protocol_fields_cannot_be_injected_as_arguments(self):
        server = Server(allow_write=True)
        server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        response = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "cyrs_get_state", "arguments": {"runtime": 1, "method": "save_preset"}}})
        self.assertIn("error", response)

    def test_generate_effect_accepts_optional_controls_and_legacy_body(self):
        server = Server(r"\\.\pipe\CyRSAssistant-123", allow_write=True)
        server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        basic = {"session": "s", "runtime": 1, "generation": 2, "revision": 3, "body": "return color;"}
        for extra in ({}, {"name": "Bloom", "parameters": [], "replace_effect": "OldBloom.fx"}):
            args = {**basic, **extra}
            with patch("companion.mcp.Client") as client:
                client.return_value.call.return_value = {"ok": True}
                result = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "cyrs_generate_effect", "arguments": args}})
                self.assertNotIn("error", result)
                client.return_value.call.assert_called_once_with("generate_effect", **args)
