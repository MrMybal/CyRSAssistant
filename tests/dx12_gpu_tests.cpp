#include "shader_tools.hpp"
#include "dxc_tools.hpp"
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <d3dcompiler.h>
#include <wrl/client.h>
#include <iostream>
using Microsoft::WRL::ComPtr;
using namespace cyrs;
int main() {
    try {
        ComPtr<ID3D12Device> device;
        HRESULT hr = D3D12CreateDevice(nullptr, D3D_FEATURE_LEVEL_11_0, IID_PPV_ARGS(&device));
        if (FAILED(hr)) {
            ComPtr<IDXGIFactory4> factory; ComPtr<IDXGIAdapter> warp;
            require(SUCCEEDED(CreateDXGIFactory2(0, IID_PPV_ARGS(&factory))), "No DXGI factory");
            require(SUCCEEDED(factory->EnumWarpAdapter(IID_PPV_ARGS(&warp))), "No WARP adapter");
            require(SUCCEEDED(D3D12CreateDevice(warp.Get(), D3D_FEATURE_LEVEL_11_0, IID_PPV_ARGS(&device))), "No DX12 device");
        }
        D3D12_ROOT_SIGNATURE_DESC root_desc{};
        root_desc.Flags = D3D12_ROOT_SIGNATURE_FLAG_ALLOW_INPUT_ASSEMBLER_INPUT_LAYOUT;
        ComPtr<ID3DBlob> root_blob, errors;
        require(SUCCEEDED(D3D12SerializeRootSignature(&root_desc, D3D_ROOT_SIGNATURE_VERSION_1, &root_blob, &errors)), "Root serialization failed");
        ComPtr<ID3D12RootSignature> root;
        require(SUCCEEDED(device->CreateRootSignature(0, root_blob->GetBufferPointer(), root_blob->GetBufferSize(), IID_PPV_ARGS(&root))), "Root creation failed");
        const char *source = "float4 main(uint id:SV_VertexID):SV_Position { return float4((id==1)?1:-1,(id==2)?1:-1,0,1); }";
        const auto vs = dxc_tools::compile(source, "vs_6_0");
        const auto ps = shader_tools::compile("float4 main():SV_Target { return float4(1,0,0,1); }", "ps_6_0");
        const auto replacement = shader_tools::compile("float4 main():SV_Target { return float4(0,1,0,1); }", "ps_6_0");
        shader_tools::compatible(shader_tools::reflect(ps), shader_tools::reflect(replacement));
        D3D12_GRAPHICS_PIPELINE_STATE_DESC desc{};
        desc.pRootSignature = root.Get(); desc.VS = {vs.data(), vs.size()};
        desc.PS = {ps.data(), ps.size()}; desc.SampleMask = UINT_MAX;
        desc.RasterizerState.FillMode = D3D12_FILL_MODE_SOLID; desc.RasterizerState.CullMode = D3D12_CULL_MODE_NONE;
        desc.RasterizerState.DepthClipEnable = TRUE;
        desc.DepthStencilState.DepthFunc = D3D12_COMPARISON_FUNC_ALWAYS;
        desc.DepthStencilState.FrontFace = desc.DepthStencilState.BackFace = {D3D12_STENCIL_OP_KEEP,D3D12_STENCIL_OP_KEEP,D3D12_STENCIL_OP_KEEP,D3D12_COMPARISON_FUNC_ALWAYS};
        auto &blend = desc.BlendState.RenderTarget[0];
        blend.SrcBlend = blend.SrcBlendAlpha = D3D12_BLEND_ONE;
        blend.DestBlend = blend.DestBlendAlpha = D3D12_BLEND_ZERO;
        blend.BlendOp = blend.BlendOpAlpha = D3D12_BLEND_OP_ADD;
        blend.LogicOp = D3D12_LOGIC_OP_NOOP; blend.RenderTargetWriteMask = D3D12_COLOR_WRITE_ENABLE_ALL;
        desc.PrimitiveTopologyType = D3D12_PRIMITIVE_TOPOLOGY_TYPE_TRIANGLE;
        desc.NumRenderTargets = 1; desc.RTVFormats[0] = DXGI_FORMAT_R8G8B8A8_UNORM; desc.SampleDesc.Count = 1;
        ComPtr<ID3D12PipelineState> original, changed;
        require(SUCCEEDED(device->CreateGraphicsPipelineState(&desc, IID_PPV_ARGS(&original))), "GPU refused original DXIL PSO");
        desc.PS = {replacement.data(), replacement.size()};
        require(SUCCEEDED(device->CreateGraphicsPipelineState(&desc, IID_PPV_ARGS(&changed))), "GPU refused replacement DXIL PSO");
        ComPtr<ID3D12CommandAllocator> allocator; ComPtr<ID3D12GraphicsCommandList> list;
        require(SUCCEEDED(device->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT, IID_PPV_ARGS(&allocator))), "Allocator failed");
        require(SUCCEEDED(device->CreateCommandList(0, D3D12_COMMAND_LIST_TYPE_DIRECT, allocator.Get(), original.Get(), IID_PPV_ARGS(&list))), "Command list failed");
        list->SetGraphicsRootSignature(root.Get()); list->SetPipelineState(changed.Get()); list->SetPipelineState(original.Get());
        require(SUCCEEDED(list->Close()), "Command list validation failed");
        std::cout << "DX12 GPU accepted original and replacement DXIL PSOs; bind/restore recording succeeded\n";
        return 0;
    } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
