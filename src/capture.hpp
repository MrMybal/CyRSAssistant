#pragma once
#include <reshade.hpp>
#include "protocol.hpp"
#include <algorithm>
#include <cstring>

namespace cyrs {
inline std::string base64(const std::vector<uint8_t> &bytes) {
    static constexpr char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string out;
    out.reserve((bytes.size() + 2) / 3 * 4);
    for (size_t i = 0; i < bytes.size(); i += 3) {
        const uint32_t bits = (uint32_t(bytes[i]) << 16) |
            (i + 1 < bytes.size() ? uint32_t(bytes[i + 1]) << 8 : 0) |
            (i + 2 < bytes.size() ? uint32_t(bytes[i + 2]) : 0);
        out += alphabet[(bits >> 18) & 63]; out += alphabet[(bits >> 12) & 63];
        out += i + 1 < bytes.size() ? alphabet[(bits >> 6) & 63] : '=';
        out += i + 2 < bytes.size() ? alphabet[bits & 63] : '=';
    }
    return out;
}
inline json capture_frame(reshade::api::effect_runtime *runtime) {
    using reshade::api::format;
    uint32_t width = 0, height = 0;
    runtime->get_screenshot_width_and_height(&width, &height);
    require(width && height && uint64_t(width) * height <= 16777216, "Capture dimensions unsupported (maximum 16 megapixels)");
    const auto desc = runtime->get_device()->get_resource_desc(runtime->get_current_back_buffer());
    const auto pixel_format = reshade::api::format_to_default_typed(desc.texture.format, 0);
    const bool ten = pixel_format == format::r10g10b10a2_unorm || pixel_format == format::b10g10r10a2_unorm;
    const bool bgra = pixel_format == format::b8g8r8a8_unorm || pixel_format == format::b8g8r8x8_unorm || pixel_format == format::b10g10r10a2_unorm;
    require(ten || bgra || pixel_format == format::r8g8b8a8_unorm || pixel_format == format::r8g8b8x8_unorm,
        "Capture supports 8-bit and packed 10-bit buffers; floating-point HDR is not yet supported");
    require(desc.texture.width == width && desc.texture.height == height, "Back buffer dimensions changed");
    std::vector<uint8_t> raw(size_t(width) * height * 4);
    require(runtime->capture_screenshot(raw.data()), "ReShade capture failed");
    const double scale = std::min(1.0, 1280.0 / std::max(width, height));
    const uint32_t out_width = std::max(1u, static_cast<uint32_t>(width * scale));
    const uint32_t out_height = std::max(1u, static_cast<uint32_t>(height * scale));
    std::vector<uint8_t> rgb(size_t(out_width) * out_height * 3);
    for (uint32_t y = 0; y < out_height; ++y) for (uint32_t x = 0; x < out_width; ++x) {
        const auto source = raw.data() + (size_t(y * height / out_height) * width + x * width / out_width) * 4;
        auto target = rgb.data() + (size_t(y) * out_width + x) * 3;
        if (ten) {
            uint32_t packed; std::memcpy(&packed, source, sizeof(packed));
            target[bgra ? 2 : 0] = static_cast<uint8_t>((packed & 1023) * 255 / 1023);
            target[1] = static_cast<uint8_t>(((packed >> 10) & 1023) * 255 / 1023);
            target[bgra ? 0 : 2] = static_cast<uint8_t>(((packed >> 20) & 1023) * 255 / 1023);
        } else {
            target[0] = source[bgra ? 2 : 0]; target[1] = source[1]; target[2] = source[bgra ? 0 : 2];
        }
    }
    return {{"width", out_width}, {"height", out_height}, {"source_width", width}, {"source_height", height},
        {"pixel_format", "rgb8"}, {"encoding", "base64"}, {"data", base64(rgb)},
        {"color_note", "Display values, no HDR tone mapping; not a calibrated color measurement"}};
}
}
