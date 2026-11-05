---
id: catalog
title: Catalogue, descriptions et portabilité
description: Catalogue, descriptions et portabilité
section: Guide utilisateur
order: 11
sourceRevision: 1
---

## Vue d’ensemble {#overview}

Le catalogue disque complète l’inventaire ReShade chargé. Il parcourt EffectSearchPaths et TextureSearchPaths, calcule les empreintes et signale ajouts, modifications et suppressions. Les descriptions sont générées sur demande CLI explicite, pas automatiquement pour chaque effet depuis l’overlay.

1. Utilisez le paquet de développement et Python 3.11+ pour ces commandes. Précisez --pipe / --runtime si la découverte est ambiguë.
2. Exécutez scan pour actualiser CyRSAssistant/library/catalog.json. Le suffixe /** active le parcours récursif d’un chemin configuré.
3. Corrigez erreurs de scan et noms FX en doublon avant une description réutilisable.
4. Exécutez describe avec un nom unique. Sources et métadonnées sont envoyées au fournisseur API configuré pour cette demande CLI ; les descriptions sont marquées non vérifiées visuellement.
5. Exportez métadonnées/descriptions, importez-les dans un autre jeu possédant les mêmes fichiers puis rescanez.

```bash
python -m companion scan
python -m companion describe Tonemap.fx
python -m companion export catalogue-portable.json
python -m companion import catalogue-portable.json
```

L’export portable n’embarque ni sources de shaders, ni textures, ni identifiants. Installez les packs séparément. Une dépendance modifiée invalide prudemment l’analyse en cache. Les identifiants temporaires et valeurs courantes ne sont pas des identités portables de shaders.

```callout
{"type": "info", "title": "Note", "body": "Le scan ne télécharge aucun shader et ne surveille pas continuellement les dossiers. Scanner les effets énumère les paramètres chargés ; scan en CLI inspecte le disque. Conservez CyRSAssistant/library lors des mises à jour."}
```

## À lire aussi {#related}

- [Utilisation avancée en ligne de commande](doc:cli)
- [Inspecter et régler les effets installés](doc:effects)
- [Mises à jour, sauvegardes et retour arrière](doc:update)
