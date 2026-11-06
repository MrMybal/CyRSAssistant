---
id: effects
title: Inspect and tune installed effects
description: Read real effect values, edit techniques, undo changes and save a preset.
section: Rendering / ReShade effects
order: 6
revision: 3
---

## Overview {#overview}

1. Open Effects and Scan effects to enumerate loaded techniques and parameters.
2. Use Filter; expand Techniques or Parameters. Read filenames, labels, values and tooltips.
3. Toggle a technique or edit a value. Confirm numeric edits with Enter. Read-only values cannot be edited here.
4. Compare the rendering, Undo last edit when available, then Save preset only to persist the current settings.

| Action | What it changes |
| --- | --- |
| Scan effects | Refreshes the loaded inventory and IDs; normally clears undo. |
| Load / reload effects | Asks ReShade to recompile FX on the next frame. |
| Undo last edit | Restores one tracked patch if values still match and the inventory remains valid. |
| Save preset | Writes the active preset through ReShade. |

Scan is not a compiler reload or download. After adding an FX to a configured search folder, reload effects. Performance mode or compilation errors may leave no editable values. Chat still works.

```callout
{"type": "info", "title": "Note", "body": "Undo has one in-memory step. Manual edits, refreshes or reloads may invalidate it. Technique order is not changed. There are no automatic historical preset backups; keep copies before substantial edits."}
```

## Related topics {#related}

- [Generate a new ReShade FX](doc:create)
- [Replace an existing FX](doc:replace-fx)
- [Troubleshooting](doc:troubleshooting)
