---
id: catalog
title: Catalog, descriptions and portability
description: Scan shader files, create reusable descriptions and transfer metadata.
section: Advanced use
order: 11
revision: 3
---

## Overview {#overview}

The disk catalog complements the loaded ReShade inventory. It scans configured EffectSearchPaths and TextureSearchPaths, fingerprints files and reports additions, modifications and removals. Descriptions are generated on explicit CLI request, not automatically for every effect from the overlay.

1. Use the developer package and Python 3.11+ for these commands. Specify --pipe / --runtime if discovery is ambiguous.
2. Run scan to update CyRSAssistant/library/catalog.json. A /** suffix on a configured path enables recursive scanning.
3. Resolve scan errors and duplicate FX filenames before requesting a reusable description.
4. Run describe with a unique filename. Source and metadata are sent to the API provider configured for this CLI request; descriptions are marked not visually verified.
5. Export metadata/descriptions, import them in another game with matching shader files, then rescan.

```bash
python -m companion scan
python -m companion describe Tonemap.fx
python -m companion export catalogue-portable.json
python -m companion import catalogue-portable.json
```

Portable exports do not bundle shader sources, textures or credentials. Install required shader packs separately. A changed dependency conservatively invalidates cached analysis. Transient runtime IDs and current values are not portable shader identities.

```callout
{"type": "info", "title": "Note", "body": "Scanning does not download shaders or watch folders continuously. Native Scan effects enumerates loaded parameters; CLI scan inspects disk files. Keep CyRSAssistant/library during updates."}
```

## Related topics {#related}

- [Advanced command-line use](doc:cli)
- [Inspect and tune installed effects](doc:effects)
- [Updates, backups and rollback](doc:update)
