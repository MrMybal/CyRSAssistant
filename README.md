# CyRSAssistant

English | [Français](README.fr.md)

An AI assistant inside ReShade. Chat about the look you want, inspect installed effects and their actual parameters, adjust a preset, generate effects and replace selected game shaders.

Version 0.7.0 is a Windows x64 prototype built against ReShade 6.8 / API 20. FX generation and temporary pixel shader replacement have been exercised in Stray with DX11 and DX12. DXIL compilation and Shader Model 6 PSO creation have also been tested on a DX12 device. Visual quality still needs evaluation in each game.

## Language

The interface defaults to **English**. Select **Options > Language > Français** to switch to French. The setting is saved for this game and takes effect without restarting. New assistant responses use the selected language unless you explicitly request another language. Existing conversation messages remain unchanged; an ongoing request finishes in its original language.

Translations for the overlay and companion share JSON catalogs. See [Adding a language](docs/localization.md).

## Features

- Chat with Codex CLI, Claude Code CLI, an OpenAI-compatible API or a local model. The background service starts from the overlay and reports connection status.
- Inspect real effect filenames, techniques, parameter names, values, bounds, descriptions and FX source. The assistant can read more information through tools as needed.
- Adjust settings, verify applied values, undo the last edit and explicitly save the active preset.
- Generate standalone ReShade FX with named controls. Replace an existing FX by compiling a new effect, disabling the old one and keeping its source for restoration.
- Inspect captured DX11/DX12 pixel shaders, compile replacements, check signatures and resource contracts, and activate them at the next game bind.
- Maintain a disk catalog with fingerprints, changes, generated descriptions and portable metadata export/import.
- Connect external MCP clients for reads and, with `--allow-write`, supported edits.

## Get started

Read the [installation and connection guide](docs/getting-started.md). Copy the add-on, companion executable and runtime folder together. No terminal is needed for normal use from ReShade.

In **Options > Permission mode**, choose:

- **Automatic** (default): requested reads and actions run without extra approval; one rendering operation per message.
- **Ask each time**: review each rendering change and each source/disassembly read before transmission to the provider. Names and values remain directly readable.
- **Full access to ReShade tools**: the assistant can chain multiple rendering operations to complete a request.

These permissions cover this add-on's tools. They do not grant a terminal or arbitrary filesystem access, change the Codex application's permissions, or override the separate MCP write setting. Changing permission mode cancels the pending request. Ambiguous targets can still require clarification.

## Build

Requires Windows x64, Visual Studio 2022 with C++ and Windows SDK, and Python 3.11+.

```powershell
python tools/bootstrap.py
python tools/build.py
python -m venv build/packaging-env
build/packaging-env/Scripts/python.exe -m pip install pyinstaller==6.20.0
python tools/build_service.py
python -m unittest discover -s tests -p 'test_*.py'
python tools/package.py
```

The package is written to `dist/CyRSAssistant-0.7.0.zip` and includes sources. Dependencies use pinned versions and checksums from their official projects. CyGameCapture and CyGPUInspector are not dependencies.

## Current limits

There is no shader-pack downloading, automatic screenshot analysis or automatic HUD identification yet. Native replacement supports captured DX11/DX12 pixel shaders; other stages and Vulkan are not supported. A shader may be shared by several objects. The assistant receives disassembly and reflection, not the game's original HLSL, and may decline an uncertain reconstruction. Replacements are not automatically restored after restarting the game.

Technique order is not changed. Undo keeps one edit in memory and can be invalidated by an inventory change or reload. Saving writes the active preset; automatic historical preset backups are not implemented.

OpenCode and Antigravity can use the MCP interface from their own clients; they do not have direct provider connectors in the overlay yet. A recognized CLI login does not guarantee model access; the first message checks it. Responses are displayed when completed, without streaming.

## Conversation and provider data

The overlay keeps up to 32 messages in memory. Recent exchanges accompany requests to the selected provider, including after switching providers. Starting a new conversation clears the local context without restoring rendering changes. Runtime history disappears when the game closes; this does not delete records retained by the provider.

The API key stays in memory for the current session. Provider, model, endpoint, language and permission mode are saved in ReShade.ini. Provider requests include the relevant chat and shader data required by the selected tools. Compiler output and existing shader annotations retain their original language.

## License

CyRSAssistant by Cyberalien is licensed under GPL-3.0-only. See [LICENSE](LICENSE) and [THIRD_PARTY.md](THIRD_PARTY.md) for dependency licenses.
