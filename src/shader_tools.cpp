#include "shader_tools.hpp"
#include "dxc_tools.hpp"
#include <windows.h>
#include <d3dcompiler.h>
#include <d3d11shader.h>
#include <bcrypt.h>
#include <wrl/client.h>
#include <algorithm>
#include <regex>
#include <cstring>
#include <sstream>

namespace cyrs::shader_tools {
using Microsoft::WRL::ComPtr;
bool is_dxil(const std::vector<uint8_t> &code) {
    if (code.size() < 32 || std::memcmp(code.data(), "DXBC", 4)) return false;
    uint32_t count; std::memcpy(&count, code.data() + 28, 4);
    if (count > (code.size() - 32) / 4) return false;
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t offset; std::memcpy(&offset, code.data() + 32 + size_t(i) * 4, 4);
        if (size_t(offset) + 8 <= code.size() && std::memcmp(code.data() + offset, "DXIL", 4) == 0) return true;
    }
    return false;
}
std::vector<uint8_t> compile(const std::string &source, const std::string &profile) {
    require(!source.empty() && source.size() <= 65536, "HLSL source must contain 1..65536 bytes");
    require(source.find('#') == std::string::npos && source.find('\0') == std::string::npos, "HLSL preprocessor directives are not allowed");
    if (profile.rfind("ps_6_", 0) == 0) return dxc_tools::compile(source, profile);
    require(profile == "ps_5_0" || profile == "ps_5_1", "Unsupported pixel shader profile");
    ComPtr<ID3DBlob> code, errors;
    const HRESULT hr = D3DCompile(source.data(), source.size(), "CyRSAssistant.hlsl", nullptr, nullptr, "main", profile.c_str(),
        D3DCOMPILE_ENABLE_STRICTNESS | D3DCOMPILE_OPTIMIZATION_LEVEL1, 0, &code, &errors);
    if (FAILED(hr)) {
        std::string message = errors ? std::string(static_cast<const char *>(errors->GetBufferPointer()), errors->GetBufferSize()) : "D3DCompile failed";
        throw std::runtime_error(message.substr(0, 16000));
    }
    const auto *data = static_cast<const uint8_t *>(code->GetBufferPointer());
    return {data, data + code->GetBufferSize()};
}
json reflect(const std::vector<uint8_t> &code) {
    if (is_dxil(code)) return dxc_tools::reflect(code);
    ComPtr<ID3D11ShaderReflection> reflection;
    require(SUCCEEDED(D3DReflect(code.data(), code.size(), IID_PPV_ARGS(&reflection))), "DXBC reflection unavailable; replacement refused");
    D3D11_SHADER_DESC desc{}; reflection->GetDesc(&desc);
    require(D3D11_SHVER_GET_TYPE(desc.Version) == D3D11_SHVER_PIXEL_SHADER, "Only D3D11 pixel shaders are supported");
    // GetNumInterfaceSlots is unreliable on stripped DXBC: inspect its chunk table
    // first. Do not query metadata that has been removed by the game's compiler.
    require(code.size() >= 32 && std::memcmp(code.data(), "DXBC", 4) == 0, "Expected DXBC container");
    auto word = [&](size_t offset) { uint32_t v; require(offset + 4 <= code.size(), "Invalid DXBC chunk table"); std::memcpy(&v, code.data() + offset, 4); return v; };
    const auto chunks = word(28);
    require(chunks <= (code.size() - 32) / 4, "Invalid DXBC chunk count");
    bool has_reflection = false;
    for (uint32_t i = 0; i < chunks; ++i) {
        const auto offset = word(32 + size_t(i) * 4);
        require(size_t(offset) + 8 <= code.size(), "Invalid DXBC chunk offset");
        if (std::memcmp(code.data() + offset, "RDEF", 4) == 0) has_reflection = true;
    }
    if (has_reflection) require(reflection->GetNumInterfaceSlots() == 0, "Dynamic shader class linkage is unsupported");
    else {
        const auto assembly = disassemble(code);
        require(assembly.find("dcl_interface") == std::string::npos && assembly.find("dcl_function_table") == std::string::npos,
            "Dynamic shader class linkage is unsupported");
    }
    json result = {{"inputs", json::array()}, {"outputs", json::array()}, {"resources", json::array()}, {"buffers", json::array()}, {"instructions", desc.InstructionCount}, {"metadata_present", has_reflection}, {"binding_declarations", json::array()}};
    // Token declarations survive removal of RDEF. Comparing compiler-produced
    // declarations verifies slots, dimensions, types, sampler modes and CB sizes.
    std::istringstream assembly(disassemble(code));
    std::string line;
    while (std::getline(assembly, line)) {
        if (line.rfind("dcl_constantbuffer ", 0) == 0 || line.rfind("dcl_resource_", 0) == 0 ||
            line.rfind("dcl_sampler ", 0) == 0 || line.rfind("dcl_uav_", 0) == 0) {
            while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
            result["binding_declarations"].push_back(line);
        }
    }
    for (int direction = 0; direction < 2; ++direction) {
        for (UINT i = 0; i < (direction ? desc.OutputParameters : desc.InputParameters); ++i) {
            D3D11_SIGNATURE_PARAMETER_DESC p{};
            const auto hr = direction ? reflection->GetOutputParameterDesc(i, &p) : reflection->GetInputParameterDesc(i, &p);
            require(SUCCEEDED(hr), "Cannot reflect shader signature");
            result[direction ? "outputs" : "inputs"].push_back({{"semantic", p.SemanticName}, {"index", p.SemanticIndex},
                {"register", p.Register}, {"system", p.SystemValueType}, {"type", p.ComponentType}, {"mask", p.Mask}});
        }
    }
    for (UINT i = 0; i < desc.BoundResources; ++i) {
        D3D11_SHADER_INPUT_BIND_DESC p{}; reflection->GetResourceBindingDesc(i, &p);
        result["resources"].push_back({{"name", p.Name}, {"type", p.Type}, {"slot", p.BindPoint}, {"count", p.BindCount}, {"dimension", p.Dimension}, {"return_type", p.ReturnType}});
    }
    for (UINT i = 0; i < desc.ConstantBuffers; ++i) {
        auto buffer = reflection->GetConstantBufferByIndex(i);
        D3D11_SHADER_BUFFER_DESC b{}; buffer->GetDesc(&b);
        json variables = json::array();
        for (UINT j = 0; j < b.Variables; ++j) {
            D3D11_SHADER_VARIABLE_DESC v{}; buffer->GetVariableByIndex(j)->GetDesc(&v);
            variables.push_back({{"name", v.Name}, {"offset", v.StartOffset}, {"size", v.Size}});
        }
        result["buffers"].push_back({{"name", b.Name}, {"size", b.Size}, {"variables", variables}});
    }
    result["encoding"] = "DXBC";
    result["profile"] = "ps_5_0";
    // SM5.1 uses register spaces and range declarations not yet covered by this parser.
    require((desc.Version & 15) == 0, "DXBC Shader Model 5.1 reflection is not supported yet");
    return result;
}
void compatible(const json &original, const json &replacement) {
    require(original.at("encoding") == replacement.at("encoding"), "Cannot mix DXBC and DXIL shaders in a replacement");
    // Keep the exact output contract; each used input/resource must exist in the original.
    require(original.at("outputs") == replacement.at("outputs"), "Replacement output signature differs from the original");
    for (const auto &input : replacement.at("inputs")) {
        bool found = false;
        for (const auto &old : original.at("inputs")) if (old == input) found = true;
        require(found, "Replacement requires a new or changed vertex input");
    }
    for (const auto &declaration : replacement.at("binding_declarations")) {
        bool found = false;
        for (const auto &old : original.at("binding_declarations")) if (old == declaration) found = true;
        require(found, "Replacement changes a DXBC resource declaration (slot, size, type or sampling mode)");
    }
    if (!original.at("metadata_present").get<bool>()) return;
    for (auto resource : replacement.at("resources")) {
        resource.erase("name"); bool found = false;
        for (auto old : original.at("resources")) { old.erase("name"); if (old == resource) found = true; }
        require(found, "Replacement requires an incompatible resource binding");
    }
    for (const auto &buffer : replacement.at("buffers")) {
        // HLSL generated from reflection must preserve constant buffer names and offsets.
        bool found = false;
        for (const auto &old : original.at("buffers")) if (old == buffer) found = true;
        require(found, "Replacement constant buffer layout differs from the original");
    }
}
std::string disassemble(const std::vector<uint8_t> &code) {
    if (is_dxil(code)) return dxc_tools::disassemble(code);
    ComPtr<ID3DBlob> blob;
    require(SUCCEEDED(D3DDisassemble(code.data(), code.size(), 0, nullptr, &blob)), "Cannot disassemble shader");
    require(blob->GetBufferSize() <= 256 * 1024, "Shader too large for AI inspection");
    return std::string(static_cast<const char *>(blob->GetBufferPointer()), blob->GetBufferSize());
}
std::string hash(const std::vector<uint8_t> &code) {
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    require(BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0, "SHA256 unavailable");
    unsigned char digest[32]{};
    const auto status = BCryptHash(algorithm, nullptr, 0, const_cast<PUCHAR>(code.data()), static_cast<ULONG>(code.size()), digest, sizeof(digest));
    BCryptCloseAlgorithmProvider(algorithm, 0);
    require(status >= 0, "SHA256 failed");
    const char *hex = "0123456789abcdef";
    std::string out; for (auto b : digest) { out += hex[b >> 4]; out += hex[b & 15]; } return out;
}
std::string generated_fx(const std::string &body, const json &parameters, const std::string &title) {
    require(parameters.is_array() && parameters.size() <= 16, "Expected at most 16 generated parameters");
    auto quoted = [](const std::string &value) {
        require(!value.empty() && value.size() <= 100, "Invalid generated label");
        for (unsigned char ch : value) require(ch >= 32 && ch != '\\' && ch != '\"', "Invalid label character");
        return json(value).dump();
    };
    const auto title_literal = quoted(title);
    std::string uniforms, declarations;
    std::set<std::string> names;
    for (const auto &parameter : parameters) {
        const auto name = parameter.at("name").get<std::string>();
        require(std::regex_match(name, std::regex("[A-Za-z][A-Za-z0-9_]{0,31}")) && names.insert(name).second, "Invalid or duplicate generated parameter name");
        const double low = parameter.at("min").get<double>(), high = parameter.at("max").get<double>();
        const double value = parameter.at("default").get<double>(), step = parameter.value("step", 0.01);
        require(std::isfinite(low) && std::isfinite(high) && std::isfinite(value) && std::isfinite(step) && low < high && low >= -1e6 && high <= 1e6 && value >= low && value <= high && step > 0 && step <= high-low, "Invalid generated parameter bounds");
        const auto symbol = "CyRSP_" + name;
        declarations += "float " + symbol + ";\n";
        uniforms += "uniform float " + symbol + " < ui_type = \"slider\"; ui_label = " + quoted(parameter.value("label", name)) + "; ui_min = " + json(low).dump() + "; ui_max = " + json(high).dump() + "; ui_step = " + json(step).dump() + "; > = " + json(value).dump() + ";\n";
    }

    require(!body.empty() && body.size() <= 16384, "Generated shader body must contain 1..16384 bytes");
    require(body.find('#') == std::string::npos && body.find('\0') == std::string::npos, "Generated shader directives are forbidden");
    // A function body only: balanced braces prevent escaping into global declarations.
    int depth = 0;
    for (char c : body) { if (c == '{') ++depth; if (c == '}') require(--depth >= 0, "Generated body escapes its function"); }
    require(depth == 0, "Unbalanced generated body");
    require(!std::regex_search(body, std::regex(R"(\b(while|for|do|asm|technique|pass|texture|sampler|uniform)\b)")), "Generated body uses unsupported declarations or loops");
    const std::string function = "float3 CyRSShade(float2 uv, float3 color) {\n" + body + "\n}\n";
    // Compile the same function before writing any FX file. No includes or external files.
    compile("Texture2D tex : register(t0); SamplerState smp : register(s0); float CyRSTime; float2 CyRSPixelSize;\nfloat3 CyRSSample(float2 uv) { return tex.SampleLevel(smp,uv,0).rgb; }\n" + declarations + function + "float4 main(float4 pos:SV_Position,float2 uv:TEXCOORD0):SV_Target { return float4(CyRSShade(uv,CyRSSample(uv)),1); }");
    return "// Generated by CyRSAssistant. Standalone portable ReShade FX.\n"
        "texture CyRSColor : COLOR;\nsampler CyRSBuffer { Texture = CyRSColor; };\n"
        "uniform float CyRSAmount < ui_type = \"slider\"; ui_min = 0.0; ui_max = 1.0; ui_label = \"Intensity\"; > = 1.0;\n"
        "uniform float CyRSTime < source = \"timer\"; >;\n"
        "static const float2 CyRSPixelSize = float2(1.0/BUFFER_WIDTH, 1.0/BUFFER_HEIGHT);\n"
        "float3 CyRSSample(float2 uv) { return tex2D(CyRSBuffer,uv).rgb; }\n" + uniforms + function +
        "void CyRSVS(uint id:SV_VertexID,out float4 pos:SV_Position,out float2 uv:TEXCOORD0) { uv=float2((id<<1)&2,id&2); pos=float4(uv*float2(2,-2)+float2(-1,1),0,1); }\n"
        "float4 CyRSPS(float4 pos:SV_Position,float2 uv:TEXCOORD0):SV_Target { float3 c=CyRSSample(uv); return float4(lerp(c,CyRSShade(uv,c),CyRSAmount),1); }\n"
        "technique CyRSGenerated < ui_label = " + title_literal + "; > { pass { VertexShader=CyRSVS; PixelShader=CyRSPS; } }\n";
}
}
