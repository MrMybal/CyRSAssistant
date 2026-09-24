"""Assemble a local test distribution without installing into any game."""
from pathlib import Path
import shutil
import zipfile
import tempfile
import sys
import hashlib

root = Path(__file__).resolve().parents[1]
binary = root / "build/bin/Release/CyRSAssistant.addon64"
if not binary.exists():
    raise SystemExit("Build the add-on first")
staging = tempfile.TemporaryDirectory(prefix="cyrs-package-")
destination = Path(staging.name) / "CyRSAssistant-0.7.0"
destination.mkdir(parents=True, exist_ok=True)
shutil.copy2(binary, destination / binary.name)
service = binary.with_name("CyRSAssistantCompanion.exe")
if not service.exists():
    raise SystemExit("Build the service first: python tools/build_service.py")
shutil.copy2(service, destination / service.name)
shutil.copytree(binary.parent / "CyRSAssistantRuntime", destination / "CyRSAssistantRuntime", dirs_exist_ok=True)
shutil.copytree(root / "companion", destination / "companion", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
shutil.copytree(root / "docs", destination / "docs", ignore=shutil.ignore_patterns("validation-*.md"))
shutil.copy2(root / "README.md", destination / "README.md")
for name in ("README.fr.md", "LICENSE", "THIRD_PARTY.md"):
    shutil.copy2(root / name, destination / name)
licenses = destination / "licenses"
licenses.mkdir(exist_ok=True)
for source, name in [("reshade/LICENSE.md", "ReShade.txt"), ("imgui/LICENSE.txt", "DearImGui.txt"), ("json/LICENSE.MIT", "nlohmann-json.txt")]:
    shutil.copy2(root / "third_party" / source, licenses / name)
shutil.copy2(Path(sys.base_prefix) / "LICENSE.txt", licenses / "Python.txt")
shutil.copy2(root / "build/packaging-env/Lib/site-packages/pyinstaller-6.20.0.dist-info/licenses/COPYING.txt", licenses / "PyInstaller.txt")
shutil.copy2(root / "tools/dependencies.lock.json", destination / "dependencies.lock.json")
for module, filename in [("companion.mcp", "run_mcp.py"), ("companion", "run_companion.py")]:
    (destination / filename).write_text(f'import runpy\nrunpy.run_module("{module}", run_name="__main__")\n', encoding="utf-8")
sources = destination / "source"
sources.mkdir()
for name in ("src", "companion", "tools", "tests"):
    shutil.copytree(root / name, sources / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
for name in ("CMakeLists.txt", "README.md", "README.fr.md", "LICENSE", "THIRD_PARTY.md"):
    shutil.copy2(root / name, sources / name)
shutil.copytree(destination / "docs", sources / "docs")
archive_path = root / "dist/CyRSAssistant-0.7.0.zip"
archive_path.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(destination.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            archive.write(path, path.relative_to(destination.parent))
archive_path.with_suffix(".zip.sha256").write_text(hashlib.sha256(archive_path.read_bytes()).hexdigest() + "  " + archive_path.name + "\n", encoding="ascii")
staging.cleanup()
print(archive_path)
