---
id: cli
title: Advanced command-line use
description: Use the companion command line to inspect, plan, apply and restore changes.
section: Guides
order: 13
revision: 3
parent: catalog
---

## Overview {#overview}

The install ZIP is self-contained for the overlay. The developer ZIP adds companion/ and Python CLI/MCP modules. Run these commands from that package directory with Python 3.11+. Do not run historical watch alongside the integrated service.

```bash
python -m companion discover
python -m companion state
python -m companion scan
python -m companion ask "Make colors slightly cooler" --dry-run > plan.json
python -m companion apply plan.json
python -m companion undo
python -m companion save
python -m companion reload
```

ask applies changes unless --dry-run is supplied. Review a dry-run plan, then apply only to the same current session/generation/revision. Stale plans are refused. save writes the preset; undo uses the single tracked snapshot.

```bash
python -m companion --pipe "\\.\pipe\CyRSAssistant-12345" --runtime 1 state
```

Replace the example PID/runtime with discovery results. Global --pipe and --runtime precede the subcommand. Legacy CLI provider requests use CYRS_API_URL, CYRS_MODEL and optionally CYRS_API_KEY in the process environment; they do not reuse the overlay’s session-only key.

```callout
{"type": "info", "title": "Note", "body": "CLI diagnostics may expose local paths. Review them before sharing. Use the overlay connection for the standard assistant workflow; watch is a legacy manual pathway."}
```

## Related topics {#related}

- [Catalog, descriptions and portability](doc:catalog)
- [External MCP clients](doc:mcp)
- [Limits and technical reference](doc:reference)
