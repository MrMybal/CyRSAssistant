# CyRSAssistant — Version notes

[Back to README](README.md) · [Français](VERSION.fr.md)

**Application: 0.10.1 · Stage: PROTOTYPE**<br>
**Published package: 0.10.1 · Windows x64**<br>
**Target: ReShade 6.8 / API 20 with full add-on support**

This prerelease is intended for testing and feedback. Rendering quality and compatibility depend on the game and selected shaders. Publication does not establish stable support for every game.

## Changes in 0.10.1 — local MCP profiles

- CyMCPSDK 0.7.1 at `34d4bcae126bc83d1a2925b5047dac36e3d09d92`, built from the pinned local source snapshot.
- Optional loopback HTTP MCP in Options, defaulting to Free for missing profile choices.
- Preserve explicit profiles; provide Free, Local controlled, Token only and Protected. Keep argument/version validation in every profile.
- CLI/stdIO and integrated chat retain their existing permissions. The install ZIP includes the updated binaries and complete offline manual.

[Download 0.10.1 and release notes](https://github.com/MrMybal/CyRSAssistant/releases/tag/v0.10.1)

## Changes in 0.10.0 — CyMCPSDK integration

- CyMCPSDK 0.7.0, revision `791d4d7d7680213b282ec8529d248a10f8494d77`, compiled from its pinned native sources.
- Shared operation registry for integrated chat, console and MCP, preserving native validation, undo and explicit preset saves.
- Streamed conversations, cancellation, provider/model discovery, explicit attachments and optional private session checkpoints.
- Separate controls for compact discovery, retained/chunked results, disk spooling, TTL/change notifications, metadata-only metrics and API context windows.
- Existing Python CLI commands and launch flags retained. Only explicitly configured read-only tools are delegated to external MCP applications.

[Download 0.10.0 and release notes](https://github.com/MrMybal/CyRSAssistant/releases/tag/v0.10.0) · [Installation ZIP checksum](https://github.com/MrMybal/CyRSAssistant/releases/download/v0.10.0/CyRSAssistant-0.10.0-windows-x64.zip.sha256) · [Developer ZIP checksum](https://github.com/MrMybal/CyRSAssistant/releases/download/v0.10.0/CyRSAssistant-0.10.0.zip.sha256)

The package includes CyRSAssistantCLI.exe and the complete 27-page-per-language manual. Preserve private SDK options/history while updating all binaries together.

## Changes in 0.9.0

- Complete illustrated CyDoc help: 26 pages per language, English by default and a complete French edition, screenshots, SVG diagrams, search, themes and public API examples.
- Help tab, contextual Help buttons and F1 when the CyRSAssistant overlay has focus, opening the appropriate local documentation page.
- Hierarchical reader navigation, a wider sidebar, page descriptions and image enlargement inside the documentation window.
- The same complete HTML reader bundled for offline use and published on GitHub Pages, with compatibility redirects for older documentation links.
- Complete bundled runtime license notices and corresponding developer sources alongside the installation ZIP.

The included reader is **CyDoc 0.1.0**, pinned to revision `6ddf9a582defb2f11fbb3f992afef6f98dcadc93`. Its version is separate from the CyRSAssistant application version.

[Official release notes and downloads](https://github.com/MrMybal/CyRSAssistant/releases/tag/v0.9.0) · [Installation ZIP checksum](https://github.com/MrMybal/CyRSAssistant/releases/download/v0.9.0/CyRSAssistant-0.9.0-windows-x64.zip.sha256) · [Developer ZIP checksum](https://github.com/MrMybal/CyRSAssistant/releases/download/v0.9.0/CyRSAssistant-0.9.0.zip.sha256)

## Updating and rollback

Close the game. Keep a copy of the previous add-on, companion, runtime and notices before extracting the complete new package next to the ReShade DLL. Preserve ReShade.ini, presets, generated shaders and CyRSAssistant/library. Restore the previous binaries and runtime together to roll back. See the [update guide](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/en/update).

## Known issues

There is no itemized confirmed-bug list for this prototype release. Consult the [issue tracker](https://github.com/MrMybal/CyRSAssistant/issues) for reports or [report a problem](https://github.com/MrMybal/CyRSAssistant/issues/new). The limitations below describe product boundaries; they do not establish that there are no bugs.

## Current limitations

- **Platforms and native shaders:** the supplied build is Windows x64. Native replacement supports captured DX11/DX12 pixel shaders; other stages and Vulkan are not supported. Original game shader names and HLSL are usually unavailable; native shaders are identified by fingerprint. A shared shader can affect several objects, and the assistant may decline an uncertain reconstruction.
- **DX12 replacement:** each relevant pipeline state is rebuilt with its other stages, render state and root signature. Current pipelines must all succeed before activation. A future incompatible pipeline disables the replacement and reports an error. Already recorded command lists can still reference a previous shader version.
- **Generated FX:** generation produces constrained, standalone effects with up to 16 named controls, without loops or external dependencies. Compilation does not guarantee the requested visual result.
- **Editing and restoration:** technique order is not changed. Undo keeps one edit in memory and can be invalidated by an inventory change or reload. Shader replacements are not automatically reactivated when the game restarts. Saving writes the active preset; automatic historical preset backups are not implemented.
- **Unavailable automation:** shader-pack downloading, automatic screenshot analysis and automatic HUD identification are not implemented.
- **Providers and chat:** native agents require a compatible installed CLI and account. An initialized SDK session does not prove model access or quota. The response streams when the selected provider supports it. Automatic and Ask each time allow one rendering operation per message; Full access allows eight. Remote tools require an explicit allowlist. Chat, stdio and controlled HTTP profiles delegate read-only tools; HTTP Free and Token only can invoke all allowlisted tools, subject to the remote application’s own permissions. Native-agent accounts and each provider/model combination still need target validation.
- **History and data:** the overlay retains the complete in-memory conversation; state polling returns the latest 32 messages. A provider switch seeds up to 16 prior messages / 24,000 characters. Optional private SDK checkpoints retain sessions across restarts; optional API context projection does not discard stored history. Without persistence, closing the game clears local chat. Provider-side retention is separate. API keys remain in session memory.

## References

- [English manual](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/en/start) · [Documentation française](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/fr/start).
- [Release history](https://github.com/MrMybal/CyRSAssistant/releases) · [Source repository](https://github.com/MrMybal/CyRSAssistant).
