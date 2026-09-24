#pragma once
#include "protocol.hpp"
#include <vector>
#include <string>

namespace cyrs::shader_tools {
std::vector<uint8_t> compile(const std::string &source, const std::string &profile = "ps_5_0");
bool is_dxil(const std::vector<uint8_t> &code);
json reflect(const std::vector<uint8_t> &code);
std::string disassemble(const std::vector<uint8_t> &code);
std::string hash(const std::vector<uint8_t> &code);
void compatible(const json &original, const json &replacement);
std::string generated_fx(const std::string &body, const json &parameters = json::array(), const std::string &title = "Generated effect");
}
