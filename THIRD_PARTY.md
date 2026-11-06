# Third-party components

The complete license texts are in `LICENCES/` at the root of both ZIP distributions. See [SOURCES.txt](LICENCES/SOURCES.txt) for upstream sources and [AssistantRuntime-Notices.txt](LICENCES/AssistantRuntime-Notices.txt) for the frozen companion's components.

| Component | Use | Included notice |
| --- | --- | --- |
| CyDoc 0.1.0 (pinned source archive) | Local documentation reader and image module | LICENCES/CyDoc.txt |
| ReShade 6.8.0 | Add-on API and ImGui bridge | LICENCES/ReShade.txt |
| Dear ImGui 1.92.5-docking | Overlay interface | LICENCES/DearImGui.txt |
| nlohmann/json 3.12.0 | JSON protocol | LICENCES/nlohmann-json.txt |
| Microsoft DXC 1.8.2505.32 | DXIL compilation and validation | LICENCES/DXC-LLVM.txt, LICENCES/DXC-Microsoft.txt |
| Python 3.11.5 and its bundled libraries | Standalone companion | LICENCES/Python.txt, LICENCES/AssistantRuntime-Notices.txt |
| PyInstaller 6.20.0 | Companion bootloader and runtime hooks | LICENCES/PyInstaller.txt |

CyRSAssistant remains GPL-3.0-only. Third-party components retain their own licenses. Native dependency downloads are pinned in the bootstrap scripts and `tools/dependencies.lock.json`. The frozen Python runtime and additional upstream notices are pinned in `tools/runtime-licenses.lock.json`.

CyToolsCore and CyUEMCPSDK are not included or required by this ReShade add-on. The companion, transport and MCP interface are implemented by CyRSAssistant. The Cy SDKs' MIT licensing does not change this product's license.

The DXC notices also remain alongside its DLLs in `CyRSAssistantRuntime/`. In the install ZIP, this document and the original product `LICENSE` are in `CyRSAssistant/`; their central notices folder is `../LICENCES/`.

CyDoc is pinned by commit and package SHA-256 in .CyDocBuild/cydoc.lock.json. Its MIT notice is also included in the complete offline export. Node.js, marked, PrismJS and esbuild are generation dependencies, not installed application runtimes. Only the image module is shipped; no Three.js runtime is included.
