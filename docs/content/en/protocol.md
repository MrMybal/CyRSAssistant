---
id: protocol
title: Local bridge API
description: Protocol 1, version tokens, native commands and trust boundaries.
section: Developer reference
order: 100
revision: 1
kind: api
---

## Transport {#transport}

The game exposes `\\.\pipe\CyRSAssistant-<pid>`, restricted to its Windows user SID and rejecting remote clients. A worker handles pipe I/O; ReShade callbacks alone read or mutate the runtime.

Each connection carries one request and response. Frames are a four-byte little-endian unsigned length followed by UTF-8 JSON. The client acknowledges a complete response with one byte before closing. Limits: 1 MiB per request, 8 MiB per response. I/O is cancellable during shutdown.

Every request contains `protocol: 1`, a nonempty `request_id` of at most 100 characters, and `method`. All methods except `list_sessions` require an explicit `runtime`. See the indexed [dispatcher](doc:source-src-addon-cpp#source), [bridge](doc:source-src-bridge-cpp#source) and [Python client](doc:source-companion-transport-py#source).

## State and edits {#state}

| Method | Additional fields | Result |
| --- | --- | --- |
| `list_sessions` | none | Session and runtime identifiers |
| `get_state` | runtime | Loaded effects, names, types, bounds, values, roots and version tokens |
| `scan_effects` | runtime | Enumerates loaded effects; increments generation and discards undo |
| `apply_patch` | full version, changes; optional prompt_id | Validates all changes before writing; verifies readback and attempts rollback on mismatch |
| `undo` | full version | Restores the last patch if touched values still match |
| `save_preset` | full version | Saves the active preset through ReShade |
| `reload_effects` | full version | Reloads FX; invalidates IDs and undo |
| `assistant_reply` | session, runtime, prompt_id, message | Displays the reply only while that prompt is pending |
| `assistant_progress` | session, runtime, prompt_id, message | Updates the current operation status |

Full version means `session`, `runtime`, `generation` and `revision` read from the current state. Parameter/technique IDs are indexes scoped to a generation, never portable shader identities. Re-enumerate after reload, reconnection or runtime changes.

A patch has at most 64 `{kind, id, value}` entries. Techniques use a boolean; parameters use typed component arrays. Replies have `ok: true` plus a result or `ok: false` plus `error`.

Recent mutation replies are retained to deduplicate exact retries: at most 256 requests and approximately 16 MiB. A retained request ID cannot be reused with another payload. Read-only polls are not cached. Version preconditions still apply.

Queued commands expire after five seconds without an appropriate runtime callback. A timeout can race an already started operation: read state before retrying. A closed or minimized game may stop presenting; expired commands do not apply when rendering resumes.

## Native shaders and generation {#shaders}

`list_game_shaders(runtime)` returns captured SHA-256 bytecode identities, bind counters, `api` and per-shader `encoding`, `pipelines`, `replaceable_pipelines`, `limitation` and `error`. `inspect_game_shader(runtime, hash)` returns assembly, reflection, surviving binding declarations and the original stage/profile. This is not the original HLSL.

Mutations require the full version and accept an optional `prompt_id` to reject cancelled overlay work:

- `generate_effect(body, name?, title?, parameters?, replace_effect?)` precompiles a constrained float3 body, writes a content-addressed FX in the first configured effect root and reloads effects. Poll `generated.phase`: compiling, initializing, ready, cancelled or error. No different source overwrites an existing generated file.
- Up to 16 float parameters have `{name, label, min, max, default, step}` and become `CyRSP_<name>` controls. `CyRSPixelSize` supplies inverse buffer dimensions. Global declarations/includes are not accepted.
- `replace_effect` identifies an exact loaded FX filename; all its techniques must be editable. Activation changes only after successful initialization and verification. Original source remains intact.
- `restore_generated_effect()` restores the previous technique states of the most recent FX replacement.
- `replace_game_shader(hash, source)` compiles `main` for the original profile, validates signatures/resources, and activates at subsequent binds. Returns original/replacement hashes and, for DX12, `rebuilt_pipelines`.
- `enable_game_shader(hash, enabled)` toggles a compiled replacement; `restore_game_shaders()` disables all replacements on the runtime device.

Original bytecode is retained. Hashes cover all bytecode bytes, not semantic meaning. Capture is bounded to 4096 hashes / 64 MiB per device. DX11 retains at most 64 GPU replacement versions until teardown. [Native workflow](doc:native-shaders).

## DX12 / DXIL {#dx12}

All currently required DX12 PSO variants are created before publishing a replacement. A failure destroys only unpublished variants and preserves the previous rule. Later compatible PSOs receive variants; an incompatible one disables the rule with a visible error.

Capture limits: 4096 PSO snapshots / 128 MiB, at most 4 MiB each. Stages, vertex layouts and semantic names are deeply copied; the root signature has a retained COM reference. At most 256 GPU PSO variants remain until teardown. Restoration does not rewrite command lists already recorded.

DXIL uses Microsoft DXC 1.8.2505.32; register spaces, signatures, constants and resources are checked. DXBC 5.1, mesh/raytracing pipelines and other shader stages are not supported.

References: [ReShade examples](https://github.com/crosire/reshade/blob/main/examples/README.md), [D3DReflect](https://learn.microsoft.com/windows/win32/api/d3dcompiler/nf-d3dcompiler-d3dreflect), [DX12 pipeline state](https://learn.microsoft.com/windows/win32/direct3d12/managing-graphics-pipeline-state-in-direct3d-12), [pinned DXC release](https://github.com/microsoft/DirectXShaderCompiler/releases/tag/v1.8.2505.1).

## Conversation {#conversation}

`get_state.conversation` holds at most 32 `{role, content, mode}` objects per runtime in RAM. Provider context is bounded to 16 prior messages / 24,000 characters. `prompt_id` rejects stale responses. Cancelling does not restore previous edits.

`send_chat(runtime, session, text)` uses the Send button's validation: connected provider, no pending request and 1–4095 UTF-8 bytes, not whitespace alone. It returns `prompt_id`. No effect or shader selection is required. Overlay messages use mode 3; legacy modes 0/1/2 remain interpreted by the companion.

The model tools page inventories with `get_effects` and `get_parameters`. `read_effect_source` resolves FX/FXH only under configured roots and refuses ambiguous duplicates and traversal. Model responses never execute a shell or arbitrary native methods.

## Permissions {#permissions}

`get_state.permissions` exposes `mode` (0 Automatic, 1 Ask each time, 2 Full access), `epoch` and current `request`. `set_permission_mode(runtime, session, mode)` cancels pending work and persists the mode. Local UI controls are not model tools.

`request_action_permission(runtime, session, prompt_id, action, payload, summary)` returns a unique permission ID and pending/approved status. `resolve_action_permission(permission_id, allow)` applies the panel decision. The companion keeps its heartbeat alive while waiting.

An approval is bound to the exact payload, prompt and permission epoch, and consumed once. Source reading uses `consume_read_permission` before reading/transmission. Denial/cancellation interrupts the action. External MCP writes enabled by `--allow-write` remain separate.

## Language {#language}

`get_state.language` and `get_connection.connection.language` expose the saved locale. `set_language(runtime, session, language)` persists it to ReShade.ini. English is the default/fallback; French and supported regional codes resolve to their base language.

Changing language preserves rendering revisions, conversation, connection epochs, pending requests and permission tokens. Existing/pending replies keep their language; future requests use the new one. [Localization](doc:localization).

## CyDoc help controls {#help}

These local UI commands are not AI/MCP tools:

- `get_help_state(runtime)` returns the selected page, anchor/media, locale, last launched file URL and local error status.
- `open_help(runtime, session, chapter?, anchor?, media?, query?, open?)` validates stable page/section/media IDs, then opens the installed CyDoc reader through a correctly encoded file URL. `chapter` keeps the original 21 IDs and also accepts indexed documentation pages.
- `open: false` clears the local launch status; it cannot close an external browser window. This replaces the 0.8 floating ImGui manual window.
- Reading help does not call a provider or change rendering, history or permissions. The old `index.en.html#start` and `index.fr.html#start` entry files redirect to the equivalent CyDoc route.

[Native help integration](doc:source-src-manual-cpp#source) · [External MCP](doc:mcp).
