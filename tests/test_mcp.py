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
        result = subprocess.run([sys.executable, "-m", "companion.mcp"], input="\n".join(json.dumps(m) for m in messages) + "\n", capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(responses), 3)
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual({t["name"] for t in responses[1]["result"]["tools"]}, {"cyrs_list_sessions", "cyrs_get_state", "cyrs_capture_frame", "cyrs_list_game_shaders", "cyrs_inspect_game_shader"})
        self.assertIn("error", responses[2])

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
