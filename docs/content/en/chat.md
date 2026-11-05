---
id: chat
title: Chat, history and useful requests
description: Chat, history and useful requests
section: User guide
order: 4
revision: 1
---

## Overview {#overview}

1. Connect and open Chat. Ordinary conversation needs no loaded effect or selected shader.
2. Write in Your message. Enter adds a line; Ctrl+Enter or Send submits.
3. Wait for progress. The response appears when finished, without streaming.
4. If an approval appears, inspect values/code and choose Allow this action or Deny this action.
5. Review the result before refining, restoring or saving.

```image
{"id": "chat-preview", "src": "assets/screenshots/chat-preview.png", "alt": "Earlier v0.4.0 capture: chat history and an FX-generation example. Data access and controls have evolved since this capture.", "controls": "minimal"}
```

Earlier v0.4.0 capture: chat history and an FX-generation example. Data access and controls have evolved since this capture.

```text
List the installed bloom FX and read their parameter names, values and ranges. Do not change anything yet.
```

```text
Make colors slightly warmer while keeping current exposure. Use installed effects and report the values changed.
```

The assistant can page through names, values, bounds, descriptions and permitted FX/FXH sources or native inspection. Exact filenames reduce ambiguity. A hash identifies game bytecode, not its visual purpose.

New conversation clears local history and the draft, without undoing rendering. Copy conversation copies the transcript; messages also have Copy. One request runs at a time. Cancel request stops later actions; already applied changes remain active.

## Related topics {#related}

- [Permissions and approvals](doc:permissions)
- [Inspect and tune installed effects](doc:effects)
- [History, storage and provider data](doc:history-privacy)
