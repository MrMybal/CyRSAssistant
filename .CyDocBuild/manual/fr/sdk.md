---
id: sdk
title: CyMCPSDK, CLI et options avancées
description: Utiliser le registre partagé, les résultats privés, les sessions et les outils externes configurés.
section: Référence
parent: cli
order: 18
sourceRevision: 4
---

## Vue d’ensemble {#overview}

La version 0.10.1 intègre **CyMCPSDK 0.7.1**, révision `34d4bcae126bc83d1a2925b5047dac36e3d09d92`. Core, Platform, Http, MCP et AI sont compilés depuis l’archive de sources épinglée. La supervision de moteur local et ChatUI ne sont pas liés : l’application utilise des services locaux existants et le pont ImGui de ReShade ne fournit pas CyUI DocumentViews. Le panneau reçoit les événements Conversation depuis un worker ; les modifications ReShade restent sur le thread du jeu.

## Opérations partagées {#operations}

Le tchat, le CLI natif et MCP partagent 27 définitions et handlers. `CyRSAssistantCLI.exe tools` les liste ; `describe NOM` donne les schémas complets d’entrée et de sortie. Les noms `cyrs_` de l’ancien serveur MCP sont conservés. Lisez l’état courant et utilisez sa session, sa génération et sa révision avant une modification. Une action refusée ou expirée n’est jamais relancée automatiquement.

| Domaine | Opérations |
| --- | --- |
| Runtime | list_sessions, get_state, get_help_state, capture_frame |
| Effets | get_effects, get_parameters, read_effect_source, scan_effects, apply_patch, undo, save_preset, reload_effects |
| Génération | generate_effect, restore_generated_effect |
| Shaders natifs | list_game_shaders, inspect_game_shader, replace_game_shader, enable_game_shader, restore_game_shaders |
| Catalogue | catalog_scan, catalog_read, catalog_export, catalog_import, store_effect_description |
| Résultats | result_read, resource_grep, refresh |

Ajoutez `cyrs_` devant chaque nom. Les handlers du catalogue réutilisent l’implémentation Python existante via le compagnon fourni. L’export renvoie du JSON portable : redirigez-le dans votre script au lieu de donner au modèle un chemin de sortie arbitraire. Les commandes Python restent disponibles, y compris l’import/export de fichiers explicites et l’ancienne planification JSON. Les réglages de connexion, clés, changements d’autorisation, validations et soumissions récursives de tchat sont volontairement exclus des outils du modèle. L’ouverture de la documentation reste une action de l’interface.

## CLI et MCP {#connection}

Créez `read-parameters.json` avec le JSON suivant. Le fichier évite les différences de guillemets entre les terminaux Windows.

```json
{"runtime":1}
```

```powershell
CyRSAssistantCLI.exe --help
CyRSAssistantCLI.exe discover
CyRSAssistantCLI.exe tools
CyRSAssistantCLI.exe describe cyrs_get_parameters
CyRSAssistantCLI.exe --args-file read-parameters.json call cyrs_get_parameters
CyRSAssistantCLI.exe mcp
```

La découverte, les schémas et les métadonnées des fournisseurs ne nécessitent ni jeu ni interface graphique. Les opérations actives s’adressent à une instance ReShade déjà lancée. Utilisez `--pipe` lorsque plusieurs jeux sont découverts ; le processus sélectionné reste fixé. L’argument `runtime` de l’outil identifie son runtime. L’assistant intégré est limité au sien.

L’écriture exige `--allow-write` côté CLI/MCP **et** le mode d’autorisation courant de l’application. Le mode À la demande utilise les véritables boutons du panneau. Un CLI non interactif échoue avec `ApprovalRequired`, sauf si `--wait-for-approval` a été explicitement fourni pour un usage supervisé. Un « oui » du modèle ne vaut pas validation. Les codes de sortie sont 0 en cas de succès, 2 pour un usage CLI invalide, 3 pour un accès refusé ou une validation nécessaire et 1 pour les autres échecs. Les résultats JSON vont sur stdout et les diagnostics sur stderr.

