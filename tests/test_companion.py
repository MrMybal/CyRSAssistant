import copy
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

from companion import catalog
from companion.provider import Provider, validate_plan
from companion.transport import Client, read_exact


STATE = {"parameters": [{"id": 0, "effect": "Color.fx", "name": "Exposure", "type": "float", "readonly": False, "value": [0.5], "min": 0, "max": 1}],
         "techniques": [{"id": 0, "effect": "Color.fx", "name": "Color", "value": False}]}
PLAN = {"message": "Réglage proposé", "changes": [{"kind": "parameter", "id": 0, "value": [0.7]}]}


class CatalogueTests(unittest.TestCase):
    def test_scan_delta_description_invalidation_and_portability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shaders = root / "game1" / "shaders"
            shaders.mkdir(parents=True)
            (shaders / "Color.fx").write_text('#include "Common.fxh"\ntechnique Color {}')
            (shaders / "Common.fxh").write_text("// original dependency")
            library = root / "game1" / "library"
            initial = catalog.scan([(shaders, True)], library, STATE)
            self.assertEqual(len(initial["changes"]["added"]), 2)
            effect = initial["effects"][0]
            self.assertEqual(effect["runtime_match"], "loaded")
            catalog.store_description(library, effect, "Color control", "test")
            unchanged = catalog.scan([(shaders, True)], library, STATE)
            self.assertEqual(unchanged["changes"], {"added": [], "modified": [], "removed": []})
            self.assertEqual(unchanged["effects"][0]["description"]["text"], "Color control")
            exported = root / "portable.json"
            catalog.export_library(library, exported)
            self.assertNotIn(str(root), exported.read_text())
            other = root / "game2" / "library"
            self.assertEqual(catalog.import_library(other, exported), 1)
            reused = catalog.scan([(shaders, True)], other, STATE)
            self.assertIsNotNone(reused["effects"][0]["description"])
            (shaders / "Common.fxh").write_text("// changed dependency")
            changed = catalog.scan([(shaders, True)], library, STATE)
            self.assertEqual(len(changed["changes"]["modified"]), 1)
            self.assertIsNone(changed["effects"][0]["description"])
            (shaders / "Color.fx").unlink()
            deleted = catalog.scan([(shaders, True)], library, STATE)
            self.assertEqual(len(deleted["changes"]["removed"]), 1)

    def test_duplicate_filename_not_matched_to_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder in ("a", "b"):
                (root / folder).mkdir()
                (root / folder / "Color.fx").write_text("// shader")
            result = catalog.scan([(root, True)], root / "library", STATE)
            self.assertTrue(all(e["runtime_match"] == "ambiguous" for e in result["effects"]))

    def test_import_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            imported = root / "bad.json"
            catalog.write_json(imported, {"schema_version": 1, "descriptions": [{"fingerprint": "../../outside", "text": "bad"}]})
            with self.assertRaises(ValueError):
                catalog.import_library(root / "library", imported)

    def test_missing_root_is_not_a_complete_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = catalog.scan([(root / "absent", True)], root / "library")
            self.assertFalse(result["complete"])


class PlanTests(unittest.TestCase):
    def test_valid_plan(self):
        validate_plan(PLAN, STATE)

    def test_invalid_plans(self):
        for value in ([True], [2.0], [float("nan")], [0.1, 0.2], "0.5"):
            plan = copy.deepcopy(PLAN)
            plan["changes"][0]["value"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_plan(plan, STATE)
        plan = copy.deepcopy(PLAN)
        plan["changes"][0]["id"] = 99
        with self.assertRaises(ValueError):
            validate_plan(plan, STATE)

    def test_dynamic_parameter_refused(self):
        state = copy.deepcopy(STATE)
        state["parameters"][0]["readonly"] = True
        with self.assertRaises(ValueError):
            validate_plan(PLAN, state)

    def test_provider_http_contract(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                data = json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(PLAN)}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {"CYRS_API_URL": f"http://127.0.0.1:{server.server_port}/v1/chat/completions", "CYRS_MODEL": "test", "CYRS_API_KEY": ""}):
                self.assertEqual(Provider().plan("Plus clair", STATE), PLAN)
            self.assertEqual(received[0]["response_format"], {"type": "json_object"})
            self.assertNotIn("base_path", received[0]["messages"][1]["content"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_remote_plaintext_endpoint_refused(self):
        with patch.dict(os.environ, {"CYRS_API_URL": "http://example.com/chat/completions", "CYRS_MODEL": "test"}):
            with self.assertRaises(ValueError):
                Provider()


class TransportTests(unittest.TestCase):
    def test_truncated_frame(self):
        with self.assertRaises(ConnectionError):
            read_exact(io.BytesIO(b"x"), 2)

    @unittest.skipUnless(os.name == "nt" and Path("build/Release/bridge_harness.exe").exists(), "Build the native harness first")
    def test_real_named_pipe_and_request_deduplication(self):
        process = subprocess.Popen(["build/Release/bridge_harness.exe"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            pipe = process.stdout.readline().strip()
            self.assertTrue(pipe.startswith("\\\\.\\pipe\\CyRSAssistant-"))
            client = Client(pipe)
            first = client.call("echo", runtime=1, request_id="fixed", text="é" * 40000)
            second = client.call("echo", runtime=1, request_id="fixed", text="é" * 40000)
            self.assertEqual(first, second)
            self.assertEqual(first["processed"], 1)
            with self.assertRaisesRegex(RuntimeError, "reused"):
                client.call("echo", runtime=1, request_id="fixed", text="changed")
            with self.assertRaisesRegex(RuntimeError, "Unsupported protocol"):
                client.call("echo", runtime=1, protocol=2)
            with self.assertRaisesRegex(RuntimeError, "timeout"):
                client.call("echo", runtime=999)
            final = client.call("echo", runtime=1)
            self.assertEqual(final["processed"], 2)
        finally:
            process.communicate("\n", timeout=5)
            self.assertEqual(process.returncode, 0)


if __name__ == "__main__":
    unittest.main()
