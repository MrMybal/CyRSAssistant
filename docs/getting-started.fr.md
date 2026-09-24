# Connexion depuis ReShade

[English](getting-started.md) | Français

L’interface démarre en anglais. Dans **Options > Language**, choisissez **Français** pour retrouver les libellés de ce guide. Ce choix est mémorisé par jeu, sans effacer la conversation.

Copiez `CyRSAssistant.addon64`, `CyRSAssistantCompanion.exe` **et le dossier** `CyRSAssistantRuntime` à côté de ReShade, puis redémarrez le jeu. Dans l’onglet CyRSAssistant :

1. Ouvrez le sous-onglet **Connexion**, puis choisissez **Codex**, **Claude Code**, **API compatible OpenAI** ou **Modèle local**.
2. Pour les CLI, utilisez votre session existante (au besoin, connectez-vous une fois avec `codex login` ou `claude auth login`). Le modèle peut rester vide pour le modèle par défaut du CLI.
3. Pour une API, renseignez l’URL complète `/chat/completions`, le modèle et la clé éventuelle. « Connecter » effectue un petit appel de vérification.
4. Cliquez sur **Connecter**. Le service démarre automatiquement sans terminal. Le panneau indique la session locale reconnue ou la réponse du modèle, ou explique l’erreur.
5. Ouvrez le sous-onglet **Tchat**, ecrivez dans **Votre message**, puis cliquez sur **Envoyer** (ou Ctrl+Entree). Vous pouvez discuter sans effet charge et sans shader selectionne.
6. Demandez une explication, decrivez le rendu voulu ou demandez une modification. Les reglages manuels sont dans **Effets** ; les shaders du jeu sont dans **Shaders**. Le remplacement d'un shader interne du jeu demande une cible identifiee ; le remplacement d'un effet ReShade utilise son nom de fichier FX.

Le bouton d’envoi est désactivé sans connexion prête. Le service envoie un signal de présence ; après dix secondes sans signal, le panneau indique qu’il est injoignable. **Déconnecter / modifier** annule les demandes en attente avant de changer de fournisseur. Le fournisseur, l’URL et le modèle sont mémorisés dans ReShade.ini ; la clé API reste en mémoire et doit être ressaisie après le redémarrage.

Codex et Claude : la vérification de connexion lit le statut officiel du CLI, sans transmettre de requête au modèle. Le premier envoi vérifie l’accès effectif. Les réponses doivent produire un plan JSON validé avant application. OpenCode et Antigravity restent accessibles par l’interface MCP ci-dessous ; leur connexion n’est pas reflétée par le statut du compagnon intégré.

## Choisir les autorisations

Ouvrez **CyRSAssistant > Options > Mode d'autorisation**. **Automatique** est le choix par defaut : les demandes sont executees avec les outils ReShade sans autre validation. **A la demande** affiche une proposition dans le tchat avant une modification du rendu ou l'envoi de code shader ; ouvrez ses details, puis utilisez **Autoriser cette action** ou **Refuser cette action**. **Acces complet aux outils ReShade** permet plusieurs operations consecutives sans validation intermediaire.

Ce choix est memorise pour l'installation du jeu. Changer de mode annule une demande en cours. Les modes couvrent les outils de cet add-on ; ils ne modifient pas les autorisations de l'application Codex. Les questions pour preciser un effet ambigu restent possibles dans tous les modes.

## Utilisation avancée en ligne de commande

# Premier essai

## Installer l'add-on

1. Utiliser un jeu Windows 64 bits avec ReShade 6.8 et support complet des add-ons. Le prototype est compilé contre API 20 et le pont ImGui 1.92.5 ; une autre version doit être vérifiée.
2. Copier `CyRSAssistant.addon64` du paquet à côté de la DLL ReShade, ou dans le dossier d'add-ons configuré dans ReShade.
3. Lancer le jeu et ouvrir le panneau **CyRSAssistant** dans l'overlay ReShade.
4. Cliquer **Scanner les effets**. Vérifier techniques, valeurs et infobulles. Les champs numériques se valident avec Entrée. Un paramètre piloté par le runtime est affiché en lecture seule.
5. Tester un petit réglage, puis **Annuler la derniere modification**. **Enregistrer le preset** écrit explicitement le preset actif.

Ne pas confondre le scan avec un rechargement : le bouton réénumère les effets chargés. Après ajout d'un fichier FX, utiliser aussi le bouton de rechargement de ReShade pour le compiler. Le mode performance de ReShade peut supprimer les paramètres réglables.

## Compagnon local et catalogue

Le mode `watch` ci-dessous est un mode manuel historique. Ne le lancez pas en même temps que le service intégré ; utilisez **Connecter** dans ReShade pour le parcours normal.

Depuis le dossier contenant le paquet `companion/`, avec Python 3.11 ou ultérieur :

```powershell
python -m companion discover
python -m companion state
python -m companion scan
python -m companion watch
```

