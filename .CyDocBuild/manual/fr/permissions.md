---
id: permissions
title: Autorisations et validations
description: Choisissez les actions automatiques, les validations ou les opérations multiples.
section: Guides
order: 5
sourceRevision: 3
parent: chat
---

## Vue d’ensemble {#overview}

| Mode | Comportement |
| --- | --- |
| Automatique (par défaut) | Lectures et modifications demandées sans validation supplémentaire. Une opération de rendu par message. |
| À la demande | Noms et valeurs directement lisibles. Chaque modification et transmission de source/désassemblage doit être autorisée. |
| Accès complet aux outils ReShade | Lectures et plusieurs opérations de rendu sans validation intermédiaire. |

Choisissez Options > Mode d’autorisation. Le choix est mémorisé par jeu. Changer de mode annule la demande en cours et invalide ses autorisations sans restaurer les modifications précédentes.

```diagram
{"type": "flow", "title": "À la demande", "nodes": [{"id": "node-0", "label": "L’assistant propose", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Examiner valeurs ou sources", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Autoriser ou refuser dans Tchat", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Appliquer l’action approuvée", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Vérifier le résultat", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

L’autorisation concerne une action, une demande et son contenu exact. Une action modifiée doit être approuvée à nouveau. Refuser ou annuler interrompt l’action en attente. Lisez le résumé d’envoi des sources avant d’autoriser.

```callout
{"type": "info", "title": "Note", "body": "L’accès complet concerne les outils de l’add-on. Il ne donne ni terminal, ni fichiers arbitraires, ni permissions d’une autre application IA. L’écriture MCP externe reste contrôlée par --allow-write."}
```

## À lire aussi {#related}

- [Tchat, historique et demandes utiles](doc:chat)
- [Historique, stockage et données fournisseur](doc:history-privacy)
- [Clients MCP externes](doc:mcp)
