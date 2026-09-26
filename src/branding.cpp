#include "branding.hpp"
#include "resources.h"

namespace cyrs {
bool Branding::create(reshade::api::effect_runtime *runtime, HMODULE module) {
    using namespace reshade::api;
    if (view.handle) return true;
    const auto info = FindResourceW(module, MAKEINTRESOURCEW(IDR_CYRS_LOGO), MAKEINTRESOURCEW(10)); // RT_RCDATA
    constexpr uint32_t pitch = CYRS_LOGO_SIZE * 4;
    constexpr uint32_t bytes = pitch * CYRS_LOGO_SIZE;
    if (!info || SizeofResource(module, info) != bytes) return false;
    const auto loaded = LoadResource(module, info);
    if (!loaded) return false;
    const auto pixels = LockResource(loaded);
    if (!pixels) return false;
    const subresource_data data{pixels, pitch, bytes};
    auto *device = runtime->get_device();
    const resource_desc desc(CYRS_LOGO_SIZE, CYRS_LOGO_SIZE, 1, 1, format::r8g8b8a8_unorm,
        1, memory_heap::default_, resource_usage::shader_resource | resource_usage::copy_dest);
    if (!device->create_resource(desc, &data, resource_usage::shader_resource, &texture)) return false;
    if (!device->create_resource_view(texture, resource_usage::shader_resource,
            resource_view_desc(format::r8g8b8a8_unorm), &view)) {
        runtime->get_command_queue()->wait_idle();
        device->destroy_resource(texture);
        texture = {};
        return false;
    }
    return true;
}

void Branding::destroy(reshade::api::effect_runtime *runtime) {
    if (!texture.handle && !view.handle) return;
    // ReShade can still have a previously rendered overlay in flight, especially on DX12.
    runtime->get_command_queue()->wait_idle();
    auto *device = runtime->get_device();
    if (view.handle) device->destroy_resource_view(view);
    if (texture.handle) device->destroy_resource(texture);
    view = {}; texture = {};
}
}
