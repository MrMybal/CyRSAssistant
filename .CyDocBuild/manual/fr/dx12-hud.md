---
id: dx12-hud
title: DX12, restauration et limites du HUD
description: Comprenez les pipelines DX12, la restauration et les limites du retrait du HUD.
section: Guides
order: 10
sourceRevision: 3
parent: native-shaders
---

## Vue d’ensemble {#overview}

En DX12, les PSO graphiques compatibles sont reconstruits avec le nouveau pixel shader, en conservant les autres stages, états et la root signature. Tous les PSO requis doivent réussir avant activation. Un nouveau PSO incompatible désactive le remplacement avec une erreur.

DXIL utilise Microsoft DXC et son validateur fournis. Espaces de registres, signatures et ressources sont contrôlés. La compilation ne garantit pas qu’une IA reconstruise fidèlement un shader complexe du jeu.

1. Utilisez Restaurer le shader sélectionné, ou Restaurer tous les shaders originaux du périphérique.
2. La restauration s’applique aux prochains binds. Les command lists déjà enregistrées peuvent encore référencer l’ancien pipeline.
3. Lisez limitations/erreurs et ReShade Log. Gardez l’original en cas d’incertitude.

```diagram
{"type": "flow", "title": "Pourquoi un filtre final ne suffit pas pour le HUD", "nodes": [{"id": "node-0", "label": "Le jeu dessine la scène", "x": 20, "y": 20, "width": 570}, {"id": "node-1", "label": "Le HUD peut être composé dans la même image", "x": 20, "y": 120, "width": 570}, {"id": "node-2", "label": "ReShade reçoit les pixels obtenus", "x": 20, "y": 220, "width": 570}, {"id": "node-3", "label": "Une étape de rendu antérieure peut être nécessaire", "x": 20, "y": 320, "width": 570}], "edges": [{"from": "node-0", "to": "node-1"}, {"from": "node-1", "to": "node-2"}, {"from": "node-2", "to": "node-3"}]}
```

```callout
{"type": "info", "title": "Note", "body": "Il n’existe ni identification automatique du HUD ni suppression universelle. Un FX ne retrouve pas les pixels cachés en effaçant un HUD composé. CyGameCapture et CyGPUInspector ne sont pas livrés. Le remplacement natif ne couvre pas Vulkan, les stages de sommets ou les pipelines mesh/raytracing."}
```

## À lire aussi {#related}

- [Inspecter et remplacer les shaders du jeu](doc:native-shaders)
- [Capture et retour visuel](doc:capture)
- [Limites et référence technique](doc:reference)
