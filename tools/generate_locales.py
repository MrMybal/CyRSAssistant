"""Validate shared catalogs and embed them into the native add-on at build time."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.localization import CATALOGS, validate_catalogs


def generate(output):
    validate_catalogs()
    lines = ["// Generated from companion/locales/*.json. Do not edit.", "#pragma once", "#include <cstddef>",
             "namespace cyrs::i18n {", "struct Translation { const char *key; const char *value; };",
             "struct Language { const char *code; const char *name; const Translation *messages; size_t count; };"]
    quote = lambda text: json.dumps(text, ensure_ascii=False)
    for index, catalog in enumerate(CATALOGS.values()):
        lines.append(f"inline constexpr Translation messages_{index}[] = {{")
        for key, value in sorted(catalog["messages"].items()):
            lines.append("    {" + quote(key) + ", " + quote(value) + "},")
        # A sentinel permits empty future catalogs, which fall back to English.
        lines += ['    {"", ""}', "};"]
    lines.append("inline constexpr Language languages[] = {")
    for index, (code, catalog) in enumerate(CATALOGS.items()):
        lines.append("    {" + quote(code) + ", " + quote(catalog["name"]) + f", messages_{index}, {len(catalog['messages'])}" + "},")
    lines += ["};", "}", ""]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    generate(parser.parse_args().output)
