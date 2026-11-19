#pragma once
#include <sstream>
#include <wincodec.h>
#include <wrl/client.h>
#include <wincrypt.h>
#include <cymcp/core.hpp>
namespace cyrs::sdk {
inline cymcp::Json png_capture(const cymcp::Json& frame) {
    using Microsoft::WRL::ComPtr;
    using namespace cymcp;
    if(frame.at("pixel_format")!="rgb8" || frame.at("encoding")!="base64")throw Error("Capture","Unsupported RGB capture format");
    const auto encoded=frame.at("data").get<std::string>();DWORD length=0;
    if(!CryptStringToBinaryA(encoded.c_str(),static_cast<DWORD>(encoded.size()),CRYPT_STRING_BASE64,nullptr,&length,nullptr,nullptr))throw Error("Capture","Invalid capture data");
    std::vector<BYTE> pixels(length);CryptStringToBinaryA(encoded.c_str(),static_cast<DWORD>(encoded.size()),CRYPT_STRING_BASE64,pixels.data(),&length,nullptr,nullptr);
    const auto width=frame.at("width").get<UINT>(),height=frame.at("height").get<UINT>();
    if(width>1280||height>1280||uint64_t(width)*height*3!=length)throw Error("Capture","Invalid capture dimensions");
    const auto initialized=CoInitializeEx(nullptr,COINIT_MULTITHREADED);
    struct Finish{HRESULT h;~Finish(){if(SUCCEEDED(h))CoUninitialize();}} finish{initialized};
    auto check=[](HRESULT h){if(FAILED(h))throw Error("Capture","Windows PNG encoder failed");};
    ComPtr<IWICImagingFactory> factory;check(CoCreateInstance(CLSID_WICImagingFactory,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&factory)));
    ComPtr<IStream> stream;check(CreateStreamOnHGlobal(nullptr,TRUE,&stream));
    ComPtr<IWICBitmapEncoder> encoder;check(factory->CreateEncoder(GUID_ContainerFormatPng,nullptr,&encoder));check(encoder->Initialize(stream.Get(),WICBitmapEncoderNoCache));
    ComPtr<IWICBitmapFrameEncode> output;ComPtr<IPropertyBag2> properties;check(encoder->CreateNewFrame(&output,&properties));check(output->Initialize(properties.Get()));check(output->SetSize(width,height));
    auto format=GUID_WICPixelFormat24bppRGB;check(output->SetPixelFormat(&format));check(output->WritePixels(height,width*3,length,pixels.data()));check(output->Commit());check(encoder->Commit());
    STATSTG stat{};check(stream->Stat(&stat,STATFLAG_NONAME));HGLOBAL memory=nullptr;check(GetHGlobalFromStream(stream.Get(),&memory));
    auto data=static_cast<const BYTE*>(GlobalLock(memory));DWORD chars=0;
    CryptBinaryToStringA(data,stat.cbSize.LowPart,CRYPT_STRING_BASE64|CRYPT_STRING_NOCRLF,nullptr,&chars);
    std::string result(chars,'\0');CryptBinaryToStringA(data,stat.cbSize.LowPart,CRYPT_STRING_BASE64|CRYPT_STRING_NOCRLF,result.data(),&chars);GlobalUnlock(memory);
    if(!result.empty()&&result.back()=='\0')result.pop_back();
    return {{"mimeType","image/png"},{"data",result},{"width",width},{"height",height}};
}
inline cymcp::Json mcp_images(cymcp::Json response) {
    if(response.is_object()&&response.contains("result")&&response["result"].contains("structuredContent")&&response["result"]["structuredContent"].contains("capture")) {
        auto image=response["result"]["structuredContent"]["capture"];image["type"]="image";image.erase("width");image.erase("height");
        response["result"]["content"]=cymcp::Json::array({image});response["result"]["structuredContent"]["capture"].erase("data");
    }return response;
}
class McpOutput : public std::stringbuf {
    std::ostream& destination_;
  public:
    explicit McpOutput(std::ostream& out):destination_(out){}
    int sync() override {
        const auto bytes=str();str({});
        std::istringstream lines(bytes);std::string line;
        while(std::getline(lines,line)) {
            try{destination_<<mcp_images(cymcp::Json::parse(line)).dump()<<'\n';}
            catch(...){destination_<<line<<'\n';}
        }destination_.flush();return 0;
    }
};
}
