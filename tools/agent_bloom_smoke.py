"""Real-model inspection, replacement, adjustment and restoration on an isolated test FX."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.transport import Client, discover, version

client = Client(discover()[0])
runtime = client.call("list_sessions")["runtimes"][0]["runtime"]

def state():
    return client.state(runtime)

def wait_ready(filename):
    deadline = time.monotonic() + 70
    while time.monotonic() < deadline:
        value = state()
        if value["generated"]["file"] == filename and value["generated"]["phase"] in ("ready", "error"):
            assert value["generated"]["phase"] == "ready", value["generated"]
            return value
        time.sleep(0.5)
    raise RuntimeError("FX compilation timed out")

report = {"messages": [], "tools": []}

def talk(message):
    before = state()
    if before["prompt"]["pending"]:
        raise RuntimeError("Another user request is running")
    sent = client.call("send_chat", runtime=runtime, session=before["session"], text=message)
    deadline = time.monotonic() + 360
    last = None
    while time.monotonic() < deadline:
        value = state()
        assert value["prompt"]["id"] == sent["prompt_id"], "Turn superseded"
        progress = value["prompt"].get("progress")
        if progress != last:
            last = progress
            report["tools"].append(progress)
            print(progress, flush=True)
        if not value["prompt"]["pending"]:
            reply = value["conversation"][-1]["content"]
            assert not reply.startswith("Echec"), reply
            report["messages"].append(reply)
            print(reply, flush=True)
            return value
        time.sleep(0.7)
    raise RuntimeError("Conversation timed out")

initial = state()
if initial["prompt"]["pending"]:
    raise SystemExit("User turn running")
if not initial["techniques"]:
    client.call("reload_effects", **version(initial))
    deadline = time.monotonic() + 70
    while time.monotonic() < deadline:
        initial = state()
        if initial["techniques"] and not initial["loading"]:
            break
        time.sleep(0.5)
baseline = {(t["effect"], t["name"]): t["value"] for t in state()["techniques"]}
if not state()["connection"]["wanted"]:
    client.call("connect_provider", runtime=runtime, provider=0)
deadline = time.monotonic() + 35
while not state()["connection"]["ready"] and time.monotonic() < deadline:
    time.sleep(0.5)
assert state()["connection"]["ready"]
original = replacement = None
try:
    created = client.call("generate_effect", **version(state()), name="TestOriginalBloom", title="Test original bloom",
                          parameters=[{"name":"Threshold","label":"Threshold","min":0.0,"max":4.0,"default":1.25,"step":0.01},
                                      {"name":"Strength","label":"Strength","min":0.0,"max":5.0,"default":0.0,"step":0.01}],
                          body="return color + max(color - CyRSP_Threshold, 0.0) * CyRSP_Strength;")
    original = created["generated"]["file"]
    ready = wait_ready(original)
    gen = ready["generation"]
    read = talk("Lis les parametres de " + original + ". Quels sont les vrais noms, valeurs et bornes du seuil et de la puissance ? Ne modifie rien.")
    assert read["generation"] == gen
    assert "1.25" in report["messages"][-1] or "1,25" in report["messages"][-1], "Actual threshold not reported"
    question = talk("Est-ce que tu peux remplacer cet effet " + original + " par un bloom anamorphique reglable ? Reponds et demande-moi confirmation, ne modifie encore rien.")
    assert question["generated"]["file"] == original and question["generation"] == gen
    changed = talk("Oui, remplace exactement " + original + " par un bloom anamorphique. Expose Threshold (0 a 4), Strength (0 a 8), Length en pixels (1 a 200) et SoftKnee. Compile puis desactive l'ancien effet, sans ajout cumulatif.")
    replacement = changed["generated"]["file"]
    assert replacement != original and changed["generated"]["replaces"] == original, "Replacement not executed"
    assert changed["generated"]["phase"] == "ready"
    assert not any(t["value"] for t in changed["techniques"] if t["effect"] == original)
    assert any(t["value"] for t in changed["techniques"] if t["effect"] == replacement)
    controls = [p for p in changed["parameters"] if p["effect"] == replacement]
    for name in ("Threshold", "Strength", "Length", "SoftKnee"):
        assert any(p["name"] == "CyRSP_" + name for p in controls), (name, controls)
    adjusted = talk("Mets CyRSP_Threshold de " + replacement + " a 1.5, puis donne-moi la valeur relue.")
    threshold = next(p for p in adjusted["parameters"] if p["effect"] == replacement and p["name"] == "CyRSP_Threshold")
    assert threshold["value"] == [1.5], threshold
    restored = talk("Restaure l'ancien effet " + original + " et desactive son remplacement " + replacement + ".")
    assert any(t["value"] for t in restored["techniques"] if t["effect"] == original)
    assert not any(t["value"] for t in restored["techniques"] if t["effect"] == replacement)
    report["success"] = True
    report["controls"] = [{k:p[k] for k in ("name","value","min","max")} for p in controls if p["name"].startswith("CyRSP_")]
finally:
    current = state()
    if not current["prompt"]["pending"]:
        changes = []
        for t in current["techniques"]:
            key = (t["effect"],t["name"])
            expected = baseline.get(key, False) if t["effect"] in (original, replacement) or key in baseline else t["value"]
            if t["value"] != expected:
                changes.append({"kind":"technique","id":t["id"],"value":expected})
        if changes:
            client.call("apply_patch", **version(current), changes=changes)
    Path("build/agent-bloom-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("PASS: values, capability confirmation, replacement, controls, readback and restoration", flush=True)
