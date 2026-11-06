---
id: architecture
title: Fonctionnement de l’assistant
description: Comprenez comment ReShade, le compagnon et un fournisseur traitent une demande.
section: Guides
order: 120
sourceRevision: 3
parent: protocol
---

## Parcours d’une demande {#design-1}

CyRSAssistant relie le panneau ReShade à un compagnon local et au fournisseur choisi. Ouvrez Tchat pour discuter ; utilisez Effets ou Shaders pour inspecter le résultat réel.

```diagram
{"type":"flow","title":"De votre demande au résultat affiché","nodes":[{"id":"chat","label":"Votre message dans ReShade","x":20,"y":20,"width":570},{"id":"service","label":"Compagnon local et fournisseur choisi","x":20,"y":120,"width":570},{"id":"tools","label":"Lecture des effets et proposition d’une action","x":20,"y":220,"width":570},{"id":"runtime","label":"ReShade vérifie et applique l’action","x":20,"y":320,"width":570},{"id":"review","label":"Observer, ajuster ou restaurer","x":20,"y":420,"width":570}],"edges":[{"from":"chat","to":"service"},{"from":"service","to":"tools"},{"from":"tools","to":"runtime"},{"from":"runtime","to":"review"}]}
```

## Choisir la bonne cible {#design-2}

Un preset enregistre des réglages d’effets. Un FX ReShade ajoute un post-traitement. Un pixel shader natif appartient au rendu du jeu. Précisez ce que vous voulez modifier et identifiez l’effet ou le shader existant pour un remplacement.

## Répartition des composants {#design-3}

L’add-on C++ fonctionne dans ReShade. Le compagnon traite les demandes au fournisseur en dehors du thread de rendu. La documentation s’ouvre séparément dans le navigateur par défaut et ne demande aucune connexion à un fournisseur.

## L’add-on ReShade {#design-4}

Le panneau lit les techniques et paramètres chargés, accepte des modifications bornées, crée des FX et gère les remplacements de pixel shaders capturés. Les callbacks ReShade appliquent les commandes. Un rechargement invalide les anciens identifiants ; une demande périmée peut être refusée pour éviter de toucher une autre cible.

## Le compagnon local {#design-5}

Connecter lance le compagnon. La reconnaissance d’une session CLI et la réponse effective d’un modèle sont deux états distincts. Si le service ne répond plus, déconnectez puis reconnectez-le dans Connexion. Le compagnon ne donne pas au modèle un terminal ni un accès illimité aux fichiers.

## Les fichiers du catalogue {#design-6}

Le catalogue facultatif en ligne de commande se trouve dans CyRSAssistant/library. Il conserve les métadonnées scannées et les descriptions demandées explicitement. Gardez ce dossier lors des mises à jour. Les exports portables contiennent descriptions et métadonnées ; les shaders doivent être installés séparément.

## Les outils de l’assistant {#design-7}

Le tchat peut lire les noms et valeurs, inspecter une source FX ou un désassemblage autorisé, appliquer des réglages, générer un FX et demander un remplacement natif. Le mode d’autorisation règle les validations et le nombre d’opérations. Les clients MCP externes ont leur propre conversation et une activation d’écriture séparée.

## Appliquer, observer et restaurer {#design-8}

1. Décrivez un changement limité et reconnaissable.
2. Laissez l’assistant examiner les réglages actuels.
3. Observez la scène après application.
4. Affinez la demande, annulez la modification suivie ou restaurez un remplacement.
5. Enregistrez explicitement le preset lorsque le résultat vous convient.

## Installer les packs vous-même {#design-9}

L’add-on ne télécharge pas de packs sur le web. Installez leurs fichiers dans un dossier de shaders configuré pour ReShade, puis utilisez Charger / recharger les effets. Scanner les effets actualise les contrôles chargés ; cette action n’installe pas les fichiers absents.

## Les contrats des shaders natifs {#design-10}

Une empreinte identifie du bytecode, pas son rôle visuel. Le remplacement préserve les signatures, liaisons de ressources et contrats de pipeline pris en charge. Seuls les pixel shaders DX11/DX12 capturés sont concernés. Un shader partagé peut affecter plusieurs objets.

## Lire l’état actuel {#design-11}

L’état de connexion décrit l’accès au fournisseur. Celui d’un effet généré décrit sa compilation et son activation. Les erreurs de shaders natifs expliquent les limites de capture ou de remplacement. Une compilation réussie ne prouve pas que le résultat visuel convient.

## Pour poursuivre {#design-12}

- [Régler un effet existant](doc:effects)
- [Générer un FX](doc:create)
- [Remplacer un shader du jeu](doc:native-shaders)
- [API du pont local](doc:protocol)
