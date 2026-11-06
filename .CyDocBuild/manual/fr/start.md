---
id: start
title: Commencer ici
description: Connectez un fournisseur IA et réalisez un premier réglage réversible.
section: Premiers pas
order: 0
sourceRevision: 3
---

## Vue d’ensemble {#overview}

CyRSAssistant est un add-on ReShade Windows x64. Décrivez un rendu, inspectez les noms et valeurs réels, réglez un preset, générez un FX ou remplacez un pixel shader identifié. Un compagnon séparé relie le jeu au fournisseur choisi.

1. Installez le ZIP complet à côté de la DLL ReShade du véritable exécutable du jeu.
2. Ouvrez ReShade (Home par défaut, ou votre raccourci), puis CyRSAssistant.
3. Choisissez un fournisseur dans Connexion et connectez-vous.
4. Posez une question dans Tchat. Vérifiez le résultat avant de sauvegarder le preset.

```diagram
{"type": "flow", "title": "Votre première session", "nodes": [{"id": "node-0", "label": "Installer le ZIP", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Connecter un fournisseur", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "Décrire ou inspecter", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Vérifier le résultat", "x": 20, "y": 320, "width": 570}, {"id": "node-4", "label": "Enregistrer ou restaurer", "x": 20, "y": 420, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}, {"from": "node-3", "to": "node-4"}]}
```

```callout
{"type": "info", "title": "Note", "body": "L’aide fonctionne sans connexion et sans effet chargé. Elle ouvre le lecteur CyDoc fourni dans le navigateur via file://, sans requête fournisseur ni modification du rendu."}
```

L’anglais est la langue par défaut. Options > Language > Français change immédiatement l’interface et sélectionne le français au prochain lancement du manuel. Le lecteur CyDoc propose un sélecteur English / Français qui conserve page, section et média.

## À lire aussi {#related}

- [Installation et prérequis](doc:install)
- [Connecter un fournisseur](doc:connect)
- [Tchat, historique et demandes utiles](doc:chat)
- [Dépannage](doc:troubleshooting)