La détection automatique exige un seul processus de jeu. Si plusieurs add-ons tournent, utiliser le pipe affiché dans ReShade :

```powershell
python -m companion --pipe '\\.\pipe\CyRSAssistant-12345' --runtime 1 state
```

Remplacer `12345` par le PID réel. Les options globales `--pipe` et `--runtime` se placent avant la sous-commande. Si plusieurs runtimes sont présents, le compagnon demande de choisir explicitement leur identifiant.

Le scan écrit `CyRSAssistant/library/catalog.json` sous le chemin de base ReShade. Il observe les dossiers `EffectSearchPaths` et `TextureSearchPaths` ; le suffixe `/**` active la récursion. Les fichiers supérieurs à 32 Mio sont signalés comme erreurs de scan. Les doublons de noms d'effets restent ambigus au lieu d'être associés arbitrairement au runtime.

`watch` suit les demandes du panneau et rescane après un changement de génération ou un clic sur **Scan effects**. Il ne surveille pas encore continuellement le système de fichiers. Arrêt : Ctrl+C.

## Connecter une API et demander un rendu

Dans le terminal qui lancera le compagnon, configurer :

```powershell
$env:CYRS_API_URL = 'https://VOTRE-SERVEUR/v1/chat/completions'
$env:CYRS_MODEL = 'IDENTIFIANT-DU-MODELE'
# Fournir CYRS_API_KEY dans l'environnement si le serveur l'exige.
python -m companion watch
```

L'URL doit être complète. HTTPS est requis, sauf pour un serveur local sur localhost/127.0.0.1/::1. Le serveur doit accepter `messages` et `response_format: {"type":"json_object"}` et renvoyer une réponse Chat Completions complète. Aucun modèle ni fournisseur n'est présélectionné.

Dans ReShade, saisir une demande puis **Send and apply**. Le modèle reçoit la demande et les métadonnées des effets chargés, sans capture ni chemin absolu du jeu. Le compagnon valide sa réponse ; l'add-on revalide l'état courant avant application. Si les réglages changent pendant la génération, la commande est refusée et une nouvelle demande est nécessaire. **Cancel request** empêche l'application d'une réponse encore en attente, mais n'annule pas un réglage déjà appliqué.

En ligne de commande :

```powershell
python -m companion ask 'Un rendu légèrement plus froid, sans trop assombrir'
python -m companion ask 'Réduire la saturation' --dry-run > plan.json
python -m companion apply plan.json
python -m companion undo
python -m companion save
```

