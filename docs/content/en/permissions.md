---
id: permissions
title: Permissions and approvals
description: Permissions and approvals
section: User guide
order: 5
revision: 1
---

## Overview {#overview}

| Mode | Behavior |
| --- | --- |
| Automatic (default) | Reads and requested edits without extra approval. One rendering operation per message. |
| Ask each time | Names and values directly readable. Each rendering edit and source/disassembly transmission needs approval. |
| Full access to ReShade tools | Reads and multiple rendering operations without intermediate approval. |

Select Options > Permission mode. The choice is saved per game. Changing mode cancels a pending request and invalidates its approvals, without restoring earlier edits.

```diagram
{"type": "flow", "title": "Ask each time", "nodes": [{"id": "node-0", "label": "Assistant proposes", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Inspect values or source", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Allow or deny in Chat", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Apply approved action", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Verify result", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

Approval belongs to one action, request and exact payload. A changed action needs another approval. Denying or cancelling interrupts the pending action. Review source-transmission summaries before approving.

```callout
{"type": "info", "title": "Note", "body": "Full access covers the add-on’s tools. It does not grant a terminal, arbitrary files or permissions in another AI app. External MCP writing is separately controlled by --allow-write."}
```

## Related topics {#related}

- [Chat, history and useful requests](doc:chat)
- [History, storage and provider data](doc:history-privacy)
- [External MCP clients](doc:mcp)
