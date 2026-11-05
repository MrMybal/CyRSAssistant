#include <imgui.h>
#include "manual.hpp"
#include "manual_model.hpp"
#include "resources.h"
#include <windows.h>
#include <shellapi.h>
#include <wincodec.h>
#include <wrl/client.h>
#include <algorithm>
#include <filesystem>
#include <vector>

namespace cyrs::manual {
namespace {
using nlohmann::json;
using namespace reshade::api;
using Microsoft::WRL::ComPtr;
const std::string &str(const json &value) { return value.get_ref<const std::string &>(); }

bool decode_png(HMODULE module, int identifier, Image &image, std::vector<uint8_t> &pixels) {
    const auto info = FindResourceW(module, MAKEINTRESOURCEW(identifier), MAKEINTRESOURCEW(10));
    if (!info) return false;
    const auto size = SizeofResource(module, info);
    if (!size || size > 16 * 1024 * 1024) return false;
    const auto loaded = LoadResource(module, info);
    auto *data = loaded ? static_cast<BYTE *>(LockResource(loaded)) : nullptr;
    if (!data) return false;
    const HRESULT com = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    if (FAILED(com) && com != RPC_E_CHANGED_MODE) return false;
    struct ComScope { bool owned; ~ComScope() { if (owned) CoUninitialize(); } } scope{SUCCEEDED(com)};
    ComPtr<IWICImagingFactory> factory;
    ComPtr<IWICStream> stream;
    ComPtr<IWICBitmapDecoder> decoder;
    ComPtr<IWICBitmapFrameDecode> frame;
    ComPtr<IWICFormatConverter> converter;
    if (FAILED(CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&factory))) ||
        FAILED(factory->CreateStream(&stream)) ||
        FAILED(stream->InitializeFromMemory(data, size)) ||
        FAILED(factory->CreateDecoderFromStream(stream.Get(), nullptr, WICDecodeMetadataCacheOnLoad, &decoder)) ||
        FAILED(decoder->GetFrame(0, &frame)) ||
        FAILED(frame->GetSize(&image.width, &image.height)) ||
        !image.width || !image.height || image.width > 4096 || image.height > 4096 ||
        uint64_t(image.width) * image.height > 16 * 1024 * 1024 ||
        FAILED(factory->CreateFormatConverter(&converter)) ||
        FAILED(converter->Initialize(frame.Get(), GUID_WICPixelFormat32bppRGBA, WICBitmapDitherTypeNone, nullptr, 0, WICBitmapPaletteTypeCustom))) return false;
    pixels.resize(static_cast<size_t>(image.width) * image.height * 4);
    return SUCCEEDED(converter->CopyPixels(nullptr, image.width * 4, static_cast<UINT>(pixels.size()), pixels.data()));
}

Image &load_image(effect_runtime *runtime, HMODULE module, State &state, const std::string &asset) {
    auto &image = state.images[asset];
    if (image.attempted) return image;
    image.attempted = true;
    const int identifier = asset == "chat" ? IDR_CYRS_MANUAL_CHAT : asset == "connection" ? IDR_CYRS_MANUAL_CONNECTION : 0;
    std::vector<uint8_t> pixels;
    if (!identifier || !decode_png(module, identifier, image, pixels)) return image;
    const subresource_data data{pixels.data(), image.width * 4, image.width * image.height * 4};
    const resource_desc desc(image.width, image.height, 1, 1, format::r8g8b8a8_unorm, 1, memory_heap::default_,
                             resource_usage::shader_resource | resource_usage::copy_dest);
    auto *device = runtime->get_device();
    if (!device->create_resource(desc, &data, resource_usage::shader_resource, &image.texture)) return image;
    if (!device->create_resource_view(image.texture, resource_usage::shader_resource, resource_view_desc(format::r8g8b8a8_unorm), &image.view)) {
        runtime->get_command_queue()->wait_idle();
        device->destroy_resource(image.texture);
        image.texture = {};
    }
    return image;
}

void flow_diagram(const json &block) {
    ImGui::SeparatorText(str(block["title"]).c_str());
    const float width = std::max(80.0f, ImGui::GetContentRegionAvail().x);
    const float padding = 12.0f;
    const auto &items = block["items"];
    for (size_t i = 0; i < items.size(); ++i) {
        const auto &text = str(items[i]);
        const float wrap = std::max(20.0f, width - padding * 2);
        const ImVec2 text_size = ImGui::CalcTextSize(text.c_str(), nullptr, false, wrap);
        const float height = text_size.y + padding * 2;
        const ImVec2 origin = ImGui::GetCursorScreenPos();
        auto *draw = ImGui::GetWindowDrawList();
        draw->AddRectFilled(origin, ImVec2(origin.x + width, origin.y + height), IM_COL32(20, 51, 55, 255), 7);
        draw->AddRect(origin, ImVec2(origin.x + width, origin.y + height), IM_COL32(64, 214, 201, 220), 7);
        draw->AddText(ImGui::GetFont(), ImGui::GetFontSize(), ImVec2(origin.x + padding, origin.y + padding),
                      IM_COL32(234, 244, 243, 255), text.c_str(), nullptr, wrap);
        ImGui::Dummy(ImVec2(width, height));
        if (i + 1 < items.size() && block.value("layout", std::string()) != "choices") {
            const auto arrow = ImGui::GetCursorScreenPos();
            const float x = arrow.x + width / 2;
            draw->AddLine(ImVec2(x, arrow.y), ImVec2(x, arrow.y + 14), IM_COL32(64, 214, 201, 255), 2);
            draw->AddTriangleFilled(ImVec2(x - 5, arrow.y + 10), ImVec2(x + 5, arrow.y + 10), ImVec2(x, arrow.y + 17), IM_COL32(64, 214, 201, 255));
            ImGui::Dummy(ImVec2(width, 20));
        }
    }
}

