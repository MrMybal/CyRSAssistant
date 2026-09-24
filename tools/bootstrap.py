"""Download version-pinned, upstream-only build headers (no project code reuse)."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1] / "third_party"
LOCK = json.loads(Path(__file__).with_name("dependencies.lock.json").read_text(encoding="utf-8"))


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def verify(name, url, data):
    actual = {"url": url, "sha256": hashlib.sha256(data).hexdigest()}
    if actual != LOCK[name]:
        raise ValueError(f"Dependency {name} does not match dependencies.lock.json")
    return actual


def main():
    ROOT.mkdir(exist_ok=True)
    manifest = {}
    for name, url, prefix, names in [
        ("reshade", "https://codeload.github.com/crosire/reshade/zip/refs/tags/v6.8.0", "reshade-6.8.0/", None),
        ("imgui", "https://codeload.github.com/ocornut/imgui/zip/refs/tags/v1.92.5-docking", "imgui-1.92.5-docking/", {"imgui.h", "imconfig.h", "LICENSE.txt"}),
    ]:
        data = fetch(url)
        manifest[name] = verify(name, url, data)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for entry in archive.infolist():
                if entry.is_dir() or not entry.filename.startswith(prefix):
                    continue
                relative = entry.filename[len(prefix):]
                if names is not None:
                    selected = relative in names
                else:
                    selected = (relative.startswith("include/") and relative.endswith(".hpp")) or relative == "LICENSE.md"
                if selected:
                    path = ROOT / name / relative
                    if not path.resolve().is_relative_to(ROOT.resolve()):
                        raise ValueError("Unsafe archive path")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archive.read(entry))
    url = "https://raw.githubusercontent.com/nlohmann/json/v3.12.0/single_include/nlohmann/json.hpp"
    data = fetch(url)
    manifest["json"] = verify("json", url, data)
    path = ROOT / "json" / "nlohmann" / "json.hpp"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    (ROOT / "json" / "LICENSE.MIT").write_bytes(fetch("https://raw.githubusercontent.com/nlohmann/json/v3.12.0/LICENSE.MIT"))
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Upstream headers ready in", ROOT)


if __name__ == "__main__":
    main()
