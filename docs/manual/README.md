# Manual sources

The 0.8 JSON catalog and ImGui/HTML renderers have been replaced by CyDoc. Maintained sources are in ../content/en and ../content/fr. See [Build and authoring](../content/en/authoring.md) or [le guide français](../content/fr/authoring.md).

Run npm ci --omit=peer, then npm run docs:build or npm run docs:check. Output: build/help. The build also produces the native help route catalog. Keep stable page/anchor/media IDs and translation revision metadata. Old index.en.html/index.fr.html chapter links remain local redirects.
