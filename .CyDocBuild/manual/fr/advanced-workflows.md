---
id: advanced-workflows
title: Parcours avancés : CLI, catalogue et shaders
description: Utilisez le catalogue, l’API en ligne de commande et les clients externes.
section: Guides
order: 110
sourceRevision: 3
parent: cli
---

Ce guide conserve les exemples détaillés du premier guide français, actualisés pour les commandes disponibles. Les étapes de validation décrivent les vérifications à mener, et non une promesse de résultat visuel.

## Utilisation avancée en ligne de commande {#advanced-1}

Utilisez ces commandes pour piloter explicitement un catalogue, une requête API ou un client externe. Le tchat normal s’utilise directement dans le panneau ReShade.

## Premier réglage {#advanced-2}

Commencez par une modification limitée, puis vérifiez son effet avant d’ajouter une autre opération.

## Installer l'add-on {#advanced-3}

1. Utiliser un jeu Windows 64 bits avec ReShade 6.8 et support complet des add-ons. Le prototype est compilé contre API 20 et le pont ImGui 1.92.5 ; une autre version doit être vérifiée.
2. Copier `CyRSAssistant.addon64` du paquet à côté de la DLL ReShade, ou dans le dossier d'add-ons configuré dans ReShade.
3. Lancer le jeu et ouvrir le panneau **CyRSAssistant** dans l'overlay ReShade.
4. Cliquer **Scanner les effets**. Vérifier techniques, valeurs et infobulles. Les champs numériques se valident avec Entrée. Un paramètre piloté par le runtime est affiché en lecture seule.
5. Tester un petit réglage, puis **Annuler la derniere modification**. **Enregistrer le preset** écrit explicitement le preset actif.

Ne pas confondre le scan avec un rechargement : le bouton réénumère les effets chargés. Après ajout d'un fichier FX, utiliser aussi le bouton de rechargement de ReShade pour le compiler. Le mode performance de ReShade peut supprimer les paramètres réglables.

## Compagnon local et catalogue {#advanced-4}

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

## Connecter une API et demander un rendu {#advanced-5}

Dans le terminal qui lancera le compagnon, configurer :

```powershell
$env:CYRS_API_URL = 'https://VOTRE-SERVEUR/v1/chat/completions'
$env:CYRS_MODEL = 'IDENTIFIANT-DU-MODELE'
# Fournir CYRS_API_KEY dans l'environnement si le serveur l'exige.
python -m companion watch
```

L'URL doit être complète. HTTPS est requis, sauf pour un serveur local sur localhost/127.0.0.1/::1. Le serveur doit accepter `messages` et `response_format: {"type":"json_object"}` et renvoyer une réponse Chat Completions complète. En CLI, fournissez explicitement le modèle et le serveur ; ce chemin ne réutilise pas la connexion du panneau.

Dans ReShade, saisir une demande puis **Envoyer**. Le modèle reçoit la demande et les métadonnées pertinentes ; la lecture de sources ou de désassemblage peut transmettre du contenu selon le mode d’autorisation. Le tchat intégré ne transmet pas automatiquement une capture. Le compagnon valide sa réponse ; l'add-on revalide l'état courant avant application. Si les réglages changent pendant la génération, la commande est refusée et une nouvelle demande est nécessaire. **Annuler la demande** empêche l'application d'une réponse encore en attente, mais n'annule pas un réglage déjà appliqué.

En ligne de commande :

```powershell
python -m companion ask 'Un rendu légèrement plus froid, sans trop assombrir'
python -m companion ask 'Réduire la saturation' --dry-run > plan.json
python -m companion apply plan.json
python -m companion undo
python -m companion save
```

