# CyRSAssistant — Version notes

[Back to README](README.md) · [Français](VERSION.fr.md)

**Application: 0.9.0 · Stage: PROTOTYPE**<br>
**Available package: Windows x64 · published November 6, 2026**<br>
**Target: ReShade 6.8 / API 20 with full add-on support**

This prerelease is intended for testing and feedback. Rendering quality and compatibility depend on the game and selected shaders. Publication does not establish stable support for every game.

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

The published 0.9.0 release notes do not include an itemized confirmed-bug list. Consult the [issue tracker](https://github.com/MrMybal/CyRSAssistant/issues) for reports or [report a problem](https://github.com/MrMybal/CyRSAssistant/issues/new). The limitations below describe product boundaries; they do not establish that there are no bugs.

## Documented limitations

- **Platforms and native shaders:** the supplied build is Windows x64. Native replacement supports captured DX11/DX12 pixel shaders; other stages and Vulkan are not supported. Original game shader names and HLSL are usually unavailable; native shaders are identified by fingerprint. A shared shader can affect several objects, and the assistant may decline an uncertain reconstruction.
- **DX12 replacement:** each relevant pipeline state is rebuilt with its other stages, render state and root signature. Current pipelines must all succeed before activation. A future incompatible pipeline disables the replacement and reports an error. Already recorded command lists can still reference a previous shader version.
- **Generated FX:** generation produces constrained, standalone effects with up to 16 named controls, without loops or external dependencies. Compilation does not guarantee the requested visual result.
- **Editing and restoration:** technique order is not changed. Undo keeps one edit in memory and can be invalidated by an inventory change or reload. Shader replacements are not automatically reactivated when the game restarts. Saving writes the active preset; automatic historical preset backups are not implemented.
- **Unavailable automation:** shader-pack downloading, automatic screenshot analysis and automatic HUD identification are not implemented.
- **Providers and chat:** OpenCode and Antigravity can use external MCP clients but have no direct provider connector in the overlay. A recognized CLI session does not guarantee model access. Responses appear when complete, without streaming. Automatic and Ask each time modes allow one rendering operation per message; Full access allows multiple operations within the tool limits.
- **History and data:** the runtime retains up to 32 messages in RAM. Up to 16 prior messages, limited to 24,000 characters, accompany requests with relevant shader/tool data. Changing providers retains that recent context. Closing the game clears local chat; it does not erase provider records. API keys remain in session memory. See [history and provider data](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/en/history-privacy).

## References

- [English manual](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/en/start) · [Documentation française](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/fr/start).
- [Release history](https://github.com/MrMybal/CyRSAssistant/releases) · [Source repository](https://github.com/MrMybal/CyRSAssistant).
