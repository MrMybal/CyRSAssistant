#pragma once
#include <reshade.hpp>

namespace cyrs {
// Each effect runtime owns a separate view on its graphics device.
struct Branding {
    reshade::api::resource texture{};
    reshade::api::resource_view view{};
    bool create(reshade::api::effect_runtime *runtime, HMODULE module);
    void destroy(reshade::api::effect_runtime *runtime);
};
}
