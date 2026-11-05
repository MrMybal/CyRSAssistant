#include "manual_model.hpp"
#include "manual_data.hpp"
#include <windows.h>
#include <algorithm>
#include <climits>

namespace cyrs::manual {
const nlohmann::json &document(std::string language) {
    static const auto books = [] {
        std::vector<nlohmann::json> result;
        for (const auto &entry : manual_data::documents) {
            std::string encoded;
            for (size_t i = 0; i < entry.count; ++i) encoded += entry.chunks[i];
            result.push_back(nlohmann::json::parse(encoded));
        }
        return result;
    }();
    for (auto &c : language) {
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
        if (c == '_') c = '-';
    }
    for (const auto &book : books) if (book["code"] == language) return book;
    language = language.substr(0, language.find('-'));
    for (const auto &book : books) if (book["code"] == language) return book;
    for (const auto &book : books) if (book["code"] == "en") return book;
    throw std::runtime_error("English manual is missing");
}

std::string fold(std::string_view text) {
    if (text.empty() || text.size() > INT_MAX) return {};
    const int count = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text.data(), static_cast<int>(text.size()), nullptr, 0);
    if (count <= 0) return {};
    std::wstring wide(count, 0);
    MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text.data(), static_cast<int>(text.size()), wide.data(), count);
    const int size = FoldStringW(MAP_COMPOSITE, wide.data(), count, nullptr, 0);
    if (size <= 0) return {};
    std::wstring decomposed(size, 0);
    FoldStringW(MAP_COMPOSITE, wide.data(), count, decomposed.data(), size);
    const int lower_size = LCMapStringEx(LOCALE_NAME_INVARIANT, LCMAP_LOWERCASE, decomposed.data(), size, nullptr, 0, nullptr, nullptr, 0);
    if (lower_size <= 0) return {};
    std::wstring lower(lower_size, 0);
    LCMapStringEx(LOCALE_NAME_INVARIANT, LCMAP_LOWERCASE, decomposed.data(), size, lower.data(), lower_size, nullptr, nullptr, 0);
    lower.erase(std::remove_if(lower.begin(), lower.end(), [](wchar_t c) { return c >= 0x0300 && c <= 0x036f; }), lower.end());
    if (lower.empty()) return {};
    const int bytes = WideCharToMultiByte(CP_UTF8, 0, lower.data(), static_cast<int>(lower.size()), nullptr, 0, nullptr, nullptr);
    std::string result(bytes, 0);
    WideCharToMultiByte(CP_UTF8, 0, lower.data(), static_cast<int>(lower.size()), result.data(), bytes, nullptr, nullptr);
    return result;
}

std::vector<size_t> search(const nlohmann::json &book, std::string_view query) {
    auto needle = fold(query);
    const auto first = needle.find_first_not_of(" \t\r\n");
    needle = first == std::string::npos ? "" : needle.substr(first, needle.find_last_not_of(" \t\r\n") - first + 1);
    std::vector<size_t> results;
    const auto &chapters = book.at("chapters");
    for (size_t i = 0; i < chapters.size(); ++i)
        if (needle.empty() || fold(chapters[i].dump()).find(needle) != std::string::npos) results.push_back(i);
    return results;
}

std::filesystem::path html_path(const std::filesystem::path &addon, const std::string &language) {
    const auto code = document(language).at("code").get<std::string>();
    return addon.parent_path() / L"CyRSAssistant" / L"Documentation" / ("index." + code + ".html");
}
}
