"""Temporarily generate FX and replace one captured DX11 pixel shader, then restore."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.transport import Client, discover, version
from companion.capture import save_capture

pipes = discover()
if len(pipes) != 1:
    raise SystemExit("Expected exactly one running test game")
client = Client(pipes[0])
runtime = client.call("list_sessions")["runtimes"][0]["runtime"]
api = client.call("list_game_shaders", runtime=runtime)["inventory"]["api"]
folder = Path("build/shader-lab-test-dx12" if api == "D3D12" else "build/shader-lab-test")
folder.mkdir(parents=True, exist_ok=True)
report = {"pipe": pipes[0], "api": api, "runtime": runtime, "checks": []}
target = None
generated_file = None
try:
    state = client.state(runtime)
    result = client.call("generate_effect", **version(state), body="float gray = dot(color,float3(0.2126,0.7152,0.0722)); return lerp(color,gray.xxx,0.8);")
    generated_file = result["generated"]["file"]
    deadline = time.monotonic() + 65
    while time.monotonic() < deadline:
        state = client.state(runtime)
        if state["generated"]["phase"] in ("ready", "error"):
            break
        time.sleep(0.5)
    report["generated"] = state["generated"]
    assert state["generated"]["phase"] == "ready", state["generated"]
    report["checks"].append("Generated standalone FX compiled and activated by ReShade")
    save_capture(client, runtime, folder / "generated.png")
    tech = next(t for t in state["techniques"] if t["effect"] == generated_file)
    client.call("apply_patch", **version(state), changes=[{"kind": "technique", "id": tech["id"], "value": False}])
    report["checks"].append("Generated FX disabled after capture")
    inventory = client.call("list_game_shaders", runtime=runtime)["inventory"]
    candidates = sorted(inventory["shaders"], key=lambda s: s["binds"], reverse=True)
    report["captured_shaders"] = len(candidates)
    failures = []
    for candidate in candidates[:60]:
        if not candidate["binds"]:
            continue
        try:
            details = client.call("inspect_game_shader", runtime=runtime, hash=candidate["hash"])["shader"]
        except RuntimeError as error:
            failures.append(str(error)); continue
        outputs = details["reflection"]["outputs"]
        if len(outputs) != 1 or outputs[0]["mask"] != 15 or outputs[0]["type"] != 3 or outputs[0]["index"] != 0:
            continue
        # Preserve spelling of the semantic for conservative exact signature checks.
        semantic = outputs[0]["semantic"]
        if semantic.lower() != "sv_target":
            continue
        source = f"float4 main():{semantic}0 {{ return float4(0.1,0.5,0.2,1); }}"
        if "dcl_constantbuffer CB0[1], immediateIndexed" in details["reflection"].get("binding_declarations", []):
            source = f"cbuffer OriginalData:register(b0) {{ float4 original_color; }}; float4 main():{semantic}0 {{ return float4(original_color.rgb*float3(0.8,1,0.8),original_color.a); }}"
            report["preserved_original_constant_buffer"] = True
        state = client.state(runtime)
        try:
            result = client.call("replace_game_shader", **version(state), hash=candidate["hash"], source=source)
        except RuntimeError as error:
            failures.append(str(error)); continue
        target = candidate["hash"]
        (folder / "original_shader.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
        time.sleep(0.8)
        entry = next(s for s in client.call("list_game_shaders", runtime=runtime)["inventory"]["shaders"] if s["hash"] == target)
        report["replacement"] = result["replacement"]
        report["replacement_binds"] = entry["replacement_binds"]
        save_capture(client, runtime, folder / "replacement.png")
        assert entry["replacement_binds"] > 0, "Replacement compiled but game did not bind it during test"
        report["checks"].append("GPU accepted replacement and game actually bound it")
        break
    assert target is not None, failures[:5]
finally:
    if target:
        client.call("restore_game_shaders", **version(client.state(runtime)))
        entry = next(s for s in client.call("list_game_shaders", runtime=runtime)["inventory"]["shaders"] if s["hash"] == target)
        assert not entry["enabled"]
        count = entry["replacement_binds"]
        time.sleep(0.5)
        entry = next(s for s in client.call("list_game_shaders", runtime=runtime)["inventory"]["shaders"] if s["hash"] == target)
        assert entry["replacement_binds"] == count
        report["checks"].append("Original shader restored; replacement bind counter stopped")
    if generated_file:
        state = client.state(runtime)
        tech = next((t for t in state["techniques"] if t["effect"] == generated_file), None)
        if tech and tech["value"]:
            client.call("apply_patch", **version(state), changes=[{"kind": "technique", "id": tech["id"], "value": False}])
    (folder / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