`ask` applique les changements par défaut. `--dry-run` produit un plan sans toucher au rendu. Le plan garde les versions de l'état d'origine ; `apply` refuse un plan obsolète. La validation structurelle suit le [contrat JSON de Chat Completions](https://developers.openai.com/api/docs/guides/structured-outputs) et reste assurée localement même si le modèle produit du JSON valide.

## Mémoire transférable {#advanced-7}

```powershell
python -m companion describe Tonemap.fx
python -m companion export catalogue-portable.json
# Dans le contexte d'un autre jeu :
python -m companion import catalogue-portable.json
```

`describe` envoie le début du source FX (maximum 60 000 caractères) et ses métadonnées au fournisseur configuré. La description conserve modèle, date, empreinte et statut « non vérifiée visuellement ». Elle est réutilisée dans les prochaines demandes si ses entrées correspondent toujours.

Le cache utilise une invalidation volontairement conservatrice : toute modification d'un fichier scanné invalide les descriptions du catalogue. Ce n'est pas encore une analyse précise des dépendances par compilation. Pour réutiliser les descriptions entre jeux, conserver les mêmes fichiers et leur organisation relative dans les dossiers de recherche, dans le même ordre. Les données runtime et réglages restent propres au jeu.

L'export JSON transporte les métadonnées et descriptions ; il n'installe aucun shader et ne transporte aucune clé API. L'import remplit le cache puis rescane les fichiers réellement présents.

## Brancher un agent par MCP {#advanced-9}

Le serveur MCP fonctionne sur stdio et ne nécessite pas de clé API côté CyRSAssistant. Configurer un client acceptant des serveurs MCP locaux avec un lancement équivalent à :

```powershell
python -m companion.mcp --allow-write
```

Définir le dossier de travail sur le dossier qui contient `companion/`, ou utiliser le lanceur `run_mcp.py` du paquet :

```json
{
  "command": "python",
  "args": ["D:/CHEMIN/CyRSAssistant-<version>/run_mcp.py", "--allow-write"]
}
```

Ce fragment décrit la commande du serveur, pas le format complet de configuration propre à chaque client. Sans `--allow-write`, les outils de lecture incluent sessions, état, capture et inspection native. L’option ajoute les mutations FX, shaders, patchs, rechargement et sauvegarde ; voir [MCP](doc:mcp) et l’index du [serveur](doc:protocol#transport). Le serveur ne change pas de jeu après sa première connexion.

Le serveur utilise la [spécification MCP stdio 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports). Utilisez le format de configuration de votre client. La conversation reste dans le client externe ; elle n’est pas recopiée dans le panneau ReShade.

## Dépanner une commande {#advanced-10}

Si aucun canal n’est trouvé, laissez le jeu ouvert sous le même compte Windows. Après un délai dépassé, laissez le jeu afficher de nouvelles images et relisez son état avant de réessayer. Pour le fournisseur, vérifiez l’URL complète, le modèle et la clé requise. Le catalogue exige un dossier ReShade accessible en écriture.

## Générer un effet ou remplacer un shader {#advanced-11}

Dans **Tchat**, demandez un nouvel effet ou le remplacement d'un effet existant. L'assistant peut lire les noms, techniques, parametres (valeurs et bornes) et sources FX avec ses outils. Pour une cible ambigue, il demande quel effet remplacer. Pour une question de capacite, il propose l'operation et attend votre reponse. Le nom du nouvel effet comporte une empreinte ; le préfixe est produit par le générateur et peut exposer jusqu'a 16 controles float en plus du melange global. Les controles utiles d'un bloom peuvent inclure seuil, puissance, longueur et transition. Les sources restent limitees a une passe avec echantillonnage ecran et taps deroules.

Un remplacement FX conserve le fichier d'origine : le nouvel effet est compile et initialise, puis les techniques de l'ancien effet sont desactivees. **Restaurer l'effet remplace** dans **Effets**, ou une demande dans le tchat, restaure leurs etats precedents. La restauration concerne le dernier remplacement et reste en memoire. Les positions dans l'ordre des techniques ne sont pas garanties identiques. Une compilation reussie ne garantit pas la qualite visuelle du resultat.


Pour le jeu lui-même, ouvrez **Shaders** puis **Actualiser les shaders du jeu**. La liste est triée par nombre d’utilisations. Sélectionnez une empreinte et utilisez **Inspecter le shader selectionne** pour les signatures, déclarations de ressources et le désassemblage. Décrivez le changement à apporter puis envoyez. Le fournisseur génère du HLSL compilé avec le profil original (`ps_5_0` ou `ps_6_x`), validé avant activation au prochain bind. **Restaurer le shader selectionne** et **Restaurer tous les shaders originaux** désactivent les remplacements.

L’identification de la fonction visuelle d’un shader reste manuelle : un compteur élevé ne signifie pas qu’il dessine le HUD. Les ressources et entrées utilisées doivent respecter le contrat original ; si les métadonnées ont été retirées, les déclarations DXBC servent à contrôler registres et tailles. Le shader original n’est jamais réécrit. Au maximum 64 versions GPU en DX11 ou 256 PSO en DX12 sont conservés par périphérique jusqu’à la fermeture, afin de ne pas libérer un shader encore référencé.

Les sources proposées par le service sont archivées dans `CyRSAssistant/replacements/<empreinte originale>/`. Les fichiers de remplacement sont spécifiques au shader exact et ne sont pas réactivés automatiquement au redémarrage. Un agent MCP peut relire le HLSL et appeler `cyrs_replace_game_shader` avec l’empreinte présente dans la nouvelle session. La présence de la même empreinte ne garantit pas que l’effet visuel soit souhaitable dans un autre contexte.

### Différences DX12 {#advanced-12}

La liste affiche DXBC/DXIL et le nombre de PSO reconstructibles. Les root signatures et les ressources sont conservées ; les espaces de registres DXIL sont vérifiés. Les pipelines avec des sous-objets inconnus, mesh/raytracing ou un budget de capture dépassé sont signalés et refusés. Shader Model 5.1 DXBC n’est pas encore accepté.

Une commande DX12 déjà enregistrée garde ses références aux anciens PSO. Restaurer un shader affecte les prochains binds enregistrés par le jeu ; cela ne réécrit pas ses command lists déjà enregistrées.
