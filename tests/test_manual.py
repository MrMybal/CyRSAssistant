"""Verify the actual CyDoc export, not a hand-authored HTML imitation."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from tools.build_help import ROOT, build, validate, fingerprint

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.assets = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("img", "script", "link") and ("src" in attrs or "href" in attrs):
            self.assets.append(attrs.get("src", attrs.get("href")))

class ManualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try: cls.output = validate()
        except (ValueError, FileNotFoundError): cls.output = build(check=True)
        cls.data = json.loads((cls.output / "manifest.json").read_text(encoding="utf-8"))
    def test_complete_translations_and_common_addresses(self):
        self.assertEqual(self.data["defaultLocale"], "en")
        books = {lang: {p["id"]: p for p in self.data["pages"] if p["locale"] == lang} for lang in ("en", "fr")}
        self.assertEqual(set(books["en"]), set(books["fr"]))
        for identity, en in books["en"].items():
            fr = books["fr"][identity]
            self.assertEqual({h["id"] for h in en["headings"]}, {h["id"] for h in fr["headings"]}, identity)
            self.assertEqual(re.findall(r'data-cydoc-id="([^"]+)"', en["html"]), re.findall(r'data-cydoc-id="([^"]+)"', fr["html"]))
        report = json.loads((self.output / "translation-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["current"], 26)
        for kind in ("missing", "outdated", "untracked"): self.assertFalse(report[kind])
    def test_images_diagrams_and_only_required_module(self):
        self.assertEqual([p.name for p in self.output.glob("media-*.js")], ["media-image.js"])
        self.assertFalse((ROOT / "node_modules/three").exists())
        for locale in ("en", "fr"):
            pages = [p for p in self.data["pages"] if p["locale"] == locale and p["kind"] != "source"]
            self.assertEqual(sum(p["html"].count('class="diagram"') for p in pages), 8)
        for relative in ("screenshots/chat-preview.png", "screenshots/connection-preview.png"):
            self.assertEqual((self.output / "assets" / relative).read_bytes(), (ROOT / "assets" / relative).read_bytes())
    def test_reader_resources_are_local_and_complete(self):
        for file in self.output.glob("*.html"):
            parser = Links(); parser.feed(file.read_text(encoding="utf-8"))
            for src in parser.assets:
                self.assertNotRegex(src, r"^(https?:|//)")
                self.assertTrue((self.output / src).is_file(), src)
        for page in self.data["pages"]:
            for asset in page.get("assets", []):
                self.assertTrue((self.output / asset).is_file(), asset)
        self.assertIn("CyDoc", (self.output / "LICENSE.CyDoc.txt").read_text(encoding="utf-8"))
        self.assertIn("legacy.js", (self.output / "index.fr.html").read_text(encoding="utf-8"))
    def test_source_scope_is_distributable_code_only(self):
        files = {p["source"].split(":")[0] for p in self.data["pages"] if p["kind"] == "source"}
        self.assertTrue(files)
        for name in files:
            self.assertTrue(name.startswith(("src/", "companion/")), name)
            self.assertTrue((ROOT / name).is_file(), name)
            self.assertNotIn("third_party", name)
            self.assertNotIn("__pycache__", name)
    def test_cydoc_public_core_validates_routes_search_and_fallback(self):
        script = """
import { createDocumentation, createLink, parseLink, hasAnchor } from 'cydoc';
import fs from 'node:fs';
const data=JSON.parse(fs.readFileSync('build/help/manifest.json','utf8'));
const docs=createDocumentation(data);
if(!docs.search('threshold','en').length || !docs.search('précompil','fr').length) throw Error('Search failed');
for(const page of data.pages) for(const link of page.links || []) {
  if(!link.startsWith('#/')) continue;
  const route=parseLink(link), target=docs.resolve(route.pageId,route.locale);
  if(!target || (route.anchor && !hasAnchor(target.page,route.anchor))) throw Error('Broken '+link);
}
if(docs.canonicalRoute({locale:'fr',pageId:'quickstart'}).pageId!=='install') throw Error('Alias');
const fallback=createDocumentation({...data,pages:data.pages.filter(p=>!(p.id==='start'&&p.locale==='fr'))}).resolve('start','fr');
if(!fallback.fallback || fallback.page.locale!=='en') throw Error('Fallback');
const url=createLink({locale:'fr',pageId:'connect',anchor:'overview',state:{media:'connection-preview'}},'file:///C:/Games/Example/index.html');
if(parseLink(url.slice(url.indexOf('#'))).state.media!=='connection-preview') throw Error('Media route');
"""
        subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT, check=True)
    def test_stale_export_is_rejected(self):
        with patch("tools.build_help.fingerprint", return_value="different-inputs"):
            with self.assertRaisesRegex(ValueError, "stale"): validate()
    def test_native_catalog_contains_no_private_build_paths(self):
        text = (ROOT / "build/generated/manual_data.hpp").read_text(encoding="utf-8")
        self.assertNotIn(str(ROOT), text)
        self.assertIn('"start"', text.replace(chr(92) + '"', '"'))

if __name__ == "__main__": unittest.main()
