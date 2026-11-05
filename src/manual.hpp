#pragma once
#include <reshade.hpp>
#include <array>
#include <string>

namespace cyrs::manual {
struct State {
    std::array<char, 256> query{};
    std::string selected = "start", anchor, media, open_error;
    std::string last_url;
    bool launched = false;
};
void launch(HMODULE module, const std::string &language, State &state, const std::string &chapter,
            const std::string &anchor = {}, const std::string &media = {}, const std::string &query = {});
void draw(HMODULE module, const std::string &language, State &state);
}
