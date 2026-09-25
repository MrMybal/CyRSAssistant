# CyRSAssistant

[English](README.md) | Français

Assistant intégré à ReShade : décrire le rendu souhaité, exploiter les effets installés, régler un preset en direct et créer des effets adaptés. Les capacités avancées visent l'inspection du rendu, le masquage du HUD et le remplacement ciblé de shaders du jeu.

État : prototype 0.7.0 Windows x64, compilé avec ReShade 6.8 / API 20. Génération FX et remplacement temporaire de pixel shaders testés dans Stray en DX11 et DX12. Compilation DXIL et création de PSO Shader Model 6 testées sur un périphérique DX12. La qualité du rendu pendant une partie reste à évaluer.

## Langue

L’interface démarre en anglais. Ouvrez **Options > Language** et choisissez **Français**. Le choix est mémorisé par jeu et s’applique sans redémarrage. Les nouvelles réponses de l’IA utilisent cette langue, sauf demande explicite d’une autre langue. Les messages existants restent inchangés.

Pour ajouter une langue, voir [le guide de traduction](docs/localization.md).

## Disponible

- Panneau ReShade : inventaire, activation des techniques, édition des paramètres, annulation du dernier changement et sauvegarde explicite du preset.
- Choix du fournisseur dans le panneau : Codex CLI, Claude Code CLI, API compatible OpenAI ou modèle local. Connexion/déconnexion, état surveillé, démarrage automatique du service Windows autonome.
- Génération IA de FX autonomes : précompilation HLSL, compilation ReShade, activation et désactivation. Échantillonnage écran, couleurs, grain et vignette ; pas de boucles ni de dépendances externes.
- Remplacement réversible des pixel shaders DX11/DX12 : inventaire SHA-256, inspection DXBC, compilation HLSL, contrôle des signatures et des déclarations de ressources, activation au prochain bind du jeu.
- Catalogue sur disque : empreintes, ajouts/modifications/suppressions, descriptions IA sur demande, export/import des métadonnées.
- Interface MCP locale : lecture des effets et, avec `--allow-write`, réglages, annulation et sauvegarde pour les agents compatibles.
- Validation des types, limites annotées, générations et révisions ; rejet des commandes obsolètes et paramètres pilotés par ReShade.

## Démarrage