void open_html(HMODULE module, const std::string &language, State &state, const json &ui) {
    wchar_t name[32768]{};
    const auto length = GetModuleFileNameW(module, name, 32768);
    if (!length || length >= 32768) { state.open_error = str(ui["open_error"]); return; }
    const auto path = html_path(name, language);
    std::error_code error;
    if (!std::filesystem::is_regular_file(path, error) ||
        reinterpret_cast<INT_PTR>(ShellExecuteW(nullptr, L"open", path.c_str(), nullptr, path.parent_path().c_str(), SW_SHOWNORMAL)) <= 32) {
        state.open_error = str(ui["open_error"]);
    } else state.open_error.clear();
}
}

void State::destroy(effect_runtime *runtime) {
    const bool allocated = std::any_of(images.begin(), images.end(), [](const auto &entry) { return entry.second.texture.handle || entry.second.view.handle; });
    if (allocated) runtime->get_command_queue()->wait_idle();
    for (auto &[name, image] : images) {
        if (image.view.handle) runtime->get_device()->destroy_resource_view(image.view);
        if (image.texture.handle) runtime->get_device()->destroy_resource(image.texture);
    }
    images.clear();
}

void draw(effect_runtime *runtime, HMODULE module, const std::string &language, State &state) {
    ++state.draws;
    const auto &book = document(language);
    const auto &ui = book.at("ui");
    const auto &chapters = book.at("chapters");
    const auto &lang = str(book["code"]);
    ImGui::TextWrapped("%s", str(ui["title"]).c_str());
    if (ImGui::Button((str(ui["open"]) + "###open_manual").c_str())) open_html(module, language, state, ui);
    if (!state.open_error.empty()) ImGui::TextWrapped("%s", str(ui["open_error"]).c_str());
    if (ImGui::InputText((str(ui["search"]) + "###manual_search").c_str(), state.query.data(), state.query.size())) state.rebuild = true;
    if (state.rebuild || state.last_query != state.query.data() || state.last_language != lang) {
        state.matches = search(book, state.query.data());
        state.last_query = state.query.data(); state.last_language = lang; state.rebuild = false;
        bool found = false;
        for (const auto index : state.matches) if (chapters[index]["id"] == state.selected) found = true;
        if (!found && !state.matches.empty()) { state.selected = str(chapters[state.matches.front()]["id"]); state.scroll_top = true; }
    }
    ImGui::SliderFloat((str(ui["text_size"]) + "###manual_text_size").c_str(), &state.text_scale, .8f, 1.6f, "%.1fx");
    // PushFont expects the unscaled base size; GetFontSize already includes ReShade's scale.
    ImGui::PushFont(nullptr, ImGui::GetStyle().FontSizeBase * state.text_scale);
    struct FontScope { ~FontScope() { ImGui::PopFont(); } } font_scope;
    if (state.matches.empty()) { ImGui::TextWrapped("%s", str(ui["empty"]).c_str()); return; }
    size_t selected = state.matches.front();
    for (const auto index : state.matches) if (chapters[index]["id"] == state.selected) selected = index;
    const bool wide = ImGui::GetContentRegionAvail().x >= 620.0f * state.text_scale;
    if (wide) {
        const float side = std::min(240.0f, ImGui::GetContentRegionAvail().x * .30f);
        ImGui::BeginChild("manual_contents", ImVec2(side, 0), true);
        ImGui::TextUnformatted(str(ui["contents"]).c_str());
        for (const auto index : state.matches) {
            const auto &chapter = chapters[index];
            if (ImGui::Selectable((str(chapter["title"]) + "###manual_" + str(chapter["id"])).c_str(), index == selected)) {
                state.selected = str(chapter["id"]); selected = index; state.scroll_top = true;
            }
            if (ImGui::IsItemHovered()) ImGui::SetTooltip("%s", str(chapter["title"]).c_str());
        }
        ImGui::EndChild(); ImGui::SameLine();
    } else if (ImGui::BeginCombo((str(ui["contents"]) + "###manual_contents_combo").c_str(), str(chapters[selected]["title"]).c_str())) {
        for (const auto index : state.matches)
            if (ImGui::Selectable((str(chapters[index]["title"]) + "###manual_" + str(chapters[index]["id"])).c_str(), selected == index)) {
                state.selected = str(chapters[index]["id"]); selected = index; state.scroll_top = true;
            }
        ImGui::EndCombo();
    }
    ImGui::BeginChild("manual_article", ImVec2(0, 0), true);
    if (state.scroll_top) { ImGui::SetScrollY(0); state.scroll_top = false; }
    const auto &chapter = chapters[selected];
    ImGui::TextWrapped("%s", str(chapter["title"]).c_str());
    ImGui::Separator();
    for (size_t index = 0; index < chapter["blocks"].size(); ++index) {
        const auto &block = chapter["blocks"][index];
        const auto &kind = str(block["type"]);
        ImGui::PushID(static_cast<int>(index));
        if (kind == "paragraph" || kind == "note") {
            if (kind == "note") ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(.48f, .9f, .85f, 1));
            ImGui::TextWrapped("%s", str(block["text"]).c_str());
            if (kind == "note") ImGui::PopStyleColor();
        } else if (kind == "heading") ImGui::SeparatorText(str(block["text"]).c_str());
        else if (kind == "code" || kind == "example") {
            ImGui::TextWrapped("%s", str(block["text"]).c_str());
            if (ImGui::SmallButton((str(ui["copy"]) + "###manual_copy").c_str())) ImGui::SetClipboardText(str(block["text"]).c_str());
        } else if (kind == "steps" || kind == "bullets") {
            size_t number = 1;
            for (const auto &item : block["items"]) {
                if (kind == "steps") ImGui::TextWrapped("%zu. %s", number++, str(item).c_str());
                else { ImGui::Bullet(); ImGui::SameLine(); ImGui::TextWrapped("%s", str(item).c_str()); }
            }
        } else if (kind == "flow") flow_diagram(block);
        else if (kind == "table") {
            if (ImGui::BeginTable("manual_table", static_cast<int>(block["headers"].size()), ImGuiTableFlags_Borders | ImGuiTableFlags_RowBg | ImGuiTableFlags_SizingStretchProp)) {
                for (const auto &header : block["headers"]) ImGui::TableSetupColumn(str(header).c_str());
                ImGui::TableHeadersRow();
                for (const auto &row : block["rows"]) {
                    ImGui::TableNextRow();
                    for (const auto &cell : row) { ImGui::TableNextColumn(); ImGui::TextWrapped("%s", str(cell).c_str()); }
                }
                ImGui::EndTable();
            }
        } else if (kind == "image") {
            const auto &asset = str(block["asset"]);
            auto &picture = load_image(runtime, module, state, asset);
            if (picture.view.handle) {
                const float width = std::max(1.0f, std::min(static_cast<float>(picture.width), ImGui::GetContentRegionAvail().x));
                ImGui::Image(static_cast<ImTextureID>(picture.view.handle), ImVec2(width, width * picture.height / picture.width));
                if (ImGui::IsItemClicked()) { state.enlarged = asset; ImGui::OpenPopup("###manual_illustration"); }
                if (ImGui::IsItemHovered()) ImGui::SetTooltip("%s", str(ui["image"]).c_str());
            } else ImGui::TextWrapped("%s", str(ui["unavailable"]).c_str());
            ImGui::TextWrapped("%s", str(block["caption"]).c_str());
            if (ImGui::BeginPopupModal((str(ui["figure"]) + "###manual_illustration").c_str(), nullptr, ImGuiWindowFlags_AlwaysAutoResize)) {
                auto &large = load_image(runtime, module, state, state.enlarged);
                if (large.view.handle) {
                    const auto available = ImGui::GetIO().DisplaySize;
                    const float scale = std::min({1.0f, available.x * .85f / large.width, available.y * .75f / large.height});
                    ImGui::Image(static_cast<ImTextureID>(large.view.handle), ImVec2(large.width * scale, large.height * scale));
                }
                if (ImGui::Button((str(ui["close"]) + "###manual_close").c_str())) ImGui::CloseCurrentPopup();
                ImGui::EndPopup();
            }
        } else if (kind == "related") {
            for (const auto &target : block["chapters"])
                for (const auto &other : chapters) if (other["id"] == target)
                    if (ImGui::SmallButton((str(other["title"]) + "###related_" + str(target)).c_str())) {
                        state.selected = str(target); state.query.fill(0); state.rebuild = true; state.scroll_top = true;
                    }
        }
        ImGui::Spacing(); ImGui::PopID();
    }
    if (selected > 0 && ImGui::Button((str(ui["previous"]) + "###manual_previous").c_str())) {
        state.selected = str(chapters[selected - 1]["id"]); state.query.fill(0); state.rebuild = true; state.scroll_top = true;
    }
    if (selected + 1 < chapters.size()) {
        if (selected > 0) ImGui::SameLine();
        if (ImGui::Button((str(ui["next"]) + "###manual_next").c_str())) {
            state.selected = str(chapters[selected + 1]["id"]); state.query.fill(0); state.rebuild = true; state.scroll_top = true;
        }
    }
    ImGui::EndChild();
}
}
