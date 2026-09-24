"""Read-only access to runtime metadata and FX files under configured shader roots."""
import hashlib
from pathlib import Path
from .localization import tr as _, localized

PARAMETER_FIELDS = ("id", "name", "label", "effect", "type", "value", "min", "max", "readonly", "description", "source", "rows", "columns", "array_length")


def parameters(state, effect="", query="", offset=0, limit=80):
    items = [{k: p[k] for k in PARAMETER_FIELDS if k in p} for p in state.get("parameters", [])
             if (not effect or p.get("effect") == effect) and
             (not query or query.casefold() in (p.get("name", "") + " " + p.get("label", "") + " " + p.get("effect", "")).casefold())]
    offset = max(0, int(offset)); limit = max(1, min(100, int(limit)))
    return {"items": items[offset:offset+limit], "total": len(items), "offset": offset,
            "next_offset": offset+limit if offset+limit < len(items) else None}


def effects(state, query="", offset=0):
    names = sorted({x["effect"] for x in state.get("techniques", []) + state.get("parameters", [])})
    items = [{"file": name, "techniques": [t for t in state.get("techniques", []) if t["effect"] == name],
              "parameter_count": sum(p["effect"] == name for p in state.get("parameters", []))} for name in names
             if not query or query.casefold() in (name + " " + " ".join(t["name"] for t in state.get("techniques", []) if t["effect"] == name)).casefold()]
    offset = max(0, int(offset))
    return {"items": items[offset:offset+100], "total": len(items), "next_offset": offset+100 if offset+100 < len(items) else None}


@localized(0)
def read_source(state, filename, offset=0):
    if not isinstance(filename, str) or Path(filename).name != filename or any(c in filename for c in ("/", "\\", ":")) or Path(filename).suffix.lower() not in (".fx", ".fxh"):
        raise ValueError(_("Specify an exact FX/FXH filename, not a path."))
    matches = set()
    for entry in state.get("search_paths", []):
        recursive = entry.replace("\\", "/").endswith("/**")
        root = (Path(state["base_path"]) / (entry[:-3] if recursive else entry)).resolve()
        candidates = root.rglob(filename) if recursive else [root / filename]
        for path in candidates:
            resolved = path.resolve()
            if resolved.is_relative_to(root) and resolved.is_file():
                matches.add(resolved)
    if len(matches) != 1:
        raise ValueError(_("FX source missing or ambiguous across configured shader roots."))
    path = matches.pop()
    with path.open("rb") as stream:
        data = stream.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError(_("FX source exceeds 1 MiB."))
    text = data.decode("utf-8-sig", errors="replace")
    offset = max(0, int(offset)); end = offset + 24000
    return {"file": filename, "sha256": hashlib.sha256(data).hexdigest(), "source": text[offset:end],
            "offset": offset, "next_offset": end if end < len(text) else None, "characters": len(text)}
