---
id: cli
title: Utilisation avancée en ligne de commande
description: Utilisation avancée en ligne de commande
section: Guide utilisateur
order: 13
sourceRevision: 1
---

## Vue d’ensemble {#overview}

Le ZIP d’installation est autonome pour l’overlay. Le ZIP de développement ajoute companion/ et les modules Python CLI/MCP. Lancez les commandes depuis ce dossier avec Python 3.11+. Ne lancez pas l’ancien watch avec le service intégré.

```bash
python -m companion discover
python -m companion state
python -m companion scan
python -m companion ask "Refroidir légèrement les couleurs" --dry-run > plan.json
python -m companion apply plan.json
python -m companion undo
python -m companion save
python -m companion reload
```

ask applique les changements sauf avec --dry-run. Examinez le plan puis appliquez-le à la même session/génération/révision courante. Les plans obsolètes sont refusés. save écrit le preset ; undo utilise l’unique instantané suivi.

```bash
python -m companion --pipe "\\.\pipe\CyRSAssistant-12345" --runtime 1 state
```

Remplacez le PID/runtime d’exemple par les résultats de découverte. --pipe et --runtime précèdent la sous-commande. Les demandes CLI historiques utilisent CYRS_API_URL, CYRS_MODEL et éventuellement CYRS_API_KEY dans leur environnement ; elles ne récupèrent pas la clé de session de l’overlay.

```callout
{"type": "info", "title": "Note", "body": "Les diagnostics CLI peuvent exposer des chemins locaux. Relisez-les avant partage. Utilisez la connexion de l’overlay pour l’assistant standard ; watch est un ancien parcours manuel."}
```

## À lire aussi {#related}

- [Catalogue, descriptions et portabilité](doc:catalog)
- [Clients MCP externes](doc:mcp)
- [Limites et référence technique](doc:reference)
