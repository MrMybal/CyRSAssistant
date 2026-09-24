#pragma once
#include <reshade.hpp>
#include "protocol.hpp"

namespace cyrs::shader_lab {
void register_events();
void unregister_events();
json inventory(reshade::api::device *device);
json inspect(reshade::api::device *device, const std::string &hash);
json replace(reshade::api::device *device, const std::string &hash, const std::string &source);
void enable(reshade::api::device *device, const std::string &hash, bool enabled);
void restore_all(reshade::api::device *device);
}
