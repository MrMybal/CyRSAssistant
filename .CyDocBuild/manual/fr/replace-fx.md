---
id: replace-fx
title: Remplacer un effet FX existant
description: Identifiez un FX, compilez son remplacement et restaurez l’effet précédent.
section: Guides
order: 8
sourceRevision: 3
parent: effects
---

## Vue d’ensemble {#overview}

Remplacer un FX diffère d’un ajout d’effet et d’un remplacement natif du jeu. Identifiez le nom exact du FX chargé. Si plusieurs blooms existent, demandez d’abord leurs noms.

```text
Inspecte Bloom.fx chargé et ses réglages. Remplace ce FX par une version anamorphique avec seuil et intensité réglable sur une plage utile. N’ajoute pas un deuxième bloom en parallèle.
```

1. Identifiez le fichier et lisez sa source et ses paramètres lorsque cela est autorisé.
2. Demandez un remplacement explicite. Une cible ambiguë exige une précision. Une question de capacité peut recevoir une explication avant une action.
3. Le nouveau FX est compilé et initialisé avant désactivation des techniques originales. Le fichier original est conservé.
4. Vérifiez l’activation du nouvel effet et la désactivation des anciennes techniques.
5. Restaurer l’effet remplacé retrouve les activations précédemment suivies et coupe le remplacement.

```diagram
{"type": "flow", "title": "Remplacement FX réversible", "nodes": [{"id": "node-0", "label": "Identifier le FX original", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Compiler un nouveau FX séparé", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Initialiser sa technique", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Désactiver les techniques originales", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Restaurer l’original suivi si nécessaire", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

```callout
{"type": "info", "title": "Note", "body": "La restauration suit le remplacement le plus récent en mémoire. Redémarrage, rechargement ou modifications ultérieures peuvent la rendre indisponible. Gardez des copies des sources/presets ; ce n’est pas un historique permanent."}
```

## À lire aussi {#related}

- [Générer un nouvel effet ReShade FX](doc:create)
- [Inspecter et remplacer les shaders du jeu](doc:native-shaders)
- [Inspecter et régler les effets installés](doc:effects)
