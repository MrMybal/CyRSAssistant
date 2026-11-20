---
id: sdk
title: CyMCPSDK, CLI and advanced options
description: Use the shared operation registry, private results, session history and configured external tools.
section: Reference
parent: cli
order: 18
revision: 4
---

## Overview {#overview}

Version 0.10.1 integrates **CyMCPSDK 0.7.1**, revision `34d4bcae126bc83d1a2925b5047dac36e3d09d92`. Core, Platform, Http, MCP and AI are compiled from the pinned source archive. Local engine supervision and ChatUI are not linked: the application connects to existing local services, and ReShade's ImGui bridge does not provide CyUI DocumentViews. The existing chat panel receives Conversation events on a worker, while all ReShade changes stay on the game's thread.

## Shared operations {#operations}

Chat, the native CLI and MCP share 27 operation definitions and handlers. `CyRSAssistantCLI.exe tools` lists them; `describe NAME` gives the full input/output schemas. `cyrs_` names from the earlier MCP server are retained. Read the current state and use its session/generation/revision before editing. A rejected or expired action is never automatically retried.

| Area | Operations |
| --- | --- |
| Runtime | list_sessions, get_state, get_help_state, capture_frame |
| Effects | get_effects, get_parameters, read_effect_source, scan_effects, apply_patch, undo, save_preset, reload_effects |
| Generation | generate_effect, restore_generated_effect |
| Native shaders | list_game_shaders, inspect_game_shader, replace_game_shader, enable_game_shader, restore_game_shaders |
| Catalog | catalog_scan, catalog_read, catalog_export, catalog_import, store_effect_description |
| Results | result_read, resource_grep, refresh |

Prefix each name above with `cyrs_`. Catalog handlers reuse the existing Python catalog implementation through the bundled companion. Export returns portable JSON; redirect it in your script instead of granting the model an arbitrary output path. Existing Python CLI commands remain available, including explicit file import/export and legacy JSON planning. Connection settings, keys, permission-mode changes, approval resolution and recursive chat submission are deliberately not model tools. Documentation opening stays a user interface action.

## CLI and MCP {#connection}

Create `read-parameters.json` with the following JSON. Using a file avoids differences in Windows shell quoting.

```json
{"runtime":1}
```

```powershell
CyRSAssistantCLI.exe --help
CyRSAssistantCLI.exe discover
CyRSAssistantCLI.exe tools
CyRSAssistantCLI.exe describe cyrs_get_parameters
CyRSAssistantCLI.exe --args-file read-parameters.json call cyrs_get_parameters
CyRSAssistantCLI.exe mcp
```

Discovery, schemas and provider metadata need no game or graphical interface. Live operations address an already running ReShade instance. Use `--pipe` when several games are discovered; the selected process is pinned. A tool's `runtime` argument identifies its runtime. The integrated assistant is restricted to its own runtime.

Writes require `--allow-write` for the CLI/MCP server **and** the current application permission mode. Ask mode requires the actual overlay approval buttons. A noninteractive CLI write fails with `ApprovalRequired` unless `--wait-for-approval` was explicitly supplied for supervised use. No `yes` in a model reply grants approval. Exit codes are 0 for success, 2 for invalid CLI usage, 3 for denied access/required approval and 1 for other failures. JSON results go to stdout and diagnostics to stderr.

The native command-line MCP entry point uses local stdio, launched with the same executable and optional `--pipe`/`--allow-write` flags. Access is the local process/OS user's access; there is no public network listener or token to paste into chat. Native agents that need MCP receive a separate authenticated loopback endpoint owned by the SDK worker. Its secret is passed through the SDK's private provider configuration. HTTP supports request/response and finite SSE; use stdio for persistent SDK subscriptions.


```json
{"mcpServers":{"cyrsassistant":{"command":"C:/Games/Example/CyRSAssistantCLI.exe","args":["mcp"]}}}
```

This is a generic native stdio configuration; use the actual executable path and the client’s configuration format. Add `--pipe` before `mcp` when several games run, and `--allow-write` only for a trusted writing client.

## Local HTTP MCP access {#local-access}

Enable **Options > Enable local MCP**. The local companion starts the server independently of a chat provider. Copy its `http://127.0.0.1:<port>/mcp` address. The server listens on loopback only; the port changes when restarted.

| Profile | Token | Operations |
| --- | --- | --- |
| Free (default) | None; address alone | All exposed operations without extra confirmation. |
| Local controlled | None; address alone | Existing assistant permission mode. |
| Token only | Session Bearer token | All exposed operations without extra confirmation. |
| Protected | Session Bearer token | Existing assistant permission mode. |

Argument schemas, parameter bounds, runtime identity and session/generation/revision checks always apply. Free applies to this HTTP server; CLI/stdIO write flags and the integrated chat permission mode keep their existing behavior. An explicit remote-tool allowlist is still required.

