---
id: native-shaders
title: Inspecter et remplacer les shaders du jeu
description: Inspectez les pixel shaders capturés et remplacez une cible identifiée.
section: Rendu / Shaders du jeu
order: 9
sourceRevision: 3
---

## Vue d’ensemble {#overview}

Shaders observe les pixel shaders DX11/DX12 capturés après démarrage de l’add-on, identifiés par SHA-256 du bytecode. Les noms sémantiques et le HLSL original sont généralement absents. Compteurs et ressources ne prouvent pas qu’un shader dessine le HUD, le bloom ou un objet.

1. Actualisez les shaders du jeu pendant le rendu de la scène concernée.
2. Sélectionnez une empreinte et Inspecter le shader sélectionné pour lire signatures, ressources et désassemblage.
3. Identifiez la cible par analyse réelle du rendu, pas par la seule empreinte.
4. Demandez le remplacement de cette cible exacte. L’assistant peut refuser une reconstruction incertaine.
5. Après compilation et contrôles, le remplacement est armé pour les prochains binds du jeu. Inspectez la scène et restaurez si nécessaire.

```diagram
{"type": "flow", "title": "Remplacement natif", "nodes": [{"id": "node-0", "label": "Capturer le bytecode original", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Inspecter empreinte et contrats", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Identifier la cible", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Compiler un HLSL compatible", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Armer les prochains binds", "x": 20, "y": 420, "width": 570}, {"id": "node-5", "label": "Restaurer les liaisons originales", "x": 20, "y": 520, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}, {"from": "node-4", "to": "node-5"}]}
```

Le HLSL proposé est archivé sous CyRSAssistant/replacements/<empreinte-originale>/ avec ses métadonnées. Ce n’est pas un rejeu automatique : redémarrer ne réactive pas un remplacement. Le bytecode original capturé reste intact.

```callout
{"type": "info", "title": "Note", "body": "Un shader partagé peut affecter plusieurs objets. Le remplacement d’un pixel shader ne peut pas changer librement sommets, agencement des ressources ou contrats du pipeline. Signatures/ressources/pipelines incompatibles sont refusés."}
```

## À lire aussi {#related}

- [DX12, restauration et limites du HUD](doc:dx12-hud)
- [Dépannage](doc:troubleshooting)
- [Limites et référence technique](doc:reference)
