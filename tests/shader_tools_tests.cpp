#include "shader_tools.hpp"
#include <iostream>
#include <functional>
#include <d3dcompiler.h>
#include <wrl/client.h>

using namespace cyrs::shader_tools;
int main() {
    unsigned checks = 0;
    auto rejected = [&](const std::function<void()> &f) { bool failed = false; try { f(); } catch (const std::exception &) { failed = true; } if (!failed) throw std::runtime_error("Expected rejection"); ++checks; };
    try {
        const auto original = compile("float4 main(float4 pos:SV_Position):SV_Target { return float4(1,0,0,1); }");
        const auto replacement = compile("float4 main(float4 pos:SV_Position):SV_Target { return float4(0,1,0,1); }");
        compatible(reflect(original), reflect(replacement)); ++checks;
        const auto dxil = compile("cbuffer B:register(b0,space1) { float4 value; }; float4 main():SV_Target { return value; }", "ps_6_0");
        if (!is_dxil(dxil) || reflect(dxil)["profile"] != "ps_6_0") return 7; ++checks;
        compatible(reflect(dxil), reflect(dxil)); ++checks;
        if (disassemble(dxil).find("target datalayout") == std::string::npos) return 8; ++checks;
        rejected([&] { compatible(reflect(dxil), reflect(compile("cbuffer B:register(b0,space2) { float4 value; }; float4 main():SV_Target { return value; }", "ps_6_0"))); });
        rejected([&] { compatible(reflect(dxil), reflect(original)); });
        Microsoft::WRL::ComPtr<ID3DBlob> stripped;
        if (FAILED(D3DStripShader(original.data(), original.size(), D3DCOMPILER_STRIP_REFLECTION_DATA, &stripped))) return 5;
        auto bytes = static_cast<const uint8_t *>(stripped->GetBufferPointer());
        compatible(reflect(std::vector<uint8_t>(bytes, bytes + stripped->GetBufferSize())), reflect(replacement)); ++checks;
        const auto resource_shader = compile("cbuffer B:register(b0) { float4 value; }; float4 main():SV_Target { return value; }");
        Microsoft::WRL::ComPtr<ID3DBlob> stripped_resource;
        if (FAILED(D3DStripShader(resource_shader.data(), resource_shader.size(), D3DCOMPILER_STRIP_REFLECTION_DATA, &stripped_resource))) return 6;
        bytes = static_cast<const uint8_t *>(stripped_resource->GetBufferPointer());
        auto stripped_contract = reflect(std::vector<uint8_t>(bytes, bytes + stripped_resource->GetBufferSize()));
        compatible(stripped_contract, reflect(resource_shader)); ++checks;
        rejected([&] { compatible(stripped_contract, reflect(compile("cbuffer B:register(b1) { float4 value; }; float4 main():SV_Target { return value; }"))); });
        if (hash(original).size() != 64 || hash(original) == hash(replacement)) return 2; ++checks;
        if (disassemble(original).find("ps_5_0") == std::string::npos) return 3; ++checks;
        rejected([&] { compile("not valid HLSL"); });
        rejected([&] { compile("#include \"C:/secret\"\n"); });
        rejected([&] { compatible(reflect(original), reflect(compile("float4 main(float4 pos:SV_Position):SV_Target1 { return 1; }"))); });
        rejected([&] { compatible(reflect(original), reflect(compile("Texture2D t:register(t7); float4 main(float4 pos:SV_Position):SV_Target { return t.Load(int3(pos.xy,0)); }"))); });
        auto fx = generated_fx("float gray=dot(color,float3(0.2126,0.7152,0.0722)); return gray.xxx;");
        if (fx.find("technique CyRSGenerated") == std::string::npos || fx.find("#include") != std::string::npos) return 4; ++checks;
        generated_fx("return lerp(color,CyRSSample(uv+float2(0.001,0)),0.5);"); ++checks;
        rejected([&] { generated_fx("} technique escape { }"); });
        rejected([&] { generated_fx("while(true) {} return color;"); });
        rejected([&] { generated_fx("return missing_variable;"); });
        cyrs::json sliders = cyrs::json::array({{{"name", "Threshold"}, {"label", "Threshold"}, {"min", 0.0}, {"max", 4.0}, {"default", 1.0}, {"step", 0.01}}});
        auto controlled = generated_fx("return max(color - CyRSP_Threshold, 0.0) + CyRSSample(uv + CyRSPixelSize);", sliders, "Anamorphic bloom");
        if (controlled.find("uniform float CyRSP_Threshold") == std::string::npos || controlled.find("ui_max = 4.0") == std::string::npos) return 9; ++checks;
        rejected([&] { auto bad = sliders; bad[0]["default"] = 5; generated_fx("return color;", bad); });
        rejected([&] { auto bad = sliders; bad[0]["name"] = "x; injected"; generated_fx("return color;", bad); });
        rejected([&] { auto bad = sliders; bad.push_back(bad[0]); generated_fx("return color;", bad); });
        rejected([&] { generated_fx("return color;", sliders, "bad\"label"); });

        std::cout << checks << " shader compiler, reflection and generation checks passed\n";
        return 0;
    } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
