# Composants tiers

Les licences originales sont conservées dans le paquet distribué.

| Composant | Utilisation | Licence livrée |
| --- | --- | --- |
| ReShade 6.8.0 | API add-on et pont ImGui | licenses/ReShade.txt |
| Dear ImGui 1.92.5-docking | Interface | licenses/DearImGui.txt |
| nlohmann/json 3.12.0 | Protocole JSON | licenses/nlohmann-json.txt |
| Microsoft DirectX Shader Compiler 1.8.2505.32 | Compilation et validation DXIL | CyRSAssistantRuntime/LICENSE-LLVM.txt et LICENSE-MS.txt |
| Python 3.11 | Compagnon autonome | licenses/Python.txt |
| PyInstaller 6.20.0 | Lanceur du compagnon | licenses/PyInstaller.txt |

Les sources de CyRSAssistant sont sous GPL-3.0-only. Les composants tiers restent soumis à leurs propres licences. Les versions et empreintes de téléchargement des dépendances natives sont définies dans les scripts bootstrap et leur fichier de verrouillage.

## Documentation reader

CyDoc 0.1.0 is used to build the English and French documentation. Its MIT notice is in [LICENCES/CyDoc.txt](LICENCES/CyDoc.txt) and in the exported reader. The package is pinned by commit and SHA-256 in tools/cydoc.lock.json. Only the image module is included in the reader; Three.js is not required.
