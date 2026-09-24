# Adding a language

The overlay and Python companion share the UTF-8 catalogs in `companion/locales/`. English is the default and fallback. `en.json` is the canonical catalog: each key is the English source text and its value is identical. `fr.json` supplies French translations.

To add a language:

1. Copy `en.json` to a new file such as `de.json`.
2. Set `code` to the filename stem and `name` to the language's own display name, such as `Deutsch`.
3. Translate the values in `messages`. Keep keys unchanged. Missing keys fall back to English; remove a key if its translation is not ready. Never leave empty values.
4. Keep named placeholders such as `{file}` and printf placeholders such as `%s`, `%zu` and `%llu`. Named placeholders can be reordered; printf argument order and types must stay unchanged. Do not add `###` or NUL characters.
5. Run `python -m unittest discover -s tests -p 'test_*.py'`, then rebuild both binaries with `python tools/build.py` and `python tools/build_service.py`. Run `python tools/package.py` to create the distribution.

The language selector discovers catalog metadata during the build. No C++ language enumeration or Python provider switch needs editing. CMake generates an embedded native lookup table; PyInstaller includes the JSON catalogs. Adding a translation therefore requires rebuilding and replacing the add-on and companion together. The packaged Python companion reads its bundled catalogs directly.

For a new UI message, add its English key/value to `en.json`, add translations and call `tr`/`ui_label` in the overlay or `tr` in Python. Use complete sentences with named placeholders rather than concatenating translated fragments. Widget labels use a stable `###` identifier so switching language preserves tab selection and editing state.

`[CYRSASSISTANT] Language=en` in ReShade.ini is the default; `fr` selects French. Unknown codes fall back to English, and supported regional codes such as `fr-FR` resolve to their base language. Runtime snapshots and connection configuration include `language`; the local `set_language` command persists the same setting as the UI. It is not exposed as an AI tool.

Python requests pin their language using a ContextVar, including worker-pool requests. A language change does not clear conversation history, change shader identifiers, restart the provider, cancel an approval or mutate rendering. Existing messages and pending request results retain their original language. New model requests ask for replies and new labels in the selected language, while allowing an explicit user request for another language.

Names and descriptions supplied by installed shaders, disassembly and external compiler diagnostics are not translated. English/French use ReShade's Latin glyph coverage. Languages needing other scripts also require checking font glyphs, shaping and layout in the target ReShade build.
