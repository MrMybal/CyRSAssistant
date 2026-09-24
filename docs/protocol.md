# Local protocol v1

The game exposes `\\.\pipe\CyRSAssistant-<pid>`, restricted to its Windows user SID and rejecting remote clients. A worker handles pipe I/O; ReShade callbacks alone read or mutate the runtime.

Each connection carries one request and one response. Frames are a 4-byte little-endian unsigned length followed by UTF-8 JSON. The client sends one acknowledgement byte after receiving the complete response, before closing. Requests are limited to 1 MiB and responses to 8 MiB. I/O is cancellable during shutdown.

Requests contain `protocol: 1`, a nonempty `request_id` (maximum 100 characters), and `method`. All methods except `list_sessions` require an explicit `runtime` identifier. See `src/addon.cpp` for the dispatch contract and `companion/transport.py` for a client.

| Method | Additional fields | Result |
| --- | --- | --- |
| `list_sessions` | none | Session identifier and runtime identifiers |
| `get_state` | runtime | Current catalogue, values, configuration roots and version tokens |
| `scan_effects` | runtime | Re-enumerates loaded effects, increments generation and discards undo |
| `apply_patch` | session, runtime, generation, revision, changes; optional prompt_id | Validates all changes before writing, checks resulting values, attempts rollback on mismatch |
| `undo` | session, runtime, generation, revision | Restores the last patch if touched values still match |
| `save_preset` | session, runtime, generation, revision | Requests saving the active preset through ReShade |
| `assistant_reply` | session, runtime, prompt_id, message | Shows the reply only if the prompt is still pending |

Version tokens come from `get_state`. Parameter and technique IDs are indexes scoped to one generation. Never persist them as portable shader identities. Re-enumerate after reloading, reconnecting or changing runtime. `changes` contains up to 64 entries of `{kind, id, value}`. A technique value is boolean; parameter values are typed component arrays.

Replies use `ok: true` with a result or `ok: false` with `error`. The bridge retains the most recent mutation replies (up to 256 requests, approximately 16 MiB) to deduplicate exact retries. Reusing a retained request ID with a different payload is refused. Read-only state polls are not cached. Version preconditions remain necessary even when retrying.

Queued commands expire after five seconds without an appropriate runtime callback. A timeout can race an operation already started: read the current state before retrying and never assume a timeout means no change occurred. Closed or minimized games may stop presenting frames. The queue does not apply expired commands when rendering resumes.

The MCP server wraps only an explicit allowlist of these methods, with writes opt-in at startup. Chat Completions responses cannot inject arbitrary native methods. Shader source actions are explicit methods in v0.2; source is compiled under fixed entry points/profiles without includes. No model response is executed as a shell command.

## Shader laboratory (0.2)

Read methods: `list_game_shaders(runtime)` returns SHA-256 identities and bind counters; `inspect_game_shader(runtime, hash)` returns DXBC assembly and reflection, including surviving binding declarations for stripped shaders.

Mutation methods require the full version tuple (`session`, `runtime`, `generation`, `revision`), plus an optional `prompt_id` to reject cancelled overlay work:

- `generate_effect(body)`: precompile a float3 function body, write a content-addressed standalone FX in the first effect search directory, reload all effects, then activate only while its originating request is valid. Poll `get_state.generated.phase`: compiling, initializing, ready, cancelled or error. Files are not overwritten with different content.
- `replace_game_shader(hash, source)`: compile main/ps_5_0, validate original input/output and DXBC bindings, create a GPU shader, then replace at subsequent game binds. Returns the original and replacement hashes.
- `enable_game_shader(hash, enabled)`: toggle an existing replacement.
- `restore_game_shaders()`: disable all replacements for the runtime device.

The original bytecode remains intact. GPU versions are kept until device teardown (64-version cap); shader capture is bounded to 4096 unique hashes / 64 MiB per device. Only DX11 pixel shaders are supported. Hashes include all original bytecode bytes and are not semantic hashes.

