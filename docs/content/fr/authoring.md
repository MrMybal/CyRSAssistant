---
id: authoring
title: Construire et maintenir ce manuel
description: Construire et maintenir ce manuel
section: Référence développeur
order: 140
sourceRevision: 1
---

## Génération et paquet {#build}

Node.js 22+ et npm sont requis seulement à la génération. Le lecteur exige JavaScript dans un navigateur, sans Node, Python, CDN ou serveur local.

```bash
npm ci --omit=peer
npm run docs:build
npm run docs:check
python tools/build.py
python tools/build_service.py
python tools/package.py --install
python tools/package.py
```

Les deux commandes docs compilent, valident et exportent. tools/build.py génère aussi l’aide via CMake. Le paquet refuse un export absent/périmé puis copie tout build/help dans CyRSAssistant/Documentation des deux ZIP. Les sources développeur incluent configuration, Markdown, assets, scripts, verrou npm et archive CyDoc épinglée. Le compagnon exige toujours son environnement Python de build épinglé.

## Contenu et adresses stables {#content}

Éditez docs/content/en et fr, pas le HTML/data.js générés. Les langues partagent IDs, ancres explicites et médias. Gardez les 21 anciens IDs. L’index ne parcourt que src/companion distribués : aucun build, catalogue utilisateur, test, identifiant ou source tiers.

L’anglais porte revision ; sa traduction, sourceRevision correspondant. Un changement de sens exige mise à jour et revue. Le build refuse la prose absente/dépassée/non suivie. Voir [Langues](doc:localization).

Les images ont des IDs explicites et controls minimal ; les captures réelles d’anciennes versions sont identifiées dans leur légende. Ne retouchez pas les pixels pour simuler une interface nouvelle. Les schémas sont des fences diagram compilées en SVG. Seul image est activé : aucun besoin de graph, gallery, video, gif ou mesh ; aucun lecteur Three.js n’est livré.

## Intégration et compatibilité {#host}

tools/docs_reader.mjs utilise les entrées publiques cydoc/viewer et cydoc, les fournisseurs locaux par scripts classiques, le thème Nord avec identité turquoise et l’espace de stockage cyrsassistant-help. La CLI exporte manifest et module image ; le bundle hôte personnalise l’application sans modifier les sources CyDoc.

Le lecteur conserve clavier/tactile, agrandissement dans la fenêtre, ancres et positions. Le C++ transforme le chemin installé avec UrlCreateFromPathW puis ajoute la route CyDoc encodée. Aucun chemin non échappé n’est concaténé à une URL file.

index.en.html/index.fr.html et anciennes empreintes de chapitres redirigent par le bootstrap local. Les alias préservent des IDs courants. open_help garde les chapitres mais lance le navigateur ; open=false efface le statut local sans fermer le navigateur.

## Dépendances et contrôles {#dependencies}

CyDoc 0.1.0 est épinglé au commit 774f2a7eabf7dd181a98ffc5add115b580b67f42 et à l’empreinte SHA-256 de l’archive dans tools/cydoc.lock.json. Le verrou npm fixe le compilateur ; npm ci --omit=peer évite le peer Three.js inutile. N’installez pas un autre paquet public homonyme. Les licences restent en anglais ; l’application reste GPL-3.0-only.

L’index est lexical, sans analyse sémantique complète C++/Python. Il colore les sources distribués, leurs dépendances reconnues et les adresses de lignes. Doxygen/TypeDoc sont inutiles ici.

Contrôlez liens, IDs/ancres/médias bilingues, révisions, ressources locales, bundles, anciennes URL, chemins Unicode et ZIP. Testez file:// et le lancement natif Windows. Linux/macOS/Android ne sont pas des cibles du produit ; le stockage hors environnements testés reste à vérifier.

Essai Chrome Windows facultatif : `node tests/manual_browser_smoke.mjs`. Passez le dossier exporté en premier argument, ou définissez CHROME_PATH. Il lance un navigateur headless isolé et bloque HTTP/HTTPS.
