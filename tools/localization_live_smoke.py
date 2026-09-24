"""Verify language switching and real chat replies in an empty test-game conversation."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.transport import Client, discover


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipe")
    parser.add_argument("--chat", action="store_true", help="Send two synthetic chat requests to the configured CLI provider")
    args = parser.parse_args()
    pipes = [args.pipe] if args.pipe else discover()
    if len(pipes) != 1:
        raise SystemExit("Expected one running test game, or specify --pipe")
    client = Client(pipes[0])
    runtime = client.call("list_sessions")["runtimes"][-1]["runtime"]
    initial = client.state(runtime)
    if initial["prompt"]["pending"]:
        raise SystemExit("A user request is running; test deferred")
    if args.chat and initial["conversation"]:
        raise SystemExit("Real chat test requires an empty conversation; existing messages are preserved")
    original_language = initial.get("language", "en")
    report = {"default_language": original_language, "checks": []}
    try:
        for code in ("fr", "en", "unsupported"):
            before = client.state(runtime)
            expected = "fr" if code == "fr" else "en"
            result = client.call("set_language", runtime=runtime, session=before["session"], language=code)
            after = client.state(runtime)
            assert result["language"] == after["language"] == expected
            assert after["conversation"] == before["conversation"]
            assert after["prompt"] == before["prompt"]
            assert after["permissions"] == before["permissions"]
            assert client.call("get_connection", runtime=runtime)["connection"]["language"] == expected
            report["checks"].append({"language": code, "resolved": expected, "history_and_permissions_preserved": True})
        print("PASS: language switch, fallback, history and permissions", flush=True)
        if args.chat:
            current = client.state(runtime)
            if not current["connection"]["wanted"]:
                if current["connection"]["provider"] not in (0, 1):
                    raise SystemExit("Real chat smoke test requires an already configured CLI provider")
                client.call("connect_provider", runtime=runtime, provider=current["connection"]["provider"])
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                current = client.state(runtime)
                if current["connection"]["ready"]:
                    break
                if current["connection"]["phase"] == "error":
                    raise RuntimeError("Provider connection failed")
                time.sleep(0.5)
            assert current["connection"]["ready"], "Provider did not become ready"
            for code in ("en", "fr"):
                client.call("set_language", runtime=runtime, session=current["session"], language=code)
                state = client.state(runtime)
                sent = client.call("send_chat", runtime=runtime, session=state["session"], text="Start your reply with the two-letter code of the interface language you were instructed to use, then give one short greeting. Do not call tools or change rendering.")
                deadline = time.monotonic() + 200
                while time.monotonic() < deadline:
                    current = client.state(runtime)
                    if current["prompt"]["id"] != sent["prompt_id"]:
                        raise RuntimeError("Test superseded by another request")
                    if not current["prompt"]["pending"]:
                        break
                    time.sleep(0.7)
                assert not current["prompt"]["pending"], "Reply timeout"
                message = current["conversation"][-1]
                assert message["role"] == "assistant" and message["content"].lower().startswith(code), "Unexpected response language"
                assert current["revision"] == state["revision"] and current["generated"] == state["generated"], "Rendering changed"
                assert current["conversation"][:-2] == state["conversation"], "Earlier history changed"
                report["checks"].append({"language": code, "reply": message["content"], "render_unchanged": True})
                print("PASS: real " + code + " reply; rendering and earlier history unchanged", flush=True)
    finally:
        current = client.state(runtime)
        client.call("set_language", runtime=runtime, session=current["session"], language=original_language)
        output = Path("build/localization-live-report.json")
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
