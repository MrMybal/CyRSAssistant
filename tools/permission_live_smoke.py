"""Exercise overlay approval state with the installed service and a generated test FX."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.transport import Client, discover, version

client=Client(discover()[0]); runtime=client.call("list_sessions")["runtimes"][0]["runtime"]
state=lambda:client.state(runtime)
initial=state()
assert not initial["prompt"]["pending"], "Another user request is active"
target="CyRS_AnamorphicHorizontalBloom_fff8fa85605d8c8f.fx"
if not initial["connection"]["wanted"]:
    client.call("connect_provider",runtime=runtime,provider=0)
deadline=time.monotonic()+40
while not state()["connection"]["ready"] and time.monotonic()<deadline: time.sleep(0.5)
assert state()["connection"]["ready"]
report=[]

def mode(value):
    current=state()
    assert not current["prompt"]["pending"]
    client.call("set_permission_mode",runtime=runtime,session=current["session"],mode=value)
    assert state()["permissions"]["mode"]==value

def talk(prompt, decision=None):
    current=state()
    sent=client.call("send_chat",runtime=runtime,session=current["session"],text=prompt)
    approved=False; observed=[]; last=None
    deadline=time.monotonic()+240
    while time.monotonic()<deadline:
        current=state()
        assert current["prompt"]["id"]==sent["prompt_id"], "Superseded turn"
        request=current.get("permissions",{}).get("request")
        if request and request["status"]=="pending" and request["id"] not in observed:
            assert decision is not None, "Unexpected approval in automatic/full mode"
            assert request["action"]=="read_effect_source", request["action"]
            assert request["payload"]["file"]==target
            observed.append(request["id"])
            print("Approval visible:",request["summary"],flush=True)
            # The same native decide path is used by the overlay buttons.
            client.call("resolve_action_permission",runtime=runtime,session=current["session"],prompt_id=sent["prompt_id"],permission_id=request["id"],allow=decision)
            approved=decision
        if current["prompt"].get("progress")!=last:
            last=current["prompt"].get("progress");print(last,flush=True)
        if not current["prompt"]["pending"]:
            answer=current["conversation"][-1]["content"]
            print(answer,flush=True)
            if decision is not None: assert observed, "Expected an approval request"
            if decision is False: assert "refusee" in answer.lower(), answer
            else: assert not answer.startswith("Echec"), answer
            report.append({"mode":current["permissions"]["mode"],"approved":approved,"approval_count":len(observed),"reply":answer})
            return
        time.sleep(0.5)
    raise RuntimeError("Reply timed out")

prompt="Lis le code source de "+target+" avec read_effect_source, puis donne l'expression exacte du decalage horizontal d. Ne modifie pas le rendu."
try:
    mode(1); talk(prompt,False)
    talk("Je veux cette fois autoriser la lecture du fichier. "+prompt,True)
    mode(0); talk("Relis le fichier pour verifier la formule. "+prompt)
    mode(2); talk("Relis le fichier avec tes outils. "+prompt)
finally:
    if not state()["prompt"]["pending"]: mode(0)
    Path("build/permission-live-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("PASS: refusal, approval, automatic, full; source read by Codex; default restored to automatic",flush=True)
