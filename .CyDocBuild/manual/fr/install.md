---
id: install
title: Installation et prérequis
description: Placez l’add-on, le compagnon, DXC et le manuel près de l’exécutable de rendu.
section: Guides
order: 1
sourceRevision: 3
parent: start
---

## Vue d’ensemble {#overview}

Utilisez un jeu Windows 64 bits et ReShade 6.8 avec support complet des add-ons. L’intégration cible l’API 20 et le pont ImGui 1.92.5. Le remplacement natif concerne les pixel shaders Direct3D 11/12, pas toutes les API graphiques.

1. Fermez le jeu et sauvegardez une installation existante.
2. Repérez la DLL ReShade, par exemple dxgi.dll ou d3d11.dll. Utilisez le dossier de l’exécutable de rendu, pas un lanceur séparé.
3. Extrayez le ZIP d’installation dans ce dossier en gardant ses sous-dossiers. Le ZIP de développement a une autre arborescence.
4. Lancez le jeu, vérifiez ReShade > Add-ons / Log, puis ouvrez CyRSAssistant.

```text
Dossier du jeu
  CyRSAssistant.addon64
  CyRSAssistantCompanion.exe
  CyRSAssistantRuntime/
    dxcompiler.dll
    dxil.dll
    LICENSE-LLVM.txt
    LICENSE-MS.txt
  CyRSAssistant/
    INSTALL.txt
    Documentation/
      Documentation.html
      DocAI.md
      DocData/
        assets/
  LICENCES/
```

Python est intégré au compagnon. L’overlay ne demande ni Python séparé ni terminal. Installez et connectez séparément le CLI fournisseur si vous choisissez Codex ou Claude Code.

```callout
{"type": "info", "title": "Note", "body": "Gardez CyRSAssistantRuntime à côté de l’add-on pour DXC, ainsi que Documentation et LICENCES. L’add-on n’installe ni packs de shaders, ni CLI fournisseur, ni poids de modèles."}
```

## À lire aussi {#related}

- [Mises à jour, sauvegardes et retour arrière](doc:update)
- [Connecter un fournisseur](doc:connect)
- [Dépannage](doc:troubleshooting)
