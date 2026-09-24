# Architecture proposée

Ce document décrit la conception et les objectifs à long terme. Le prototype 0.3.1 possède aussi la génération FX, le remplacement de pixel shaders DX11/DX12 et un historique de conversation. Le README et le protocole précisent les fonctions disponibles ; les outils proposés ci-dessous ne sont pas tous implémentés.

## Expérience attendue

Dans un panneau ReShade, l'utilisateur écrit par exemple : « Je veux un rendu cinéma, plus froid, sans noirs bouchés ». L'assistant consulte les effets disponibles, prépare des réglages, les applique et permet de comparer puis d'annuler. Une image de référence pourra compléter la demande lorsque le connecteur choisi accepte les images.

Il faut distinguer trois objets : un preset contient les réglages et l'ordre des effets ; un effet ReShade est un programme de post-traitement ; un shader du jeu appartient à son moteur de rendu. Leur création, leur installation et leur remplacement demandent des outils différents.

## Composants

### Add-on C++ dans ReShade

- Panneau de conversation, état de connexion, catalogue, boutons Scanner, Comparer, Annuler et Enregistrer.
- Lecture des effets chargés, techniques, paramètres, annotations et valeurs courantes.
- Application de commandes typées et bornées, sauvegarde explicite des presets.
- Capture ponctuelle du rendu pour les connecteurs disposant de vision.
- File de commandes consommée dans un callback ReShade approprié ; aucun appel réseau ou LLM bloquant sur le thread de rendu.
- Invalidation des identifiants runtime après rechargement des effets ; les commandes obsolètes sont rejetées.
- Prise en charge de plusieurs runtimes : chaque commande cible une session et un runtime précis.

### Service local compagnon

- Conversation, recherche du catalogue, indexation des fichiers et génération de descriptions.
- Adaptateurs vers fournisseurs IA et agents externes. Connexion API et connexion à un agent sont deux modes distincts.
- Serveur d'outils, éventuellement MCP, pour les clients compatibles. La compatibilité avec Codex, Claude, Antigravity et OpenCode doit être vérifiée individuellement avant de l'annoncer.
- Téléchargement, vérification et préparation des paquets de shaders hors du processus du jeu.
- Communication locale proposée : named pipe Windows avec accès limité à l'utilisateur, protocole JSON versionné et limites de taille.
- Les secrets de connexion restent dans le stockage utilisateur, hors des dossiers exportables.

L'interface de l'assistant reste dans ReShade ; le service absorbe les traitements longs et isole les défaillances des connecteurs.

## Catalogue portable

Stockage proposé à côté de la configuration ReShade de chaque installation :

```text
CyRSAssistant/
  library/catalog.json
  library/descriptions/
  profiles/<game-id>/
  sessions/
  backups/
  generated/
```

Le catalogue commun décrit les effets, leurs usages et leurs dépendances. Les profils contiennent les observations propres au jeu : profondeur disponible, API graphique, réglages retenus et règles HUD. Copier une description ne signifie pas qu'un réglage sera visuellement identique sur un autre jeu.

Chaque entrée comprend : identifiant stable, chemin relatif, empreinte du contenu, empreintes des includes et textures, origine et révision si connues, licence, techniques, paramètres et annotations. Une description IA séparée indique son auteur/modèle, sa date, la version du schéma, les empreintes analysées et son statut de validation. Les coûts GPU mesurés restent attachés au matériel, à la résolution et au profil du jeu.

Le scan combine les répertoires de recherche configurés dans ReShade et l'état réellement chargé. Il distingue fichiers présents, effets chargés et effets indisponibles ; les détails d'une erreur de compilation ne sont affichés que s'ils sont accessibles. Il signale ajouts, modifications et suppressions, et invalide les descriptions touchées par une dépendance modifiée. Un bouton permet de relancer le scan ; une surveillance avec temporisation peut suivre ensuite.

L'export contient les métadonnées, descriptions et profils choisis, sans secrets ni chemins absolus requis. À l'import, les fichiers locaux sont rapprochés par empreinte et les dépendances manquantes sont signalées. La redistribution des sources doit respecter leur licence.

## Outils proposés à l'assistant

Contrat conceptuel, à implémenter et versionner :

- `get_capabilities`, `get_session_state` : capacités disponibles et contexte du jeu.
- `scan_library`, `search_library`, `describe_effect` : inventaire et mémoire réutilisable.
- `get_effect_parameters`, `get_preset` : état réel avant modification.
- `apply_preset_patch`, `restore_snapshot`, `save_preset` : réglages avec annulation.
- `capture_frame` : retour visuel ponctuel.
- `search_packages`, `stage_package`, `install_package` : acquisition contrôlée.
- `stage_effect`, `reload_effects` : création ou modification d'un effet FX.
- À terme : `inspect_pipeline`, `test_hud_rule`, `stage_shader_replacement`.

