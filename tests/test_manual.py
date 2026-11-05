import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
import unittest

from tools.generate_manual import ASSETS, ROOT, generate, load_books, svg_flow


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.refs = []
        self.lang = None
        self.sources = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise AssertionError("Duplicate HTML ID")
            self.ids.add(attrs["id"])
        if tag == "html": self.lang = attrs.get("lang")
        if tag == "a": self.refs.append(attrs.get("href", ""))
        if tag in ("img", "script", "link") and ("src" in attrs or "href" in attrs):
            self.sources.append(attrs.get("src", attrs.get("href")))


class ManualTests(unittest.TestCase):
    def test_every_chapter_and_block_has_both_languages(self):
        books = load_books()
        self.assertEqual([b["code"] for b in books], ["en", "fr"])
        self.assertEqual(len(books[0]["chapters"]), 21)
        for en, fr in zip(books[0]["chapters"], books[1]["chapters"]):
            self.assertEqual(en["id"], fr["id"])
            self.assertEqual([b["type"] for b in en["blocks"]], [b["type"] for b in fr["blocks"]])
        self.assertIn("English", books[0]["name"])
        self.assertEqual(books[1]["ui"]["contents"], "Sommaire")

    def test_html_is_self_contained_with_working_links_and_images(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            generate(output=output)
            for language in ("en", "fr"):
                parser = Page()
                text = (output / f"index.{language}.html").read_text(encoding="utf-8")
                parser.feed(text)
                self.assertEqual(parser.lang, language)
                for ref in parser.refs:
                    if ref.startswith("#"):
                        self.assertIn(ref[1:], parser.ids)
                    elif ref:
                        self.assertTrue((output / ref).is_file(), ref)
                for ref in parser.sources:
                    self.assertNotRegex(ref, r"^(?:https?:|//)")
                    self.assertTrue((output / ref).is_file(), ref)
                self.assertNotIn("<script src=", text)
                self.assertIn("beforeprint", text)
                self.assertIn('type="search"', text)
                self.assertEqual(len([i for i in parser.ids if i in {c["id"] for c in load_books()[0]["chapters"]}]), 21)
            self.assertEqual((output / "index.html").read_bytes(), (output / "index.en.html").read_bytes())
            for key, path in ASSETS.items():
                self.assertEqual((output / "assets" / (key + ".png")).read_bytes(), path.read_bytes())

    def test_diagrams_preserve_both_language_labels_and_escape_markup(self):
        flow = {"title": "Example <script>", "items": ["A & B", "Then <next>"]}
        svg = svg_flow(flow)
        self.assertIn("A &amp; B", svg)
        self.assertIn("&lt;next&gt;", svg)
        self.assertNotIn("<script>", svg)

    def test_missing_translation_or_link_fails_the_build(self):
        books = load_books()
        for corruption in ("chapter", "ui", "link", "image"):
            broken = copy.deepcopy(books)
            if corruption == "chapter": broken[1]["chapters"].pop()
            elif corruption == "ui": broken[1]["ui"].pop("search")
            elif corruption == "link": broken[0]["chapters"][0]["blocks"][-1]["chapters"] = ["not-a-chapter"]
            else: broken[0]["chapters"][0]["blocks"].append({"type":"image","asset":"../../secret","caption":"x"})
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "docs/manual").mkdir(parents=True)
                for book in broken:
                    (root / "docs/manual" / (book["code"] + ".json")).write_text(json.dumps(book), encoding="utf-8")
                with self.assertRaises(ValueError): load_books(root)

    def test_native_header_contains_both_languages_without_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            header = Path(temp) / "manual_data.hpp"
            generate(header=header)
            text = header.read_text(encoding="utf-8")
            self.assertIn('{"en", document_', text)
            self.assertIn('{"fr", document_', text)
            self.assertNotIn(str(ROOT), text)
            self.assertNotIn("C:/Users/", text)
            self.assertIn("UTF-8", text)


if __name__ == "__main__":
    unittest.main()
