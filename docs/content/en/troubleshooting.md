---
id: troubleshooting
title: Troubleshooting
description: Troubleshooting
section: User guide
order: 16
revision: 1
---

## Overview {#overview}

| Symptom | Checks and recovery |
| --- | --- |
| Add-on missing | Confirm Windows x64, full add-on support, actual rendering executable folder, and ReShade Add-ons / Log. |
| Send disabled | Connect a provider, enter nonblank text, wait for the current request or cancel it. |
| CLI ready, no model reply | First message checks model access. Verify login, model, quota and provider availability outside the game. |
| API connection fails | Check full /chat/completions URL, model, JSON support, key and server. Remote HTTP is refused. |
| Local service unreachable | Disconnect/reconnect. Confirm CyRSAssistantCompanion.exe is next to the add-on. Missing heartbeat is reported after ten seconds. |
| No editable values | Reload effects; inspect compilation errors and performance mode. Chat still works. |
| Ambiguous FX source | Resolve duplicate filenames in overlapping search roots, or identify a unique loaded FX. |
| Generated effect fails | Read final status and ReShade Log. Correct the specific compiler error or request a simpler supported effect. |
| Old bloom remains | Check whether you requested addition or replacement, the exact target and technique activation. |
| Shader hash not found | Render the relevant scene after startup and refresh. A game update can change bytecode/hashes. |
| DX12 replacement refused | Read contract/pipeline errors. Confirm complete DXC runtime. Preserve the original. |
| Request timed out | Read current state before retrying: an action may have started. Keep the game rendering frames. |
| HTML manual missing | Re-extract CyRSAssistant/Documentation. Help reports the missing directory; re-extract the complete ZIP. |

1. Note visible status, action, exact FX filename/hash and graphics API.
2. Try a limited recovery: reconnect, refresh or restore as relevant; do not resubmit edits blindly.
3. Collect relevant Log/compiler lines and reproduction steps only. Remove personal paths, credentials and private chat details before sharing.

## Related topics {#related}

- [Connect a provider](doc:connect)
- [Inspect and tune installed effects](doc:effects)
- [Inspect and replace game shaders](doc:native-shaders)
- [Limits and technical reference](doc:reference)
