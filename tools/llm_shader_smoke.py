"""One real Codex shader-generation request, native compilation, activation and cleanup."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.service import CliProvider
from companion.generation import FX_SYSTEM, checked_response
from companion.transport import Client, discover, version
from companion.capture import save_capture

provider = CliProvider({"provider": 0})
print(provider.check(), flush=True)
response = provider.complete(FX_SYSTEM, "Create subtle cinematic teal shadows, warm highlights and a soft vignette. Only use color and uv. No loops or texture sampling needed. Explain briefly in French.")
body = checked_response(response, "body", 16384)
folder = Path("build/shader-lab-test")
folder.mkdir(parents=True, exist_ok=True)
(folder / "codex-generation.json").write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
pipes = discover()
if len(pipes) != 1:
    raise SystemExit("Expected one test game")
client = Client(pipes[0])
filename = None
try:
    result = client.call("generate_effect", **version(client.state(1)), body=body)
    filename = result["generated"]["file"]
    deadline = time.monotonic() + 65
    while time.monotonic() < deadline:
        state = client.state(1)
        if state["generated"]["phase"] in ("ready", "error"):
            break
        time.sleep(0.5)
    assert state["generated"]["phase"] == "ready", state["generated"]
    save_capture(client, 1, folder / "codex-generated.png")
    report = {"provider": "Codex CLI", "generated": state["generated"], "real_model_request": True, "restored": False}
finally:
    if filename:
        state = client.state(1)
        tech = next((t for t in state["techniques"] if t["effect"] == filename), None)
        if tech and tech["value"]:
            client.call("apply_patch", **version(state), changes=[{"kind": "technique", "id": tech["id"], "value": False}])
report["restored"] = True
(folder / "codex-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2), flush=True)
