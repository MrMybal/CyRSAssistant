---
id: mcp
title: External MCP clients
description: Connect an external MCP client with read-only tools or explicit write access.
section: External clients
order: 14
revision: 6
---

## Overview {#overview}

## Local HTTP server {#local-http}

In 0.10.1, enable **Options > Enable local MCP** and use **Copy MCP address**. No chat-provider connection is needed. In the default **Free** profile, the loopback address alone gives access to every exposed operation, without a token or extra confirmation. Argument and version validation stay active.

Choose **Local controlled**, **Token only** or **Protected** when those combinations are wanted. Existing explicit profile choices are retained; missing choices migrate to Free. Token profiles use **Copy MCP token** for the current session. See [all profiles and migration rules](doc:sdk#local-access).

## Native stdio server {#stdio}


In version 0.10.0, run `CyRSAssistantCLI.exe mcp` from the installation directory, with `--allow-write` only for a trusted client. `python -m companion.mcp` forwards to the SDK server. Writes also obey the overlay permission mode; Ask mode requires the real approval buttons. See [connection, tools and retained results](doc:sdk).

An external MCP client can start the developer package’s stdio server, including OpenCode or Antigravity when they support a local MCP command. OpenCode and Antigravity are also provider choices in version 0.10.0.

```bash
python -m companion.mcp
# Opt in to writes for a trusted client:
python -m companion.mcp --allow-write
```

```json
{
  "mcpServers": {
    "cyrsassistant": {
      "command": "python",
      "args": ["-m", "companion.mcp"],
      "cwd": "<developer-package-directory>"
    }
  }
}
```

This is a generic example: each client has its own configuration format and working-directory support. Use its equivalent for the directory containing companion/. Specify --pipe for multiple games. The server pins the discovered game instead of silently switching processes.

| Read-only by default | With --allow-write |
| --- | --- |
| List runtimes; read names, parameters and values; capture a frame; list/inspect native shaders. | Generate/replace FX; compile/toggle native replacements; restore; apply/undo patches; save presets; reload. |

```callout
{"type": "info", "title": "Note", "body": "External MCP conversation is not copied into overlay history. Stdio MCP writing additionally requires --allow-write and obeys the application permission mode. Writes still require current version tokens and valid payloads; connection does not grant arbitrary native methods or filesystem access."}
```

## Related topics {#related}

- [Permissions and approvals](doc:permissions)
- [Capture and visual feedback](doc:capture)
- [History, storage and provider data](doc:history-privacy)
