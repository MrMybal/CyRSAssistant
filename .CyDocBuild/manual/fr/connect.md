---
id: connect
title: Connecter un fournisseur
description: Choisissez une session CLI ou une API et comprenez l’état de connexion.
section: Guides
order: 3
sourceRevision: 5
parent: start
---

## Vue d’ensemble {#overview}

La version 0.10.0 utilise les conversations CyMCPSDK. Le sélecteur propose aussi OpenCode ACP, Antigravity, OpenAI Responses, Anthropic Messages, Ollama et LM Studio. Les identifiants de modèles proviennent du fournisseur lorsqu’il les expose ; déconnectez/modifiez pour les changer. Un CLI installé ne prouve pas l’accès au compte ou au modèle. Voir [l’intégration SDK](doc:sdk).

| Fournisseur | Prérequis |
| --- | --- |
| Codex (session CLI) | CLI installé et connexion valide. Modèle vide utilise son défaut. |
| Claude Code (session CLI) | CLI installé et connexion valide. Modèle vide utilise son défaut. |
| API compatible OpenAI | URL Chat Completions complète, modèle et clé si nécessaire. |
| Modèle local (API) | Serveur local compatible lancé et identifiant réel du modèle. |
| OpenCode ACP | CLI OpenCode compatible, compte et modèle configurés. |
| Antigravity | Agent natif compatible installé et son compte. |
| OpenAI Responses | Base API Responses, identifiant réel du modèle et clé. |
| Anthropic Messages | Base API Messages, identifiant réel du modèle et clé. |
| Ollama | Service Ollama lancé et modèle déjà installé. |
| LM Studio | Serveur LM Studio lancé et modèle déjà chargé. |

1. Utilisez Déconnecter / modifier avant de changer les réglages actifs.
2. Choisissez le fournisseur. Pour Chat Completions, conservez l’URL complète existante ou utilisez sa base API. Les autres adaptateurs utilisent leur URL de base et l’identifiant réel du modèle.
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

Les serveurs distants exigent HTTPS ; HTTP est accepté uniquement sur localhost. Le serveur doit implémenter l’adaptateur choisi : Chat Completions, Responses, Messages, Ollama ou LM Studio. Modèle local n’installe ni ne lance un modèle.

```callout
{"type": "info", "title": "Note", "body": "Connecter initialise la session SDK et tente la découverte des modèles lorsqu’elle est disponible. Aucun message payant n’est envoyé pour tester l’inférence. Le message suivant vérifie l’accès réel au modèle ; contrôlez URL, session, modèle et quota."}
```

## À lire aussi {#related}

- [Dépannage](doc:troubleshooting)
- [Historique, stockage et données fournisseur](doc:history-privacy)
- [Clients MCP externes](doc:mcp)