Le point d’entrée MCP natif en ligne de commande utilise stdio local, lancé avec le même exécutable et les options facultatives `--pipe` et `--allow-write`. L’accès est celui du processus et de l’utilisateur du système ; aucun serveur réseau public ni jeton à coller dans le tchat n’est requis. Les agents natifs nécessitant MCP reçoivent une adresse loopback authentifiée distincte, possédée par le worker SDK. Son secret passe par la configuration privée du fournisseur gérée par le SDK. HTTP prend en charge les requêtes/réponses et SSE fini ; utilisez stdio pour les abonnements SDK persistants.


```json
{"mcpServers":{"cyrsassistant":{"command":"C:/Games/Example/CyRSAssistantCLI.exe","args":["mcp"]}}}
```

Cette configuration stdio native est générique : utilisez le chemin réel de l’exécutable et le format de votre client. Ajoutez `--pipe` avant `mcp` lorsque plusieurs jeux sont ouverts, et `--allow-write` seulement pour un client de confiance autorisé à écrire.

## Accès MCP HTTP local {#local-access}

Activez **Options > Activer le MCP local**. Le compagnon démarre le serveur indépendamment d’un fournisseur de tchat. Copiez son adresse `http://127.0.0.1:<port>/mcp`. Le serveur écoute uniquement sur loopback ; le port change au redémarrage.

| Profil | Jeton | Opérations |
| --- | --- | --- |
| Free (défaut) | Aucun ; adresse seule | Toutes les opérations exposées sans confirmation supplémentaire. |
| Local contrôlé | Aucun ; adresse seule | Mode d’autorisation existant de l’assistant. |
| Jeton seul | Jeton Bearer de session | Toutes les opérations exposées sans confirmation supplémentaire. |
| Protégé | Jeton Bearer de session | Mode d’autorisation existant de l’assistant. |

Les schémas, bornes des paramètres, identité du runtime et jetons session/génération/révision restent vérifiés. Free concerne ce serveur HTTP ; les options d’écriture CLI/stdIO et les autorisations du tchat gardent leur comportement. Les outils distants nécessitent toujours une liste d’autorisation explicite.

Les choix `MCPAccessProfile` existants dans ReShade.ini sont conservés : 0 Free, 1 Local contrôlé, 2 Jeton seul, 3 Protégé. En leur absence, un `local_access_profile` explicite ou l’ancien `mcp_profile` dans sdk-options.json est repris ; sinon le profil migre vers Free. Une valeur explicite inconnue empêche l’activation. `MCPEnabled` reste facultatif. Les autres réglages et fichiers utilisateur sont conservés.

Pour les profils à jeton, **Copier le jeton MCP** copie le jeton de la session. Configurez séparément l’autorisation Bearer du client. Le jeton et la capacité interne du pont sont exclus des instantanés publics, mesures et historiques enregistrés. Un redémarrage ou changement de profil renouvelle le jeton ; désactiver le serveur ferme son processus. L’adresse HTTP interne des agents natifs du tchat reste distincte, avec ses autorisations de tchat.

## Options indépendantes {#options}

Copiez le fichier fourni `sdk-options.example.json` vers `CyRSAssistant/sdk-options.json` sous le dossier de base ReShade de ce jeu. L’exemple n’est jamais activé ni copié automatiquement sur vos réglages. Reconnectez-vous après modification. Pour un processus console, fournissez explicitement `--options FICHIER`. Les chemins relatifs d’historique, de stockage et de mesures sont résolus à côté de ce fichier.

