---
id: install
title: Installation and requirements
description: Place the add-on, companion, DXC runtime and manual beside the rendering executable.
section: Guides
order: 1
revision: 4
parent: start
---

## Overview {#overview}

Use a 64-bit Windows game, ReShade 6.8 with full add-on support and the Microsoft Visual C++ 2015–2022 x64 runtime. The integration targets API 20 and the ImGui 1.92.5 bridge. Native game-shader replacement supports Direct3D 11/12 pixel shaders, not every graphics API.

1. Close the game and back up an existing installation.
2. Find the folder containing the game’s ReShade DLL, such as dxgi.dll or d3d11.dll. Use the rendering executable’s folder, not a separate launcher.
3. Extract the install ZIP directly there, retaining its folders. The developer ZIP has a different layout.
4. Start the game, check ReShade > Add-ons / Log, then open CyRSAssistant.

```text
Game folder
  CyRSAssistant.addon64
  CyRSAssistantCompanion.exe
  CyRSAssistantCLI.exe
  CyRSAssistantRuntime/
    dxcompiler.dll
    dxil.dll
    LICENSE-LLVM.txt
    LICENSE-MS.txt
  CyRSAssistant/
    INSTALL.txt
    sdk-options.example.json
    Documentation/
      Documentation.html
      DocAI.md
      DocData/
        assets/
  LICENCES/
```

Python is bundled in the companion. Normal overlay use needs neither a separate Python installation nor a terminal. Install and sign in to the selected native provider separately. API/local profiles use an existing server; they do not install models. Optional advanced settings use a separate sdk-options.json, described in [SDK options](doc:sdk#options).

```callout
{"type": "info", "title": "Note", "body": "Keep CyRSAssistantRuntime next to the add-on for DXC, and retain Documentation and LICENCES. The add-on does not install shader packs, provider CLIs or model weights."}
```

## Related topics {#related}

- [Updates, backups and rollback](doc:update)
- [Connect a provider](doc:connect)
- [Troubleshooting](doc:troubleshooting)
