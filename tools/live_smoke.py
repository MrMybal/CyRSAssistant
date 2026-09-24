"""Exercise a running game through CyRSAssistant; always undo the temporary edit."""
import argparse
import base64
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.transport import Client, discover, version
from companion.capture import png_bytes

parser = argparse.ArgumentParser()
parser.add_argument("--pipe")
parser.add_argument("--output", type=Path, default=Path("build/stray-test"))
args = parser.parse_args()
pipes = [args.pipe] if args.pipe else discover()
if len(pipes) != 1:
    raise SystemExit("Choose one running add-on with --pipe")
client = Client(pipes[0])
state = client.state(1)
parameter = next(p for p in state["parameters"] if p["effect"] == "Tonemap.fx" and p["name"] == "Saturation")
technique = next(t for t in state["techniques"] if t["effect"] == "Tonemap.fx" and t["name"] == "Tonemap")
args.output.mkdir(parents=True, exist_ok=True)
report = {"session": state["session"], "parameters": len(state["parameters"]), "techniques": len(state["techniques"]), "checks": []}


def capture(name):
    frame = client.call("capture_frame", runtime=1)["frame"]
    (args.output / (name + ".png")).write_bytes(png_bytes(frame))
    pixels = base64.b64decode(frame["data"])
    count = len(pixels) // 3
    chroma = sum(abs(pixels[i] - pixels[i + 1]) + abs(pixels[i + 2] - pixels[i + 1]) for i in range(0, len(pixels), 3)) / count
    report[name + "_mean_chroma"] = chroma


capture("before")
bad = {**version(state), "changes": [{"kind": "parameter", "id": parameter["id"], "value": [-2]}]}
try:
    client.call("apply_patch", **bad)
    raise AssertionError("Out-of-bounds edit was accepted")
except RuntimeError as error:
    if "minimum" not in str(error):
        raise
    report["checks"].append("Out-of-bounds edit rejected")
request = {**version(state), "changes": [
    {"kind": "parameter", "id": parameter["id"], "value": [-1.0]},
    {"kind": "technique", "id": technique["id"], "value": True}]}
applied = False
try:
    client.call("apply_patch", **request)
    applied = True
    time.sleep(1)
    changed = client.state(1)
    assert changed["parameters"][parameter["id"]]["value"] == [-1.0]
    assert changed["techniques"][technique["id"]]["value"] is True
    report["checks"].append("Tonemap saturation and technique changed in real runtime")
    capture("desaturated")
    try:
        client.call("apply_patch", **request)
        raise AssertionError("Stale edit was accepted")
    except RuntimeError as error:
        if "changed" not in str(error):
            raise
        report["checks"].append("Stale revision rejected")
finally:
    if applied:
        client.call("undo", **version(client.state(1)))
        restored = client.state(1)
        assert restored["parameters"][parameter["id"]]["value"] == parameter["value"]
        assert restored["techniques"][technique["id"]]["value"] == technique["value"]
        report["checks"].append("Original parameter and technique state restored")
        time.sleep(0.25)
        capture("restored")
report["preset_saved"] = False
(args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