| Option | Valeur par défaut / comportement |
| --- | --- |
| compact_discovery / discovery_threshold | true / 32 ; les grands catalogues du fournisseur utilisent recherche, chargement du schéma et invocation. La liste MCP complète reste accessible. |
| large_results / inline_bytes | true / 65 536 ; les workers persistants du tchat/MCP conservent les gros résultats sous forme de ressources privées. Un appel CLI ponctuel renvoie tout le JSON. |
| result_ttl_ms / memory_quota_bytes | 300 000 / 67 108 864 ; les références opaques expirent ou peuvent être évincées au quota. Suivez firstUri/nextUri du manifeste avec cyrs_result_read. Une expiration signale une erreur sans rejouer l’action. |
| disk_spooling / disk_quota_bytes / spool_directory | false / 268 435 456 / dossier explicitement choisi ; stockage privé facultatif sur disque. |
| cache_ttl_ms / notifications | 30 000 / false ; cache des métadonnées de découverte/lecture et journal de changements borné, indépendant. Les mutations tools/call ne sont pas mémorisées. |
| remote_notifications | false ; les abonnements distants compatibles invalident les caches de découverte/lecture. Les autres serveurs conservent le TTL et la reconnexion explicite. |
| metrics / metrics_file | false / JSONL privé facultatif ; noms d’opérations, durées, volumes, statuts et accès au cache uniquement. Aucun message, corps d’outil, clé ou identifiant de session. |
| context_bytes / context_recent_turns | 0 / 8 ; budget facultatif en octets pour la projection du contexte API. L’historique intégral, les consignes système, le tour actif et les échanges d’outils complets restent stockés. Les agents CLI gèrent leur propre contexte. Aucun résumé automatique n’est configuré. |
| persist_history / restore_history / history_directory | false / false / dossier privé explicite ; checkpoints SDK facultatifs. Restaurez avec le même compte fournisseur, la même adresse et le même modèle. Aucune action interrompue n’est rejouée. La restauration explicite exige un point de reprise existant ; désactivez-la pour la première connexion. |

Le panneau conserve toute la conversation en mémoire ; le suivi de l’état ne renvoie que les 32 derniers messages et leur nombre total. La conservation SDK est facultative et contient les données privées de conversation et des pièces jointes, sans configuration du fournisseur ni clé API. Les messages utilisateur et assistant restaurés sont rechargés dans le panneau. Une nouvelle conversation crée une session SDK neuve et retire le checkpoint actif enregistré. Les favoris et notes du lecteur documentaire sont distincts.

## Autres applications {#remote}

`remote_tools` est une liste d’autorisation explicite. Chaque serveur fournit un `id`, soit une `url` HTTP et un éventuel `token_env`, soit un `executable` natif avec `arguments` et un éventuel `cwd`, et un tableau `tools` des noms distants exacts. Les identifiants secrets appartiennent à la variable d’environnement nommée, jamais à ce JSON. `cyrs_refresh` actualise explicitement les schémas délégués et les caches de lecture. `allow_resources: true` active aussi des outils qualifiés de liste et de lecture des ressources distantes ; suivez leurs liens de blocs via l’outil de lecture de ce serveur. Le tchat, stdio et les profils HTTP contrôlés délèguent uniquement les outils annoncés en lecture seule. Free et Jeton seul en HTTP peuvent appeler tout outil explicitement autorisé ; l’application distante applique toujours ses propres permissions.

Le SDK suit la pagination des outils distants et préserve chaque schéma d’entrée sélectionné. Les mots-clés de schéma ou capacités de transport non pris en charge provoquent une erreur plutôt qu’un connecteur fictif. Les erreurs distantes remontent comme échecs d’outil. Aucun dossier de recherche système, exécutable ripgrep, shell, poids de modèle, installateur de pilote ou découverte automatique de serveurs externes n’est activé par défaut.

## Périmètre {#limits}

La plateforme livrée est Windows x64. La console native utilise le runtime Microsoft Visual C++ 2015–2022 x64, comme la compilation de l’add-on. Le paquet conserve le compilateur de shaders et le runtime du compagnon existants.

L’import du catalogue et les aperçus d’autorisation restent bornés par le pont local existant : requêtes de 1 Mio et aperçus de 100 000 octets. Les sources FX sont limitées aux dossiers de shaders configurés et paginées par position d’octet UTF-8 ; les noms, valeurs et bornes utilisent des lectures filtrées et paginées. L’inspection native reste celle des pixel shaders DX11/DX12, sans reconstruction de leur source. La capture PNG reste disponible via MCP ; appeler cet outil ne transforme pas automatiquement chaque fournisseur en modèle de vision. Joignez un fichier uniquement si le fournisseur choisi prend en charge son type.

## À lire aussi {#related}

- [Tchat](doc:chat)
- [Autorisations](doc:permissions)
- [Clients MCP externes](doc:mcp)
- [Historique et données transmises](doc:history-privacy)
