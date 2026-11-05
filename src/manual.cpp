#include <imgui.h>
#include "manual.hpp"
#include "manual_model.hpp"
#include "localization.hpp"
#include <windows.h>
#include <shellapi.h>
#include <filesystem>
#include <stdexcept>

namespace cyrs::manual {
void launch(HMODULE module, const std::string &language, State &state, const std::string &chapter,
            const std::string &anchor, const std::string &media, const std::string &query) {
    wchar_t name[32768]{};
    const auto length = GetModuleFileNameW(module, name, 32768);
    if (!length || length >= 32768) throw std::runtime_error("Cannot locate the installed add-on");
    const auto url = help_url(name, language, chapter, anchor, media, query);
    std::error_code error;
    const auto path = html_path(name);
    if (!std::filesystem::is_regular_file(path, error))
        throw std::runtime_error("The CyDoc manual is missing. Re-extract the complete CyRSAssistant/Documentation folder from the ZIP.");
    if (reinterpret_cast<INT_PTR>(ShellExecuteW(nullptr, L"open", url.c_str(), nullptr, path.parent_path().c_str(), SW_SHOWNORMAL)) <= 32)
        throw std::runtime_error("The local CyDoc manual could not be opened. Check your default browser.");
    state.selected = chapter; state.anchor = anchor; state.media = media;
    const auto bytes = WideCharToMultiByte(CP_UTF8, 0, url.data(), static_cast<int>(url.size()), nullptr, 0, nullptr, nullptr);
    state.last_url.resize(bytes);
    WideCharToMultiByte(CP_UTF8, 0, url.data(), static_cast<int>(url.size()), state.last_url.data(), bytes, nullptr, nullptr);
    state.launched = true; state.open_error.clear();
}
void draw(HMODULE module, const std::string &language, State &state) {
    auto tr = [&](const char *text) { return i18n::translate(language, text); };
    auto label = [&](const char *text) { return i18n::label(language, text); };
    const auto &book = document(language);
    const auto *selected = page(book, state.selected);
    if (!selected) { state.selected = "start"; selected = page(book, state.selected); }
    ImGui::TextWrapped("%s", tr("CyDoc - local illustrated documentation"));
    ImGui::TextWrapped("%s", tr("The manual opens in your default browser, fully offline. It includes guides, images, diagrams, API reference and distributed source code."));
    if (ImGui::BeginCombo(label("Help topic").c_str(), selected->at("title").get_ref<const std::string &>().c_str())) {
        for (const auto &entry : book.at("pages")) {
            if (entry.value("kind", "") == "source") continue;
            const auto id = entry.at("id").get<std::string>();
            if (ImGui::Selectable((entry.at("title").get<std::string>() + "###help_" + id).c_str(), state.selected == id)) state.selected = id;
        }
        ImGui::EndCombo();
    }
    ImGui::InputText(label("Search documentation").c_str(), state.query.data(), state.query.size());
    if (ImGui::Button(label("Open documentation").c_str())) {
        try { launch(module, language, state, state.selected, {}, {}, state.query.data()); }
        catch (const std::exception &e) { state.open_error = e.what(); }
    }
    ImGui::TextWrapped("%s", tr("Language follows Options at launch. In the reader: Ctrl+K searches; browser zoom adjusts text; Escape reduces enlarged images."));
    if (!state.open_error.empty()) ImGui::TextWrapped("%s", tr(state.open_error.c_str()));
}
}
