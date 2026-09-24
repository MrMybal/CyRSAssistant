"""Validate one model-generated resource-preserving replacement in the running test game."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.service import CliProvider
from companion.generation import REPLACEMENT_SYSTEM, checked_response
from companion.transport import Client, discover, version

pipes = discover()
if len(pipes) != 1:
    raise SystemExit("Expected one test game")
client = Client(pipes[0])
inventory = client.call("list_game_shaders", runtime=1)["inventory"]["shaders"]
target = None
for item in sorted(inventory, key=lambda s: s["binds"], reverse=True):
    shader = client.call("inspect_game_shader", runtime=1, hash=item["hash"])["shader"]
    if shader["reflection"]["binding_declarations"] == ["dcl_constantbuffer CB0[1], immediateIndexed"] and len(shader["reflection"]["outputs"]) == 1:
        target = item["hash"]
        break
if not target:
    raise SystemExit("No suitable simple shader to validate resource preservation")
provider = CliProvider({"provider": 0})
print("Requesting a resource-preserving replacement from Codex...", flush=True)
response = provider.complete(REPLACEMENT_SYSTEM, json.dumps({"request": "Test technique: reconstruct this simple shader, multiply its output RGB by float3(0.9,1,0.9), and preserve its original alpha and the original constant buffer. Explain in French.", "shader": shader}))
source = checked_response(response, "source", 65536)
if not source:
    raise SystemExit(response["message"])
folder = Path("build/shader-lab-test")
(folder / "codex-replacement.json").write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
report = {"provider": "Codex CLI", "real_model_request": True, "original_hash": target}
applied = False
try:
    result = client.call("replace_game_shader", **version(client.state(1)), hash=target, source=source)
    applied = True
    report["replacement"] = result["replacement"]
    start = next(s for s in client.call("list_game_shaders", runtime=1)["inventory"]["shaders"] if s["hash"] == target)["replacement_binds"]
    time.sleep(0.5)
    end = next(s for s in client.call("list_game_shaders", runtime=1)["inventory"]["shaders"] if s["hash"] == target)["replacement_binds"]
    assert end > start, "Model source compiled but was not used by the game"
    report["observed_binds"] = end - start
finally:
    if applied:
        client.call("enable_game_shader", **version(client.state(1)), hash=target, enabled=False)
        report["restored"] = True
(folder / "codex-replacement-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2), flush=True)
