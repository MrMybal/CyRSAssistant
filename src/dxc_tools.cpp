#include "dxc_tools.hpp"
#include <windows.h>
#include <objbase.h>
#include <oaidl.h>
#include <dxcapi.h>
#include <d3d12shader.h>
#include <wrl/client.h>
#include <filesystem>

namespace cyrs::dxc_tools {
using Microsoft::WRL::ComPtr;
namespace {
int module_anchor;
DxcCreateInstanceProc factory() {
    static auto create = [] {
        HMODULE module = nullptr;
        require(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
            reinterpret_cast<LPCWSTR>(&module_anchor), &module) != 0, "Cannot locate add-on module");
        wchar_t path[32768]{}; GetModuleFileNameW(module, path, 32768);
        auto directory = std::filesystem::path(path).parent_path() / L"CyRSAssistantRuntime";
        const auto flags = LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_DEFAULT_DIRS;
        require(LoadLibraryExW((directory / L"dxil.dll").c_str(), nullptr, flags) != nullptr, "Missing CyRSAssistantRuntime/dxil.dll; install the complete package");
        const auto library = LoadLibraryExW((directory / L"dxcompiler.dll").c_str(), nullptr, flags);
        require(library != nullptr, "Missing CyRSAssistantRuntime/dxcompiler.dll; install the complete package");
        auto proc = reinterpret_cast<DxcCreateInstanceProc>(GetProcAddress(library, "DxcCreateInstance"));
        require(proc != nullptr, "DXC runtime does not export DxcCreateInstance");
        return proc;
    }();
    return create;
}
template<class T> ComPtr<T> instance(REFCLSID clsid) {
    ComPtr<T> result;
    require(SUCCEEDED(factory()(clsid, IID_PPV_ARGS(&result))), "Cannot create DXC component"); return result;
}
ComPtr<ID3D12ShaderReflection> reflection(const std::vector<uint8_t> &code) {
    auto utils = instance<IDxcUtils>(CLSID_DxcUtils);
    ComPtr<IDxcBlobEncoding> blob;
    require(SUCCEEDED(utils->CreateBlob(code.data(), static_cast<UINT32>(code.size()), DXC_CP_ACP, &blob)), "DXC cannot read shader bytes");
    auto container = instance<IDxcContainerReflection>(CLSID_DxcContainerReflection);
    require(SUCCEEDED(container->Load(blob.Get())), "DXC cannot load shader container");
    UINT32 part = 0;
    require(SUCCEEDED(container->FindFirstPartKind(DXC_PART_DXIL, &part)), "Missing DXIL part");
    ComPtr<ID3D12ShaderReflection> result;
    require(SUCCEEDED(container->GetPartReflection(part, IID_PPV_ARGS(&result))), "DXIL reflection is unavailable; replacement refused");
    return result;
}
}
std::vector<uint8_t> compile(const std::string &source, const std::string &profile) {
    require(profile.size() == 6 && (profile.rfind("ps_6_", 0) == 0 || profile.rfind("vs_6_", 0) == 0) && profile[5] >= '0' && profile[5] <= '9', "Unsupported DXIL shader profile");
    auto compiler = instance<IDxcCompiler3>(CLSID_DxcCompiler);
    std::wstring target(profile.begin(), profile.end());
    const wchar_t *arguments[] = {L"-E", L"main", L"-T", target.c_str(), L"-Ges", L"-O1"};
    DxcBuffer input{source.data(), source.size(), DXC_CP_UTF8};
    ComPtr<IDxcResult> result;
    require(SUCCEEDED(compiler->Compile(&input, arguments, static_cast<UINT32>(std::size(arguments)), nullptr, IID_PPV_ARGS(&result))), "DXC compile invocation failed");
    HRESULT status = E_FAIL; result->GetStatus(&status);
    if (FAILED(status)) {
        ComPtr<IDxcBlobUtf8> errors;
        result->GetOutput(DXC_OUT_ERRORS, IID_PPV_ARGS(&errors), nullptr);
        throw std::runtime_error(errors ? std::string(errors->GetStringPointer(), errors->GetStringLength()).substr(0, 16000) : "DXIL compilation failed");
    }
    ComPtr<IDxcBlob> object;
    require(SUCCEEDED(result->GetOutput(DXC_OUT_OBJECT, IID_PPV_ARGS(&object), nullptr)) && object, "No DXIL object produced");
    const auto *bytes = static_cast<const uint8_t *>(object->GetBufferPointer());
    return {bytes, bytes + object->GetBufferSize()};
}
json reflect(const std::vector<uint8_t> &code) {
    auto r = reflection(code);
    D3D12_SHADER_DESC desc{};
    require(SUCCEEDED(r->GetDesc(&desc)), "Cannot reflect DXIL shader");
    require(((desc.Version >> 16) & 0xffff) == 0, "Only DXIL pixel shaders are supported");
    json result = {{"encoding", "DXIL"}, {"profile", "ps_" + std::to_string((desc.Version >> 4) & 15) + "_" + std::to_string(desc.Version & 15)},
        {"metadata_present", true}, {"binding_declarations", json::array()}, {"inputs", json::array()}, {"outputs", json::array()},
        {"resources", json::array()}, {"buffers", json::array()}, {"instructions", desc.InstructionCount}};
    for (int output = 0; output < 2; ++output) for (UINT i = 0; i < (output ? desc.OutputParameters : desc.InputParameters); ++i) {
        D3D12_SIGNATURE_PARAMETER_DESC p{};
        require(SUCCEEDED(output ? r->GetOutputParameterDesc(i, &p) : r->GetInputParameterDesc(i, &p)), "Cannot reflect DXIL signature");
        result[output ? "outputs" : "inputs"].push_back({{"semantic", p.SemanticName}, {"index", p.SemanticIndex}, {"register", p.Register},
            {"system", p.SystemValueType}, {"type", p.ComponentType}, {"mask", p.Mask}, {"stream", p.Stream}, {"precision", p.MinPrecision}});
    }
    for (UINT i = 0; i < desc.BoundResources; ++i) {
        D3D12_SHADER_INPUT_BIND_DESC p{};
        require(SUCCEEDED(r->GetResourceBindingDesc(i, &p)), "Cannot reflect DXIL resource");
        result["resources"].push_back({{"name", p.Name}, {"type", p.Type}, {"slot", p.BindPoint}, {"space", p.Space}, {"count", p.BindCount}, {"dimension", p.Dimension}, {"return_type", p.ReturnType}});
    }
    for (UINT i = 0; i < desc.ConstantBuffers; ++i) {
        auto buffer = r->GetConstantBufferByIndex(i); D3D12_SHADER_BUFFER_DESC b{};
        require(SUCCEEDED(buffer->GetDesc(&b)), "Missing DXIL constant buffer metadata");
        json variables = json::array();
        for (UINT j = 0; j < b.Variables; ++j) {
            D3D12_SHADER_VARIABLE_DESC v{};
            require(SUCCEEDED(buffer->GetVariableByIndex(j)->GetDesc(&v)), "Missing DXIL variable metadata");
            variables.push_back({{"name", v.Name}, {"offset", v.StartOffset}, {"size", v.Size}});
        }
        result["buffers"].push_back({{"name", b.Name}, {"size", b.Size}, {"variables", variables}});
    }
    return result;
}
std::string disassemble(const std::vector<uint8_t> &code) {
    auto compiler = instance<IDxcCompiler3>(CLSID_DxcCompiler);
    DxcBuffer input{code.data(), code.size(), 0};
    ComPtr<IDxcResult> result;
    require(SUCCEEDED(compiler->Disassemble(&input, IID_PPV_ARGS(&result))), "DXIL disassembly unavailable");
    ComPtr<IDxcBlobUtf8> text;
    require(SUCCEEDED(result->GetOutput(DXC_OUT_DISASSEMBLY, IID_PPV_ARGS(&text), nullptr)) && text, "No DXIL disassembly returned");
    require(text->GetStringLength() <= 256 * 1024, "Shader too large for AI inspection");
    return {text->GetStringPointer(), text->GetStringLength()};
}
}
