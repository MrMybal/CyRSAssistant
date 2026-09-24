#include "localization.hpp"
#include <iostream>
#include <stdexcept>
using namespace cyrs;
int main() {
    try {
        auto check = [](bool value) { if (!value) throw std::runtime_error("Localization check failed"); };
        check(i18n::normalize("") == "en");
        check(i18n::normalize("unknown") == "en");
        check(i18n::normalize("FR_fr") == "fr");
        check(std::string(i18n::translate("en", "Send")) == "Send");
        check(std::string(i18n::translate("fr", "Send")) == "Envoyer");
        check(std::string(i18n::translate("fr", "API key")) == "Clé API");
        check(std::string(i18n::translate("fr", "Untranslated compiler diagnostic")) == "Untranslated compiler diagnostic");
        const auto en = i18n::label("en", "Send"), fr = i18n::label("fr", "Send");
        check(en.substr(en.find("###")) == fr.substr(fr.find("###")));
        for (const auto &language : i18n::languages)
            for (size_t i = 0; i < language.count; ++i)
                check(std::string(i18n::translate(language.code, language.messages[i].key)) == language.messages[i].value);
        std::cout << "Catalog lookup, fallback, accents and stable widget IDs passed\n";
        return 0;
    } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
