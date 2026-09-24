"""Pinned official Microsoft DXC runtime, isolated from a game's own compiler DLLs."""
import hashlib
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = "https://api.nuget.org/v3-flatcontainer/microsoft.direct3d.dxc/1.8.2505.32/microsoft.direct3d.dxc.1.8.2505.32.nupkg"
SHA256 = "c6e82b70c14552f1dd58e4a79c93eeab1567eeb0a9ee63a51564c410429bce3e"

def prepare():
    archive = ROOT / "build/dxc.nupkg"
    archive.parent.mkdir(exist_ok=True)
    if not archive.exists():
        with urllib.request.urlopen(URL, timeout=60) as response:
            archive.write_bytes(response.read())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError("DXC package SHA256 mismatch")
    destination = ROOT / "third_party/dxc"
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for source in ("build/native/bin/x64/dxcompiler.dll", "build/native/bin/x64/dxil.dll", "LICENSE-LLVM.txt", "LICENSE-MS.txt"):
            (destination / Path(source).name).write_bytes(bundle.read(source))
    for output in (ROOT / "build/bin/Release/CyRSAssistantRuntime", ROOT / "build/Release/CyRSAssistantRuntime"):
        output.mkdir(parents=True, exist_ok=True)
        for file in destination.iterdir():
            shutil.copy2(file, output / file.name)

if __name__ == "__main__":
    prepare()
