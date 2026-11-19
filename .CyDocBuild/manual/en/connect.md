---
id: connect
title: Connect a provider
description: Choose a CLI session or API endpoint and understand the connection status.
section: Guides
order: 3
revision: 5
parent: start
---

## Overview {#overview}

Version 0.10.0 uses CyMCPSDK conversations. The provider selector additionally offers OpenCode ACP, Antigravity, OpenAI Responses, Anthropic Messages, Ollama and LM Studio. Available model IDs come from the configured provider when supported; disconnect/edit to change them. Never treat an installed CLI as proof of account or model access. See [SDK integration](doc:sdk).

| Provider | Requirements |
| --- | --- |
| Codex (CLI session) | Installed CLI and valid login. Empty Model uses its default. |
| Claude Code (CLI session) | Installed CLI and valid login. Empty Model uses its default. |
| OpenAI-compatible API | Full Chat Completions URL, model ID and key if required. |
| Local model (API) | Running compatible local server and actual model ID. |
| OpenCode ACP | Compatible OpenCode CLI and configured account/model. |
| Antigravity | Compatible installed native agent and its account. |
| OpenAI Responses | Responses API base URL, real model ID and key. |
| Anthropic Messages | Messages API base URL, real model ID and key. |
| Ollama | Running Ollama service and an already installed model. |
| LM Studio | Running LM Studio server and an already loaded model. |

1. Use Disconnect / edit before changing active settings.
2. Choose the provider. For Chat Completions, keep the existing full URL or use its API base URL. Other adapters use their API base URL and the real model ID.
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

Remote servers require HTTPS; HTTP is accepted only on localhost. The endpoint must implement the selected adapter (Chat Completions, Responses, Messages, Ollama or LM Studio). Local model does not install or start a model.

```callout
{"type": "info", "title": "Note", "body": "Connect initializes the SDK session and attempts model discovery when supported. It does not send a paid model prompt or prove inference access. The next message verifies actual model access; check endpoint, login, model and quota."}
```

## Related topics {#related}

- [Troubleshooting](doc:troubleshooting)
- [History, storage and provider data](doc:history-privacy)
- [External MCP clients](doc:mcp)
