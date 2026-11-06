---
id: troubleshooting
title: Dépannage
description: Résolvez les problèmes de connexion, compilation, paramètres et documentation.
section: Guides
order: 16
sourceRevision: 3
parent: update
---

## Vue d’ensemble {#overview}

| Symptôme | Vérifications et reprise |
| --- | --- |
| Add-on absent | Vérifiez Windows x64, le support complet des add-ons, le dossier du véritable exécutable et ReShade Add-ons / Log. |
| Envoyer désactivé | Connectez un fournisseur, saisissez un texte non vide, attendez la demande active ou annulez-la. |
| CLI prêt, aucune réponse du modèle | Le premier message vérifie l’accès au modèle. Vérifiez session, modèle, quota et disponibilité hors du jeu. |
| Échec de connexion API | Vérifiez URL /chat/completions complète, modèle, JSON, clé et serveur. HTTP distant est refusé. |
| Service local injoignable | Déconnectez/reconnectez. Vérifiez CyRSAssistantCompanion.exe à côté de l’add-on. L’absence de signal est rapportée après dix secondes. |
| Aucune valeur modifiable | Rechargez, inspectez les erreurs et le mode performance. Le tchat reste utilisable. |
| Source FX ambiguë | Corrigez les noms en doublon dans les racines qui se recouvrent, ou identifiez un FX chargé unique. |
| Échec d’effet généré | Lisez l’état final et Log. Corrigez l’erreur précise ou demandez un effet plus simple pris en charge. |
| Ancien bloom toujours actif | Vérifiez ajout ou remplacement, cible exacte et activations des techniques. |
| Empreinte introuvable | Affichez la scène après démarrage et actualisez. Une mise à jour du jeu peut changer bytecode/empreintes. |
| Remplacement DX12 refusé | Lisez les erreurs de contrat/pipeline. Vérifiez le runtime DXC complet. Gardez l’original. |
| Demande expirée | Relisez l’état avant de réessayer : une action peut avoir commencé. Laissez le jeu produire des images. |
| Manuel HTML absent | Réextrayez CyRSAssistant/Documentation. Aide signale le dossier absent ; réextrayez le ZIP complet. |

1. Notez l’état visible, l’action, le fichier FX/empreinte exact et l’API graphique.
2. Essayez une reprise limitée : reconnexion, actualisation ou restauration ; ne renvoyez pas aveuglément des modifications.
3. Recueillez uniquement les lignes Log/compilateur utiles et les étapes de reproduction. Retirez chemins personnels, identifiants et échanges privés avant partage.

## À lire aussi {#related}

- [Connecter un fournisseur](doc:connect)
- [Inspecter et régler les effets installés](doc:effects)
- [Inspecter et remplacer les shaders du jeu](doc:native-shaders)
- [Limites et référence technique](doc:reference)
