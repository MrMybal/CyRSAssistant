"""Build with VS 2022; normalize duplicate Windows environment key casing."""
import os
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
from bootstrap_dxc import prepare
prepare()
cmake = shutil.which("cmake")
if not cmake:
    vswhere = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    install = subprocess.check_output([str(vswhere), "-latest", "-products", "*", "-property", "installationPath"], text=True).strip()
    cmake = str(Path(install) / "Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe")
env = {k.upper(): v for k, v in os.environ.items()}
subprocess.run([cmake, "--fresh", "-S", str(root), "-B", str(root / "build"), "-A", "x64"], env=env, check=True)
subprocess.run([cmake, "--build", str(root / "build"), "--config", "Release"], env=env, check=True)
subprocess.run([str(Path(cmake).with_name("ctest.exe")), "--test-dir", str(root / "build"), "-C", "Release", "--output-on-failure"], env=env, check=True)
