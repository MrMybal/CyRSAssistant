---
id: connect
title: Connect a provider
description: Connect a provider
section: User guide
order: 3
revision: 1
---

## Overview {#overview}

| Provider | Requirements |
| --- | --- |
| Codex (CLI session) | Installed CLI and valid login. Empty Model uses its default. |
| Claude Code (CLI session) | Installed CLI and valid login. Empty Model uses its default. |
| OpenAI-compatible API | Full Chat Completions URL, model ID and key if required. |
| Local model (API) | Running compatible local server and actual model ID. |

1. Use Disconnect / edit before changing active settings.
2. Choose the provider. For an API, enter the full /chat/completions URL and the model expected by the server.
3. Enter a key in API key if needed; never in chat.
4. Click Connect. The companion starts automatically.
5. For CLI providers, the first normal message checks model access. A recognized login alone does not prove access or quota.

```image
{"id": "connection-preview", "src": "assets/screenshots/connection-preview.png", "alt": "Earlier development capture in French: provider selection and a recognized local Codex session. The current layout uses Connection.", "controls": "minimal"}
```

Earlier development capture in French: provider selection and a recognized local Codex session. The current layout uses Connection.

```text
URL: http://127.0.0.1:1234/v1/chat/completions
Model: the identifier reported by your server
API key: only if that server requires one
```

Remote servers require HTTPS; HTTP is accepted only on localhost. The endpoint must accept Chat Completions JSON requests and JSON responses. Local model does not install or start a model.

```callout
{"type": "info", "title": "Note", "body": "CLI Connect checks the local login without a model prompt. API Connect sends a small test to the selected server. Verify endpoint, login, model and quota when troubleshooting."}
```

## Related topics {#related}

- [Troubleshooting](doc:troubleshooting)
- [History, storage and provider data](doc:history-privacy)
- [External MCP clients](doc:mcp)
