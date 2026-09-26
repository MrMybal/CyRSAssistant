"""Build the background executable after installing PyInstaller in build/packaging-env."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
subprocess.run([str(root / "build/packaging-env/Scripts/python.exe"), "-m", "PyInstaller",
    "--noconfirm", "--clean", "--onefile", "--noconsole", "--name", "CyRSAssistantCompanion",
    "--icon", str(root / "assets/cyrsassistant-logo.ico"),
    "--paths", str(root), "--add-data", str(root / "companion/locales") + ";companion/locales", "--distpath", str(root / "build/bin/Release"),
    "--workpath", str(root / "build/pyinstaller"), "--specpath", str(root / "build"),
    str(root / "tools/service_entry.py")], cwd=root, check=True)
