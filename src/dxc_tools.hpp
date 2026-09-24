#pragma once
#include "shader_tools.hpp"
namespace cyrs::dxc_tools {
std::vector<uint8_t> compile(const std::string &source, const std::string &profile);
json reflect(const std::vector<uint8_t> &code);
std::string disassemble(const std::vector<uint8_t> &code);
}
