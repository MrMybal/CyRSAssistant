---
id: start
title: Start here
description: Connect an AI provider and make your first reversible rendering change.
section: Get started
order: 0
revision: 3
---

## Overview {#overview}

CyRSAssistant is a Windows x64 ReShade add-on. Describe a look, inspect real effect names and values, tune a preset, generate a new FX or replace an identified game pixel shader. A separate companion connects the game to your provider.

1. Install the complete ZIP beside the ReShade DLL used by the actual game executable.
2. Open ReShade (Home by default, or your configured shortcut), then CyRSAssistant.
3. Choose a provider in Connection and connect.
4. Ask in Chat. Review the result before saving the preset.

```diagram
{"type": "flow", "title": "Your first session", "nodes": [{"id": "node-0", "label": "Install the ZIP", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Connect a provider", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Describe or inspect", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Review the result", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Save or restore", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

```callout
{"type": "info", "title": "Note", "body": "Help works while disconnected and with no loaded effects. It opens the packaged CyDoc reader in your default browser through file://. Reading never calls a provider or changes rendering."}
```

English is the default. Options > Language > Français switches the interface immediately and selects French for the next manual launch. The reader also offers an English / Français selector while keeping page and section IDs.

## Related topics {#related}

- [Installation and requirements](doc:install)
- [Connect a provider](doc:connect)
- [Chat, history and useful requests](doc:chat)
- [Troubleshooting](doc:troubleshooting)
