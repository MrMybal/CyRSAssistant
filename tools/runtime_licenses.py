"""Record the interpreter and notices used to freeze the companion, without local paths."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import pyexpat
import re
import ssl
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]

def runtime_info():
    return {"python": sys.version.split()[0], "pyinstaller": importlib.metadata.version("pyinstaller"),
            "openssl": ssl.OPENSSL_VERSION, "expat": pyexpat.EXPAT_VERSION, "zlib": zlib.ZLIB_RUNTIME_VERSION}

def verify():
    expected = json.loads((ROOT / "tools/runtime-licenses.lock.json").read_text(encoding="utf-8"))
    actual = runtime_info()
    for name, value in actual.items():
        if expected[name] != value:
            raise ValueError(f"{name} differs from the licensed runtime: expected {expected[name]}, got {value}. Update the runtime lock and notices together.")
    dist = importlib.metadata.distribution("pyinstaller")
    copying = next(f for f in dist.files if str(f).endswith("licenses/COPYING.txt"))
    originals = {"Python.txt": Path(sys.base_prefix) / "LICENSE.txt", "PyInstaller.txt": Path(dist.locate_file(copying))}
    for name, path in originals.items():
        if (ROOT / "LICENCES" / name).read_bytes() != path.read_bytes():
            raise ValueError(f"{name} does not match the build interpreter's original license")
    for name, source in expected["notices"].items():
        if hashlib.sha256((ROOT / "LICENCES" / name).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Changed upstream license: {name}")
    return actual

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path)
    args = parser.parse_args()
    actual = verify()
    if args.record:
        from PyInstaller.archive.readers import CArchiveReader
        reader = CArchiveReader(str(args.record))
        dll = f"python{sys.version_info.major}{sys.version_info.minor}.dll"
        if reader.extract(dll) != (Path(sys.base_prefix) / dll).read_bytes():
            raise ValueError("Frozen interpreter differs from the licensed build interpreter")
        modules = []
        for name, entry in reader.toc.items():
            if entry[-1] == "z":
                modules.extend(reader.open_embedded_archive(name).toc)
        if any("cytools" in name.lower() or "cyuemcp" in name.lower() for name in modules):
            raise ValueError("A Cy SDK is now bundled: add its version, license and integration checks before packaging")
        version = re.search(r"project\(CyRSAssistant VERSION ([0-9.]+)", (ROOT / "CMakeLists.txt").read_text()).group(1)
        manifest = {"application_version": version, "components": actual,
                    "sha256": hashlib.sha256(args.record.read_bytes()).hexdigest(),
                    "license_sha256": {name: hashlib.sha256((ROOT / "LICENCES" / name).read_bytes()).hexdigest()
                                       for name in ("Python.txt", "PyInstaller.txt")}}
        args.record.with_suffix(".build.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Companion runtime and original license texts verified.")

if __name__ == "__main__":
    main()
