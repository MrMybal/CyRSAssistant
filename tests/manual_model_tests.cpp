#include "manual_model.hpp"
#include <stdexcept>
#define CHECK(value) do { if (!(value)) throw std::runtime_error(#value); } while (false)
#include <iostream>

int main() {
    using namespace cyrs::manual;
    const auto &en = document("en");
    const auto &fr = document("FR_fr");
    CHECK(en.at("code") == "en" && fr.at("code") == "fr");
    CHECK(document("../../elsewhere").at("code") == "en");
    CHECK(document("de-DE").at("code") == "en");
    CHECK(en.at("chapters").size() == 21);
    CHECK(en.at("chapters").size() == fr.at("chapters").size());
    for (size_t i = 0; i < en.at("chapters").size(); ++i)
        CHECK(en.at("chapters")[i].at("id") == fr.at("chapters")[i].at("id"));
    CHECK(fold("ÉCRAN, Génération") == "ecran, generation");
    CHECK(search(fr, "  GENERATION  ") == search(fr, "génération"));
    CHECK(!search(fr, "précompil").empty());
    CHECK(!search(en, "THRESHOLD").empty());
    CHECK(search(en, "").size() == 21);
    CHECK(search(en, "unfindable_92701").empty());
    const auto addon = std::filesystem::path(L"C:/Games/Example/CyRSAssistant.addon64");
    CHECK(html_path(addon, "fr-FR") == addon.parent_path() / "CyRSAssistant/Documentation/index.fr.html");
    CHECK(html_path(addon, "../../private") == addon.parent_path() / "CyRSAssistant/Documentation/index.en.html");
    CHECK(html_path(addon, "en").filename() == "index.en.html");
    std::cout << "Manual language fallback, chapter parity, accent-insensitive search and bounded offline paths passed\n";
}