Existing `MCPAccessProfile` choices in ReShade.ini are preserved (0 Free, 1 Local controlled, 2 Token only, 3 Protected). When absent, an explicit `local_access_profile` or legacy `mcp_profile` in sdk-options.json is retained; otherwise the choice migrates to Free. Unknown explicit values stop activation. `MCPEnabled` remains opt-in. Other settings and user files are preserved.

For token profiles, **Copy MCP token** copies the current session token. Configure your client’s Bearer authorization separately. Tokens and the internal bridge capability are excluded from public state snapshots, metrics and saved conversation history. A restart or profile change creates a new token; disabling the server closes its owned process. The internal HTTP endpoint used by native chat agents is separate and retains its chat permissions.

## Independent options {#options}

Copy the supplied `sdk-options.example.json` to `CyRSAssistant/sdk-options.json` under this game's ReShade base directory. The example is never activated or copied over user settings automatically. Reconnect after editing it. For a console process, supply `--options FILE` explicitly. Relative history, spool and metrics paths resolve beside that file.

| Option | Default / behavior |
| --- | --- |
| compact_discovery / discovery_threshold | true / 32; large provider catalogues use search, schema loading and invocation. MCP full tools/list remains available. |
| large_results / inline_bytes | true / 65,536; persistent chat/MCP workers retain larger results as private resources. One-shot CLI calls return complete JSON. |
| result_ttl_ms / memory_quota_bytes | 300,000 / 67,108,864; opaque result handles expire or may be evicted at the quota. Follow the manifest's firstUri/nextUri with cyrs_result_read. Expiration reports an error and never reruns an action. |
| disk_spooling / disk_quota_bytes / spool_directory | false / 268,435,456 / explicitly selected directory; optional private spill storage. |
| cache_ttl_ms / notifications | 30,000 / false; discovery/read metadata caching and an independent bounded change journal. tools/call mutations are not memoized. |
| remote_notifications | false; supported remote subscriptions invalidate discovery/read caches. Other servers retain TTL and explicit reconnection. |
| metrics / metrics_file | false / optional private JSONL; operation names, durations, sizes, status and cache hits only. No prompts, tool bodies, keys or session identifiers. |
| context_bytes / context_recent_turns | 0 / 8; optional byte budget for API history projection. Full host history, system instructions, the active turn and complete tool exchanges remain stored. Native CLI agents keep their own context. No automatic summary is configured. |
| persist_history / restore_history / history_directory | false / false / explicit private directory; optional SDK checkpoints. Restore only with the same provider account, endpoint and model. No interrupted action is replayed. Explicit restore requires an existing checkpoint; otherwise disable restore for the first connection. |

The overlay keeps the full in-memory conversation; state polling returns only its most recent 32 messages plus the total count. SDK persistence is opt-in and contains private conversation/attachment data, not provider configuration or API keys. Restored user/assistant messages are reloaded into the panel. New conversation starts a fresh SDK session and removes the active saved checkpoint. The documentation reader's own bookmarks and notes are separate.

## Other applications {#remote}

`remote_tools` is an explicit allowlist. Each server has an `id`, either an HTTP `url` plus optional `token_env`, or a native `executable` with `arguments` and optional `cwd`, and a `tools` array of exact remote names. Credentials belong in the named environment variable, never in this JSON. `cyrs_refresh` explicitly refreshes forwarded schemas and read caches. `allow_resources: true` additionally enables qualified remote resource listing/reading tools; follow remote chunk links through that server’s read tool. Chat, stdio and controlled HTTP profiles delegate only tools advertised as read-only. Free and Token only HTTP profiles can invoke every explicitly allowlisted tool; the remote application still enforces its own permissions.

The SDK follows remote tool pagination and preserves each selected input schema. Unsupported schema keywords or transport capabilities produce an error rather than an invented connector. Remote errors return as tool failures. No filesystem search root, ripgrep executable, shell, model weights, driver installer or automatic external server discovery is enabled by default.

## Boundaries {#limits}

Windows x64 is the delivered platform. The native console uses the Microsoft Visual C++ 2015–2022 x64 runtime, as does the add-on build. The package retains the existing bundled shader compiler and frozen companion runtime.

Catalog import and approval previews are bounded by the existing local bridge (1 MiB requests; 100,000-byte approval payloads). FX source reads remain restricted to configured shader roots and page by UTF-8 byte offset; names, values and limits use filtered/paginated reads. Native shader inspection remains DX11/DX12 pixel-shader inspection, not source reconstruction. PNG capture remains available to MCP; a capture tool call does not automatically turn every provider into a vision model. Attach a file only when the selected provider supports its content type.

## Related topics {#related}

- [Chat](doc:chat)
- [Permissions](doc:permissions)
- [External MCP clients](doc:mcp)
- [History and provider data](doc:history-privacy)
