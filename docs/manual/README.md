# Maintaining the embedded manual

`en.json` is the English default. `fr.json` is its French counterpart. Both catalogs use the same stable chapter IDs and block ordering. Add another language by copying the English catalog, updating `code`, `name`, all `ui` strings and chapter text. Missing languages fall back to English at runtime. UI language registration remains in `companion/locales`.

Supported blocks: paragraph, heading, note, steps, bullets, example, code, image, flow, table and related. Related links use chapter IDs. Image IDs are explicitly mapped to the two real development screenshots in `tools/generate_manual.py`; captions identify their older versions. Never edit text into a screenshot to simulate a newer build.

CMake runs `tools/generate_manual.py --header` and embeds the catalog in the add-on. PNG resources are embedded separately and decoded lazily with Windows Imaging Component; flow diagrams are drawn from translated labels. Per-runtime image resources are released after the GPU queue finishes.

`python tools/generate_manual.py --html build/manual-preview` builds a browser preview. Packaging automatically includes self-contained HTML editions and assets under `CyRSAssistant/Documentation` in both ZIP variants. There are no CDN scripts, fonts or network dependencies. The HTML default is English and language links use the same chapter IDs. Printing includes the entire manual even with a search filter active.

Run `python -m unittest discover -s tests -p 'test_*.py'` and `python tools/build.py`. Tests cover bilingual parity, references, file links, safe diagrams, package contents, native fallback, accent-insensitive search and fixed offline-file paths. Rebuild the companion when changing the application version or its language catalogs, then create the install ZIP with `python tools/package.py --install`.
