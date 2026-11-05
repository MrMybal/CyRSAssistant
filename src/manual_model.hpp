#pragma once
#include <filesystem>
#include <string>
#include <string_view>
#include <nlohmann/json.hpp>

namespace cyrs::manual {
const nlohmann::json &document(std::string language);
const nlohmann::json *page(const nlohmann::json &book, std::string_view id);
bool valid_target(const nlohmann::json &book, const std::string &id, const std::string &anchor, const std::string &media);
std::filesystem::path html_path(const std::filesystem::path &addon, const std::string &language = "en");
std::wstring help_url(const std::filesystem::path &addon, const std::string &language, const std::string &id,
                      const std::string &anchor = {}, const std::string &media = {}, const std::string &query = {});
}
