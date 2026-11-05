#include "manual_model.hpp"
#include <stdexcept>
#include <iostream>
#define CHECK(value) do { if (!(value)) throw std::runtime_error(#value); } while (false)
int main() {
    using namespace cyrs::manual;
    const auto &en = document("en");
    const auto &fr = document("FR_fr");
    CHECK(en.at("code") == "en" && fr.at("code") == "fr");
    CHECK(document("../../outside").at("code") == "en");
    CHECK(document("de-DE").at("code") == "en");
    CHECK(en.at("pages").size() == fr.at("pages").size());
    CHECK(en.at("pages").size() >= 26);
    for (const auto &entry : en.at("pages")) {
        const auto *translated = page(fr, entry.at("id").get<std::string>());
        CHECK(translated != nullptr);
        CHECK(entry.at("media") == translated->at("media"));
    }
    CHECK(valid_target(en, "connect", "overview", "connection-preview"));
    CHECK(valid_target(fr, "chat", "overview", "chat-preview"));
    CHECK(valid_target(fr, "source-src-manual-cpp", "L1", ""));
    CHECK(!valid_target(en, "connect", "absent", ""));
    CHECK(!valid_target(en, "connect", "", "chat-preview"));
    CHECK(!valid_target(en, "../secret", "", ""));
    const auto addon = std::filesystem::path(L"C:/Games/Été #1/CyRSAssistant.addon64");
    CHECK(html_path(addon, "fr").filename() == "index.html");
    const auto url = help_url(addon, "fr-FR", "connect", "overview", "connection-preview", "bloom & threshold");
    CHECK(url.find(L"file:///C:/Games/") == 0);
    CHECK(url.find(L"%20%231/") != std::wstring::npos);
    CHECK(url.find(L"#/fr/connect/overview?media=connection-preview&q=bloom%20%26%20threshold") != std::wstring::npos);
    CHECK(help_url(addon, "unknown", "start").find(L"#/en/start") != std::wstring::npos);
    for (const std::string query : {std::string(256, 'x'), std::string("bad\0value", 9)}) {
        bool rejected = false;
        try { help_url(addon, "en", "start", "", "", query); } catch (const std::invalid_argument &) { rejected = true; }
        CHECK(rejected);
    }
    std::cout << "CyDoc bilingual targets, anchors, media, fallback and encoded local routes passed\n";
}
