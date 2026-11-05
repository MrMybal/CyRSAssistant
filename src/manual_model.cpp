#include "manual_model.hpp"
#include "manual_data.hpp"
#include <windows.h>
#include <shlwapi.h>
#include <algorithm>
#include <stdexcept>
#include <vector>

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
    throw std::runtime_error("English CyDoc catalog is missing");
}

const nlohmann::json *page(const nlohmann::json &book, std::string_view id) {
    for (const auto &entry : book.at("pages")) if (entry.at("id").get_ref<const std::string &>() == id) return &entry;
    return nullptr;
}
bool valid_target(const nlohmann::json &book, const std::string &id, const std::string &anchor, const std::string &media) {
    const auto *target = page(book, id);
    if (!target) return false;
    if (!anchor.empty()) {
        bool found = false;
        for (const auto &heading : target->at("headings")) if (heading.at("id") == anchor) found = true;
        for (const auto &item : target->value("anchors", nlohmann::json::array())) if (item == anchor) found = true;
        if (!found) return false;
    }
    if (!media.empty() && std::find(target->at("media").begin(), target->at("media").end(), media) == target->at("media").end()) return false;
    return true;
}
std::filesystem::path html_path(const std::filesystem::path &addon, const std::string &) {
    return addon.parent_path() / L"CyRSAssistant" / L"Documentation" / L"index.html";
}
namespace {
std::string encode(std::string_view value) {
    constexpr char hex[] = "0123456789ABCDEF";
    std::string result;
    for (const unsigned char c : value)
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.' || c == '~') result += static_cast<char>(c);
        else { result += '%'; result += hex[c >> 4]; result += hex[c & 15]; }
    return result;
}
}
std::wstring help_url(const std::filesystem::path &addon, const std::string &language, const std::string &id,
                      const std::string &anchor, const std::string &media, const std::string &query) {
    const auto &book = document(language);
    if (!valid_target(book, id, anchor, media) || query.size() > 255 || query.find('\0') != std::string::npos)
        throw std::invalid_argument("Unknown CyDoc page, section, media or invalid search");
    const auto path = html_path(addon);
    std::vector<wchar_t> buffer(32768);
    DWORD count = static_cast<DWORD>(buffer.size());
    if (FAILED(UrlCreateFromPathW(path.c_str(), buffer.data(), &count, 0)))
        throw std::runtime_error("Cannot encode the local documentation file URL");
    std::wstring url(buffer.data());
    std::string route = "#/" + encode(book.at("code").get<std::string>()) + "/" + encode(id);
    if (!anchor.empty()) route += "/" + encode(anchor);
    bool first = true;
    const auto add = [&](const char *key, const std::string &value) {
        if (!value.empty()) { route += first ? '?' : '&'; first = false; route += key; route += "=" + encode(value); }
    };
    add("media", media);
    add("q", query);
    url.append(route.begin(), route.end()); // Route is ASCII after UTF-8 percent encoding.
    return url;
}
}
