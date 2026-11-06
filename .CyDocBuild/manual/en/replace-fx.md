---
id: replace-fx
title: Replace an existing FX
description: Identify an existing FX, compile its replacement and restore the previous effect.
section: Guides
order: 8
revision: 3
parent: effects
---

## Overview {#overview}

FX replacement differs from adding another effect and from replacing a native game shader. Identify the exact loaded FX filename. If several bloom effects exist, ask for their names first.

```text
Inspect loaded Bloom.fx and its controls. Replace that FX with an anamorphic version, keeping a threshold and useful intensity range. Do not add a second bloom alongside it.
```

1. Identify the filename and read its source/parameters when permitted.
2. Request an explicit replacement. Ambiguous targets need clarification. A capability question can receive an explanation before an action.
3. The new FX is compiled and initialized before original techniques are disabled. The original file is preserved.
4. Verify the new effect is active and the old techniques are off.
5. Restore replaced effect restores the tracked previous activation states and disables the replacement.

```diagram
{"type": "flow", "title": "Reversible FX replacement", "nodes": [{"id": "node-0", "label": "Identify original FX", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Compile separate new FX", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Initialize new technique", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Disable original techniques", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Restore tracked original if needed", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

```callout
{"type": "info", "title": "Note", "body": "Restoration tracks the most recent replacement in memory. Restart, reload or later changes can make it unavailable. Keep source/preset backups; this is not a permanent version history."}
```

## Related topics {#related}

- [Generate a new ReShade FX](doc:create)
- [Inspect and replace game shaders](doc:native-shaders)
- [Inspect and tune installed effects](doc:effects)
