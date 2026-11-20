---
id: mcp
title: Clients MCP externes
description: Connectez un client MCP en lecture seule ou avec l’écriture explicitement activée.
section: Clients externes
order: 14
sourceRevision: 6
---

## Vue d’ensemble {#overview}

## Serveur HTTP local {#local-http}

En 0.10.1, activez **Options > Activer le MCP local** puis utilisez **Copier l’adresse MCP**. Aucune connexion à un fournisseur de tchat n’est nécessaire. Avec **Free**, profil par défaut, l’adresse loopback seule donne accès à toutes les opérations exposées, sans jeton ni confirmation supplémentaire. Les arguments et versions restent validés.

Choisissez **Local contrôlé**, **Jeton seul** ou **Protégé** selon les combinaisons voulues. Les choix explicites sont conservés ; les configurations sans choix migrent vers Free. Les profils à jeton utilisent **Copier le jeton MCP** pour la session courante. Voir [les profils et la migration](doc:sdk#local-access).

## Serveur stdio natif {#stdio}


Dans la version 0.10.0, lancez `CyRSAssistantCLI.exe mcp` depuis le dossier d’installation, avec `--allow-write` uniquement pour un client de confiance. `python -m companion.mcp` redirige vers le serveur SDK. L’écriture respecte aussi le mode du panneau ; À la demande nécessite les vrais boutons. Voir [la connexion, les outils et les résultats conservés](doc:sdk).

Un client MCP externe peut lancer le serveur stdio du paquet de développement, notamment OpenCode ou Antigravity s’ils acceptent une commande MCP locale. La version 0.10.0 propose également OpenCode ACP et Antigravity comme fournisseurs dans l’overlay.

```bash
python -m companion.mcp
# Autoriser volontairement l’écriture pour un client choisi :
python -m companion.mcp --allow-write
```

```json
{
  "mcpServers": {
    "cyrsassistant": {
      "command": "python",
      "args": ["-m", "companion.mcp"],
      "cwd": "<dossier-du-paquet-de-developpement>"
    }
  }
}
```

Cet exemple est générique : chaque client a son format et sa gestion du dossier de travail. Utilisez son équivalent pour le dossier contenant companion/. Précisez --pipe pour plusieurs jeux. Le serveur se fixe au jeu découvert sans changer silencieusement de processus.

| Lecture seule par défaut | Avec --allow-write |
| --- | --- |
| Lister les runtimes ; lire noms, paramètres et valeurs ; capturer une image ; lister/inspecter les shaders natifs. | Générer/remplacer les FX ; compiler/activer les remplacements natifs ; restaurer ; appliquer/annuler ; sauvegarder ; recharger. |

```callout
{"type": "info", "title": "Note", "body": "La conversation MCP externe n’est pas copiée dans l’overlay. L’écriture MCP stdio est distincte des profils HTTP. Les écritures exigent des jetons courants et des données valides ; la connexion ne donne ni méthodes natives arbitraires ni accès général aux fichiers."}
```

## À lire aussi {#related}

- [Autorisations et validations](doc:permissions)
- [Capture et retour visuel](doc:capture)
- [Historique, stockage et données fournisseur](doc:history-privacy)
