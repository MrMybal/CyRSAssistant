---
id: chat
title: Tchat, historique et demandes utiles
description: Envoyez une demande, affinez le rendu, annulez et gérez la conversation.
section: Guides
order: 4
sourceRevision: 5
parent: start
---

## Vue d’ensemble {#overview}

La version 0.10.0 affiche le texte SDK progressivement. Annuler interrompt le fournisseur et refuse les actions devenues obsolètes ; les modifications précédentes restent actives. Le champ de pièce jointe facultatif accepte un fichier local explicitement choisi, chargé sur le worker et envoyé seulement si le fournisseur le prend en charge. Le tchat intégral reste en mémoire ; la [conservation privée des sessions](doc:sdk#options) est facultative.

1. Connectez un fournisseur puis ouvrez Tchat. Une conversation ne demande ni effet chargé ni shader sélectionné.
2. Écrivez dans Votre message. Entrée ajoute une ligne ; Ctrl+Entrée ou Envoyer transmet.
3. Attendez la progression. Le texte apparaît progressivement ; le message final remplace cet aperçu en direct.
4. Si une autorisation apparaît, examinez valeurs/code puis choisissez Autoriser cette action ou Refuser cette action.
5. Vérifiez le résultat avant d’affiner, de restaurer ou de sauvegarder.

```image
{"id": "chat-preview", "src": "assets/screenshots/chat-preview.png", "alt": "Capture antérieure v0.4.0 : historique et exemple de génération FX. L’accès aux données et les contrôles ont évolué depuis.", "controls": "minimal"}
```

Capture antérieure v0.4.0 : historique et exemple de génération FX. L’accès aux données et les contrôles ont évolué depuis.

```text
Liste les FX de bloom installés et lis les noms, valeurs et bornes de leurs paramètres. Ne modifie rien pour le moment.
```

```text
Réchauffe légèrement les couleurs en conservant l’exposition. Utilise les effets installés et indique les valeurs modifiées.
```

L’assistant peut parcourir noms, valeurs, bornes, descriptions et sources FX/FXH ou inspections natives autorisées. Un fichier exact réduit l’ambiguïté. Une empreinte identifie le bytecode du jeu, pas son rôle visuel.

Nouvelle conversation efface l’historique local et le brouillon sans annuler le rendu. Copier la conversation copie les échanges ; les messages possèdent aussi Copier. Une seule demande est active. Annuler bloque les actions ultérieures ; les changements déjà appliqués restent actifs.

## À lire aussi {#related}

- [Autorisations et validations](doc:permissions)
- [Inspecter et régler les effets installés](doc:effects)
- [Historique, stockage et données fournisseur](doc:history-privacy)
