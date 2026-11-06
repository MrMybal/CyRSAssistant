---
id: glossary
title: Glossary
description: Understand FX, presets, techniques, bytecode, PSOs and version tokens.
section: Help and reference
order: 19
revision: 3
---

## Overview {#overview}

| Term | Meaning |
| --- | --- |
| FX / FXH | ReShade post-process source / include file. |
| Technique | A render technique exposed by an FX; a file may expose several. |
| Uniform / parameter | Effect value, possibly read-only or driven by ReShade. |
| Preset | Current ReShade settings file, including activation and values. |
| Native game shader | Game-rendering bytecode, distinct from a ReShade FX. |
| Hash / fingerprint | Content identity, not a visual-purpose name. |
| DXBC / DXIL | Shader-bytecode encodings handled by supported backends. |
| PSO / root signature | DX12 pipeline state / resource-binding contract. |
| Companion | Background executable connecting the add-on to a provider. |
| MCP | Stdio tools interface for external clients. |
| Generation / revision | Version tokens used to reject outdated edits. |

## Related topics {#related}

- [Limits and technical reference](doc:reference)
- [Inspect and tune installed effects](doc:effects)
- [Inspect and replace game shaders](doc:native-shaders)
