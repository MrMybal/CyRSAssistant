import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import package as delivery


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = delivery.ROOT
        shutil.copytree(source / "LICENCES", self.root / "LICENCES")
        for folder in ("src", "companion", "tools", "tests", "assets", "docs"):
            (self.root / folder).mkdir()
            (self.root / folder / "example.txt").write_text("example")
        for name in ("LICENSE", "THIRD_PARTY.md", "README.md", "README.fr.md", "CMakeLists.txt"):
            shutil.copyfile(source / name, self.root / name)
        for name in ("runtime-licenses.lock.json", "dependencies.lock.json"):
            shutil.copyfile(source / "tools" / name, self.root / "tools" / name)
        self.binary = self.root / "build/bin/Release/CyRSAssistant.addon64"
        self.binary.parent.mkdir(parents=True)
        self.binary.write_bytes(f"CyRSAssistant {delivery.VERSION} - Cyberalien".encode())
        self.service = self.binary.with_name("CyRSAssistantCompanion.exe")
        self.service.write_bytes(b"frozen companion test fixture")
        runtime = self.binary.parent / "CyRSAssistantRuntime"
        runtime.mkdir()
        for name in delivery.RUNTIME_FILES:
            (runtime / name).write_bytes(b"runtime fixture")
        originals = {"ReShade.txt": "third_party/reshade/LICENSE.md",
                     "DearImGui.txt": "third_party/imgui/LICENSE.txt",
                     "nlohmann-json.txt": "third_party/json/LICENSE.MIT",
                     "DXC-LLVM.txt": "build/bin/Release/CyRSAssistantRuntime/LICENSE-LLVM.txt",
                     "DXC-Microsoft.txt": "build/bin/Release/CyRSAssistantRuntime/LICENSE-MS.txt"}
        for name, relative in originals.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / "LICENCES" / name, target)
        lock = json.loads((self.root / "tools/runtime-licenses.lock.json").read_text())
        self.manifest = {"application_version": delivery.VERSION,
            "components": {key: lock[key] for key in ("python", "pyinstaller", "openssl", "expat", "zlib")},
            "sha256": hashlib.sha256(self.service.read_bytes()).hexdigest(),
            "license_sha256": {name: hashlib.sha256((self.root / "LICENCES" / name).read_bytes()).hexdigest()
                               for name in ("Python.txt", "PyInstaller.txt")}}
        self.save_manifest()
        self.addCleanup(patch.stopall)
        patch.object(delivery, "ROOT", self.root).start()

    def save_manifest(self):
        self.service.with_suffix(".build.json").write_text(json.dumps(self.manifest))

    def package(self, install=True):
        with contextlib.redirect_stdout(io.StringIO()):
            return delivery.package(install)

    def test_install_contains_all_original_licenses_at_zip_root(self):
        with zipfile.ZipFile(self.package()) as archive:
            self.assertIsNone(archive.testzip())
            for name in delivery.REQUIRED_LICENSES:
                self.assertEqual(archive.read("LICENCES/" + name), (self.root / "LICENCES" / name).read_bytes())
            self.assertIn("LICENCES/SOURCES.txt", archive.namelist())
            self.assertIn("(../LICENCES/SOURCES.txt)", archive.read("CyRSAssistant/THIRD_PARTY.md").decode("utf-8"))
            self.assertIn("FRAN\u00c7AIS", archive.read("CyRSAssistant/INSTALL.txt").decode("utf-8"))
            self.assertIn("LICENCES/AssistantRuntime-Notices.txt", archive.namelist())
            self.assertNotIn("CyRSAssistantCompanion.build.json", archive.namelist())

    def test_developer_zip_contains_notices_with_buildable_sources(self):
        prefix = f"CyRSAssistant-{delivery.VERSION}/"
        with zipfile.ZipFile(self.package(False)) as archive:
            for name in delivery.REQUIRED_LICENSES:
                self.assertEqual(archive.read(prefix + "LICENCES/" + name), archive.read(prefix + "source/LICENCES/" + name))
            self.assertIn(prefix + "source/tools/runtime-licenses.lock.json", archive.namelist())

    def test_user_configuration_and_catalog_are_preserved_and_excluded(self):
        private = {"ReShade.ini": b"[CYRSASSISTANT]\nLanguage=fr\nPermissionMode=1\n",
                   "CyRSAssistant/library/catalog.json": b'{"effects": []}',
                   "reshade-shaders/Shaders/User.fx": b"user shader"}
        for name, data in private.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        with zipfile.ZipFile(self.package()) as archive:
            for name, data in private.items():
                self.assertNotIn(name, archive.namelist())
                self.assertEqual((self.root / name).read_bytes(), data)

    def test_stale_companion_cannot_replace_an_existing_archive(self):
        archive = self.package()
        original = archive.read_bytes()
        self.service.write_bytes(b"changed executable")
        with self.assertRaisesRegex(ValueError, "Companion build is stale"):
            self.package()
        self.assertEqual(archive.read_bytes(), original)

    def test_rejects_old_addon_version(self):
        self.binary.write_bytes(b"CyRSAssistant 0.7.1 - Cyberalien")
        with self.assertRaisesRegex(ValueError, "Add-on build is stale"):
            self.package()

    def test_missing_notice_stops_packaging(self):
        (self.root / "LICENCES/SOURCES.txt").unlink()
        with self.assertRaisesRegex(ValueError, "Missing required license"):
            self.package()

    def test_license_change_after_build_is_rejected(self):
        (self.root / "LICENCES/Python.txt").write_text("wrong interpreter license")
        with self.assertRaisesRegex(ValueError, "License changed since"):
            self.package()

    def test_runtime_version_mismatch_is_rejected(self):
        self.manifest["components"]["python"] = "3.12.0"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "licensed component versions"):
            self.package()

    def test_changed_upstream_notice_is_rejected(self):
        (self.root / "LICENCES/OpenSSL.txt").write_text("changed upstream text")
        with self.assertRaisesRegex(ValueError, "pinned upstream text"):
            self.package()


if __name__ == "__main__":
    unittest.main()
