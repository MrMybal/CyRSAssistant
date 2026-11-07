# CyRSAssistant — Notes de version

[Retour au README](README.fr.md) · [English](VERSION.md)

**Application : 0.9.0 · Statut : PROTOTYPE**<br>
**Paquet disponible : Windows x64 · publié le 6 novembre 2026**<br>
**Cible : ReShade 6.8 / API 20 avec prise en charge complète des add-ons**

Cette préversion est destinée aux essais et aux retours. La qualité du rendu et la compatibilité dépendent du jeu et des shaders sélectionnés. Sa publication ne constitue pas une prise en charge stable de tous les jeux.

## Changements de la version 0.9.0

- Aide CyDoc illustrée complète : 26 pages par langue, anglais par défaut et traduction française complète, captures, schémas SVG, recherche, thèmes et exemples d’API publique.
- Onglet Aide, boutons d’aide contextuels et F1 lorsque le panneau CyRSAssistant a le focus, ouvrant la bonne page documentaire locale.
- Navigation hiérarchique du lecteur, barre latérale élargie, descriptions des pages et agrandissement des images dans la fenêtre documentaire.
- Même lecteur HTML complet fourni hors ligne et publié sur GitHub Pages, avec des redirections pour les anciens liens documentaires.
- Notices de licence complètes du runtime intégré et sources développeur correspondantes à côté du ZIP d’installation.

Le lecteur intégré est **CyDoc 0.1.0**, épinglé à la révision `6ddf9a582defb2f11fbb3f992afef6f98dcadc93`. Sa version est distincte de celle de l’application CyRSAssistant.

[Notes officielles et téléchargements](https://github.com/MrMybal/CyRSAssistant/releases/tag/v0.9.0) · [Empreinte du ZIP d’installation](https://github.com/MrMybal/CyRSAssistant/releases/download/v0.9.0/CyRSAssistant-0.9.0-windows-x64.zip.sha256) · [Empreinte du ZIP développeur](https://github.com/MrMybal/CyRSAssistant/releases/download/v0.9.0/CyRSAssistant-0.9.0.zip.sha256)

## Mise à jour et retour arrière

Fermez le jeu. Conservez une copie de l’ancien add-on, du compagnon, du runtime et des notices avant d’extraire le nouveau paquet complet à côté de la DLL ReShade. Préservez ReShade.ini, les presets, les shaders générés et CyRSAssistant/library. Pour revenir en arrière, restaurez ensemble les anciens binaires et leur runtime. Voir le [guide de mise à jour](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/fr/update).

## Problèmes connus

Les notes publiées de la version 0.9.0 ne fournissent pas de liste détaillée de bugs confirmés. Consultez le [suivi des problèmes](https://github.com/MrMybal/CyRSAssistant/issues) pour les signalements ou [signalez un problème](https://github.com/MrMybal/CyRSAssistant/issues/new). Les limites ci-dessous décrivent le périmètre du produit ; elles ne garantissent pas l’absence de bugs.

## Limites documentées

- **Plateformes et shaders natifs** : le paquet fourni cible Windows x64. Le remplacement natif prend en charge les pixel shaders DX11/DX12 capturés ; les autres stages et Vulkan ne sont pas pris en charge. Les noms et le HLSL d’origine du jeu sont généralement indisponibles ; les shaders natifs sont identifiés par empreinte. Un shader partagé peut affecter plusieurs objets et l’assistant peut refuser une reconstruction incertaine.
- **Remplacement DX12** : chaque état de pipeline concerné est reconstruit avec ses autres stages, son état de rendu et sa root signature. Tous les pipelines actuels doivent réussir avant activation. Un futur pipeline incompatible désactive le remplacement et signale une erreur. Les listes de commandes déjà enregistrées peuvent encore référencer une ancienne version du shader.
- **FX générés** : la génération produit des effets autonomes contraints avec jusqu’à 16 contrôles nommés, sans boucles ni dépendances externes. La compilation ne garantit pas le résultat visuel demandé.
- **Modification et restauration** : l’ordre des techniques n’est pas modifié. L’annulation conserve une seule modification en mémoire et peut être invalidée par un changement d’inventaire ou un rechargement. Les remplacements de shaders ne sont pas réactivés automatiquement au redémarrage du jeu. L’enregistrement écrit le preset actif ; les sauvegardes historiques automatiques ne sont pas implémentées.
- **Automatismes indisponibles** : le téléchargement de packs de shaders, l’analyse automatique des captures et l’identification automatique du HUD ne sont pas implémentés.
- **Fournisseurs et tchat** : OpenCode et Antigravity peuvent utiliser des clients MCP externes, mais ne disposent pas de connecteur direct dans le panneau. Une session CLI reconnue ne garantit pas l’accès au modèle. Les réponses apparaissent une fois terminées, sans diffusion progressive. Les modes Automatique et À la demande autorisent une opération de rendu par message ; Accès complet permet plusieurs opérations dans les limites des outils.
- **Historique et données** : le runtime conserve jusqu’à 32 messages en RAM. Jusqu’à 16 messages précédents, limités à 24 000 caractères, accompagnent les demandes avec les données pertinentes des shaders et outils. Changer de fournisseur conserve ce contexte récent. Fermer le jeu efface le tchat local sans supprimer les données conservées par le fournisseur. Les clés API restent en mémoire pour la session. Voir [l’historique et les données transmises](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/fr/history-privacy).

## Références

- [Documentation française](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/fr/start) · [English manual](https://mrmybal.github.io/CyRSAssistant/Documentation.html#/en/start).
- [Versions publiées](https://github.com/MrMybal/CyRSAssistant/releases) · [Dépôt des sources](https://github.com/MrMybal/CyRSAssistant).
