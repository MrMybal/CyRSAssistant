"""Portable content-addressed catalogue. Sources remain in their original folders."""
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import uuid

INCLUDES = re.compile(r'^\s*#\s*include\s*[<"]([^">]+)[">]', re.MULTILINE)
EXTENSIONS = {".fx", ".fxh", ".png", ".jpg", ".jpeg", ".dds", ".bmp", ".tga"}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def load(path, default=None):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def roots_from_state(state):
    base = Path(state["base_path"])
    result = []
    for entry in state.get("search_paths", []) + state.get("texture_paths", []):
        recursive = entry.replace("\\", "/").endswith("/**")
        path = Path(entry[:-3] if recursive else entry)
        result.append(((base / path).resolve(), recursive))
    return result


def scan(roots, destination, state=None):
    destination = Path(destination)
    previous = load(destination / "catalog.json", {"files": []})
    files, errors = [], []
    seen = set()
    for index, (root, recursive) in enumerate(roots):
        root = Path(root).resolve()
        if not root.is_dir():
            errors.append({"root": index, "error": "Search directory missing"})
            continue
        paths = root.rglob("*") if recursive else root.glob("*")
        for path in sorted(paths):
            if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                continue
            resolved = path.resolve()
            if resolved in seen or not resolved.is_relative_to(root):
                continue
            seen.add(resolved)
            relative = path.relative_to(root).as_posix()
            try:
                size = path.stat().st_size
                if size > 32 * 1024 * 1024:
                    raise ValueError("File exceeds the 32 MiB scan limit")
                content = path.read_bytes()
                files.append({"root": index, "path": relative, "sha256": hashlib.sha256(content).hexdigest(),
                              "size": len(content), "kind": "effect" if path.suffix.lower() == ".fx" else "dependency",
                              "includes": INCLUDES.findall(content.decode("utf-8", errors="replace")) if path.suffix.lower() in (".fx", ".fxh") else []})
            except (OSError, ValueError) as exc:
                errors.append({"root": index, "path": relative, "error": type(exc).__name__})
    # Deliberately conservative: invalidate descriptions when any scanned input changes.
    # Macro includes and conditional preprocessing cannot be resolved by a regex parser.
    inventory = sorted((f["root"], f["path"], f["sha256"]) for f in files)
    context_hash = hashlib.sha256(json.dumps(inventory).encode()).hexdigest()
    old = {(f["root"], f["path"]): f["sha256"] for f in previous["files"]}
    new = {(f["root"], f["path"]): f["sha256"] for f in files}
    changes = {"added": [], "modified": [], "removed": []}
    for key in new:
        if key not in old:
            changes["added"].append(list(key))
        elif new[key] != old[key]:
            changes["modified"].append(list(key))
    for key in old:
        if key not in new:
            changes["removed"].append(list(key))
    effects = []
    for item in files:
        if item["kind"] != "effect":
            continue
        name = Path(item["path"]).name
        matching = [f for f in files if f["kind"] == "effect" and Path(f["path"]).name == name]
        techniques = [t for t in (state or {}).get("techniques", []) if t["effect"] == name] if len(matching) == 1 else []
        parameters = [p for p in (state or {}).get("parameters", []) if p["effect"] == name] if len(matching) == 1 else []
        fingerprint = hashlib.sha256((item["sha256"] + context_hash).encode()).hexdigest()
        description = load(destination / "descriptions" / (fingerprint + ".json"))
        if errors:
            description = None  # Missing inputs prevent claiming a valid cached analysis.
        effects.append({**item, "fingerprint": fingerprint,
                        "runtime_match": "ambiguous" if len(matching) > 1 else "loaded" if techniques or parameters else "not_observed",
                        "techniques": [t["name"] for t in techniques],
                        "parameters": [{k: v for k, v in p.items() if k not in ("id", "value")} for p in parameters],
                        "description": description})
    result = {"schema_version": 1, "context_hash": context_hash, "files": files, "effects": effects,
              "changes": changes, "errors": errors, "complete": not errors,
              "dependency_policy": "All scanned inputs; conservative invalidation, not a compiler dependency graph"}
    write_json(destination / "catalog.json", result)
    return result


def store_description(destination, effect, text, model):
    description = {"schema_version": 1, "fingerprint": effect["fingerprint"], "text": text,
                   "model": model, "created_at": datetime.now(timezone.utc).isoformat(),
                   "validation": "AI-generated, not visually verified"}
    write_json(Path(destination) / "descriptions" / (effect["fingerprint"] + ".json"), description)
    return description


def export_library(destination, target):
    catalog = load(Path(destination) / "catalog.json")
    if not catalog:
        raise ValueError("Scan the library first")
    # Includes neither absolute installation paths, sources nor credentials.
    descriptions = []
    for effect in catalog["effects"]:
        description = load(Path(destination) / "descriptions" / (effect["fingerprint"] + ".json"))
        if description:
            descriptions.append(description)
    write_json(target, {"schema_version": 1, "catalog": catalog, "descriptions": descriptions})


def import_library(destination, source):
    source = Path(source)
    if source.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Import exceeds 16 MiB")
    data = load(source)
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported library version")
    count = 0
    for description in data.get("descriptions", []):
        fingerprint = description.get("fingerprint", "")
        if not re.fullmatch(r"[0-9a-f]{64}", fingerprint) or not isinstance(description.get("text"), str):
            raise ValueError("Invalid description")
        if len(description["text"]) > 20000:
            raise ValueError("Description too large")
        write_json(Path(destination) / "descriptions" / (fingerprint + ".json"), description)
        count += 1
    return count
