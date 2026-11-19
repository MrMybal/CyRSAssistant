// Real D3D11/ReShade host for integration checks; no imitation of add-on operations.
#include <Windows.h>
#include <d3d11.h>
#include <dxgi.h>
#include <wrl/client.h>
LRESULT CALLBACK window_proc(HWND w,UINT m,WPARAM a,LPARAM b){if(m==WM_DESTROY){PostQuitMessage(0);return 0;}return DefWindowProcW(w,m,a,b);}
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,PWSTR,int){
    WNDCLASSW cls{};cls.lpfnWndProc=window_proc;cls.hInstance=instance;cls.lpszClassName=L"CyRSAssistantIntegration";RegisterClassW(&cls);
    auto window=CreateWindowW(cls.lpszClassName,L"CyRSAssistant — ReShade integration",WS_OVERLAPPEDWINDOW,40,40,1200,900,nullptr,nullptr,instance,nullptr);
    // Load the user's installed ReShade DXGI proxy before creating the real device.
    auto proxy=LoadLibraryW(L"dxgi.dll");if(!proxy)return 2;
    DXGI_SWAP_CHAIN_DESC options{};options.BufferDesc.Width=1152;options.BufferDesc.Height=832;options.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;
    options.SampleDesc.Count=1;options.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;options.BufferCount=2;options.OutputWindow=window;options.Windowed=TRUE;options.SwapEffect=DXGI_SWAP_EFFECT_DISCARD;
    Microsoft::WRL::ComPtr<ID3D11Device> device;Microsoft::WRL::ComPtr<ID3D11DeviceContext> context;Microsoft::WRL::ComPtr<IDXGISwapChain> swap;
    auto result=D3D11CreateDeviceAndSwapChain(nullptr,D3D_DRIVER_TYPE_HARDWARE,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&options,&swap,&device,nullptr,&context);
    if(FAILED(result))return 3;
    Microsoft::WRL::ComPtr<ID3D11Texture2D> back;swap->GetBuffer(0,IID_PPV_ARGS(&back));Microsoft::WRL::ComPtr<ID3D11RenderTargetView> target;device->CreateRenderTargetView(back.Get(),nullptr,&target);
    ShowWindow(window,SW_SHOW);MSG message{};
    while(message.message!=WM_QUIT){while(PeekMessageW(&message,nullptr,0,0,PM_REMOVE)){TranslateMessage(&message);DispatchMessageW(&message);}const float color[]={.14f,.27f,.32f,1.f};context->OMSetRenderTargets(1,target.GetAddressOf(),nullptr);context->ClearRenderTargetView(target.Get(),color);swap->Present(1,0);}
    return 0;
}
