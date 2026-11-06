---
id: update
title: Updates, backups and rollback
description: Update files while keeping presets, settings, catalogs and generated shaders.
section: Help and reference
order: 17
revision: 3
---

## Overview {#overview}

1. Close the game before replacing binaries. Back up the add-on, companion, runtime and notices together.
2. Separately preserve ReShade.ini, presets, generated FX, CyRSAssistant/library and replacements.
3. Extract the new ZIP to the same location, merging folders. Keep Documentation and LICENCES. Do not delete the existing CyRSAssistant folder; it may contain user data.
4. Start and verify version, language, permissions, provider and effects. Session-only keys need re-entry.
5. To roll back, close the game and restore the previous matched binary/runtime/notices set. Preserve user configurations unless explicitly restoring their backups too.

No automatic updater is provided. Keep the matching install ZIP and corresponding developer/source ZIP. Do not mix binaries from different versions. CyDoc content and UI translations are built for the same application version.

```callout
{"type": "info", "title": "Note", "body": "Closing the game ends RAM-only conversations and temporary native replacements. Preset saving and keeping generated FX are different from making a native replacement persistent. This workflow does not delete backups."}
```

## Related topics {#related}

- [Installation and requirements](doc:install)
- [History, storage and provider data](doc:history-privacy)
- [Licenses and sources](doc:licensing)
