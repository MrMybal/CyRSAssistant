---
id: history-privacy
title: Historique, stockage et données fournisseur
description: Historique, stockage et données fournisseur
section: Guide utilisateur
order: 15
sourceRevision: 1
---

## Vue d’ensemble {#overview}

| Donnée | Durée / emplacement |
| --- | --- |
| Conversation | Jusqu’à 32 messages en RAM par runtime ReShade. Perdus à la fermeture du runtime/jeu. |
| Contexte fournisseur | Jusqu’à 16 messages précédents / 24 000 caractères, plus demande et données de shaders/outils utiles. |
| Réglages | Fournisseur, URL, modèle, langue et autorisations dans ReShade.ini. |
| Clé API | Mémoire de la session ; à ressaisir au redémarrage. |
| Catalogue | CyRSAssistant/library : métadonnées et descriptions demandées. |
| Archive de remplacement | CyRSAssistant/replacements : HLSL proposé et métadonnées, sans rejeu. |
| FX générés / preset | Dossiers de shaders configurés / preset actif, écrits par les opérations correspondantes. |

Changer de fournisseur conserve les échanges récents locaux, qui peuvent accompagner la demande suivante au nouveau fournisseur. Nouvelle conversation efface ce contexte local, sans supprimer les traces fournisseur ni restaurer le rendu.

```diagram
{"type": "flow", "title": "Parcours des données", "nodes": [{"id": "node-0", "label": "Message et contexte récent", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Noms et valeurs utiles", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Source/désassemblage autorisé si nécessaire", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Fournisseur choisi", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Réponse et outils validés", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

Les autorisations de lecture importent car le code/désassemblage peut être transmis. Le tchat intégré ne voit pas automatiquement les captures. Les clients MCP externes décident séparément de leurs envois aux modèles.

```callout
{"type": "info", "title": "Note", "body": "Conservation, facturation et accès au compte relèvent du fournisseur. Ne saisissez pas de secrets dans le tchat. Copier place les échanges dans le presse-papiers : relisez avant partage. Le manuel lui-même est local et ne demande ni compagnon ni réseau. CyDoc peut conserver favoris et notes privées dans le stockage du navigateur selon sa politique file:// ; utilisez ses contrôles d’export pour en garder une copie."}
```

## À lire aussi {#related}

- [Tchat, historique et demandes utiles](doc:chat)
- [Autorisations et validations](doc:permissions)
- [Mises à jour, sauvegardes et retour arrière](doc:update)
