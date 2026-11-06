---
id: architecture
title: How the assistant works
description: Understand how ReShade, the companion and a provider process a request.
section: Guides
order: 120
revision: 3
parent: protocol
---

## How a request runs {#design-1}

CyRSAssistant connects the ReShade panel to a local companion and the provider you select. Open Chat for the conversation; use Effects or Shaders to inspect the actual result.

```diagram
{"type":"flow","title":"From your request to the rendered result","nodes":[{"id":"chat","label":"Your message in ReShade","x":20,"y":20,"width":570},{"id":"service","label":"Local companion and selected provider","x":20,"y":120,"width":570},{"id":"tools","label":"Read current effects and propose an action","x":20,"y":220,"width":570},{"id":"runtime","label":"ReShade checks and applies the action","x":20,"y":320,"width":570},{"id":"review","label":"Inspect the result, adjust or restore","x":20,"y":420,"width":570}],"edges":[{"from":"chat","to":"service"},{"from":"service","to":"tools"},{"from":"tools","to":"runtime"},{"from":"runtime","to":"review"}]}
```

## Choose the correct target {#design-2}

A preset stores effect settings. A ReShade FX adds post-processing. A native pixel shader belongs to the game’s rendering pipeline. State which one you want to change and identify the existing effect or shader when replacing it.

## What runs where {#design-3}

The C++ add-on runs inside ReShade. The companion handles provider requests outside the rendering thread. The documentation opens separately in your default browser and does not need a provider connection.

## The ReShade add-on {#design-4}

The panel reads loaded techniques and parameters, accepts bounded edits, creates FX and manages captured pixel shader replacements. ReShade callbacks apply runtime commands. A reload invalidates old parameter IDs; an old request can be refused rather than editing a new target accidentally.

## The local companion {#design-5}

Connect starts the companion. A recognized CLI login and a successful model response are separate states. If the service stops responding, disconnect and reconnect from Connection. The companion does not give the model a terminal or unrestricted file access.

## Catalog files {#design-6}

The optional command-line catalog is stored in CyRSAssistant/library. It records scanned metadata and descriptions requested explicitly. Keep this folder during updates. Portable exports carry descriptions and metadata; shader files must be installed separately.

## Tools available to the assistant {#design-7}

Chat can read named effects and parameter values, inspect authorized FX sources or native shader assembly, apply settings, generate an FX and request a native replacement. Permission mode controls approvals and the number of rendering operations. External MCP clients have their own conversation and a separate write switch.

## Apply, inspect and restore {#design-8}

1. Describe a small, recognizable change.
2. Let the assistant inspect current settings.
3. Review the scene after application.
4. Refine the request, undo the tracked patch or restore a replacement.
5. Save the preset explicitly when satisfied.

## Install shader packs yourself {#design-9}

The add-on does not download packs from the web. Install the files in a configured ReShade shader directory, then use Load / reload effects. Scan effects refreshes loaded controls; it does not install missing files.

## Native shader contracts {#design-10}

A captured hash identifies bytecode, not its visual purpose. Replacement preserves the supported signatures, resource bindings and pipeline contract. Only captured DX11/DX12 pixel shaders are supported. A shared shader can affect several objects.

## Read the current status {#design-11}

Connection status describes provider access. Generated-effect status describes compilation and activation. Native-shader errors describe capture or replacement limits. A successful compilation alone does not establish that the scene looks right.

## Where to look next {#design-12}

- [Tune an existing effect](doc:effects)
- [Generate an FX](doc:create)
- [Replace a game shader](doc:native-shaders)
- [Local bridge API](doc:protocol)