References: [ReShade add-on examples](https://github.com/crosire/reshade/blob/main/examples/README.md), [Microsoft D3DReflect](https://learn.microsoft.com/windows/win32/api/d3dcompiler/nf-d3dcompiler-d3dreflect).

## DX12 / DXIL (0.3)

`list_game_shaders` ajoute `api` ainsi que, pour chaque shader, `encoding`, `pipelines`, `replaceable_pipelines`, `limitation` et `error`. `inspect_game_shader.stage` contient le profil réel retenu. `replace_game_shader` compile avec ce profil et retourne `rebuilt_pipelines`.

Les variantes de tous les PSO DX12 actifs sont créées avant la publication du remplacement ; un échec détruit seulement les variantes non publiées et conserve le remplacement précédent. Les nouveaux PSO du jeu reçoivent une variante si la règle est active. S’ils sont impossibles à reconstruire, la règle est désactivée avec une erreur visible.

Capture : 4096 identités de shaders / 64 MiB, jusqu’à 4096 snapshots de PSO / 128 MiB, maximum 4 MiB par snapshot. Copies profondes des stages, dispositions de sommets et noms de sémantiques ; référence COM conservée sur la root signature. Variantes GPU conservées jusqu’au teardown (64 en DX11, 256 PSO en DX12). Les command lists déjà enregistrées ne sont pas réécrites lors d’une restauration.

DXIL utilise le runtime officiel Microsoft DXC 1.8.2505.32 ; ses espaces de registres, signatures, constantes et ressources sont contrôlés. DXBC 5.1 et les pipelines mesh/raytracing ne sont pas couverts.

Références : [Pipeline state DX12](https://learn.microsoft.com/en-us/windows/win32/direct3d12/managing-graphics-pipeline-state-in-direct3d-12), [DXC 1.8.2505.1 / binaires 1.8.2505.32](https://github.com/microsoft/DirectXShaderCompiler/releases/tag/v1.8.2505.1).

## Conversation (0.3.1)

`get_state` expose `conversation` : au plus 32 objets `{role, content, mode}`. L’historique est propre au runtime et reste en mémoire. Le compagnon borne le contexte transmis aux fournisseurs à 16 messages et 24 000 caractères. Les réponses obsolètes restent rejetées par `prompt_id`. Annuler une demande ne restaure pas les modifications déjà appliquées.

## Tchat (0.4.0)

`send_chat` prend `runtime`, `session`, `text` (1 a 4095 octets UTF-8 hors espaces seuls). Il utilise la meme validation que le bouton Envoyer : connexion prete et aucune demande en attente. Il retourne `prompt_id`. Aucune selection de shader ni aucun effet charge ne sont requis. Les messages du panneau utilisent `prompt.mode = 3` ; les modes 0, 1 et 2 restent interpretes par le compagnon pour compatibilite. Le routeur de conversation retourne une reponse ou une action autorisee ; les mutations conservent les verifications de session, revision et prompt.

## Inspection et effets parametrables (0.5.0)

`get_state` reste la source des noms, labels, types, valeurs et bornes des parametres. Le compagnon propose des outils pages `get_effects`, `get_parameters` et `read_effect_source` (FX/FXH resolus uniquement dans les racines configurees, refus des doublons et des traversals). Il propose aussi l'inventaire et l'inspection des shaders natifs.

`generate_effect` accepte maintenant `name`, `title`, `parameters` et `replace_effect` en option. Chaque parametre est un float `{name, label, min, max, default, step}` ; il devient `CyRSP_<name>` dans le corps HLSL et un controle ReShade. Maximum 16, noms et bornes valides, pas d'injection de declarations. `CyRSPixelSize` fournit les dimensions inversees du buffer. `replace_effect` est un nom FX charge exact : toutes ses techniques doivent etre modifiables. Le fichier original n'est pas ecrase. La bascule des activations intervient apres l'initialisation du nouveau shader et est verifiee.

`restore_generated_effect` utilise les jetons de version habituels et restaure les techniques du dernier effet remplace. `assistant_progress` prend runtime/session/prompt_id/message et alimente le statut du travail en cours. Les commandes marquees par prompt_id sont refusees apres annulation ou remplacement de la demande.

## Autorisations (0.6.0)

`get_state.permissions` expose `mode` (0 automatique, 1 a la demande, 2 acces complet), `epoch` et la demande courante (`request`). `set_permission_mode` prend runtime/session/mode, annule une demande en cours et memorise le mode. Ces commandes de controle local ne sont pas exposees aux outils du modele.

`request_action_permission` prend runtime/session/prompt_id/action/payload/summary. La reponse contient un identifiant unique et un statut pending ou approved. `resolve_action_permission` applique la decision des boutons du panneau (permission_id/allow). Le compagnon attend en gardant son signal de presence actif. Un refus ou une annulation interrompt l'action.

Les mutations de l'assistant en mode a la demande exigent `permission_id` et le payload exact approuve. Le jeton est consomme une fois, lie au prompt et a la revision du mode. Les lectures de source utilisent `consume_read_permission` avant lecture et envoi au fournisseur. Les commandes MCP directes autorisees par `--allow-write` restent distinctes de la conversation integree.

## Language (0.7.0)

`get_state.language` and `get_connection.connection.language` expose the saved interface language code. English (`en`) is the default; French (`fr`) is included. `set_language` takes `runtime`, `session` and `language`, returns the resolved language code and persists it to ReShade.ini. Unsupported codes fall back to English; supported regional codes resolve to their base language.

Changing language does not modify rendering revisions, conversation contents, connection epochs, pending requests or permission tokens. It is a local UI setting and is not exposed as an assistant tool. New provider requests use the selected response language; a request already running retains its original language. See [localization](localization.md) for catalog and build details.
