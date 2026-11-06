---
id: native-shaders
title: Inspect and replace game shaders
description: Inspect captured pixel shaders and replace a precisely identified target.
section: Rendering / Game shaders
order: 9
revision: 3
---

## Overview {#overview}

Shaders observes DX11/DX12 pixel shaders captured after add-on startup, identified by SHA-256 bytecode hashes. Original semantic names or HLSL are usually unavailable. Counters and bindings do not prove a shader draws the HUD, bloom or an object.

1. Refresh game shaders while the relevant scene is rendered.
2. Select a hash and Inspect selected shader for signatures, resources and disassembly.
3. Identify the intended target through actual rendering analysis, not the hash alone.
4. Request a replacement for that exact target. The assistant may decline an uncertain reconstruction.
5. After compilation and compatibility checks, the replacement is armed for subsequent game binds. Inspect the scene and restore if unsuitable.

```diagram
{"type": "flow", "title": "Native replacement", "nodes": [{"id": "node-0", "label": "Capture original bytecode", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Inspect hash and contracts", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Identify the target", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Compile compatible HLSL", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Arm subsequent binds", "x": 20, "y": 420, "width": 570}, {"id": "node-5", "label": "Restore original bindings", "x": 20, "y": 520, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}, {"from": "node-4", "to": "node-5"}]}
```

Proposed HLSL is archived under CyRSAssistant/replacements/<original-hash>/ with metadata. This is not automatic replay: restarting does not reactivate a previous replacement. Captured original bytecode remains intact.

```callout
{"type": "info", "title": "Note", "body": "A shared shader can affect several objects. Pixel-shader replacement cannot freely change vertex processing, resource layouts or pipeline contracts. Unsupported signatures/resources/pipelines are rejected."}
```

## Related topics {#related}

- [DX12, restoration and HUD limits](doc:dx12-hud)
- [Troubleshooting](doc:troubleshooting)
- [Limits and technical reference](doc:reference)
