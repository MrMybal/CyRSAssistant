---
id: effects
title: Inspecter et régler les effets installés
description: Lisez les valeurs réelles, réglez les techniques, annulez et sauvegardez un preset.
section: Rendu / Effets ReShade
order: 6
sourceRevision: 3
---

## Vue d’ensemble {#overview}

1. Ouvrez Effets et Scanner les effets pour énumérer les techniques et paramètres chargés.
2. Utilisez Filtre et dépliez Techniques ou Paramètres. Lisez fichiers, libellés, valeurs et infobulles.
3. Activez une technique ou modifiez une valeur. Validez les nombres avec Entrée. Les valeurs en lecture seule ne se modifient pas ici.
4. Comparez le rendu, utilisez Annuler la dernière modification si disponible, puis Enregistrer le preset uniquement pour conserver ces réglages.

| Action | Modification |
| --- | --- |
| Scanner les effets | Actualise l’inventaire chargé et les identifiants ; efface normalement l’annulation. |
| Charger / recharger les effets | Demande la recompilation des FX à la prochaine image. |
| Annuler la dernière modification | Restaure une modification suivie si les valeurs correspondent encore et l’inventaire reste valide. |
| Enregistrer le preset | Écrit le preset actif via ReShade. |

Le scan n’est ni un rechargement du compilateur ni un téléchargement. Après ajout d’un FX dans un dossier configuré, rechargez les effets. Le mode performance ou une erreur de compilation peut supprimer les valeurs modifiables. Le tchat reste disponible.

```callout
{"type": "info", "title": "Note", "body": "L’annulation possède une étape en mémoire. Modifications manuelles, scans ou rechargements peuvent l’invalider. L’ordre des techniques n’est pas modifié. Il n’existe pas de sauvegardes historiques automatiques des presets ; gardez des copies avant de gros changements."}
```

## À lire aussi {#related}

- [Générer un nouvel effet ReShade FX](doc:create)
- [Remplacer un effet FX existant](doc:replace-fx)
- [Dépannage](doc:troubleshooting)
