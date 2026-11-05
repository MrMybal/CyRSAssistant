---
id: localization
title: Ajouter une langue
description: Ajouter une langue
section: Référence développeur
order: 130
sourceRevision: 1
---

# Traduire le panneau et le compagnon {#overlay-localization}

Les catalogues UTF-8 `companion/locales/en.json` et `fr.json` sont partagés par le C++ et Python. L’anglais est le défaut/repli ; ses clés sont les textes anglais et ses valeurs identiques.

1. Copiez en.json vers, par exemple, de.json.
2. Définissez code selon le nom de fichier et name selon le nom de la langue.
3. Traduisez les valeurs de messages sans changer les clés. Une clé absente se replie sur l’anglais ; supprimez une traduction inachevée plutôt que de laisser une valeur vide.
4. Gardez les paramètres nommés `{file}` et printf `%s`/`%zu`/`%llu`. Les paramètres nommés peuvent être réordonnés, pas l’ordre/type printf. N’ajoutez ni `###` ni NUL.
5. Lancez les tests Python, puis reconstruisez add-on et compagnon avec tools/build.py et tools/build_service.py avant le paquet.

Le sélecteur découvre les métadonnées au build ; aucune énumération C++ ni branche de fournisseur Python n’est nécessaire. CMake génère la table native et PyInstaller embarque les JSON : remplacez les deux binaires ensemble.

Pour un message neuf, ajoutez sa clé/valeur anglaise et ses traductions, utilisez tr/ui_label et privilégiez des phrases complètes avec paramètres nommés. Les identifiants de widgets `###` restent stables pendant un changement de langue.

`[CYRSASSISTANT] Language=en` est le défaut dans ReShade.ini ; fr sélectionne le français. Un code inconnu se replie sur en ; fr-FR reconnu résout fr. Les états/connexions exposent language ; set_language est un contrôle local persistant, pas un outil IA.

Python fixe la langue par ContextVar, y compris dans les workers. Changer de langue ne vide pas le tchat, ne modifie pas les shaders, ne redémarre pas le fournisseur, n’annule pas une autorisation et ne change pas le rendu. Messages existants et réponses en cours gardent leur langue ; les nouvelles demandes utilisent le choix courant, sauf demande explicite différente.

Noms/descriptions des shaders, désassemblage et diagnostics externes ne sont pas traduits. Anglais/français utilisent les glyphes latins ReShade ; d’autres écritures exigent de vérifier glyphes, shaping et disposition.

## Traductions CyDoc {#manual-localization}

Le manuel est dans docs/content/en et docs/content/fr. Conservez les mêmes IDs de pages, ancres explicites et médias. L’anglais déclare revision ; sa traduction déclare sourceRevision correspondant, après vérification du sens.

Ajoutez une langue à cydoc.config.json et aux catalogues du panneau, créez son dossier, puis lancez `npm run docs:check`. CyDoc se replie sur l’anglais en cas de contenu absent. Le build du produit refuse les traductions de prose absentes, dépassées ou non suivies ; build/help/translation-report.json enregistre ce contrôle. Les pages source sont générées dans les deux langues et exclues du suivi de prose.

CyDoc 0.1.0 traduit son interface en anglais/français, sans RTL. D’autres écritures demandent des essais de navigateur/police/disposition. L’URL d’aide suit la langue de l’application au lancement ; le lecteur peut ensuite changer de langue indépendamment et garder page, section et média.
