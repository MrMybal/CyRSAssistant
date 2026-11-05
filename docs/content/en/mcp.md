---
id: mcp
title: External MCP clients
description: External MCP clients
section: User guide
order: 14
revision: 1
---

## Overview {#overview}

An external MCP client can start the developer package’s stdio server, including OpenCode or Antigravity when they support a local MCP command. These are not additional provider choices in the overlay.

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
{"type": "info", "title": "Note", "body": "External MCP conversation is not copied into overlay history. MCP writing is separate from integrated permission modes. Writes still require current version tokens and valid payloads; connection does not grant arbitrary native methods or filesystem access."}
```

## Related topics {#related}

- [Permissions and approvals](doc:permissions)
- [Capture and visual feedback](doc:capture)
- [History, storage and provider data](doc:history-privacy)
