---
id: authoring
title: Build and maintain this manual
description: Build and maintain this manual
section: Developer reference
order: 140
revision: 2
---

## Generate and package {#build}

Node.js 22+ and npm are build-time requirements only. The reader needs JavaScript in a browser, not Node, Python, a CDN or a local web server.

```bash
npm ci --omit=peer
npm run docs:build
npm run docs:check
python tools/build.py
python tools/build_service.py
python tools/package.py --install
python tools/package.py
```

Both docs commands compile, validate and export. tools/build.py also generates help through CMake. Packaging refuses a stale/missing export and copies all of build/help into CyRSAssistant/Documentation in both ZIPs. Developer sources include configuration, Markdown, assets, build tools, npm lock and the pinned local CyDoc archive. The frozen companion still requires its pinned Python build environment.

## Content and stable addresses {#content}

Edit docs/content/en and fr, not generated HTML/data.js. Both locales have the same page IDs, explicit section anchors and media IDs. Keep the original 21 chapter IDs. Source pages are generated from distributed src/companion only; no build folders, user catalogs, tests, credentials or third-party source are indexed.

Use revision in English and matching sourceRevision in translations. A changed meaning needs a revision update and translation review. The build refuses missing/outdated/untracked prose. Adding a language is described in [Localization](doc:localization).

Images use explicit IDs and controls minimal; the screenshots are real older development captures, identified in their captions. Do not modify their pixels to simulate a new interface. Diagrams are CyDoc diagram fences compiled into SVG. Only image is enabled; graph, gallery, video, GIF and mesh have no justification, and no Three.js reader is shipped.

## Host integration and compatibility {#host}

tools/docs_reader.mjs imports public cydoc/viewer and cydoc APIs, supplies classic-script local media/resource loaders, chooses the Nord theme with turquoise branding and namespaces reading data as cyrsassistant-help. The stock CLI exports the manifest and image module; the host bundle adds product branding without changing CyDoc sources.

The browser reader retains keyboard/touch controls, in-window enlargement, anchors and reading positions. Native C++ converts the installed absolute path with UrlCreateFromPathW, then appends percent-encoded CyDoc routes. No unescaped path is concatenated into a file URL.

index.en.html/index.fr.html and old chapter hashes redirect through the local legacy bootstrap. Config aliases preserve common renamed page IDs. Native open_help keeps chapter IDs but launches the browser; open=false clears local status without closing a browser.

## Dependency and validation scope {#dependencies}

CyDoc 0.1.0 is pinned to commit 774f2a7eabf7dd181a98ffc5add115b580b67f42 and a vendored package SHA-256 in tools/cydoc.lock.json. npm lock pins compiler dependencies; npm ci --omit=peer avoids the unused Three.js peer. Do not install an unrelated public package by name. License texts remain English, and CyRSAssistant stays GPL-3.0-only.

The source index is lexical, not a full C++/Python semantic API extractor. It highlights distributed source, documented dependencies and source-line addresses. Doxygen/TypeDoc are not required here.

Tests must check manifest links, bilingual IDs/anchors/media, translation revisions, local assets, selected bundles, legacy URLs, Unicode paths and packaged contents. Test the exported file:// reader and native help launch on Windows. Linux/macOS/Android are not product targets; browser storage behavior outside tested environments remains to verify.

Optional Windows Chrome smoke test: `node tests/manual_browser_smoke.mjs`. Pass an exported directory as the first argument, or set CHROME_PATH. It launches an isolated headless browser and blocks HTTP/HTTPS requests.

## GitHub Pages publication {#publication}

The [English online manual](https://mrmybal.github.io/CyRSAssistant/#/en/start) and [French online manual](https://mrmybal.github.io/CyRSAssistant/#/fr/start) use the same reader, content and image module as the offline export. No application executable, service, configuration, npm dependency tree or source archive is deployed to Pages.

```bash
npm ci --omit=peer
npm run docs:pages
npm run docs:pages:check
node tests/manual_browser_smoke.mjs build/pages-project/site
node tests/manual_browser_smoke.mjs build/pages-project/site --http
```

The artifact is build/pages-project/site. The Pages builder uses docs/reference-sources.json to preserve the versioned source reference independently of the application branch. This matters when the online manual describes a development version newer than the published application. Update that reference intentionally from the corresponding application checkout with `python tools/build_pages.py --refresh-sources`, then review and commit the snapshot with the documentation. The installed manual continues to index the actual application sources through tools/build_help.py.

The Documentation GitHub Actions workflow rebuilds and checks relevant pushes to main, validates pull requests without deploying, and supports manual dispatch. It tests the file reader and a project subpath, then uploads only the checked export and deploys it to the github-pages environment. All actions and the CyDoc archive are pinned. Project-relative resources and hash routes support both GitHub Pages and file URLs. The legacy index.en.html/index.fr.html addresses remain valid.
