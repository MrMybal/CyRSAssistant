#pragma once
#include <filesystem>
#include <string>
#include <string_view>
#include <vector>
#include <nlohmann/json.hpp>

namespace cyrs::manual {
const nlohmann::json &document(std::string language);
std::string fold(std::string_view text);
std::vector<size_t> search(const nlohmann::json &book, std::string_view query);
std::filesystem::path html_path(const std::filesystem::path &addon, const std::string &language);
}
