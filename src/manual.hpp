#pragma once
#include <reshade.hpp>
#include <array>
#include <map>
#include <string>
#include <vector>

namespace cyrs::manual {
struct Image {
    reshade::api::resource texture{};
    reshade::api::resource_view view{};
    uint32_t width = 0, height = 0;
    bool attempted = false;
};
struct State {
    std::array<char, 256> query{};
    std::string selected = "start", last_query, last_language, open_error;
    std::string enlarged;
    std::vector<size_t> matches;
    bool rebuild = true, scroll_top = false, window_open = false;
    uint64_t draws = 0;
    float text_scale = 1.0f;
    std::map<std::string, Image> images;
    void destroy(reshade::api::effect_runtime *runtime);
};
void draw(reshade::api::effect_runtime *runtime, HMODULE module, const std::string &language, State &state);
}
