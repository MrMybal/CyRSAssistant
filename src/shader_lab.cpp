#include "shader_lab.hpp"
#include "shader_tools.hpp"
#include "pipeline_snapshot.hpp"
#include <map>
#include <mutex>
#include <memory>

namespace cyrs::shader_lab {
using namespace reshade::api;
namespace {
struct Shader {
    std::string hash;
    std::vector<uint8_t> code;
    pipeline replacement{};
    bool enabled = false;
    std::vector<uint8_t> replacement_code;
    std::string error;
    uint64_t binds = 0, replacements = 0;
};
struct TrackedPipeline {
    std::string hash, error;
    std::shared_ptr<PipelineSnapshot> snapshot;
    pipeline replacement{};
};
struct Device {
    std::map<std::string, Shader> shaders;
    std::map<uint64_t, TrackedPipeline> handles;
    std::vector<pipeline> owned;
    size_t bytes = 0, dropped = 0, pipeline_bytes = 0;
};
std::recursive_mutex mutex;
std::map<device *, Device> devices;
thread_local bool internal = false;
struct Guard { bool before = internal; Guard() { internal = true; } ~Guard() { internal = before; } };
pipeline build_variant(device *dev, const PipelineSnapshot &snapshot, const std::vector<uint8_t> &code) {
    shader_desc desc{}; desc.code = code.data(); desc.code_size = code.size();
    auto objects = snapshot.variant(desc);
    pipeline result{}; Guard guard;
    require(dev->create_pipeline(snapshot.layout, static_cast<uint32_t>(objects.size()), objects.data(), &result), "GPU refused the reconstructed DX12 graphics pipeline");
    return result;
}
void init_pipeline(device *dev, pipeline_layout layout, uint32_t count, const pipeline_subobject *objects, pipeline handle) {
    if (internal || (dev->get_api() != device_api::d3d11 && dev->get_api() != device_api::d3d12)) return;
    try {
        for (uint32_t i = 0; i < count; ++i) {
            if (objects[i].type != pipeline_subobject_type::pixel_shader || objects[i].count != 1 || !objects[i].data) continue;
            const auto &desc = *static_cast<const shader_desc *>(objects[i].data);
            if (!desc.code || !desc.code_size || desc.code_size > 1024 * 1024) continue;
            const auto *data = static_cast<const uint8_t *>(desc.code);
            std::vector<uint8_t> code(data, data + desc.code_size);
            auto hash = shader_tools::hash(code);
            std::lock_guard<std::recursive_mutex> lock(mutex);
            auto &state = devices[dev];
            if (!state.shaders.count(hash)) {
                if (state.shaders.size() >= 4096 || state.bytes + code.size() > 64 * 1024 * 1024) { ++state.dropped; continue; }
                Shader shader; shader.hash = hash; shader.code = std::move(code);
                state.bytes += shader.code.size(); state.shaders.emplace(hash, std::move(shader));
            }
            if (state.handles.count(handle.handle)) continue; // ReShade may report AddRef as init.
            TrackedPipeline tracked; tracked.hash = hash;
            auto &shader = state.shaders.at(hash);
            if (dev->get_api() == device_api::d3d12) {
                try {
                    require(layout.handle != 0, "DX12 pipeline root signature is unavailable");
                    auto captured = std::make_shared<PipelineSnapshot>(count, objects, layout);
                    require(state.handles.size() < 4096 && state.pipeline_bytes + captured->bytes <= 128 * 1024 * 1024, "DX12 pipeline capture budget reached");
                    auto root = reinterpret_cast<IUnknown *>(layout.handle);
                    root->AddRef(); captured->root_signature = std::shared_ptr<IUnknown>(root, [](IUnknown *p) { p->Release(); });
                    if (shader.enabled) {
                        require(state.owned.size() < 256, "DX12 pipeline version limit reached");
                        state.owned.reserve(256);
                        tracked.replacement = build_variant(dev, *captured, shader.replacement_code);
                        state.owned.push_back(tracked.replacement);
                    }
                    state.pipeline_bytes += captured->bytes; tracked.snapshot = std::move(captured);
                } catch (const std::exception &e) {
                    tracked.error = e.what();
                    // A new uncloneable PSO must not create an unnoticed partial replacement.
                    if (shader.enabled) { shader.enabled = false; shader.error = tracked.error; }
                }
            }
            state.handles.emplace(handle.handle, std::move(tracked));
        }
    } catch (...) { /* Never propagate inspection failure into the game's shader creation. */ }
}
void destroy_pipeline(device *dev, pipeline handle) {
    if (internal) return;
    std::lock_guard<std::recursive_mutex> lock(mutex);
    const auto it = devices.find(dev);
    if (it != devices.end()) {
        auto &state = it->second;
        auto entry = state.handles.find(handle.handle);
        if (entry != state.handles.end()) {
            if (entry->second.snapshot) state.pipeline_bytes -= entry->second.snapshot->bytes;
            state.handles.erase(entry);
        }
    }
}
void bind_pipeline(command_list *cmd, pipeline_stage stages, pipeline handle) {
    if (internal || static_cast<uint32_t>(stages & pipeline_stage::pixel_shader) == 0) return;
    std::lock_guard<std::recursive_mutex> lock(mutex);
    const auto device_it = devices.find(cmd->get_device());
    if (device_it == devices.end()) return;
    auto &state = device_it->second;
    const auto it = state.handles.find(handle.handle);
    if (it == state.handles.end()) return;
    auto &shader = state.shaders.at(it->second.hash); ++shader.binds;
    const bool dx12 = cmd->get_device()->get_api() == device_api::d3d12;
    auto replacement = dx12 ? it->second.replacement : shader.replacement;
    if (shader.enabled && replacement.handle) {
        Guard guard;
        cmd->bind_pipeline(dx12 ? pipeline_stage::all_graphics : pipeline_stage::pixel_shader, replacement);
        ++shader.replacements;
    }
}
void destroy_device(device *dev) {
    std::lock_guard<std::recursive_mutex> lock(mutex);
    auto it = devices.find(dev);
    if (it == devices.end()) return;
    Guard guard;
    for (auto pipeline : it->second.owned) dev->destroy_pipeline(pipeline);
    devices.erase(it);
}
Shader &find(device *dev, const std::string &hash) {
    require(dev->get_api() == device_api::d3d11 || dev->get_api() == device_api::d3d12, "Game shader replacement requires Direct3D 11 or 12");
    auto it = devices.find(dev);
    require(it != devices.end() && it->second.shaders.count(hash), "Unknown game shader hash; inspect the current session");
    return it->second.shaders.at(hash);
}
}
json inventory(device *dev) {
    std::lock_guard<std::recursive_mutex> lock(mutex);
    json result = {{"supported", dev->get_api() == device_api::d3d11 || dev->get_api() == device_api::d3d12}, {"api", dev->get_api() == device_api::d3d12 ? "D3D12" : dev->get_api() == device_api::d3d11 ? "D3D11" : "unsupported"}, {"scope", "DX11/DX12 pixel shaders (DXBC 5.0 and DXIL 6.x)"}, {"shaders", json::array()}, {"dropped", 0}};
    auto it = devices.find(dev);
    if (it == devices.end()) return result;
    result["dropped"] = it->second.dropped;
    for (const auto &pair : it->second.shaders) {
        const auto &s = pair.second;
        size_t pipelines = 0, replaceable = 0;
        std::string limitation;
        for (const auto &p : it->second.handles) if (p.second.hash == s.hash) {
            ++pipelines;
            if (dev->get_api() == device_api::d3d11 || p.second.snapshot) ++replaceable;
            else limitation = p.second.error;
        }
        result["shaders"].push_back({{"hash", s.hash}, {"bytes", s.code.size()}, {"binds", s.binds}, {"replacement_binds", s.replacements}, {"enabled", s.enabled}, {"has_replacement", !s.replacement_code.empty()}, {"pipelines", pipelines}, {"replaceable_pipelines", replaceable}, {"limitation", limitation}, {"error", s.error}, {"encoding", shader_tools::is_dxil(s.code) ? "DXIL" : "DXBC"}});
    }
    return result;
}
json inspect(device *dev, const std::string &hash) {
    std::lock_guard<std::recursive_mutex> lock(mutex);
    const auto &s = find(dev, hash);
    auto reflection = shader_tools::reflect(s.code);
    return {{"hash", hash}, {"stage", reflection["profile"]}, {"api", dev->get_api() == device_api::d3d12 ? "D3D12" : "D3D11"}, {"reflection", reflection}, {"assembly", shader_tools::disassemble(s.code)}};
}
json replace(device *dev, const std::string &hash, const std::string &source) {
    std::lock_guard<std::recursive_mutex> lock(mutex);
    auto &s = find(dev, hash);
    const auto original = shader_tools::reflect(s.code);
    auto bytecode = shader_tools::compile(source, original.at("profile"));
    shader_tools::compatible(original, shader_tools::reflect(bytecode));
    auto &state = devices.at(dev);
    Guard guard;
    size_t rebuilt = 1;
    if (dev->get_api() == device_api::d3d12) {
        std::vector<TrackedPipeline *> targets;
        for (auto &p : state.handles) if (p.second.hash == hash) {
            require(bool(p.second.snapshot), p.second.error.c_str()); targets.push_back(&p.second);
        }
        require(!targets.empty(), "No live DX12 pipeline uses this shader");
        require(state.owned.size() + targets.size() <= 256, "DX12 pipeline version limit reached; restart before creating more");
        state.owned.reserve(256);
        std::vector<pipeline> pending; pending.reserve(targets.size());
        try { for (const auto target : targets) pending.push_back(build_variant(dev, *target->snapshot, bytecode)); }
        catch (...) { for (auto p : pending) dev->destroy_pipeline(p); throw; }
        // Commit only after ALL live PSOs rebuilt successfully. Previously recorded
        // command lists can still reference older versions, so retain them until teardown.
        for (size_t i = 0; i < pending.size(); ++i) { targets[i]->replacement = pending[i]; state.owned.push_back(pending[i]); }
        rebuilt = targets.size();
    } else {
        require(state.owned.size() < 64, "64 shader versions reached; restart the game before creating more");
        state.owned.reserve(64);
        shader_desc desc{}; desc.code = bytecode.data(); desc.code_size = bytecode.size();
        pipeline_subobject object{pipeline_subobject_type::pixel_shader, 1, &desc};
        pipeline replacement{};
        require(dev->create_pipeline({}, 1, &object, &replacement), "The GPU refused the replacement shader");
        state.owned.push_back(replacement); s.replacement = replacement;
    }
    const auto replacement_hash = shader_tools::hash(bytecode);
    s.replacement_code = std::move(bytecode); s.enabled = true; s.error.clear();
    return {{"hash", hash}, {"replacement_hash", replacement_hash}, {"enabled", true}, {"rebuilt_pipelines", rebuilt}, {"activation", "next_game_bind"}};
}
void enable(device *dev, const std::string &hash, bool enabled) {
    std::lock_guard<std::recursive_mutex> lock(mutex);
    auto &s = find(dev, hash);
    require(!enabled || !s.replacement_code.empty(), "No compiled replacement for this shader");
    if (enabled && dev->get_api() == device_api::d3d12) {
        for (const auto &p : devices.at(dev).handles) if (p.second.hash == hash)
            require(p.second.replacement.handle != 0, "Some DX12 pipelines lack a replacement; compile again before enabling");
    }
    s.enabled = enabled;
}
void restore_all(device *dev) {
    std::lock_guard<std::recursive_mutex> lock(mutex);
    auto it = devices.find(dev);
    if (it != devices.end()) for (auto &pair : it->second.shaders) pair.second.enabled = false;
}
void register_events() {
    reshade::register_event<reshade::addon_event::init_pipeline>(init_pipeline);
    reshade::register_event<reshade::addon_event::destroy_pipeline>(destroy_pipeline);
    reshade::register_event<reshade::addon_event::bind_pipeline>(bind_pipeline);
    reshade::register_event<reshade::addon_event::destroy_device>(destroy_device);
}
void unregister_events() {
    reshade::unregister_event<reshade::addon_event::init_pipeline>(init_pipeline);
    reshade::unregister_event<reshade::addon_event::destroy_pipeline>(destroy_pipeline);
    reshade::unregister_event<reshade::addon_event::bind_pipeline>(bind_pipeline);
    reshade::unregister_event<reshade::addon_event::destroy_device>(destroy_device);
    std::lock_guard<std::recursive_mutex> lock(mutex);
    while (!devices.empty()) destroy_device(devices.begin()->first);
}
}
