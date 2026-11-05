---
id: create
title: Générer un nouvel effet ReShade FX
description: Générer un nouvel effet ReShade FX
section: Guide utilisateur
order: 7
sourceRevision: 1
---

## Vue d’ensemble {#overview}

Demandez explicitement un ajout pour obtenir un nouvel effet. L’assistant génère un FX autonome contraint, le précompile, écrit un nouveau CyRS_<nom>_<empreinte>.fx identifié par son contenu dans un dossier configuré, recharge ReShade et vérifie l’activation.

```text
Ajoute un bloom anamorphique avec intensité, seuil, transition douce et étalement horizontal. Garde les effets existants actifs et propose des plages de réglage utiles.
```

```diagram
{"type": "flow", "title": "Cycle de génération", "nodes": [{"id": "node-0", "label": "Décrire un ajout", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Générer et précompiler", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Écrire un nouveau FX", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Recharger et initialiser", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Relire les valeurs et vérifier l’activation", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

Jusqu’à 16 contrôles float nommés sont pris en charge. Le corps utilise les fonctions autorisées d’échantillonnage écran/couleur, temps et taille de pixel. Includes, déclarations et boucles libres sont refusés. Certaines demandes dépassent ces capacités.

1. Attendez le résultat final ; compilation et initialisation sont des étapes intermédiaires.
2. Lisez le fichier et les paramètres, puis inspectez-les dans Effets ou ReShade Accueil.
3. Jugez l’image réelle et les performances. Compiler ne prouve ni l’un ni l’autre.
4. Désactivez le dernier effet généré si nécessaire. Sa source reste sur disque. Enregistrer le preset conserve les activations/réglages, pas une garantie de qualité.

```callout
{"type": "info", "title": "Note", "body": "La génération recharge les effets et peut interrompre brièvement le rendu. Après erreur/annulation, inspectez Effets et Log avant de réessayer. Annuler ne supprime pas les fichiers et ne restaure pas les changements déjà appliqués."}
```

## À lire aussi {#related}

- [Remplacer un effet FX existant](doc:replace-fx)
- [Inspecter et régler les effets installés](doc:effects)
- [Dépannage](doc:troubleshooting)
