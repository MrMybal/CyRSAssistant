import ast
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess
from threading import Barrier
import unittest
from unittest.mock import Mock, patch

from companion.localization import CATALOGS, localized, normalize, render_message, tr, using_language, validate_catalogs
from companion.chat import respond
from companion.permissions import describe
from companion.service import answer, connect


class LocalizationTests(unittest.TestCase):
    def test_default_unsupported_and_regional_languages(self):
        self.assertEqual(tr("Send"), "Send")
        self.assertEqual(normalize(None), "en")
        self.assertEqual(normalize("not-supported"), "en")
        self.assertEqual(normalize("fr-FR"), "fr")
        self.assertEqual(normalize("FR_fr"), "fr")
        with using_language("fr-FR"):
            self.assertEqual(tr("API key"), "Clé API")
            self.assertEqual(tr("unknown diagnostic {from compiler}"), "unknown diagnostic {from compiler}")
        self.assertEqual(tr("Send"), "Send")

    def test_catalog_coverage_and_format_arguments(self):
        validate_catalogs()
        self.assertEqual(set(CATALOGS["en"]["messages"]), set(CATALOGS["fr"]["messages"]))
        broken = copy.deepcopy(CATALOGS)
        broken["fr"]["messages"]["Working... %llu s"] = "Traitement... %s"
        with self.assertRaises(ValueError):
            validate_catalogs(broken)
        broken = copy.deepcopy(CATALOGS)
        broken["fr"]["messages"]["Request failed: {error}"] = "Erreur : {secret}"
        with self.assertRaises(ValueError):
            validate_catalogs(broken)

    def test_translations_cannot_add_unsafe_printf_directives(self):
        for translation in ("Envoyer %n", "Envoyer %", "Envoyer %*s", "Envoyer %Q"):
            broken = copy.deepcopy(CATALOGS)
            broken["fr"]["messages"]["Send"] = translation
            with self.assertRaises(ValueError):
                validate_catalogs(broken)

    def test_all_localized_call_sites_exist_in_catalog(self):
        root = Path(__file__).resolve().parents[1]
        keys = set(CATALOGS["en"]["messages"])
        for path in (root / "companion").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("_", "tr") and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    self.assertIn(node.args[0].value, keys, path.name)
        source = (root / "src/addon.cpp").read_text(encoding="utf-8-sig")
        for literal in re.findall(r'(?:\btr|\bui_label)\(("(?:[^"\\]|\\.)*")\)', source):
            self.assertIn(json.loads(literal), keys)

    def test_concurrent_requests_do_not_share_language(self):
        barrier = Barrier(2)
        @localized(0)
        def request(state):
            barrier.wait(timeout=5)
            return str(tr("Send"))
        with ThreadPoolExecutor(max_workers=2) as pool:
            en = pool.submit(request, {"language": "en"})
            fr = pool.submit(request, {"language": "fr"})
            self.assertEqual(en.result(), "Send")
            self.assertEqual(fr.result(), "Envoyer")
        self.assertEqual(tr("Send"), "Send")

    def test_saved_status_rerenders_without_reconnecting(self):
        with patch("companion.service.cli_path", return_value="codex.exe"), patch("companion.service.run_cli", return_value=subprocess.CompletedProcess([], 0, "", "")):
            _, status = connect({"provider": 0, "language": "fr"})
        self.assertIn("premier envoi", status)
        self.assertIn("first message", render_message(status, "en"))
        self.assertIn("premier envoi", render_message(status, "fr"))

    def test_language_switch_keeps_history_and_shader_identifiers(self):
        state = {"session": "test", "runtime": 1, "generation": 0, "revision": 0,
                 "prompt": {"id": 1, "pending": True, "mode": 3, "text": "Hello"},
                 "conversation": [{"role": "user", "content": "Appelons ce rendu Ambre"}, {"role": "assistant", "content": "D'accord"}],
                 "parameters": [{"id": 0, "name": "Threshold", "effect": "Bloom.fx", "type": "float", "value": [1.25]}],
                 "techniques": []}
        original = copy.deepcopy(state)
        client, provider = Mock(), Mock()
        provider.complete.return_value = {"message": "reply", "action": "reply"}
        for language, name in (("en", "English"), ("fr", "Français")):
            state["language"] = language
            respond(client, 1, provider, state)
            system, encoded = provider.complete.call_args.args
            self.assertIn(name, system)
            context = json.loads(encoded)
            self.assertEqual(context["conversation"], [{**m, "mode": 0} for m in original["conversation"]])
            parameter = context["runtime"]["parameters"]["items"][0]
            self.assertEqual((parameter["name"], parameter["effect"], parameter["value"]), ("Threshold", "Bloom.fx", [1.25]))
        self.assertEqual(state["conversation"], original["conversation"])
        client.call.assert_not_called()

    def test_approval_previews_and_failures_follow_language(self):
        for code, preview, failure in (("en", "Read and send", "Request failed"), ("fr", "Lire et transmettre", "Échec de la demande")):
            state = {"language": code, "session": "s", "prompt": {"id": 1, "mode": 3}}
            self.assertTrue(describe("read_effect_source", {"file": "Bloom.fx"}, state).startswith(preview))
            client = Mock()
            with patch("companion.service.respond", side_effect=ValueError("diagnostic")):
                answer(client, 1, Mock(), state)
            self.assertIn(failure, client.call.call_args.kwargs["message"])


if __name__ == "__main__":
    unittest.main()
