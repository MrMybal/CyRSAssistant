"""Build a complete static CyDoc site without application binaries or a server."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ("cyrsassistant-logo-turquoise.png", "screenshots/chat-preview.png", "screenshots/connection-preview.png")


def refresh_sources():
    config = json.loads((ROOT / "cydoc.config.json").read_text(encoding="utf-8"))
    files = {}
    for folder in ("src", "companion"):
        for path in sorted((ROOT / folder).rglob("*")):
            if path.is_file() and path.suffix in (".cpp", ".hpp", ".h", ".py") and "__pycache__" not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = path.read_text(encoding="utf-8")
    revision = subprocess.check_output(["git", "-c", "safe.directory=" + ROOT.as_posix(), "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    snapshot = {"version": config["version"], "revision": revision, "files": files}
    (ROOT / "docs/reference-sources.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Refreshed documentation reference: {len(files)} source files")


def build():
    lock = json.loads((ROOT / "tools/cydoc.lock.json").read_text(encoding="utf-8"))
    if hashlib.sha256((ROOT / lock["package"]).read_bytes()).hexdigest() != lock["sha256"]:
        raise ValueError("CyDoc archive hash mismatch")
    installed = ROOT / "node_modules/cydoc/package.json"
    if not installed.is_file() or json.loads(installed.read_text(encoding="utf-8"))["version"] != lock["version"]:
        raise ValueError("Install pinned documentation dependencies with npm ci --omit=peer")
    node = shutil.which("node")
    if not node or int(subprocess.check_output([node, "--version"], text=True).lstrip("v").split(".")[0]) < 22:
        raise ValueError("Node.js 22+ is required to generate documentation")
    config = json.loads((ROOT / "cydoc.config.json").read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / "docs/reference-sources.json").read_text(encoding="utf-8"))
    if snapshot["version"] != config["version"] or not re.fullmatch(r"[0-9a-f]{40}", snapshot["revision"]):
        raise ValueError("Documentation reference version/revision mismatch; refresh it intentionally")
    if config["modules"] != ["image"]:
        raise ValueError("Only the image module is required")
    staging = ROOT / "build/pages-project"
    # Only remove this explicitly checked, dedicated staging directory.
    if staging.resolve() != ROOT.resolve() / "build/pages-project" or staging.is_symlink():
        raise ValueError("Unexpected Pages staging path")
    if staging.exists(): shutil.rmtree(staging)
    staging.mkdir(parents=True)
    shutil.copytree(ROOT / "docs/content", staging / "docs/content")
    for name in ASSETS:
        target = staging / "assets" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "assets" / name, target)
    for name, content in snapshot["files"].items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name or relative.parts[0] not in ("src", "companion") or relative.suffix not in (".cpp", ".hpp", ".h", ".py"):
            raise ValueError("Invalid reference source path: " + name)
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    config["out"] = "site"
    (staging / "cydoc.config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    output = staging / "site"
    subprocess.run([node, str(ROOT / "tools/export_help.mjs"), "check", "--project", str(staging), "--output", str(output)], cwd=ROOT, check=True)
    (output / ".nojekyll").write_text("", encoding="utf-8")
    subprocess.run([node, str(ROOT / "tools/check_pages.mjs"), str(output)], cwd=ROOT, check=True)
    print("Pages artifact: build/pages-project/site (documentation only)")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-sources", action="store_true", help="Refresh the reviewed source reference from this application checkout before building")
    args = parser.parse_args()
    if args.refresh_sources: refresh_sources()
    build()
