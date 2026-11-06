---
id: tour
title: Se repérer dans l’interface
description: Repérez Tchat, Connexion, Effets, Shaders, Options et l’aide contextuelle.
section: Guides
order: 2
sourceRevision: 3
parent: start
---

## Vue d’ensemble {#overview}

| Zone | Rôle |
| --- | --- |
| En-tête | État fournisseur et autorisations. |
| Tchat | Conversation, progression, annulation et validations. |
| Options | Langue et mode d’autorisation. |
| Connexion | Fournisseur, modèle, URL, clé de session et connexion. |
| Effets | Scan/rechargement, techniques, valeurs, annulation, presets et FX générés. |
| Shaders | Empreintes natives, inspection et restauration. |
| Aide | Manuel hors ligne, recherche, illustrations et schémas. |

L’état prêt du fournisseur ne mesure pas la qualité d’un effet. Vérifiez séparément l’état de l’effet. Replier Techniques ou Paramètres masque les lignes sans désactiver les effets.

Utilisez Ouvrir la documentation dans Aide ou un bouton contextuel à côté des outils. CyDoc ouvre la bonne page dans le navigateur par défaut, sans WebView, serveur local ni installation de lecteur.

Appuyez sur F1 lorsque l’onglet CyRSAssistant a le focus pour ouvrir son aide contextuelle. Utilisez le zoom du navigateur pour la taille de lecture. CyDoc conserve positions, onglets de code et navigation pendant la session. Ctrl+K ouvre la recherche ; F1 revient à Commencer ici. L’agrandissement des images reste dans le lecteur ; Échap le réduit.

```diagram
{"type": "flow", "title": "Quel parcours ?", "nodes": [{"id": "node-0", "label": "Question : Tchat", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Fournisseur : Connexion", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Réglage : Effets", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Code natif : Shaders", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Explication : Aide", "x": 20, "y": 420, "width": 570}], "edges": []}
```

## À lire aussi {#related}

- [Connecter un fournisseur](doc:connect)
- [Inspecter et régler les effets installés](doc:effects)
- [Inspecter et remplacer les shaders du jeu](doc:native-shaders)
