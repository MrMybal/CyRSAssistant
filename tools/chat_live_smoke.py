"""Exercise the installed chat service with two real model replies, without rendering edits."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.transport import Client, discover

pipes = discover()
if len(pipes) != 1:
    raise SystemExit("Expected one running CyRSAssistant test game")
client = Client(pipes[0])
runtime = client.call("list_sessions")["runtimes"][0]["runtime"]
state = client.state(runtime)
if state["prompt"]["pending"]:
    raise SystemExit("A user request is running; test deferred")
if not state["connection"]["wanted"]:
    client.call("connect_provider", runtime=runtime, provider=0)
deadline = time.monotonic() + 35
while time.monotonic() < deadline:
    state = client.state(runtime)
    if state["connection"]["ready"]:
        break
    if state["connection"]["phase"] == "error":
        raise RuntimeError(state["connection"]["message"])
    time.sleep(0.5)
assert state["connection"]["ready"], state["connection"]
baseline = {k: state[k] for k in ("generation", "revision", "parameters", "techniques", "generated")}
report = {"initial_effects": len(state["techniques"]), "selected_shader": state["prompt"]["shader_hash"], "messages": []}
for message in ["Bonjour ! Peut-on simplement discuter ici ? Pour notre conversation, appelons mon style prefere Ambre. Ne modifie rien au rendu.",
                "Quel nom ai-je donne a mon style prefere dans mon message precedent ? Reponds brievement, sans modifier le rendu."]:
    state = client.state(runtime)
    sent = client.call("send_chat", runtime=runtime, session=state["session"], text=message)
    deadline = time.monotonic() + 200
    while time.monotonic() < deadline:
        current = client.state(runtime)
        if current["prompt"]["id"] != sent["prompt_id"]:
            raise RuntimeError("Test superseded by another request")
        if not current["prompt"]["pending"]:
            break
        time.sleep(0.7)
    assert not current["prompt"]["pending"], "Reply timed out"
    reply = current["conversation"][-1]
    assert reply["role"] == "assistant" and not reply["content"].startswith("Echec"), reply
    report["messages"].append(reply["content"])
    print(reply["content"], flush=True)
assert "ambre" in report["messages"][-1].lower(), "History not recalled"
assert all(current[k] == v for k, v in baseline.items()), "Chat changed the rendering"
report["render_unchanged"] = True
out = Path("build/chat-live-report.json")
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("PASS: installed service, two real replies, remembered history, no rendering change", flush=True)
