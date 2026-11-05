---
id: history-privacy
title: History, storage and provider data
description: History, storage and provider data
section: User guide
order: 15
revision: 1
---

## Overview {#overview}

| Data | Lifetime / location |
| --- | --- |
| Conversation | Up to 32 messages in RAM per ReShade runtime. Lost when runtime/game closes. |
| Provider context | Up to 16 prior messages / 24,000 characters, plus relevant request and shader/tool data. |
| Settings | Provider, endpoint, model, language and permissions in ReShade.ini. |
| API key | Memory for the session; enter again after restart. |
| Catalog | CyRSAssistant/library: metadata and requested descriptions. |
| Replacement archive | CyRSAssistant/replacements: proposed HLSL and metadata, without replay. |
| Generated FX / preset | Configured shader folders / active preset, written by corresponding operations. |

Switching providers keeps local recent history, which may accompany the next request to the newly selected provider. New conversation clears local context; it does not erase provider records or restore rendering.

```diagram
{"type": "flow", "title": "Request data path", "nodes": [{"id": "node-0", "label": "Your message and recent context", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Relevant effect names and values", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Authorized source/disassembly if needed", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Selected provider", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Validated response and tools", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

Source-reading permissions matter because code/disassembly can be transmitted. Integrated chat does not automatically see screenshots. External MCP clients independently decide what they send to models.

```callout
{"type": "info", "title": "Note", "body": "Provider retention, billing and account access belong to the provider. Do not type secrets in chat. Copy puts transcript contents on the clipboard; review before sharing. This manual itself is local and needs no companion or network. CyDoc can keep reader bookmarks and private notes in browser storage, depending on the file-origin policy; use its export controls for a separate copy."}
```

## Related topics {#related}

- [Chat, history and useful requests](doc:chat)
- [Permissions and approvals](doc:permissions)
- [Updates, backups and rollback](doc:update)
