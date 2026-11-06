---
id: capture
title: Capture et retour visuel
description: Capturez une image et donnez un retour visuel depuis un client externe.
section: Guides
order: 12
sourceRevision: 3
parent: native-shaders
---

## Vue d’ensemble {#overview}

La CLI et MCP externe peuvent capturer une image courante. Le tchat intégré ne reçoit pas automatiquement de captures : décrivez vos observations après un réglage. Un shader compilé n’est pas une comparaison visuelle.

```bash
python -m companion capture capture.png
```

La dimension maximale est 1280 pixels. La capture effectue une lecture GPU et peut inclure l’overlay ReShade. Ce n’est ni un enregistrement continu ni un tone mapping HDR. Un redimensionnement pendant la capture peut demander un nouvel essai.

1. Préparez la scène et demandez une capture en lecture seule.
2. Examinez l’image et notez les réglages de comparaison.
3. Avec un client IA externe, décidez explicitement si vous lui transmettez l’image ; les règles de données de son fournisseur s’appliquent.

## À lire aussi {#related}

- [Clients MCP externes](doc:mcp)
- [Historique, stockage et données fournisseur](doc:history-privacy)
- [DX12, restauration et limites du HUD](doc:dx12-hud)