Chaque modification inclut un identifiant de requête, la session, la génération du runtime et les préconditions attendues. Le service valide les types et le périmètre ; l'add-on revalide l'état réel avant exécution. Les réponses distinguent succès, refus, erreur et application partielle. Une répétition de requête ne doit pas appliquer deux fois une opération.

## Boucle de réglage et création en direct

1. Lire les effets et valeurs disponibles ; identifier les dépendances nécessaires au rendu demandé.
2. Sauvegarder l'état initial et préparer une modification limitée.
3. Valider paramètres, types et techniques avant application.
4. Appliquer, lire les valeurs résultantes et proposer une comparaison visuelle.
5. Ajuster selon le retour utilisateur ou une capture si la vision est disponible.
6. Enregistrer le résultat ou restaurer l'état initial.

Les modifications FX passent par des fichiers préparés séparément, une sauvegarde et un rechargement contrôlé. Un échec doit restaurer les fichiers précédents et tenter leur rechargement ; la compilation GPU ne peut pas être promise sans interruption. Le mode performance peut rendre les paramètres indisponibles : le signaler clairement avant un réglage interactif.

## Recherche et téléchargement

Commencer par une liste de dépôts connus et des révisions précises. GitHub est une origine traçable, pas une garantie de sûreté. Conserver URL, commit, empreintes et licence ; contrôler les chemins des archives, les tailles, les extensions et les dépendances. Ne pas exécuter de script d'installation fourni par un paquet de shaders. Préparer les téléchargements à part, puis installer avec sauvegarde et possibilité de retour arrière.

Les README, commentaires et descriptions récupérés servent de données au modèle, jamais d'instructions autorisant d'autres actions. Les recherches devront distinguer presets, sources FX et add-ons natifs.

## HUD et shaders du jeu

Masquer un HUD déjà composé dans l'image finale n'est pas une fonction universelle d'un effet de post-traitement. Il faut identifier une étape du rendu : ignorer certains dessins, capturer avant le HUD, ou appliquer les effets avant celui-ci répondent à des besoins distincts.

CyGameCapture et CyGPUInspector sont uniquement des références de conception, conformément à la demande de l'utilisateur. Ne pas les intégrer, les embarquer ou créer de dépendance vers eux. CyRSAssistant implémentera ses propres mécanismes nécessaires.

Un profil de remplacement doit identifier le jeu et sa version, l'API graphique, l'empreinte du shader original et ses contraintes de ressources. Une mise à jour du jeu peut invalider le profil. Ne pas activer un remplacement sur une correspondance incertaine. Prévoir un interrupteur global de restauration.

Le remplacement est techniquement illustré dans les exemples ReShade, mais une modification à chaud universelle n'est pas acquise : création des pipelines, format du bytecode, ressources et durée de vie GPU doivent être traités par backend. L'inspection ne garantit pas l'accès au code source d'origine. Le premier prototype avancé devra cibler un jeu et une API précis.

## Étapes et critères de validation

1. **Socle natif** : construire un add-on, afficher son panneau et inventorier techniques et paramètres dans un jeu de test. Épingler la version du SDK et vérifier la variante ReShade avec support add-on requise.
2. **Commande locale** : modifier un paramètre depuis le service, vérifier sa lecture, annuler et sauvegarder un preset. Tester déconnexion et rechargement sans utiliser de handles périmés.
3. **Mémoire portable** : scanner, détecter les changements d'effets et de dépendances, exporter puis réimporter dans une deuxième installation.
4. **Premier connecteur IA** : transformer une demande en commandes valides sur les effets existants. Rejeter les paramètres inventés et conserver l'annulation.
5. **Acquisition et génération** : installer un paquet traçable et créer un effet FX ; vérifier le retour arrière après une compilation échouée.
6. **Fonctions propres au jeu** : implémenter nos mécanismes en s'appuyant sur les exemples étudiés, sans dépendance aux deux add-ons ; tester une règle HUD puis un remplacement ciblé.

Premier jalon recommandé : assistant dans ReShade capable de scanner les effets installés, régler un preset par une demande textuelle et annuler l'opération.

## Sources consultées le 22 septembre 2026

- [API publique ReShade](https://github.com/crosire/reshade/blob/main/include/reshade_api.hpp) : inventaire et modification des paramètres, captures, sauvegarde, durée de vie des handles.
- [Exemples officiels](https://github.com/crosire/reshade/blob/main/examples/README.md) : notamment shader_dump et shader_replace.
- [Documentation ReShade](https://crosire.github.io/reshade-docs/) : référence pour l'implémentation à venir.

Ces références suivent actuellement la branche principale ; l'implémentation devra épingler un commit du SDK. Le présent document décrit une proposition, pas des fonctions déjà testées dans un jeu.
