---
id: connect
title: Connecter un fournisseur
description: Connecter un fournisseur
section: Guide utilisateur
order: 3
sourceRevision: 1
---

## Vue d’ensemble {#overview}

| Fournisseur | Prérequis |
| --- | --- |
| Codex (session CLI) | CLI installé et connexion valide. Modèle vide utilise son défaut. |
| Claude Code (session CLI) | CLI installé et connexion valide. Modèle vide utilise son défaut. |
| API compatible OpenAI | URL Chat Completions complète, modèle et clé si nécessaire. |
| Modèle local (API) | Serveur local compatible lancé et identifiant réel du modèle. |

1. Utilisez Déconnecter / modifier avant de changer les réglages actifs.
2. Choisissez le fournisseur. Pour une API, indiquez l’URL /chat/completions complète et le modèle attendu.
3. Saisissez la clé dans Clé API si nécessaire ; jamais dans le tchat.
4. Cliquez sur Connecter. Le compagnon démarre automatiquement.
5. Pour les CLI, le premier message normal vérifie l’accès au modèle. La session reconnue seule ne prouve ni cet accès ni le quota.

```image
{"id": "connection-preview", "src": "assets/screenshots/connection-preview.png", "alt": "Capture de développement antérieure en français : choix du fournisseur et session locale Codex reconnue. L’interface actuelle utilise Connexion.", "controls": "minimal"}
```

Capture de développement antérieure en français : choix du fournisseur et session locale Codex reconnue. L’interface actuelle utilise Connexion.

```text
URL : http://127.0.0.1:1234/v1/chat/completions
Modèle : identifiant indiqué par votre serveur
Clé API : uniquement si le serveur en exige une
```

Les serveurs distants exigent HTTPS ; HTTP est accepté uniquement sur localhost. Le serveur doit accepter les requêtes JSON Chat Completions et les réponses JSON. Modèle local n’installe ni ne lance un modèle.

```callout
{"type": "info", "title": "Note", "body": "Connecter vérifie la session CLI locale sans demande au modèle. Une connexion API envoie un petit test au serveur choisi. Vérifiez URL, session, modèle et quota en cas d’erreur."}
```

## À lire aussi {#related}

- [Dépannage](doc:troubleshooting)
- [Historique, stockage et données fournisseur](doc:history-privacy)
- [Clients MCP externes](doc:mcp)
