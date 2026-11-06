---
id: reference
title: Limits and technical reference
description: Check supported APIs, effect limits, capture sizes and tool budgets.
section: Guides
order: 18
revision: 3
parent: troubleshooting
---

## Overview {#overview}

| Item | Current limit / behavior |
| --- | --- |
| Chat | 32 RAM messages. Provider history: 16 prior messages / 24,000 characters. Input: 4095 UTF-8 bytes. |
| Tool budget | Automatic / Ask each time: 8 calls and one rendering operation. Full access: 16 calls and 8 rendering operations. |
| Patch | Up to 64 parameter/technique changes; current types and bounds are checked. |
| Generated FX | 16 named float controls; constrained body without unrestricted loops/includes. |
| Catalog | 32 MiB per scanned file; JSON import up to 16 MiB; descriptions up to 20,000 characters. |
| Native shaders | DX11/DX12 pixel shaders; 4096 captured hashes / 64 MiB per device. |
| DX12 snapshots | 4096 PSO snapshots / 128 MiB, at most 4 MiB each. |
| GPU replacement lifetime | Retained until device teardown; at most 64 DX11 versions or 256 DX12 PSO variants. |
| Capture | Single frame, maximum dimension 1280; no continuous recording or HDR tone mapping. |
| Local bridge | Protocol 1, local Windows user pipe; request up to 1 MiB, reply up to 8 MiB. |

Session, runtime, generation and revision tokens protect against stale edits. Parameter IDs are transient indexes, not portable identities. Reload can invalidate IDs and undo. A timed-out command may already have started: read current state first.

```callout
{"type": "info", "title": "Note", "body": "Not implemented: shader-pack web downloading, automatic screenshot analysis in integrated chat, automatic HUD identification, Vulkan/other-stage native replacement, historical preset backups, native-replacement replay and response streaming."}
```

## Related topics {#related}

- [Glossary](doc:glossary)
- [Inspect and replace game shaders](doc:native-shaders)
- [External MCP clients](doc:mcp)