`ask` applique les changements par défaut. `--dry-run` produit un plan sans toucher au rendu. Le plan garde les versions de l'état d'origine ; `apply` refuse un plan obsolète. La validation structurelle suit le [contrat JSON de Chat Completions](https://developers.openai.com/api/docs/guides/structured-outputs) et reste assurée localement même si le modèle produit du JSON valide.

## Mémoire transférable

```powershell
python -m companion describe Tonemap.fx
python -m companion export catalogue-portable.json
# Dans le contexte d'un autre jeu :
python -m companion import catalogue-portable.json
```

`describe` envoie le début du source FX (maximum 60 000 caractères) et ses métadonnées au fournisseur configuré. La description conserve modèle, date, empreinte et statut « non vérifiée visuellement ». Elle est réutilisée dans les prochaines demandes si ses entrées correspondent toujours.

Le cache utilise une invalidation volontairement conservatrice : toute modification d'un fichier scanné invalide les descriptions du catalogue. Ce n'est pas encore une analyse précise des dépendances par compilation. Pour réutiliser les descriptions entre jeux, conserver les mêmes fichiers et leur organisation relative dans les dossiers de recherche, dans le même ordre. Les données runtime et réglages restent propres au jeu.

L'export JSON transporte les métadonnées et descriptions ; il n'installe aucun shader et ne transporte aucune clé API. L'import remplit le cache puis rescane les fichiers réellement présents.

## Brancher un agent par MCP

Le serveur MCP fonctionne sur stdio et ne nécessite pas de clé API côté CyRSAssistant. Configurer un client acceptant des serveurs MCP locaux avec un lancement équivalent à :

```powershell
python -m companion.mcp --allow-write
```

Définir le dossier de travail sur le dossier qui contient `companion/`, ou utiliser le lanceur `run_mcp.py` du paquet :

```json
{
  "command": "python",
  "args": ["D:/CHEMIN/CyRSAssistant-0.6.0/run_mcp.py", "--allow-write"]
}
```

Ce fragment décrit la commande du serveur, pas le format complet de configuration propre à chaque client. Sans `--allow-write`, seuls `cyrs_list_sessions` et `cyrs_get_state` sont exposés. Avec l'option : `cyrs_apply_patch`, `cyrs_undo` et `cyrs_save_preset` sont ajoutés. Le serveur ne change pas de jeu après sa première connexion.

Le MCP est implémenté selon la [spécification stdio 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports), avec tests d'initialisation et d'outils. Les connexions réelles depuis Codex, Claude, Antigravity ou OpenCode ne sont pas encore validées. Le panneau de chat utilise le compagnon local et le fournisseur choisi ; le mode MCP se pilote depuis la conversation de l'agent externe.

## Validation et dépannage

Le binaire et les tests automatisés peuvent être vérifiés sans jeu. Le transport est testé avec un processus natif qui joue le rôle du runtime ; les réponses du fournisseur sont testées avec un serveur HTTP local simulé. Cela ne constitue pas un essai graphique en jeu ni un essai sur une API distante.

- Panneau absent : vérifier ReShade x64 avec add-ons, sa version et le journal `ReShade.log`.
- Paramètres absents : vérifier la compilation des effets et désactiver le mode performance pour les réglages interactifs.
- Pipe absent : vérifier que le jeu tourne et que l'add-on est chargé sous le même utilisateur Windows.
- Timeout : remettre le jeu en activité, puis relire l'état. Une fenêtre minimisée peut ne plus présenter d'images.
- Erreur fournisseur : vérifier URL complète, modèle, clé et prise en charge du mode JSON.
- Scan non inscriptible : donner au jeu/compagnon un dossier de base ReShade accessible en écriture.

Checklist du premier essai graphique : scan → petit changement → annulation → demande IA → rechargement des effets → rejet d'un ancien plan → sauvegarde volontaire. Vérifier aussi le comportement lors d'un changement de preset et de la fermeture du jeu.

## Générer un effet ou remplacer un shader

Dans **Tchat**, demandez un nouvel effet ou le remplacement d'un effet existant. L'assistant peut lire les noms, techniques, parametres (valeurs et bornes) et sources FX avec ses outils. Pour une cible ambigue, il demande quel effet remplacer. Pour une question de capacite, il propose l'operation et attend votre reponse. Le nouvel effet porte un nom descriptif `CyRS_<nom>_<empreinte>.fx` et peut exposer jusqu'a 16 controles float en plus du melange global. Les controles utiles d'un bloom peuvent inclure seuil, puissance, longueur et transition. Les sources restent limitees a une passe avec echantillonnage ecran et taps deroules.

Un remplacement FX conserve le fichier d'origine : le nouvel effet est compile et initialise, puis les techniques de l'ancien effet sont desactivees. **Restaurer l'effet remplace** dans **Effets**, ou une demande dans le tchat, restaure leurs etats precedents. La restauration concerne le dernier remplacement et reste en memoire. Les positions dans l'ordre des techniques ne sont pas garanties identiques. Une compilation reussie ne garantit pas la qualite visuelle du resultat.


Pour le jeu lui-même, ouvrez **Shaders** puis **Actualiser les shaders du jeu**. La liste est triée par nombre d’utilisations. Sélectionnez une empreinte et utilisez **Inspecter le shader selectionne** pour les signatures, déclarations de ressources et le désassemblage. Décrivez le changement à apporter puis envoyez. Le fournisseur génère du HLSL compilé avec le profil original (`ps_5_0` ou `ps_6_x`), validé avant activation au prochain bind. **Restaurer le shader selectionne** et **Restaurer tous les shaders originaux** désactivent les remplacements.

L’identification de la fonction visuelle d’un shader reste manuelle : un compteur élevé ne signifie pas qu’il dessine le HUD. Les ressources et entrées utilisées doivent respecter le contrat original ; si les métadonnées ont été retirées, les déclarations DXBC servent à contrôler registres et tailles. Le shader original n’est jamais réécrit. Au maximum 64 versions GPU en DX11 ou 256 PSO en DX12 sont conservés par périphérique jusqu’à la fermeture, afin de ne pas libérer un shader encore référencé.

Les sources proposées par le service sont archivées dans `CyRSAssistant/replacements/<empreinte originale>/`. Les fichiers de remplacement sont spécifiques au shader exact et ne sont pas réactivés automatiquement au redémarrage. Un agent MCP peut relire le HLSL et appeler `cyrs_replace_game_shader` avec l’empreinte présente dans la nouvelle session. La présence de la même empreinte ne garantit pas que l’effet visuel soit souhaitable dans un autre contexte.

### Différences DX12

La liste affiche DXBC/DXIL et le nombre de PSO reconstructibles. Les root signatures et les ressources sont conservées ; les espaces de registres DXIL sont vérifiés. Les pipelines avec des sous-objets inconnus, mesh/raytracing ou un budget de capture dépassé sont signalés et refusés. Shader Model 5.1 DXBC n’est pas encore accepté.

Une commande DX12 déjà enregistrée garde ses références aux anciens PSO. Restaurer un shader affecte les prochains binds enregistrés par le jeu ; cela ne réécrit pas ses command lists déjà enregistrées.
