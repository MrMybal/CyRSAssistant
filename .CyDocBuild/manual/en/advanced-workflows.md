---
id: advanced-workflows
title: Advanced CLI, catalog and shader workflows
description: Use the catalog, command-line API and external clients for advanced tasks.
section: Guides
order: 110
revision: 3
parent: cli
---

## Advanced command-line workflow {#advanced-1}

Use these commands when you need explicit control over a catalog, an API request or an external client. Normal chat only requires the ReShade panel.

## First experiment {#advanced-2}

Start with a small change and inspect its effect before adding another operation.

## Install and inspect {#advanced-3}

Use Windows x64, ReShade 6.8 with full add-on support, API 20 and ImGui 1.92.5. Extract the complete install ZIP alongside the ReShade DLL used by the rendering executable. Restart and open CyRSAssistant.

Scan effects, inspect techniques, values and tooltips, and confirm numeric edits with Enter. Runtime-driven values are read-only. Try a small change, Undo, then explicitly Save preset when satisfied. Scan re-enumerates loaded effects; Reload compiles newly installed FX. Performance mode can remove editable values.

## Companion and disk catalog {#advanced-4}

The overlay's Connect action starts the normal integrated service. The legacy `watch` command is a manual alternative; never run it alongside that service. Developer-package commands require Python 3.11+ from the directory containing `companion/`:

```bash
python -m companion discover
python -m companion state
python -m companion scan
python -m companion watch
python -m companion --pipe '\\.\pipe\CyRSAssistant-12345' --runtime 1 state
```

Replace the example PID/runtime with discovery results. Global options precede the subcommand. Multiple games/runtimes require explicit selection.

Scan writes `CyRSAssistant/library/catalog.json` under the ReShade base path. It reads EffectSearchPaths/TextureSearchPaths; a trailing `/**` enables recursion. Files over 32 MiB are reported as scan errors. Duplicate FX filenames remain ambiguous rather than being associated arbitrarily. Legacy watch rescans after generation/scan changes; it does not continuously watch the filesystem. Stop it with Ctrl+C.

## API connection and a look request {#advanced-5}

```text
CYRS_API_URL=https://YOUR-SERVER/v1/chat/completions
CYRS_MODEL=MODEL-IDENTIFIER
CYRS_API_KEY=provided separately only if required
```

Set these in the launching process environment for legacy CLI requests. They do not reuse the overlay's session-only credentials. The full endpoint must support messages, JSON response_format and complete Chat Completions JSON replies. HTTPS is required except on localhost/127.0.0.1/::1.

The normal overlay Chat accepts a request after connection. Relevant effect metadata accompanies it; authorized source/disassembly can also be transmitted. Screenshots are not sent automatically. The companion validates the response and the add-on revalidates current state before edits. Changed preconditions reject an old plan. Cancel stops pending work without undoing prior changes.

```bash
python -m companion ask 'Make the look slightly cooler without crushing blacks'
python -m companion ask 'Reduce saturation' --dry-run > plan.json
python -m companion apply plan.json
python -m companion undo
python -m companion save
```

Ask applies by default; dry-run only writes a plan. Apply refuses stale session/generation/revision tokens. Structural validation is local even when a provider emits valid JSON. [Protocol](doc:protocol).

## Portable descriptions {#advanced-7}

```bash
python -m companion describe Tonemap.fx
python -m companion export catalogue-portable.json
python -m companion import catalogue-portable.json
```

Describe sends the FX source prefix (maximum 60,000 characters) and metadata to the configured provider. Stored descriptions include model, date, content fingerprint and a visually-unverified status. They are reused only when inputs still match.

Invalidation is conservative: changing any scanned file invalidates descriptions; this is not dependency analysis by compilation. For reuse between games, retain identical files, relative directory organization and search-root order. Runtime values remain game-specific. Export carries metadata/descriptions, not shaders or API keys. Import populates the cache then rescans files actually present.

## External agent through MCP {#advanced-9}

Start a local stdio server from the developer package:

```bash
python -m companion.mcp
python -m companion.mcp --allow-write
```

Use the client's working-directory option for the folder containing companion, or the developer package's run_mcp.py launcher. Client configuration formats differ:

```json
{"command":"python","args":["<developer-package>/run_mcp.py","--allow-write"]}
```

Read-only tools cover sessions, state, frame capture and native shader inspection. Opt-in writes add FX/native replacement, patches, reload, undo and saving. The server pins its selected game. MCP conversation belongs to the external client; it is separate from the overlay chat. CyRSAssistant needs no provider API key to run the stdio bridge.

The implementation targets [MCP stdio 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports). Use the MCP configuration supported by your chosen client. [MCP guide](doc:mcp).

## Troubleshoot a CLI request {#advanced-10}

If discovery finds no pipe, keep the game running under the same Windows user. If a command times out, let the game present again and read its current state before retrying. For provider errors, check the full endpoint, model and required key. A catalog needs a writable ReShade base directory.

## Generate or replace {#advanced-11}

Chat can inspect real effect/technique names, parameter values/bounds and authorized sources. An ambiguous target needs clarification; a capability question can be answered without applying a change. Generated filenames carry a content fingerprint. A constrained one-pass effect supports up to 16 named float controls plus global blend. A bloom can expose threshold, strength, length and transition; sampling uses allowed screen taps rather than unrestricted shader declarations.

Replacing an FX keeps its source. After successful initialization the old techniques are disabled; Restore replaced effect restores their previous activation. Only the last replacement is tracked in memory, and technique positions are not guaranteed identical. Compilation success does not establish visual quality.

In Shaders, refresh captured hashes (sorted by usage), select a target and inspect signatures, resources and assembly. Replacement HLSL is compiled for the original profile, validated and armed at subsequent binds. Restore selected/all disables replacements. High usage does not identify a HUD shader; stripped metadata is supplemented by surviving DXBC declarations.

GPU versions stay until device teardown to protect outstanding references: 64 DX11 versions / 256 DX12 PSO variants. Proposed sources are archived under `CyRSAssistant/replacements/<original-hash>/`, not automatically replayed at restart. An external agent may explicitly submit archived source for a currently captured matching hash; matching bytes do not guarantee a desired visual result elsewhere.

### DX12 differences {#advanced-12}

The inventory shows DXBC/DXIL and reconstructible PSOs. Root signatures/resources remain compatible; DXIL register spaces are checked. Unknown subobjects, mesh/raytracing and capture-budget overflows are refused. DXBC Shader Model 5.1 is not supported. Existing command lists retain old PSO references; restoration affects subsequent binds, without rewriting recorded commands.
