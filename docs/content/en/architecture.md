---
id: architecture
title: Architecture: historical design and limits
description: Architecture: historical design and limits
section: Developer reference
order: 120
revision: 1
---

## Proposed architecture {#design-1}

This preserves the September 2026 design proposal. It is a roadmap, not a statement that every described tool exists. Compare buttons, web downloads, game profiles, disk session/backups and automatic vision remain objectives. Current capabilities are in [Start here](doc:start), [Limits](doc:reference) and [Protocol](doc:protocol). Actual SDK versions are pinned; API keys are session-only RAM data.

## Intended experience {#design-2}

A ReShade panel accepts a request such as “a cooler cinematic look without crushed blacks”. The assistant consults installed effects, prepares bounded settings, applies them, and allows inspection and undo. Reference-image input was an intended extension where a connector supports vision.

Distinguish a preset (values and effect ordering), a ReShade post-process FX, and a native game-rendering shader. Creating, installing and replacing them require different tools.

## Components {#design-3}

### Native C++ add-on {#design-4}

The proposal includes conversation/status/catalog UI; scan, compare, undo/save controls; enumeration of loaded effects, techniques, annotations and values; typed bounded commands and deliberate preset saves; one-shot captures for vision-capable clients. Current implementation has no Compare button or automatic vision loop.

A command queue is consumed in suitable ReShade callbacks. Long networking/model work stays outside the render thread. Reload invalidates runtime handles; stale requests are rejected. Every command selects a session/runtime to support multiple runtimes safely.

### Local companion {#design-5}

The companion handles chat, catalog indexing/descriptions and adapters. Direct provider connections and external-agent tools are distinct workflows; compatibility with individual clients must be verified.

Downloading/verifying shader packages outside the game was proposed but is not implemented. The implemented bridge is a versioned, bounded user-local Windows named pipe. Secrets must stay outside portable exports; current API keys remain only in RAM.

The assistant UI stays in ReShade while the companion isolates long tasks and connector failures.

## Portable catalog design {#design-6}

The proposed structure included:

```text
CyRSAssistant/
  library/catalog.json
  library/descriptions/
  profiles/<game-id>/
  sessions/
  backups/
  generated/
```

Only the actual implemented library/replacement storage should be assumed; proposed profile/session/backups directories are not promised.

The shared catalog describes effects, uses and dependencies. Planned game profiles would record depth availability, graphics API, settings and HUD rules. Copying descriptions cannot guarantee the same look in another game.

Proposed entries carry stable identity, relative path, content/include/texture fingerprints, known origin/revision/license, techniques, parameters and annotations. AI descriptions record model/date/schema, analyzed fingerprints and validation status. Measured GPU costs belong to hardware, resolution and game context.

Scanning combines configured search roots with loaded state, reports additions/changes/removals, and invalidates affected descriptions. Compilation errors can only be shown when available. Continuous filesystem monitoring remains a future extension; current invalidation is conservative rather than a compiler dependency graph.

Portable exports carry chosen metadata/descriptions without secrets or required absolute paths. Imports reconcile local files by fingerprint; redistribution of source must respect its license. The current export does not bundle profiles or shader assets.

## Proposed assistant tools {#design-7}

These were conceptual names, not the current public allowlist:

- get_capabilities / get_session_state: capabilities and game context.
- scan_library / search_library / describe_effect: catalog and reusable memory.
- get_effect_parameters / get_preset: real state before edits.
- apply_preset_patch / restore_snapshot / save_preset: changes with undo.
- capture_frame: a single visual return.
- search_packages / stage_package / install_package: controlled acquisition.
- stage_effect / reload_effects: FX creation/editing.
- Future inspect_pipeline / test_hud_rule / stage_shader_replacement.

Current names and contracts are in [Protocol](doc:protocol) and the [MCP source](doc:source-companion-mcp-py#source).

Each change needs a request ID, session/runtime generation and expected preconditions. The companion checks structure/scope, then the add-on checks real state. Results distinguish success, refusal/error and potential partial application. Retrying must not duplicate an edit.

## Tuning and creation loop {#design-8}

1. Read available effects/values and dependencies for the requested look.
2. Preserve the starting state and prepare a limited change.
3. Validate parameters, types and techniques.
4. Apply and read back values; obtain visual feedback.
5. Adjust from user feedback, or a capture in a vision-capable external client.
6. Save deliberately or restore.

The design calls for separately staged FX, backups and controlled reload. On failure a system should restore previous files where possible, without promising uninterrupted GPU compilation. The actual constrained generator preserves original FX sources and has only its documented restoration scope. Performance mode can make controls unavailable.

## Search and downloading objectives {#design-9}

A future downloader should start with known repositories and pinned revisions. GitHub gives provenance, not a safety guarantee. Record URL/commit/fingerprints/license; bound archive paths, sizes, extensions and dependencies; never execute shader-pack installation scripts. Stage separately with backup and rollback.

Remote READMEs/comments/descriptions are model data, not instructions authorizing actions. Distinguish presets, FX source and native add-ons. No downloader exists in the current product.

## HUD and native shaders {#design-10}

Post-processing cannot universally remove an already composited HUD and recover occluded pixels. Skipping draws, capturing before HUD, or injecting effects earlier are distinct rendering tasks.

CyGameCapture and CyGPUInspector are design references only; they are not dependencies or bundled components.

A replacement profile must identify game/version/API, original bytecode and resource contracts. Game updates can invalidate it. Never activate an uncertain match; provide a global restore. This principle is implemented for captured pixel-shader hashes, without permanent game-profile replay.

ReShade examples demonstrate replacement, but a universal live system requires backend-specific pipeline, bytecode/resource and GPU lifetime work. Inspection does not recover original HLSL. Current work covers DX11/DX12 pixel shaders within stated contracts.

## Original milestones and checks {#design-11}

1. Native foundation: build, display UI, enumerate effects in a target game, pin the SDK/full-add-on requirements.
2. Local commands: edit, read back, undo/save; test disconnect and reload without stale handles.
3. Portable memory: scan changes, export/import into another installation.
4. First provider: convert a request to validated operations; reject invented parameters.
5. One live FX: stage/reload, change through text and undo.

These are historical acceptance goals. Current automated/game checks are recorded in release context; visual quality must still be evaluated per game.

## Historical primary references {#design-12}

Originally consulted 22 September 2026: [public ReShade API](https://github.com/crosire/reshade/blob/main/include/reshade_api.hpp), [official dump/replace examples](https://github.com/crosire/reshade/blob/main/examples/README.md), [API documentation](https://crosire.github.io/reshade-docs/). Those links follow upstream main; the application itself uses pinned dependency versions.
