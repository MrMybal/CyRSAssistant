---
id: create
title: Generate a new ReShade FX
description: Describe a new FX and request named controls for strength, threshold or color.
section: Guides
order: 7
revision: 3
parent: effects
---

## Overview {#overview}

Ask explicitly for an addition when you want a new post-process. The assistant generates a constrained standalone FX, precompiles it, writes a new content-addressed CyRS_<name>_<hash>.fx in a configured effect folder, reloads ReShade and checks activation.

```text
Add an anamorphic bloom with intensity, threshold, soft knee and horizontal spread controls. Keep existing effects enabled and provide useful control ranges.
```

```diagram
{"type": "flow", "title": "Generation lifecycle", "nodes": [{"id": "node-0", "label": "Describe an addition", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Generate and precompile", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Write a new FX", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Reload and initialize", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Read values and verify activation", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

Up to 16 named float controls are supported. The body uses authorized screen/color sampling, time and pixel-size helpers. Unrestricted includes, declarations and loops are not accepted. Some requests exceed the generator’s capabilities.

1. Wait for the final result; compiling and initializing are intermediate states.
2. Read the generated filename and parameters, then inspect them in Effects or ReShade Home.
3. Judge the actual picture and performance. Compilation alone proves neither.
4. Disable last generated effect if unsuitable. The source stays on disk. Saving a preset persists activation/settings, not a visual-quality guarantee.

```callout
{"type": "info", "title": "Note", "body": "Generation reloads effects and may briefly interrupt rendering. After an error/cancellation, inspect Effects and Log before retrying. Cancel does not delete files or restore edits already applied."}
```

## Related topics {#related}

- [Replace an existing FX](doc:replace-fx)
- [Inspect and tune installed effects](doc:effects)
- [Troubleshooting](doc:troubleshooting)
