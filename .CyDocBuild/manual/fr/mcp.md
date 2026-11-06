---
id: mcp
title: Clients MCP externes
description: Connectez un client MCP en lecture seule ou avec l’écriture explicitement activée.
section: Clients externes
order: 14
sourceRevision: 3
---

## Vue d’ensemble {#overview}

Un client MCP externe peut lancer le serveur stdio du paquet de développement, notamment OpenCode ou Antigravity s’ils acceptent une commande MCP locale. Ce ne sont pas des choix fournisseur supplémentaires dans l’overlay.

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
{"type": "info", "title": "Note", "body": "La conversation MCP externe n’est pas copiée dans l’overlay. L’écriture MCP est distincte des modes intégrés. Les écritures exigent des jetons courants et des données valides ; la connexion ne donne ni méthodes natives arbitraires ni accès général aux fichiers."}
```

## À lire aussi {#related}

- [Autorisations et validations](doc:permissions)
- [Capture et retour visuel](doc:capture)
- [Historique, stockage et données fournisseur](doc:history-privacy)