Téléchargez **CyRSAssistant-0.7.0-windows-x64.zip** depuis la [release 0.7.0](https://github.com/MrMybal/CyRSAssistant/releases/tag/v0.7.0). Fermez le jeu et extrayez le ZIP à côté de la DLL ReShade, en conservant les sous-dossiers. Les fichiers de l’add-on sont directement à la racine du ZIP et Python est intégré.

Pour produire ce ZIP : `python tools/package.py --install`.

Voir [le guide d'installation et de connexion](docs/getting-started.fr.md). Le paquet avec sources est produit dans `dist/CyRSAssistant-0.7.0.zip` avec `python tools/package.py`.

Compilation depuis les sources (Visual Studio 2022 C++, Windows SDK et Python 3.11+) :

```powershell
python tools/bootstrap.py
python tools/build.py
python -m venv build/packaging-env
build/packaging-env/Scripts/python.exe -m pip install pyinstaller==6.20.0
python tools/build_service.py
python -m unittest discover -s tests -p 'test_*.py' -v
python tools/package.py
```

Les dépendances viennent des projets officiels, avec versions et empreintes épinglées. Aucune dépendance vers CyGameCapture ou CyGPUInspector.

## Limites du prototype

Pas encore de téléchargement de packs, analyse automatique d’images ni identification automatique du HUD. Le remplacement est limité aux pixel shaders DX11/DX12 capturés après chargement de l’add-on ; Vulkan et les autres stages ne sont pas encore pris en charge. Un shader partagé peut affecter plusieurs objets. L’IA reçoit le désassemblage et les signatures, pas le HLSL original ; elle peut refuser une reconstruction incertaine. Les remplacements ne sont pas réactivés automatiquement au redémarrage. L'ordre des techniques n'est pas modifié. L'annulation conserve un seul changement, en mémoire, et est invalidée par un scan/rechargement. La sauvegarde écrit le preset actif ; les sauvegardes historiques sur disque restent à implémenter.

Le connecteur HTTP nécessite une URL, un modèle et, selon le fournisseur, une clé API. Codex et Claude utilisent la session authentifiée de leur CLI installé. Le statut distingue la session locale reconnue d’une réponse effective du modèle. OpenCode et Antigravity peuvent utiliser MCP depuis leur interface ; ils n’ont pas encore de connecteur direct dans le panneau. MCP fournit une autre voie : les agents appellent les outils depuis leur propre interface ; leur conversation n'est pas automatiquement recopiée dans le panneau ReShade.

Voir [l'architecture et les étapes de réalisation](docs/architecture.md).

## DX12 et runtime DXC

Installer également le dossier `CyRSAssistantRuntime` fourni dans le paquet. Il contient le compilateur DXC officiel Microsoft 1.8.2505.32, son validateur et leurs licences. Le téléchargement de compilation est épinglé par SHA-256 dans `tools/bootstrap_dxc.py`.

En DX12, chaque PSO qui utilise le pixel shader sélectionné est reconstruit avec ses autres stages, son état de rendu et sa root signature. Les PSO actuels doivent tous réussir avant activation. Un nouveau PSO impossible à reconstruire désactive le remplacement et expose une erreur. La restauration s’applique aux prochains binds enregistrés : les command lists déjà enregistrées peuvent encore référencer une ancienne version. Le support DXIL ne garantit pas qu’un LLM puisse reconstruire fidèlement un shader complexe.

## Conversation

Le tchat dispose d'outils pour rechercher les effets et leurs techniques, lire les parametres nommes avec leurs valeurs et bornes, et lire les fichiers FX/FXH dans les dossiers de shaders configures. Les gros inventaires et sources sont pages. Il peut inspecter plusieurs elements avant de repondre, puis relire l'etat apres une modification. Les shaders internes du jeu sont identifies par empreinte lorsque leurs noms d'origine ne sont pas disponibles.

Le remplacement d'un effet ReShade se distingue de l'ajout et du remplacement d'un shader interne. La cible FX doit etre identifiee ; une demande ambigue appelle une precision. Un FX genere peut fournir jusqu'a 16 controles nommes. Le remplacement compile une nouvelle variante, desactive l'ancienne apres reussite et conserve une restauration du dernier remplacement en memoire. Le tchat limite chaque tour a huit appels d'outils et une operation de rendu en modes Automatique et A la demande ; Acces complet autorise jusqu'a seize appels et huit operations.

Le sous-onglet **Tchat** permet de discuter avec le fournisseur connecte, meme avec zero effet charge. Aucun mode d'action ni shader selectionne n'est requis pour envoyer un message. L'assistant repond aux questions et utilise les fonctions de reglage, generation FX ou remplacement quand la demande porte sur une modification. Les controles manuels sont separes dans **Effets**, **Shaders** et **Connexion**.

Le panneau conserve les 32 derniers messages en mémoire, avec copie du texte, annulation et nouvelle conversation. Ctrl+Entrée envoie ; Entrée ajoute une ligne. Les 16 derniers messages précédents, limités à 24 000 caractères, accompagnent les demandes au fournisseur sélectionné. L’historique disparaît à la fermeture du runtime. Effacer la conversation ne restaure pas les effets. Les réponses arrivent une fois le traitement terminé, sans streaming.

## Licence

CyRSAssistant — Cyberalien. Distribué sous GPL-3.0-only ; voir [LICENSE](LICENSE). Les composants tiers conservent leurs licences, listées dans [THIRD_PARTY.md](THIRD_PARTY.md).

## Autorisations

Dans **CyRSAssistant > Options > Mode d'autorisation**, choisissez :

- **Automatique** (par defaut) : lecture des effets et de leur code, et execution des actions demandees sans clic supplementaire.
- **A la demande** : les noms et valeurs restent accessibles. Chaque modification du rendu et chaque lecture de source FX ou desassemblage natif a transmettre au fournisseur necessite une validation dans le tchat. Les valeurs ou le code proposes peuvent etre consultes avant **Autoriser cette action** ou **Refuser cette action**.
- **Acces complet aux outils ReShade** : l'assistant peut enchainer plusieurs operations de rendu pour accomplir la demande, sans validation intermediaire.

Le choix est memorise dans ReShade.ini pour cette installation. Un changement de mode annule la demande en cours. Chaque autorisation vaut pour une action precise, dans la conversation en cours ; une action modifiee ou annulee doit etre proposee de nouveau. Les modes concernent l'assistant integre et les outils ReShade disponibles ; ils ne changent pas les permissions de l'application Codex ni l'acces MCP externe, qui reste controle par `--allow-write`.
