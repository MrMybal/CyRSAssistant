---
id: protocol
title: API du pont local
description: Protocole 1, jetons de version, commandes natives et frontières de confiance.
section: Référence développeur
order: 100
sourceRevision: 1
kind: api
---

## Transport {#transport}

Le jeu expose `\\.\pipe\CyRSAssistant-<pid>`, réservé au SID de son utilisateur Windows ; les clients distants sont refusés. Un worker gère les entrées/sorties. Seuls les callbacks ReShade lisent ou modifient le runtime.

Chaque connexion porte une requête et une réponse : longueur non signée sur quatre octets little-endian, puis JSON UTF-8. Le client acquitte la réponse complète avec un octet avant fermeture. Limites : 1 Mio par requête, 8 Mio par réponse. Les E/S sont annulables à l’arrêt.

Chaque requête contient `protocol: 1`, un `request_id` non vide de 100 caractères maximum et `method`. Toutes les méthodes sauf `list_sessions` exigent `runtime`. Voir le [dispatch](doc:source-src-addon-cpp#source), le [pont](doc:source-src-bridge-cpp#source) et le [client Python](doc:source-companion-transport-py#source).

## État et modifications {#state}

| Méthode | Champs supplémentaires | Résultat |
| --- | --- | --- |
| `list_sessions` | aucun | Identifiants de session et runtimes |
| `get_state` | runtime | Effets, noms, types, bornes, valeurs, racines et jetons |
| `scan_effects` | runtime | Réénumère les effets ; incrémente generation et supprime l’annulation |
| `apply_patch` | version complète, changes ; prompt_id facultatif | Valide avant écriture, vérifie la relecture et tente un retour arrière si nécessaire |
| `undo` | version complète | Restaure le dernier patch si les valeurs touchées correspondent |
| `save_preset` | version complète | Enregistre le preset actif par ReShade |
| `reload_effects` | version complète | Recharge les FX ; invalide les identifiants et l’annulation |
| `assistant_reply` | session, runtime, prompt_id, message | Affiche la réponse uniquement si la demande reste en attente |
| `assistant_progress` | session, runtime, prompt_id, message | Met à jour le statut de l’opération |

La version complète comprend `session`, `runtime`, `generation` et `revision`, relus dans l’état courant. Les identifiants de paramètres/techniques sont des indices liés à une génération, jamais des identités portables. Réénumérez après rechargement, reconnexion ou changement de runtime.

Un patch contient jusqu’à 64 entrées `{kind, id, value}`. Une technique utilise un booléen ; les paramètres, des tableaux de composantes typées. Les réponses contiennent `ok: true` et un résultat, ou `ok: false` et `error`.

Les réponses récentes aux mutations sont conservées pour dédupliquer les répétitions exactes : 256 requêtes et environ 16 Mio maximum. Réutiliser un identifiant conservé avec un contenu différent est refusé. Les lectures ne sont pas mises en cache. Les préconditions de version restent obligatoires.

Une commande expire après cinq secondes sans callback adapté. Une opération peut déjà avoir commencé lors d’un timeout : relisez l’état avant de réessayer. Un jeu fermé ou minimisé peut cesser de présenter des images. Les commandes expirées ne sont pas appliquées à la reprise.

## Shaders natifs et génération {#shaders}

`list_game_shaders(runtime)` retourne les empreintes SHA-256 du bytecode, les compteurs, `api` et, par shader, `encoding`, `pipelines`, `replaceable_pipelines`, `limitation` et `error`. `inspect_game_shader(runtime, hash)` retourne désassemblage, réflexion, déclarations conservées et profil d’origine. Ce n’est pas le HLSL original.

Les mutations exigent la version complète et acceptent `prompt_id` pour rejeter une demande annulée :

- `generate_effect(body, name?, title?, parameters?, replace_effect?)` précompile un corps float3 contraint, écrit un FX identifié par son contenu dans la première racine d’effets, puis recharge. Suivez `generated.phase` : compiling, initializing, ready, cancelled ou error. Un autre contenu n’écrase pas un fichier généré existant.
- Jusqu’à 16 paramètres float `{name, label, min, max, default, step}` deviennent les contrôles `CyRSP_<name>`. `CyRSPixelSize` donne les dimensions inverses du buffer. Les déclarations globales/includes sont refusés.
- `replace_effect` désigne un nom FX chargé exact, dont toutes les techniques doivent être modifiables. La bascule n’a lieu qu’après initialisation et vérification. Le source original reste intact.
- `restore_generated_effect()` restaure les techniques du dernier effet remplacé.
- `replace_game_shader(hash, source)` compile `main` pour le profil original, vérifie signatures/ressources et active aux binds suivants. Retour : empreintes originale/remplacement et `rebuilt_pipelines` en DX12.
- `enable_game_shader(hash, enabled)` bascule un remplacement compilé ; `restore_game_shaders()` désactive les remplacements du périphérique.

Le bytecode original est conservé. Les empreintes couvrent tous ses octets, pas son sens visuel. Capture : 4096 empreintes / 64 Mio par périphérique. DX11 conserve au plus 64 versions GPU jusqu’au teardown. [Parcours natif](doc:native-shaders).

## DX12 / DXIL {#dx12}

Les variantes de tous les PSO requis sont créées avant publication. Un échec détruit les variantes non publiées et conserve la règle précédente. Les futurs PSO compatibles reçoivent une variante ; un PSO incompatible désactive la règle avec une erreur visible.

Capture : 4096 snapshots / 128 Mio, 4 Mio maximum chacun. Copies profondes des stages, layouts de sommets et noms sémantiques ; référence COM conservée sur la root signature. Au plus 256 variantes GPU restent jusqu’au teardown. Restaurer ne réécrit pas les command lists déjà enregistrées.

DXIL utilise Microsoft DXC 1.8.2505.32 ; espaces de registres, signatures, constantes et ressources sont contrôlés. DXBC 5.1, mesh/raytracing et autres stages ne sont pas pris en charge.

Références : [exemples ReShade](https://github.com/crosire/reshade/blob/main/examples/README.md), [D3DReflect](https://learn.microsoft.com/windows/win32/api/d3dcompiler/nf-d3dcompiler-d3dreflect), [état du pipeline DX12](https://learn.microsoft.com/windows/win32/direct3d12/managing-graphics-pipeline-state-in-direct3d-12), [DXC épinglé](https://github.com/microsoft/DirectXShaderCompiler/releases/tag/v1.8.2505.1).

## Conversation {#conversation}

`get_state.conversation` contient jusqu’à 32 objets `{role, content, mode}` par runtime en RAM. Le fournisseur reçoit au plus 16 messages précédents / 24 000 caractères. `prompt_id` rejette les réponses périmées. Annuler ne restaure pas les modifications appliquées.

`send_chat(runtime, session, text)` valide comme Envoyer : fournisseur connecté, aucune demande en cours, de 1 à 4095 octets UTF-8 hors espaces seuls. Retour : `prompt_id`. Aucun effet/shader sélectionné n’est requis. Le panneau utilise le mode 3 ; les anciens modes 0/1/2 restent interprétés.

Le modèle consulte les inventaires paginés `get_effects` et `get_parameters`. `read_effect_source` résout FX/FXH uniquement sous les racines configurées et refuse doublons ambigus et traversées. Aucune réponse n’exécute un shell ou une méthode native arbitraire.

## Autorisations {#permissions}

`get_state.permissions` expose `mode` (0 Automatique, 1 À la demande, 2 Accès complet), `epoch` et `request`. `set_permission_mode(runtime, session, mode)` annule la demande et mémorise le choix. Les contrôles locaux ne sont pas des outils du modèle.

`request_action_permission(runtime, session, prompt_id, action, payload, summary)` retourne un identifiant unique et un statut pending/approved. `resolve_action_permission(permission_id, allow)` applique la décision du panneau. Le compagnon garde son signal de présence actif pendant l’attente.

L’accord porte sur le contenu exact, le prompt et l’époque d’autorisation ; il est consommé une fois. La lecture de source emploie `consume_read_permission` avant lecture/transmission. Refus/annulation interrompent l’action. Les écritures MCP permises par `--allow-write` restent distinctes.

## Langue {#language}

`get_state.language` et `get_connection.connection.language` donnent la langue enregistrée. `set_language(runtime, session, language)` la mémorise dans ReShade.ini. L’anglais est le défaut/repli ; français et codes régionaux reconnus résolvent leur langue de base.

Changer de langue conserve révisions de rendu, conversation, époques de connexion, demandes et autorisations. Les messages existants/en attente gardent leur langue ; les prochaines demandes emploient le nouveau choix. [Traductions](doc:localization).

## Contrôles d’aide CyDoc {#help}

Ces commandes locales ne sont pas des outils IA/MCP :

- `get_help_state(runtime)` retourne page, ancre/média, langue, dernière URL file lancée et erreur locale.
- `open_help(runtime, session, chapter?, anchor?, media?, query?, open?)` valide les identifiants stables puis ouvre le lecteur installé via une URL file encodée. `chapter` conserve les 21 anciens identifiants et accepte aussi les pages techniques indexées.
- `open: false` efface le statut local ; il ne peut pas fermer une fenêtre du navigateur externe. Ce comportement remplace la fenêtre ImGui de la 0.8.
- Lire l’aide n’appelle aucun fournisseur et ne change ni rendu, ni historique, ni permissions. Les anciennes entrées `index.en.html#start` et `index.fr.html#start` redirigent vers CyDoc.

[Intégration native](doc:source-src-manual-cpp#source) · [MCP externe](doc:mcp).
