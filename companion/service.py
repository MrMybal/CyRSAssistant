"""Background service launched by the overlay; no console or shell command interpolation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from .localization import tr as _, localized, response_instructions, render_message
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from .provider import Provider
from .transport import Client
from .__main__ import plan_request, scan_state
from .generation import generate_effect, replace_shader
from .chat import respond
from .permissions import with_permissions


def cli_path(name):
    direct = shutil.which(name + ".exe")
    if direct:
        return direct
    npm = Path(os.environ.get("APPDATA", "")) / "npm/node_modules"
    patterns = {
        "codex": "@openai/codex/node_modules/@openai/codex-win32-*/vendor/*/bin/codex.exe",
        "claude": "@anthropic-ai/claude-code/bin/claude.exe",
    }
    candidates = list(npm.glob(patterns[name]))
    if name == "claude":
        candidates.append(Path.home() / ".local/bin/claude.exe")
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise ValueError(_("{provider} CLI was not found. Install it and sign in before retrying.", provider=name))


def run_cli(args, cwd, content=None, timeout=120):
    return subprocess.run(args, input=content, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


class CliProvider(Provider):
    def __init__(self, config):
        self.name = "codex" if config["provider"] == 0 else "claude"
        self.executable = cli_path(self.name)
        self.model = config.get("model", "")

    def check(self):
        args = [self.executable, "login", "status"] if self.name == "codex" else [self.executable, "auth", "status", "--json"]
        with tempfile.TemporaryDirectory(prefix="cyrs-auth-") as cwd:
            result = run_cli(args, cwd, timeout=20)
        valid = result.returncode == 0
        if self.name == "claude" and valid:
            valid = json.loads(result.stdout).get("loggedIn") is True
        if not valid:
            raise ValueError(_("{provider} session missing or expired. Run {command}, then reconnect here.", provider=self.name, command=self.name + (" login" if self.name == "codex" else " auth login")))
        return _("{provider}: CLI session recognized. Model access is checked on the first message.", provider=self.name)

    def complete(self, system, content):
        with tempfile.TemporaryDirectory(prefix="cyrs-request-") as cwd:
            if self.name == "codex":
                output = Path(cwd) / "reply.json"
                args = [self.executable, "exec", "--skip-git-repo-check", "--sandbox", "read-only",
                        "--ephemeral", "--ignore-user-config", "-c", "features.shell_tool=false",
                        "--color", "never", "-o", str(output)]
                if self.model:
                    args += ["--model", self.model]
                args += ["-"]
                result = run_cli(args, cwd, system + "\n\n" + content, timeout=180)
                raw = output.read_text(encoding="utf-8") if output.exists() else ""
            else:
                args = [self.executable, "-p", "--tools", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                        "--settings", '{"disableAllHooks":true}', "--setting-sources", "user",
                        "--no-session-persistence", "--output-format", "json", "--system-prompt", system]
                if self.model:
                    args += ["--model", self.model]
                result = run_cli(args, cwd, content, timeout=180)
                envelope = json.loads(result.stdout) if result.returncode == 0 else {}
                if envelope.get("is_error"):
                    raise RuntimeError(_("Claude refused the request. Check the CLI session, model and quota."))
                raw = envelope.get("result", "")
            if result.returncode:
                # CLI stderr may contain account details or credentials; never echo it into the game.
                raise RuntimeError(_("{provider} failed (code {code}). Check the CLI connection and quota.", provider=self.name, code=result.returncode))
            raw = raw.strip()
            if raw.startswith("```") and raw.endswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(raw)


@localized(0)
def connect(config):
    if config["provider"] in (0, 1):
        provider = CliProvider(config)
        return provider, provider.check()
    provider = Provider(config)
    probe = provider.complete('Return only {"connected":true}.', "Connection test")
    if probe.get("connected") is not True:
        raise ValueError(_("The model did not return the expected JSON response."))
    return provider, _("API connected: model {model} responded to the test.", model=provider.model)


@localized(3)
def answer(client, runtime, provider, state):
    prompt_id = state["prompt"]["id"]
    client = with_permissions(client, runtime, state)
    try:
        mode = state["prompt"].get("mode", 0)
        if mode == 3:
            message = respond(client, runtime, provider, state)
        elif mode == 1:
            message = generate_effect(client, runtime, provider, state)
        elif mode == 2:
            message = replace_shader(client, runtime, provider, state)
        else:
            scan_state(state)
            result = plan_request(client, state, state["prompt"]["text"], provider, prompt_id)
            message = result["plan"]["message"]
            message += "\n" + (_("Changes applied. Undo is available.") if result["applied"] else _("No changes applied."))
        status = _("The provider responded to the last request.")
        phase = "ready"
    except Exception as exc:
        message = _("Request failed: {error}", error=_(str(exc)))
        status = _("The last request failed. You can send another message or try again.")
        phase = "ready"
    client.call("assistant_reply", runtime=runtime, session=state["session"], prompt_id=prompt_id, message=message.encode("utf-8")[:16000].decode("utf-8", errors="ignore"))
    return phase, status


def serve(pipe):
    client = Client(pipe)
    states = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        failures = 0
        while failures < 6:
            try:
                sessions = client.call("list_sessions")["runtimes"]
                for item in sessions:
                    runtime = item["runtime"]
                    config = client.call("get_connection", runtime=runtime)["connection"]
                    if not config["wanted"]:
                        states.pop(runtime, None)
                        continue
                    entry = states.get(runtime)
                    if not entry or entry["epoch"] != config["epoch"]:
                        entry = states[runtime] = {"epoch": config["epoch"], "phase": "connecting", "message": _("Checking the provider..."), "connect": pool.submit(connect, config)}
                    future = entry.get("connect")
                    if future and future.done():
                        entry.pop("connect")
                        try:
                            entry["provider"], entry["message"] = future.result()
                            entry["phase"] = "ready"
                        except Exception as exc:
                            entry["phase"], entry["message"] = "error", exc.args[0] if exc.args and isinstance(exc.args[0], str) else str(exc)
                    pending = entry.get("request")
                    if pending and pending.done():
                        entry.pop("request")
                        try:
                            entry["phase"], entry["message"] = pending.result()
                        except Exception:
                            entry["message"] = _("Request cancelled or session changed.")
                    client.call("connection_status", runtime=runtime, epoch=entry["epoch"], phase=entry["phase"], message=render_message(entry["message"], config.get("language", "en"))[:2048])
                    if entry["phase"] == "ready" and not entry.get("request"):
                        state = client.state(runtime)
                        if state["prompt"]["pending"]:
                            entry["request"] = pool.submit(answer, client, runtime, entry["provider"], state)
                failures = 0
            except (OSError, RuntimeError, ValueError):
                failures += 1
            time.sleep(0.7)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipe", required=True)
    serve(parser.parse_args().pipe)


if __name__ == "__main__":
    main()
