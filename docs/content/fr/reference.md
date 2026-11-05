---
id: reference
title: Limites et référence technique
description: Limites et référence technique
section: Guide utilisateur
order: 18
sourceRevision: 1
---

## Vue d’ensemble {#overview}

| Élément | Limite / comportement actuel |
| --- | --- |
| Tchat | 32 messages RAM. Historique fournisseur : 16 messages / 24 000 caractères. Saisie : 4095 octets UTF-8. |
| Budget d’outils | Automatique / À la demande : 8 appels et une opération de rendu. Accès complet : 16 appels et 8 opérations. |
| Modification groupée | Jusqu’à 64 changements de paramètres/techniques ; types et bornes courants vérifiés. |
| FX générés | 16 contrôles float nommés ; corps contraint sans boucles/includes libres. |
| Catalogue | 32 Mio par fichier ; JSON importé jusqu’à 16 Mio ; descriptions jusqu’à 20 000 caractères. |
| Shaders natifs | Pixel shaders DX11/DX12 ; 4096 empreintes / 64 Mio par périphérique. |
| Instantanés DX12 | 4096 PSO / 128 Mio, au plus 4 Mio chacun. |
| Durée des versions GPU | Conservées jusqu’à destruction du périphérique ; au plus 64 versions DX11 ou 256 variantes PSO DX12. |
| Capture | Une image, dimension maximale 1280 ; ni enregistrement continu ni tone mapping HDR. |
| Pont local | Protocole 1, pipe de l’utilisateur Windows local ; requête jusqu’à 1 Mio, réponse jusqu’à 8 Mio. |

Les jetons session, runtime, génération et révision protègent contre les modifications obsolètes. Les identifiants de paramètres sont temporaires, pas portables. Recharger peut invalider identifiants et annulation. Une commande expirée peut avoir commencé : relisez d’abord l’état.

```callout
{"type": "info", "title": "Note", "body": "Non implémentés : téléchargement web de packs, analyse automatique de captures dans Tchat, identification automatique du HUD, remplacement natif Vulkan/autres stages, historique automatique des presets, rejeu natif et réponses en streaming."}
```

## À lire aussi {#related}

- [Glossaire](doc:glossary)
- [Inspecter et remplacer les shaders du jeu](doc:native-shaders)
- [Clients MCP externes](doc:mcp)
