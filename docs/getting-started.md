# Connect from ReShade

English | [Français](getting-started.fr.md)

Use a Windows x64 game with ReShade 6.8 and full add-on support. This prototype targets API 20 and the ImGui 1.92.5 bridge; other versions require verification.

1. Copy `CyRSAssistant.addon64`, `CyRSAssistantCompanion.exe` and the complete `CyRSAssistantRuntime` folder next to ReShade, then restart the game.
2. Open **CyRSAssistant** in the ReShade overlay. The interface starts in English. Select **Options > Language > Français** for French.
3. In **Connection**, select **Codex**, **Claude Code**, **OpenAI-compatible API** or **Local model**.
4. CLI providers use an existing login. If needed, run `codex login` or `claude auth login` once outside the game. Leave Model empty to use the CLI default. For an API, enter the full `/chat/completions` URL, model and optional API key.
5. Click **Connect**. The background service starts automatically. A CLI status confirms local login; the first message checks model access. API connection performs a small model request.
6. In **Chat**, write under **Your message** and click **Send**, or press Ctrl+Enter. Enter inserts a new line. Chat works without loaded effects or a selected shader.

Use exact FX filenames when discussing a replacement. The assistant can read filenames, names and values itself. Internal game shaders usually have hashes rather than meaningful original names; a native replacement needs an identified target.

## Language and history

**Options > Language** takes effect immediately and is saved per game. Existing chat messages are preserved in their original language. A request already in progress finishes in the language it started with; subsequent requests use the new setting unless you explicitly request another language.

Unknown language codes and missing translations fall back to English. For translations beyond English and French, see [Adding a language](localization.md).

## Permissions

**Options > Permission mode** provides Automatic, Ask each time and Full access to ReShade tools. Automatic is the default. Ask each time shows the proposed change or source inspection in Chat, with **Allow this action** and **Deny this action** buttons. Full access allows multiple rendering operations in a single request.

Changing permission mode cancels a pending request. Already applied edits remain active until undone or restored. Language changes do not cancel requests or alter permissions.

## Connection and manual controls

Provider, endpoint, model, language and permission mode are stored in ReShade.ini. The API key is session-only. **Disconnect / edit** cancels pending requests before allowing provider changes. A service heartbeat missing for ten seconds is reported as unreachable; reconnect to restart the check.

**Effects** contains scanning, reload, manual values, undo, preset saving and generated-effect restoration. **Shaders** contains native shader inventory, inspection and restoration. A scan enumerates loaded effects; use reload after adding an FX file. ReShade performance mode can remove editable parameters.

## Command line and MCP

The packaged `companion/` directory can also run with Python 3.11+:

```powershell
python -m companion discover
python -m companion state
python -m companion scan
python -m companion ask 'Make the colors slightly cooler' --dry-run > plan.json
python -m companion apply plan.json
python -m companion undo
python -m companion save
python -m companion describe Tonemap.fx
python -m companion export catalogue-portable.json
python -m companion import catalogue-portable.json
```

Set `CYRS_API_URL`, `CYRS_MODEL` and optionally `CYRS_API_KEY` in the process environment for CLI model requests. HTTPS is required except for localhost. The endpoint must support Chat Completions with JSON responses. Do not run the legacy `watch` command alongside the integrated service.

If multiple games are running, supply `--pipe` and, if needed, `--runtime` before the subcommand. Use the actual pipe and runtime reported by the add-on. MCP clients can start `python -m companion.mcp`; add `--allow-write` only for write access. See [protocol details](protocol.md) and the [extended French guide](getting-started.fr.md) for advanced commands and catalog behavior.
