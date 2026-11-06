---
id: dx12-hud
title: DX12, restoration and HUD limits
description: Understand DX12 pipeline replacement, restoration and HUD removal limits.
section: Guides
order: 10
revision: 3
parent: native-shaders
---

## Overview {#overview}

In DX12, compatible graphics PSOs are rebuilt with the replacement pixel shader, preserving other stages, state and root signature. All currently required PSOs must succeed before activation. A later incompatible PSO disables the replacement with an error.

DXIL uses bundled Microsoft DXC and its validator. Register spaces, signatures and resource contracts are checked. Compilation support does not guarantee an AI can reconstruct a complex game shader faithfully.

1. Use Restore selected shader, or Restore all original shaders for the device.
2. Restoration takes effect on subsequent binds. Already recorded command lists can still reference the previous pipeline.
3. Read limitations/errors and ReShade Log. Keep the original when uncertain.

```diagram
{"type": "flow", "title": "Why a final filter cannot always remove a HUD", "nodes": [{"id": "node-0", "label": "Game scene is rendered", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "HUD may be composed into the same image", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "ReShade sees the resulting pixels", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "An earlier rendering stage may be needed", "x": 20, "y": 320, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}]}
```

```callout
{"type": "info", "title": "Note", "body": "There is no automatic HUD identification or universal removal switch. A post-process cannot recover hidden scene pixels by deleting a composited HUD. CyGameCapture and CyGPUInspector are not bundled. Native replacement does not cover Vulkan, vertex stages or mesh/raytracing pipelines."}
```

## Related topics {#related}

- [Inspect and replace game shaders](doc:native-shaders)
- [Capture and visual feedback](doc:capture)
- [Limits and technical reference](doc:reference)
