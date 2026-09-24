#pragma once
#include "localization_data.hpp"
#include <algorithm>
#include <cstring>
#include <string>
#include <string_view>

namespace cyrs::i18n {
inline const Language *find_language(std::string_view code) {
    for (const auto &language : languages) if (code == language.code) return &language;
    return nullptr;
}
inline std::string normalize(std::string code) {
    for (auto &c : code) {
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c + 'a' - 'A');
        if (c == '_') c = '-';
    }
    if (find_language(code)) return code;
    code.resize(code.find('-') == std::string::npos ? code.size() : code.find('-'));
    return find_language(code) ? code : "en";
}
inline const char *language_name(const std::string &code) {
    return find_language(normalize(code))->name;
}
inline const char *translate(const std::string &code, const char *key) {
    const auto *language = find_language(normalize(code));
    const auto *end = language->messages + language->count;
    const auto *entry = std::lower_bound(language->messages, end, std::string_view(key),
        [](const Translation &a, std::string_view b) { return std::string_view(a.key) < b; });
    return entry != end && std::strcmp(entry->key, key) == 0 ? entry->value : key;
}
inline std::string label(const std::string &code, const char *key) {
    // Keep widget state and focus stable when its visible label changes language.
    return std::string(translate(code, key)) + "###cyrs_" + key;
}
}
