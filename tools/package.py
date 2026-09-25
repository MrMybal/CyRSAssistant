"""Build either the developer distribution or a ready-to-extract ReShade install ZIP."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.search(r"project\(CyRSAssistant VERSION ([0-9.]+)", (ROOT / "CMakeLists.txt").read_text(encoding="utf-8-sig")).group(1)
RUNTIME_FILES = ("dxcompiler.dll", "dxil.dll", "LICENSE-LLVM.txt", "LICENSE-MS.txt")


def copy_licenses(destination):
    destination.mkdir(parents=True, exist_ok=True)
    for source, name in (("reshade/LICENSE.md", "ReShade.txt"), ("imgui/LICENSE.txt", "DearImGui.txt"), ("json/LICENSE.MIT", "nlohmann-json.txt")):
        shutil.copy2(ROOT / "third_party" / source, destination / name)
    shutil.copy2(Path(sys.base_prefix) / "LICENSE.txt", destination / "Python.txt")
    shutil.copy2(ROOT / "build/packaging-env/Lib/site-packages/pyinstaller-6.20.0.dist-info/licenses/COPYING.txt", destination / "PyInstaller.txt")


def installation_notes():
    return f"""CyRSAssistant {VERSION} - Windows x64

ENGLISH
Requires ReShade 6.8 with full add-on support in a 64-bit Windows game.

1. Close the game. Keep a copy of any previous CyRSAssistant installation.
2. Extract this ZIP next to the ReShade DLL, keeping its folder structure.
   CyRSAssistant.addon64, CyRSAssistantCompanion.exe and CyRSAssistantRuntime
   must be together. For engines with a launcher, use the game executable's
   actual folder, not the launcher's folder.
3. Start the game and open CyRSAssistant in the ReShade overlay.
4. In Connection, choose a provider and click Connect. Codex and Claude use
   their installed CLI and existing login. Alternatively, configure an
   OpenAI-compatible API or a local model. Python is bundled; no separate
   Python installation or manual service launch is required.
5. Write in Chat and click Send, or use Ctrl+Enter.

The interface defaults to English. French is available in Options > Language.
The language and permission mode are remembered per game. API keys are kept
in memory for the current session. This ZIP does not contain a preset or
replace your ReShade.ini.

FRANÇAIS
Nécessite ReShade 6.8 avec prise en charge complète des add-ons dans un jeu
Windows 64 bits.

1. Fermez le jeu. Conservez une copie de votre ancienne installation.
2. Extrayez ce ZIP à côté de la DLL ReShade, en conservant les sous-dossiers.
   CyRSAssistant.addon64, CyRSAssistantCompanion.exe et CyRSAssistantRuntime
   doivent rester ensemble. Si le jeu utilise un lanceur, choisissez le
   dossier du véritable exécutable du jeu.
3. Lancez le jeu et ouvrez CyRSAssistant dans l'overlay ReShade.
4. Pour le français : Options > Language > Français.
5. Dans Connexion, choisissez un fournisseur puis Connecter. Codex et Claude
   utilisent leur CLI installé et leur session existante. Vous pouvez aussi
   configurer une API compatible OpenAI ou un modèle local. Python est intégré ;
   aucune installation séparée ni aucun lancement manuel du service n'est requis.
6. Écrivez dans Tchat et cliquez sur Envoyer, ou utilisez Ctrl+Entrée.

La langue et les autorisations sont mémorisées par jeu. Les clés API restent
uniquement en mémoire pour la session. Ce ZIP ne contient pas de preset et
ne remplace pas votre ReShade.ini.

SOURCES / LICENCES
CyRSAssistant by Cyberalien - GPL-3.0-only. See LICENSE and THIRD_PARTY.md
in this folder, licenses/, and the licenses in ../CyRSAssistantRuntime/.
Source code and build instructions for this version:
https://github.com/MrMybal/CyRSAssistant/tree/v{VERSION}
https://github.com/MrMybal/CyRSAssistant/archive/refs/tags/v{VERSION}.zip
"""


def package(install=False):
    binary = ROOT / "build/bin/Release/CyRSAssistant.addon64"
    service = binary.with_name("CyRSAssistantCompanion.exe")
    if not binary.is_file() or not service.is_file():
        raise SystemExit("Build the add-on and companion first: tools/build.py and tools/build_service.py")
    suffix = "-windows-x64" if install else ""
    archive_path = ROOT / "dist" / f"CyRSAssistant-{VERSION}{suffix}.zip"
    archive_path.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cyrs-package-") as staging:
        destination = Path(staging) / f"CyRSAssistant-{VERSION}"
        destination.mkdir()
        for path in (binary, service):
            shutil.copy2(path, destination / path.name)
        runtime = destination / "CyRSAssistantRuntime"
        runtime.mkdir()
        for name in RUNTIME_FILES:
            shutil.copy2(binary.parent / "CyRSAssistantRuntime" / name, runtime / name)
        metadata = destination / "CyRSAssistant" if install else destination
        metadata.mkdir(exist_ok=True)
        for name in ("LICENSE", "THIRD_PARTY.md"):
            shutil.copy2(ROOT / name, metadata / name)
        copy_licenses(metadata / "licenses")
        shutil.copy2(ROOT / "tools/dependencies.lock.json", metadata / "dependencies.lock.json")
        if install:
            (metadata / "INSTALL.txt").write_text(installation_notes(), encoding="utf-8")
        else:
            for name in ("README.md", "README.fr.md"):
                shutil.copy2(ROOT / name, destination / name)
            shutil.copytree(ROOT / "companion", destination / "companion", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copytree(ROOT / "docs", destination / "docs", ignore=shutil.ignore_patterns("validation-*.md"))
            for module, name in (("companion.mcp", "run_mcp.py"), ("companion", "run_companion.py")):
                (destination / name).write_text(f'import runpy\nrunpy.run_module("{module}", run_name="__main__")\n', encoding="utf-8")
            sources = destination / "source"
            sources.mkdir()
            for name in ("src", "companion", "tools", "tests"):
                shutil.copytree(ROOT / name, sources / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            for name in ("CMakeLists.txt", "README.md", "README.fr.md", "LICENSE", "THIRD_PARTY.md"):
                shutil.copy2(ROOT / name, sources / name)
            shutil.copytree(destination / "docs", sources / "docs")
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            base = destination if install else destination.parent
            for path in sorted(destination.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(base))
    archive_path.with_suffix(".zip.sha256").write_text(hashlib.sha256(archive_path.read_bytes()).hexdigest() + "  " + archive_path.name + "\n", encoding="ascii")
    print(archive_path)
    return archive_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Create a runtime-only ZIP to extract next to ReShade")
    package(parser.parse_args().install)
