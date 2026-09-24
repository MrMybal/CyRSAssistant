#include <imgui.h>
#include <reshade.hpp>
#include "bridge.hpp"
#include "capture.hpp"
#include "shader_lab.hpp"
#include "shader_tools.hpp"
#include "permissions.hpp"
#include "localization.hpp"
#include <fstream>
#include <cstdio>
#include <regex>
#include <algorithm>
#include <array>
#include <map>
#include <mutex>
#include <random>
#include <filesystem>

extern "C" __declspec(dllexport) const char *NAME = "CyRSAssistant";
extern "C" __declspec(dllexport) const char *DESCRIPTION = "CyRSAssistant 0.7.0 - Cyberalien - Live shader assistant.";

namespace {
using namespace cyrs;
using namespace reshade::api;
#include "connection.hpp"
struct Parameter { effect_uniform_variable handle; json metadata; size_t count = 0; };
struct Technique { effect_technique handle; json metadata; };
struct Runtime {
    uint64_t id = 0, generation = 0, revision = 0, prompt_id = 0, scan_id = 0;
    std::vector<Parameter> parameters;
    std::vector<Technique> techniques;
    json undo = json::array(), applied = json::array();
    std::string preset, prompt, answer, status = "Ready", filter;
    std::string language = "en";
    std::array<char, 4096> input{};
    std::array<char, 256> search{};
    bool pending = false, loading = false;
    json conversation = json::array();
    bool chat_scroll = false;
    ULONGLONG prompt_started = 0;
    Connection connection;
    Permissions permissions;
    int prompt_mode = 3;
    std::string selected_hash, generated_file, generated_phase = "none", generated_message;
    uint64_t generated_prompt = 0;
    ULONGLONG generated_started = 0;
    bool generated_wait = false;
    json game_shaders = json::object();
    std::string inspected_hash, shader_inspection, generated_replaces, progress;
    json generated_previous = json::array();
};
std::recursive_mutex runtime_mutex;
std::map<effect_runtime *, Runtime> runtimes;
uint64_t next_runtime = 1;
std::string session;
Bridge bridge;

void chat_message(Runtime &state, const char *role, const std::string &text) {
    state.conversation.push_back({{"role", role}, {"content", text}, {"mode", state.prompt_mode}});
    while (state.conversation.size() > 32) state.conversation.erase(state.conversation.begin());
    state.chat_scroll = true;
}

void cancel_prompt(Runtime &state) {
    if (state.pending) chat_message(state, "system", i18n::translate(state.language, "Request cancelled. Changes already applied remain active; use the restore controls if needed."));
    state.pending = false;
    state.permissions.invalidate();
    ++state.prompt_id;
}

template<class F> std::string api_string(F read) {
    size_t size = 0;
    read(nullptr, &size);
    if (!size || size > 1024 * 1024) return {};
    std::string value(size, '\0');
    read(value.data(), &size);
    value.resize(std::char_traits<char>::length(value.c_str()));
    return value;
}
std::string annotation(effect_runtime *runtime, effect_uniform_variable handle, const char *name) {
    return api_string([&](char *data, size_t *size) { runtime->get_annotation_string_from_uniform_variable(handle, name, data, size); });
}
json read_value(effect_runtime *runtime, const Parameter &parameter) {
    json result = json::array();
    const auto &type = parameter.metadata.at("type");
    const auto n = parameter.count;
    if (!n) return result;
    if (type == "float") {
        std::array<float, 64> values{};
        runtime->get_uniform_value_float(parameter.handle, values.data(), n);
        for (size_t i = 0; i < n; ++i) result.push_back(std::isfinite(values[i]) ? json(values[i]) : json(nullptr));
    } else if (type == "int") {
        std::array<int32_t, 64> values{};
        runtime->get_uniform_value_int(parameter.handle, values.data(), n);
        for (size_t i = 0; i < n; ++i) result.push_back(values[i]);
    } else if (type == "uint") {
        std::array<uint32_t, 64> values{};
        runtime->get_uniform_value_uint(parameter.handle, values.data(), n);
        for (size_t i = 0; i < n; ++i) result.push_back(values[i]);
    } else {
        std::array<bool, 64> values{};
        runtime->get_uniform_value_bool(parameter.handle, values.data(), n);
        for (size_t i = 0; i < n; ++i) result.push_back(values[i]);
    }
    return result;
}
void scan(effect_runtime *runtime, Runtime &state, bool preserve_if_same_handles = false) {
    const auto previous_parameters = state.parameters;
    const auto previous_techniques = state.techniques;
    const auto previous_undo = state.undo, previous_applied = state.applied;
    ++state.generation;
    ++state.revision;
    state.parameters.clear(); state.techniques.clear();
    state.undo.clear(); state.applied.clear();
    runtime->enumerate_uniform_variables(nullptr, [&](effect_runtime *, effect_uniform_variable handle) {
        Parameter parameter{};
        parameter.handle = handle;
        format type{}; uint32_t rows = 0, columns = 0, length = 0;
        runtime->get_uniform_variable_type(handle, &type, &rows, &columns, &length);
        const uint64_t count = uint64_t(rows) * columns * std::max(1u, length);
        const bool supported = type == format::r32_float || type == format::r32_sint || type == format::r32_uint || type == format::r32_typeless;
        parameter.count = supported && count <= 64 ? static_cast<size_t>(count) : 0;
        auto &item = parameter.metadata;
        item = {{"id", state.parameters.size()},
            {"name", api_string([&](char *v, size_t *n) { runtime->get_uniform_variable_name(handle, v, n); })},
            {"effect", api_string([&](char *v, size_t *n) { runtime->get_uniform_variable_effect_name(handle, v, n); })},
            {"type", type == format::r32_float ? "float" : type == format::r32_sint ? "int" : type == format::r32_uint ? "uint" : "bool"},
            {"rows", rows}, {"columns", columns}, {"array_length", length},
            {"label", annotation(runtime, handle, "ui_label")}, {"description", annotation(runtime, handle, "ui_tooltip")},
            {"source", annotation(runtime, handle, "source")}};
        item["readonly"] = parameter.count == 0 || !item["source"].get<std::string>().empty();
        if (type == format::r32_float) {
            float bound;
            if (runtime->get_annotation_float_from_uniform_variable(handle, "ui_min", &bound, 1) && std::isfinite(bound)) item["min"] = bound;
            if (runtime->get_annotation_float_from_uniform_variable(handle, "ui_max", &bound, 1) && std::isfinite(bound)) item["max"] = bound;
        } else if (type == format::r32_sint) {
            int32_t bound;
            if (runtime->get_annotation_int_from_uniform_variable(handle, "ui_min", &bound, 1)) item["min"] = bound;
            if (runtime->get_annotation_int_from_uniform_variable(handle, "ui_max", &bound, 1)) item["max"] = bound;
        } else if (type == format::r32_uint) {
            uint32_t bound;
            if (runtime->get_annotation_uint_from_uniform_variable(handle, "ui_min", &bound, 1)) item["min"] = bound;
            if (runtime->get_annotation_uint_from_uniform_variable(handle, "ui_max", &bound, 1)) item["max"] = bound;
        }
        item["value"] = read_value(runtime, parameter);
        for (const auto &v : item["value"]) if (v.is_null()) item["readonly"] = true;
        state.parameters.push_back(std::move(parameter));
    });
    runtime->enumerate_techniques(nullptr, [&](effect_runtime *, effect_technique handle) {
        bool enabled = false;
        bool forced = runtime->get_annotation_bool_from_technique(handle, "enabled", &enabled, 1) && enabled;
        state.techniques.push_back({handle, {{"id", state.techniques.size()},
            {"name", api_string([&](char *v, size_t *n) { runtime->get_technique_name(handle, v, n); })},
            {"effect", api_string([&](char *v, size_t *n) { runtime->get_technique_effect_name(handle, v, n); })},
            {"value", runtime->get_technique_state(handle)}, {"readonly", forced}}});
    });
    state.preset = api_string([&](char *v, size_t *n) { runtime->get_current_preset_path(v, n); });
    bool same = preserve_if_same_handles && previous_parameters.size() == state.parameters.size() && previous_techniques.size() == state.techniques.size();
    if (same) {
        for (size_t i = 0; i < state.parameters.size(); ++i)
            if (previous_parameters[i].handle != state.parameters[i].handle || previous_parameters[i].metadata["name"] != state.parameters[i].metadata["name"] || previous_parameters[i].metadata["effect"] != state.parameters[i].metadata["effect"]) same = false;
        for (size_t i = 0; i < state.techniques.size(); ++i)
            if (previous_techniques[i].handle != state.techniques[i].handle || previous_techniques[i].metadata["name"] != state.techniques[i].metadata["name"] || previous_techniques[i].metadata["effect"] != state.techniques[i].metadata["effect"]) same = false;
    }
    if (same) { state.undo = previous_undo; state.applied = previous_applied; }
    state.loading = false;
    state.status = "Effects scanned. Undo cleared after inventory refresh.";
    if (same && !state.undo.empty()) state.status = "Effect initialized. Previous edit can still be undone.";
}
void refresh(effect_runtime *runtime, Runtime &state, bool check_handles = true) {
    // Public getters dereference handles directly. Enumeration is empty while ReShade
    // compiles, so discard old handles before reading values during a manual reload.
    if (check_handles) {
    std::vector<uint64_t> live_parameters, live_techniques;
    runtime->enumerate_uniform_variables(nullptr, [&](effect_runtime *, effect_uniform_variable h) { live_parameters.push_back(h.handle); });
    runtime->enumerate_techniques(nullptr, [&](effect_runtime *, effect_technique h) { live_techniques.push_back(h.handle); });
    if (live_parameters.empty() && live_techniques.empty() && (!state.parameters.empty() || !state.techniques.empty())) {
        state.loading = true;
        return; // Lazy GPU initialization also makes enumeration temporarily empty.
    }
    state.loading = false;
    bool handles_changed = live_parameters.size() != state.parameters.size() || live_techniques.size() != state.techniques.size();
    if (!handles_changed) {
        for (size_t i = 0; i < live_parameters.size(); ++i) if (live_parameters[i] != state.parameters[i].handle.handle) handles_changed = true;
        for (size_t i = 0; i < live_techniques.size(); ++i) if (live_techniques[i] != state.techniques[i].handle.handle) handles_changed = true;
    }
    if (handles_changed) scan(runtime, state);
    }
    bool changed = false;
    const auto preset = api_string([&](char *v, size_t *n) { runtime->get_current_preset_path(v, n); });
    if (preset != state.preset) {
        state.preset = preset; state.undo.clear(); state.applied.clear(); changed = true;
    }
    for (auto &p : state.parameters) {
        auto value = read_value(runtime, p);
        if (!p.metadata["readonly"].get<bool>() && value != p.metadata["value"]) changed = true;
        p.metadata["value"] = std::move(value);
    }
    for (auto &t : state.techniques) {
        const bool value = runtime->get_technique_state(t.handle);
        if (t.metadata["value"] != value) changed = true;
        t.metadata["value"] = value;
    }
    if (changed) ++state.revision;
}
json snapshot(effect_runtime *runtime, Runtime &state) {
    refresh(runtime, state);
    json result = {{"session", session}, {"runtime", state.id}, {"generation", state.generation}, {"revision", state.revision},
        {"parameters", json::array()}, {"techniques", json::array()}, {"preset", state.preset},
        {"pipe", bridge.name()}, {"scan_id", state.scan_id}, {"loading", state.loading}, {"undo_available", !state.undo.empty() && !state.applied.empty()},
        {"prompt", {{"id", state.prompt_id}, {"text", state.prompt}, {"pending", state.pending}, {"mode", state.prompt_mode}, {"shader_hash", state.selected_hash}, {"progress", state.progress}}},
        {"generated", {{"file", state.generated_file}, {"phase", state.generated_phase}, {"message", state.generated_message}, {"replaces", state.generated_replaces}}}};
    const auto &c = state.connection;
    result["language"] = state.language;
    result["conversation"] = state.conversation;
    result["permissions"] = state.permissions.snapshot();
    result["connection"] = {{"provider", c.provider}, {"phase", c.phase}, {"ready", connected(c)}, {"message", c.message}, {"wanted", c.wanted}};
    for (const auto &p : state.parameters) result["parameters"].push_back(p.metadata);
    for (const auto &t : state.techniques) result["techniques"].push_back(t.metadata);
    result["base_path"] = api_string([](char *v, size_t *n) { reshade::get_reshade_base_path(v, n); });
    // ReShade returns configuration arrays separated by embedded NULs.
    for (const auto &entry : {std::pair{"EffectSearchPaths", "search_paths"}, std::pair{"TextureSearchPaths", "texture_paths"}}) {
        size_t size = 0;
        reshade::get_config_value(runtime, "GENERAL", entry.first, nullptr, &size);
        result[entry.second] = json::array();
        if (size > 0 && size < 1024 * 1024) {
            std::vector<char> paths(size + 1, '\0');
            reshade::get_config_value(runtime, "GENERAL", entry.first, paths.data(), &size);
            size_t offset = 0;
            while (offset < size) {
                std::string path(paths.data() + offset);
                offset += path.size() + 1;
                if (!path.empty()) result[entry.second].push_back(path);
            }
        }
    }
    return result;
}
void write_change(effect_runtime *runtime, Runtime &state, const json &change) {
    const size_t id = change.at("id").get<size_t>();
    const auto &value = change.at("value");
    if (change.at("kind") == "technique") { runtime->set_technique_state(state.techniques.at(id).handle, value.get<bool>()); return; }
    const auto &p = state.parameters.at(id);
    const auto &type = p.metadata.at("type");
    if (type == "float") { auto v = value.get<std::vector<float>>(); runtime->set_uniform_value_float(p.handle, v.data(), v.size()); }
    else if (type == "int") { auto v = value.get<std::vector<int32_t>>(); runtime->set_uniform_value_int(p.handle, v.data(), v.size()); }
    else if (type == "uint") { auto v = value.get<std::vector<uint32_t>>(); runtime->set_uniform_value_uint(p.handle, v.data(), v.size()); }
    else { std::array<bool, 64> v{}; for (size_t i = 0; i < value.size(); ++i) v[i] = value[i].get<bool>(); runtime->set_uniform_value_bool(p.handle, v.data(), value.size()); }
}
void apply(effect_runtime *runtime, Runtime &state, const json &request) {
    const auto before = snapshot(runtime, state);
    require(!state.loading, "Effects are initializing; retry after loading completes");
    const auto changes = validate_patch(before, request);
    json undo = json::array();
    for (const auto &c : changes) {
        const auto &items = before.at(c.at("kind") == "parameter" ? "parameters" : "techniques");
        undo.push_back({{"kind", c.at("kind")}, {"id", c.at("id")}, {"value", items[c.at("id").get<size_t>()].at("value")}});
    }
    for (const auto &c : changes) write_change(runtime, state, c);
    refresh(runtime, state, false);
    // A setter can be intercepted by another add-on: check what was actually applied.
    bool matched = true;
    for (const auto &c : changes) {
        const auto id = c.at("id").get<size_t>();
        const auto &actual = c.at("kind") == "parameter" ? state.parameters[id].metadata["value"] : state.techniques[id].metadata["value"];
        if (actual != c.at("value")) matched = false;
    }
    if (!matched) {
        for (const auto &c : undo) write_change(runtime, state, c);
        refresh(runtime, state, false);
        state.undo = undo;
        state.applied.clear();
        throw std::runtime_error("Runtime did not accept all values; rollback attempted. Inspect current state.");
    }
    state.undo = std::move(undo); state.applied = changes;
    ++state.revision;
    state.status = "Changes applied. Undo available; preset not saved yet.";
}
void undo(effect_runtime *runtime, Runtime &state) {
    require(!state.undo.empty() && !state.applied.empty(), "No reversible edit in this generation");
    refresh(runtime, state);
    require(!state.loading, "Effects are initializing; retry after loading completes");
    for (const auto &c : state.applied) {
        const auto id = c.at("id").get<size_t>();
        const auto &actual = c.at("kind") == "parameter" ? state.parameters.at(id).metadata["value"] : state.techniques.at(id).metadata["value"];
        require(actual == c.at("value"), "Edited values changed elsewhere; undo refused");
    }
    for (const auto &c : state.undo) write_change(runtime, state, c);
    refresh(runtime, state, false);
    for (const auto &c : state.undo) {
        const auto id = c.at("id").get<size_t>();
        const auto &actual = c.at("kind") == "parameter" ? state.parameters.at(id).metadata["value"] : state.techniques.at(id).metadata["value"];
        require(actual == c.at("value"), "Undo was intercepted; inspect current state");
    }
    state.undo.clear(); state.applied.clear(); ++state.revision;
    state.status = "Previous values restored in memory. Save explicitly to persist.";
}
void check_version(effect_runtime *runtime, Runtime &state, const json &request) {
    refresh(runtime, state);
    require(!state.loading, "Effects are initializing; retry after loading completes");
    require(request.at("session") == session && request.at("generation") == state.generation && request.at("revision") == state.revision,
        "Stale command; read state again");
}
void start_connection(effect_runtime *runtime, Connection &c, const std::string &language) {
                ++c.epoch; c.wanted = true; c.phase = "connecting"; c.heartbeat = 0; c.started = GetTickCount64();
                c.message = "Starting the local service and checking the provider...";
                reshade::set_config_value(runtime, "CYRSASSISTANT", "Provider", c.provider);
                reshade::set_config_value(runtime, "CYRSASSISTANT", "Endpoint", static_cast<const char *>(c.endpoint.data()));
                reshade::set_config_value(runtime, "CYRSASSISTANT", "Model", static_cast<const char *>(c.model.data()));
                try { launch_companion(bridge.name(), language); }
                catch (const std::exception &e) { c.wanted = false; c.phase = "error"; c.message = e.what(); }
}
void submit_chat(Runtime &state, const std::string &text) {
    require(connected(state.connection), "Connect a provider before sending a message.");
    require(!state.pending, "A response is already in progress.");
    require(text.size() < state.input.size() && text.find('\0') == std::string::npos && text.find_first_not_of(" \t\r\n") != std::string::npos, "The message is empty or too long.");
    state.permissions.invalidate();
    state.progress = "Processing your request..."; state.prompt = text; state.prompt_mode = 3; ++state.prompt_id; state.pending = true; state.answer.clear();
    chat_message(state, "user", state.prompt); state.input.fill(0); state.prompt_started = GetTickCount64();
}
json execute(effect_runtime *runtime, Runtime &state, const json &request) {
    const auto method = request.at("method").get<std::string>();
    if (method == "list_sessions") {
        json sessions = json::array();
        for (const auto &pair : runtimes) sessions.push_back({{"runtime", pair.second.id}, {"generation", pair.second.generation}});
        return {{"ok", true}, {"session", session}, {"runtimes", sessions}};
    }
    require(request.contains("runtime") && request.at("runtime") == state.id, "Explicit runtime required");
    if (request.contains("prompt_id"))
        require(state.pending && request.at("prompt_id") == state.prompt_id, "Prompt cancelled or superseded");
    if (method == "set_language") {
        require(request.at("session") == session, "Session changed");
        state.language = i18n::normalize(request.at("language").get<std::string>());
        reshade::set_config_value(runtime, "CYRSASSISTANT", "Language", state.language.c_str());
        return {{"ok", true}, {"language", state.language}};
    }
    if (method == "set_permission_mode") {
        require(request.at("session") == session, "Session changed");
        const int mode = request.at("mode").get<int>();
        require(mode >= 0 && mode <= 2, "Unknown permission mode");
        if (state.pending) cancel_prompt(state);
        state.permissions.set_mode(mode);
        reshade::set_config_value(runtime, "CYRSASSISTANT", "PermissionMode", mode);
        return {{"ok", true}};
    }
    if (method == "request_action_permission") {
        require(request.at("session") == session && state.pending && request.at("prompt_id") == state.prompt_id, "Prompt changed");
        const auto action = request.at("action").get<std::string>();
        require(permissioned_write(action) || action == "read_effect_source" || action == "inspect_game_shader", "Unknown permission action");
        return {{"ok", true}, {"permission", state.permissions.issue(state.prompt_id, action, request.at("payload"), request.at("summary"))}};
    }
    if (method == "resolve_action_permission") {
        require(request.at("session") == session && state.pending && request.at("prompt_id") == state.prompt_id, "Prompt changed");
        state.permissions.decide(request.at("permission_id").get<uint64_t>(), request.at("allow").get<bool>());
        return {{"ok", true}};
    }
    if (method == "consume_read_permission") {
        require(request.at("session") == session && state.pending && request.at("prompt_id") == state.prompt_id, "Prompt changed");
        const auto action = request.at("action").get<std::string>();
        require(action == "read_effect_source" || action == "inspect_game_shader", "Expected source inspection permission");
        state.permissions.consume(request.at("permission_id").get<uint64_t>(), state.prompt_id, action, request.at("payload"));
        return {{"ok", true}};
    }
    if (request.contains("prompt_id") && permissioned_write(method) && (state.permissions.mode == 1 || request.contains("permission_id"))) {
        auto payload = request;
        for (const auto *key : {"protocol", "request_id", "method", "permission_id"}) payload.erase(key);
        state.permissions.consume(request.value("permission_id", uint64_t(0)), state.prompt_id, method, payload);
    }
    if (method == "send_chat") {
        require(request.at("session") == session, "Session changed");
        submit_chat(state, request.at("text").get<std::string>());
        return {{"ok", true}, {"prompt_id", state.prompt_id}};
    }
    if (method == "assistant_progress") {
        require(request.at("session") == session, "Session changed");
        const auto progress = request.at("message").get<std::string>();
        require(progress.size() <= 512, "Progress too long");
        state.progress = progress;
        return {{"ok", true}};
    }
    if (method == "restore_generated_effect") {
        check_version(runtime, state, request);
        require(!state.generated_wait && !state.generated_previous.empty(), "No effect replacement to restore");
        auto target = runtime->find_technique(state.generated_file.c_str(), "CyRSGenerated");
        for (const auto &old : state.generated_previous) {
            const auto name = old.at("name").get<std::string>();
            require(runtime->find_technique(state.generated_replaces.c_str(), name.c_str()).handle != 0, "Original effect no longer loaded");
        }
        if (target.handle) runtime->set_technique_state(target, false);
        for (const auto &old : state.generated_previous) {
            const auto name = old.at("name").get<std::string>();
            runtime->set_technique_state(runtime->find_technique(state.generated_replaces.c_str(), name.c_str()), old.at("value").get<bool>());
        }
        state.generated_phase = "disabled"; state.generated_message = "Previous effect restored.";
        state.generated_previous.clear(); ++state.revision;
        return {{"ok", true}};
    }
    if (method == "connect_provider") {
        auto &c = state.connection;
        require(!c.wanted, "Disconnect before changing provider");
        const int provider = request.at("provider").get<int>();
        require(provider >= 0 && provider <= 3, "Unsupported provider");
        const auto endpoint = request.value("endpoint", std::string()), model = request.value("model", std::string()), key = request.value("key", std::string());
        require(endpoint.size() < c.endpoint.size() && model.size() < c.model.size() && key.size() < c.key.size(), "Connection field too long");
        c.provider = provider;
        strcpy_s(c.endpoint.data(), c.endpoint.size(), endpoint.c_str());
        strcpy_s(c.model.data(), c.model.size(), model.c_str());
        strcpy_s(c.key.data(), c.key.size(), key.c_str());
        start_connection(runtime, c, state.language);
        return {{"ok", true}};
    }
    if (method == "disconnect_provider") {
        auto &c = state.connection; c.wanted = false; ++c.epoch; c.phase = "disconnected"; c.message = "Disconnected.";
        cancel_prompt(state);
        return {{"ok", true}};
    }
    if (method == "get_connection") {
        auto &c = state.connection;
        return {{"ok", true}, {"connection", {{"epoch", c.epoch}, {"wanted", c.wanted},
            {"language", state.language}, {"provider", c.provider}, {"endpoint", c.endpoint.data()}, {"model", c.model.data()}, {"key", c.key.data()}}}};
    }
    if (method == "connection_status") {
        auto &c = state.connection;
        require(c.wanted && request.at("epoch") == c.epoch, "Connection superseded");
        auto phase = request.at("phase").get<std::string>();
        require(phase == "ready" || phase == "connecting" || phase == "error", "Invalid connection phase");
        auto message = request.at("message").get<std::string>();
        require(message.size() <= 2048, "Status too long");
        c.phase = phase; c.message = message; c.heartbeat = GetTickCount64();
        return {{"ok", true}};
    }
    if (method == "list_game_shaders") return {{"ok", true}, {"inventory", shader_lab::inventory(runtime->get_device())}};
    if (method == "inspect_game_shader") return {{"ok", true}, {"shader", shader_lab::inspect(runtime->get_device(), request.at("hash"))}};
    if (method == "replace_game_shader" || method == "enable_game_shader" || method == "restore_game_shaders" || method == "generate_effect") {
        check_version(runtime, state, request);
        if (request.contains("prompt_id")) require(state.pending && request.at("prompt_id") == state.prompt_id, "Prompt cancelled or superseded");
        if (method == "replace_game_shader") {
            auto result = shader_lab::replace(runtime->get_device(), request.at("hash"), request.at("source"));
            ++state.revision;
            return {{"ok", true}, {"replacement", result}};
        }
        if (method == "enable_game_shader") shader_lab::enable(runtime->get_device(), request.at("hash"), request.at("enabled").get<bool>());
        if (method == "restore_game_shaders") shader_lab::restore_all(runtime->get_device());
        if (method == "generate_effect") {
            require(!state.generated_wait, "Wait for the current generated effect to finish loading");
            const auto effect_name = request.value("name", std::string("GeneratedEffect"));
            require(std::regex_match(effect_name, std::regex("[A-Za-z][A-Za-z0-9_]{0,47}")), "Invalid generated effect name");
            const auto replaces = request.value("replace_effect", std::string());
            json previous = json::array();
            if (!replaces.empty()) {
                for (const auto &t : state.techniques) if (t.metadata["effect"] == replaces) {
                    require(!t.metadata["readonly"].get<bool>(), "Cannot replace a forced technique");
                    previous.push_back({{"name", t.metadata["name"]}, {"value", t.metadata["value"]}});
                }
                require(!previous.empty(), "Replacement target is not a loaded ReShade effect");
            }
            auto source = shader_tools::generated_fx(request.at("body"), request.value("parameters", json::array()), request.value("title", effect_name));
            std::vector<uint8_t> bytes(source.begin(), source.end());
            const auto filename = "CyRS_" + effect_name + "_" + shader_tools::hash(bytes).substr(0, 16) + ".fx";
            auto current = snapshot(runtime, state);
            require(!current["search_paths"].empty(), "Configure an EffectSearchPaths directory in ReShade first");
            auto root = current["search_paths"][0].get<std::string>();
            if (root.size() >= 3 && (root.substr(root.size()-3) == "/**" || root.substr(root.size()-3) == "\\**")) root.resize(root.size()-3);
            auto folder = std::filesystem::u8path(root);
            if (folder.is_relative()) folder = std::filesystem::u8path(current["base_path"].get<std::string>()) / folder;
            std::filesystem::create_directories(folder);
            const auto file = folder / filename;
            if (std::filesystem::exists(file)) {
                std::ifstream stream(file, std::ios::binary);
                std::string previous_source((std::istreambuf_iterator<char>(stream)), {});
                require(previous_source == source, "Generated filename already exists with different contents");
            } else {
                std::ofstream stream(file, std::ios::binary); stream.write(source.data(), source.size()); stream.close();
                require(!stream.fail(), "Cannot write generated FX to the effect search directory");
            }
            require(filename != replaces, "Replacement must differ from the original effect");
            state.generated_replaces = replaces; state.generated_previous = previous;
            state.generated_file = filename; state.generated_phase = "compiling"; state.generated_message = "ReShade compilation in progress...";
            state.generated_prompt = request.value("prompt_id", uint64_t(0)); state.generated_wait = true; state.generated_started = GetTickCount64();
            state.parameters.clear(); state.techniques.clear(); state.undo.clear(); state.applied.clear();
            ++state.generation;
            runtime->reload_effect_next_frame(nullptr);
        }
        ++state.revision;
        return {{"ok", true}, {"generated", {{"file", state.generated_file}, {"phase", state.generated_phase}}}};
    }
    if (method == "get_state") return {{"ok", true}, {"state", snapshot(runtime, state)}};
    if (method == "capture_frame") return {{"ok", true}, {"frame", capture_frame(runtime)}};
    if (method == "reload_effects") {
        check_version(runtime, state, request);
        ++state.generation; ++state.revision;
        state.parameters.clear(); state.techniques.clear(); state.undo.clear(); state.applied.clear();
        runtime->reload_effect_next_frame(nullptr);
        return {{"ok", true}, {"status", "reload_queued"}, {"generation", state.generation}};
    }
    if (method == "scan_effects") { scan(runtime, state); ++state.scan_id; }
    else if (method == "apply_patch") {
        if (request.contains("prompt_id")) require(state.pending && request.at("prompt_id") == state.prompt_id, "Prompt cancelled or superseded");
        apply(runtime, state, request);
    }
    else if (method == "undo") { check_version(runtime, state, request); undo(runtime, state); }
    else if (method == "save_preset") { check_version(runtime, state, request); runtime->save_current_preset(); state.status = "Preset save requested from ReShade."; }
    else if (method == "assistant_reply") {
        require(request.at("session") == session, "Session changed");
        require(state.pending && request.at("prompt_id") == state.prompt_id, "Prompt cancelled or superseded");
        const auto message = request.at("message").get<std::string>();
        require(message.size() <= 16384, "Reply too long");
        state.answer = message; state.pending = false; state.permissions.invalidate();
        chat_message(state, "assistant", message);
    } else throw std::runtime_error("Unknown method");
    return {{"ok", true}, {"state", snapshot(runtime, state)}};
}
void present(effect_runtime *runtime) {
    std::lock_guard<std::recursive_mutex> lock(runtime_mutex);
    auto it = runtimes.find(runtime);
    if (it == runtimes.end()) return;
    auto &generated = it->second;
    if (generated.generated_wait) {
        bool enumerated = false;
        effect_technique target{};
        runtime->enumerate_techniques(nullptr, [&](effect_runtime *, effect_technique h) {
            enumerated = true;
            const auto file = api_string([&](char *v, size_t *n) { runtime->get_technique_effect_name(h, v, n); });
            if (file == generated.generated_file) target = h;
        });
        if (enumerated && target.handle) {
            const bool active = generated.generated_prompt == 0 || (generated.pending && generated.prompt_id == generated.generated_prompt);
            if (!active) {
                runtime->set_technique_state(target, false); generated.generated_phase = "cancelled";
                generated.generated_message = "Effect compiled, but the request was cancelled: not activated."; generated.generated_wait = false;
            } else if (generated.generated_phase == "compiling") {
                runtime->set_technique_state(target, true);
                generated.generated_phase = "initializing";
            } else {
                bool enabled = runtime->get_technique_state(target);
                if (enabled && !generated.generated_replaces.empty()) {
                    for (const auto &old : generated.generated_previous) {
                        const auto name = old.at("name").get<std::string>();
                        if (!runtime->find_technique(generated.generated_replaces.c_str(), name.c_str()).handle) enabled = false;
                    }
                    if (enabled) for (const auto &old : generated.generated_previous) {
                        const auto name = old.at("name").get<std::string>();
                        const auto handle = runtime->find_technique(generated.generated_replaces.c_str(), name.c_str());
                        runtime->set_technique_state(handle, false);
                        if (runtime->get_technique_state(handle)) enabled = false;
                    }
                    if (!enabled) {
                        runtime->set_technique_state(target, false);
                        for (const auto &old : generated.generated_previous) {
                            const auto name = old.at("name").get<std::string>();
                            const auto handle = runtime->find_technique(generated.generated_replaces.c_str(), name.c_str());
                            if (handle.handle) runtime->set_technique_state(handle, old.at("value").get<bool>());
                        }
                    }
                }
                generated.generated_phase = enabled ? "ready" : "error";
                generated.generated_message = enabled ? "Generated effect compiled and activated. You can disable it." : "GPU initialization failed. Check the ReShade Log.";
                generated.generated_wait = false;
            }
        } else if (GetTickCount64() - generated.generated_started > 60000) {
            generated.generated_phase = "error"; generated.generated_wait = false;
            generated.generated_message = "Effect missing after compilation. Check the errors in ReShade Home / Log.";
        }
    }
    if (auto request = bridge.take(it->second.id)) {
        try { request->result.set_value(execute(runtime, it->second, request->body)); }
        catch (const std::exception &e) { request->result.set_value({{"ok", false}, {"error", e.what()}}); }
    }
}
void init(effect_runtime *runtime) {
    std::lock_guard<std::recursive_mutex> lock(runtime_mutex);
    Runtime state; state.id = next_runtime++;
    std::array<char, 32> language{}; size_t language_size = language.size();
    reshade::get_config_value(runtime, "CYRSASSISTANT", "Language", language.data(), &language_size);
    language.back() = 0; state.language = i18n::normalize(language.data());
    reshade::get_config_value(runtime, "CYRSASSISTANT", "Provider", state.connection.provider);
    reshade::get_config_value(runtime, "CYRSASSISTANT", "PermissionMode", state.permissions.mode);
    state.permissions.mode = std::clamp(state.permissions.mode, 0, 2);
    state.connection.provider = std::clamp(state.connection.provider, 0, 3);
    size_t endpoint_size = state.connection.endpoint.size(), model_size = state.connection.model.size();
    reshade::get_config_value(runtime, "CYRSASSISTANT", "Endpoint", state.connection.endpoint.data(), &endpoint_size);
    reshade::get_config_value(runtime, "CYRSASSISTANT", "Model", state.connection.model.data(), &model_size);
    state.connection.endpoint.back() = 0; state.connection.model.back() = 0;
    runtimes.emplace(runtime, std::move(state));
}
void destroy(effect_runtime *runtime) { std::lock_guard<std::recursive_mutex> lock(runtime_mutex); runtimes.erase(runtime); }
void reload(effect_runtime *runtime) {
    std::lock_guard<std::recursive_mutex> lock(runtime_mutex);
    auto it = runtimes.find(runtime);
    if (it == runtimes.end()) return;
    try {
        auto &s = it->second;
        scan(runtime, s, true);

    }
    catch (const std::exception &e) { it->second.parameters.clear(); it->second.techniques.clear(); it->second.status = e.what(); }
}
void overlay(effect_runtime *runtime) {
    std::lock_guard<std::recursive_mutex> lock(runtime_mutex);
    auto it = runtimes.find(runtime);
    if (it == runtimes.end()) return;
    auto &s = it->second;
    auto tr = [&](const char *message) { return i18n::translate(s.language, message); };
    auto ui_label = [&](const char *message) { return i18n::label(s.language, message); };
    try {
        ImGui::Text("CyRSAssistant 0.7.0 - %s", tr("AI chat"));
        auto &c = s.connection;
        const bool ready = connected(c);
        const bool lost = c.wanted && GetTickCount64() - (c.heartbeat ? c.heartbeat : c.started) >= 10000;
        const auto color = ready ? ImVec4(0.4f, 0.9f, 0.5f, 1) : (lost || c.phase == "error") ? ImVec4(1, 0.45f, 0.35f, 1) : ImVec4(1, 0.8f, 0.35f, 1);
        ImGui::TextColored(color, "%s", ready ? tr("READY") : lost ? tr("LOCAL SERVICE UNREACHABLE") : c.phase == "connecting" ? tr("CONNECTING") : c.phase == "error" ? tr("CONNECTION ERROR") : tr("DISCONNECTED"));
        ImGui::TextWrapped("%s", lost ? tr("The service is not responding. Disconnect and reconnect to check it again.") : tr(c.message.c_str()));
        if (!c.wanted && ImGui::Button(ui_label("Connect to provider").c_str())) start_connection(runtime, c, s.language);
        const char *permission_names[] = {tr("Automatic"), tr("Ask each time"), tr("Full access to ReShade tools")};
        ImGui::TextDisabled(tr("Permissions: %s"), permission_names[s.permissions.mode]);
        if (ImGui::BeginTabBar("assistant_tabs")) {
            if (ImGui::BeginTabItem(ui_label("Chat").c_str())) {
        ImGui::BeginDisabled(s.pending);
        if (ImGui::SmallButton(ui_label("New conversation").c_str())) { s.conversation.clear(); s.answer.clear(); s.prompt.clear(); s.input.fill(0); }
        ImGui::EndDisabled();
        ImGui::SameLine();
        if (ImGui::SmallButton(ui_label("Copy conversation").c_str())) {
            std::string transcript;
            for (const auto &message : s.conversation)
                transcript += message["role"].get<std::string>() + ": " + message["content"].get<std::string>() + "\n\n";
            ImGui::SetClipboardText(transcript.c_str());
        }
        ImGui::SameLine();
        if (ImGui::SmallButton(ui_label("About chat history").c_str())) ImGui::OpenPopup("chat_privacy");
        if (ImGui::BeginPopup("chat_privacy")) {
            ImGui::TextWrapped(tr("32 messages kept in memory. Recent exchanges are sent to the selected provider, including after switching providers. New conversation clears this local context without restoring the rendering."));
            ImGui::EndPopup();
        }
        const bool approval_pending = !s.permissions.request.is_null() && s.permissions.request.value("status", "") == "pending";
        ImGui::BeginChild("conversation", ImVec2(0, std::max(120.0f, ImGui::GetContentRegionAvail().y - (approval_pending ? 330.0f : 155.0f))), true);
        if (s.conversation.empty()) ImGui::TextWrapped(tr("Hello! Ask a question or describe the look you want. You can chat here even with no effects loaded or shader selected."));
        for (size_t i = 0; i < s.conversation.size(); ++i) {
            const auto &message = s.conversation[i];
            const auto role = message["role"].get<std::string>();
            ImGui::PushID(static_cast<int>(i));
            ImGui::TextColored(role == "user" ? ImVec4(0.5f, 0.75f, 1, 1) : ImVec4(0.65f, 0.9f, 0.65f, 1), "%s", role == "user" ? tr("You") : role == "assistant" ? tr("Assistant") : tr("Information"));
            ImGui::SameLine();
            if (ImGui::SmallButton(ui_label("Copy").c_str())) ImGui::SetClipboardText(message["content"].get_ref<const std::string &>().c_str());
            ImGui::TextWrapped("%s", message["content"].get_ref<const std::string &>().c_str());
            ImGui::Separator();
            ImGui::PopID();
        }
        if (s.pending) { ImGui::Text(tr("Working... %llu s"), (GetTickCount64() - s.prompt_started) / 1000); ImGui::TextWrapped("%s", tr(s.progress.c_str())); }
        if (s.chat_scroll) { ImGui::SetScrollHereY(1.0f); s.chat_scroll = false; }
        ImGui::EndChild();
        if (approval_pending) {
            ImGui::SeparatorText(tr("Approval requested"));
            ImGui::TextWrapped("%s", s.permissions.request["summary"].get_ref<const std::string &>().c_str());
            if (ImGui::CollapsingHeader(ui_label("View proposed values or code").c_str())) {
                ImGui::BeginChild("permission_details", ImVec2(0, 130), true);
                ImGui::TextWrapped("%s", s.permissions.request["payload"].dump(2).c_str());
                ImGui::EndChild();
            }
            const auto approval_id = s.permissions.request["id"].get<uint64_t>();
            if (ImGui::Button(ui_label("Allow this action").c_str())) s.permissions.decide(approval_id, true);
            ImGui::SameLine();
            if (ImGui::Button(ui_label("Deny this action").c_str())) s.permissions.decide(approval_id, false);
        }
        ImGui::TextUnformatted(tr("Your message"));
        ImGui::InputTextMultiline("##prompt", s.input.data(), s.input.size(), ImVec2(-1, 90));
        const bool shortcut = ImGui::IsItemFocused() && ImGui::GetIO().KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_Enter, false);
        const bool can_send = ready && !s.pending && std::string(s.input.data()).find_first_not_of(" \t\r\n") != std::string::npos;
        ImGui::BeginDisabled(!can_send);
        if ((ImGui::Button(ui_label("Send").c_str()) || shortcut) && can_send) {
            submit_chat(s, s.input.data());
        }
        ImGui::EndDisabled();
        ImGui::SameLine(); ImGui::TextDisabled(tr("Ctrl+Enter: send | Enter: new line"));
        if (s.pending) { if (ImGui::Button(ui_label("Cancel request").c_str())) cancel_prompt(s); }
        else if (!ready) ImGui::TextWrapped(tr("Connect a provider to send a request."));
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem(ui_label("Options").c_str())) {
                if (ImGui::BeginCombo(ui_label("Language").c_str(), i18n::language_name(s.language))) {
                    for (const auto &language : i18n::languages) {
                        const bool selected = s.language == language.code;
                        const auto choice = std::string(language.name) + "###language_" + language.code;
                        if (ImGui::Selectable(choice.c_str(), selected)) {
                            s.language = language.code;
                            reshade::set_config_value(runtime, "CYRSASSISTANT", "Language", s.language.c_str());
                        }
                        if (selected) ImGui::SetItemDefaultFocus();
                    }
                    ImGui::EndCombo();
                }
                ImGui::TextWrapped("%s", tr("The language is saved for this game. Existing messages keep their original language. A request already in progress finishes in its original language."));
                ImGui::Separator();
                ImGui::SeparatorText(tr("Built-in assistant permissions"));
                int mode = s.permissions.mode;
                if (ImGui::Combo(ui_label("Permission mode").c_str(), &mode, permission_names, 3)) {
                    if (s.pending) cancel_prompt(s);
                    s.permissions.set_mode(mode);
                    reshade::set_config_value(runtime, "CYRSASSISTANT", "PermissionMode", mode);
                }
                ImGui::TextWrapped(tr("Automatic: requested reads and actions need no extra approval. One rendering operation per message."));
                ImGui::TextWrapped(tr("Ask each time: names and values can be read directly. Approve each rendering change and each FX source or native shader inspection before it is sent to the provider."));
                ImGui::TextWrapped(tr("Full access: the assistant can use read tools and multiple rendering operations to complete your request without intermediate approvals."));
                ImGui::TextWrapped(tr("These modes cover the available ReShade tools: effects, presets and game shaders. They do not enable a terminal or arbitrary file access. Changing mode cancels a pending request. Your choice is saved for this game."));
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem(ui_label("Connection").c_str())) {
        ImGui::SeparatorText(tr("Provider connection"));
        ImGui::BeginDisabled(c.wanted);
        const char *provider_names[] = {tr("Codex (CLI session)"), tr("Claude Code (CLI session)"), tr("OpenAI-compatible API"), tr("Local model (API)")};
        ImGui::Combo(ui_label("Provider").c_str(), &c.provider, provider_names, 4);
        ImGui::InputText(ui_label("Model (empty = CLI default)").c_str(), c.model.data(), c.model.size());
        if (c.provider >= 2) {
            ImGui::InputText(ui_label("URL /chat/completions").c_str(), c.endpoint.data(), c.endpoint.size());
            ImGui::InputText(ui_label("API key").c_str(), c.key.data(), c.key.size(), ImGuiInputTextFlags_Password);
            ImGui::TextDisabled(tr("The key is kept in memory for this session only."));
        } else ImGui::TextWrapped(tr("Uses your existing CLI login. Connect checks the local session; the first message checks model access."));
        ImGui::EndDisabled();
        if (!c.wanted) {
            if (ImGui::Button(ui_label("Connect").c_str())) {
                start_connection(runtime, c, s.language);
            }
        } else if (ImGui::Button(ui_label("Disconnect / edit").c_str())) {
            c.wanted = false; ++c.epoch; c.phase = "disconnected"; c.message = "Disconnected.";
            cancel_prompt(s);
        }
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem(ui_label("Effects").c_str())) {
        if (!s.generated_previous.empty() && !s.generated_wait && ImGui::Button(ui_label("Restore replaced effect").c_str())) {
            auto request = snapshot(runtime, s); request["method"] = "restore_generated_effect";
            execute(runtime, s, request);
        }
        if (s.generated_phase != "none") {
            ImGui::TextWrapped("%s : %s", s.generated_file.c_str(), tr(s.generated_message.c_str()));
            if (ImGui::Button(ui_label("Disable last generated effect").c_str())) {
                auto technique = runtime->find_technique(s.generated_file.c_str(), "CyRSGenerated");
                if (technique.handle) runtime->set_technique_state(technique, false);
                s.generated_phase = "disabled"; s.generated_wait = false; s.generated_message = "Effect disabled. FX file kept.";
                cancel_prompt(s); ++s.revision;
            }
        }
        ImGui::Separator();
        if (ImGui::Button(ui_label("Scan effects").c_str())) { scan(runtime, s); ++s.scan_id; }
        ImGui::SameLine();
        if (ImGui::Button(ui_label("Load / reload effects").c_str())) runtime->reload_effect_next_frame(nullptr);
        ImGui::BeginDisabled(s.undo.empty() || s.loading);
        if (ImGui::Button(ui_label("Undo last edit").c_str())) undo(runtime, s);
        ImGui::EndDisabled(); ImGui::SameLine();
        if (ImGui::Button(ui_label("Save preset").c_str())) { runtime->save_current_preset(); s.status = "Preset save requested from ReShade."; }
        ImGui::TextWrapped("%s", tr(s.status.c_str()));
        ImGui::Text(tr("%zu techniques | %zu parameters"), s.techniques.size(), s.parameters.size());
        if (ImGui::CollapsingHeader(ui_label("Service diagnostics").c_str())) ImGui::TextWrapped(tr("Local pipe: %s | runtime %llu"), bridge.name().c_str(), s.id);
        ImGui::InputText(ui_label("Filter").c_str(), s.search.data(), s.search.size());
        const std::string filter(s.search.data());
        refresh(runtime, s);
        if (s.parameters.empty()) ImGui::TextWrapped(tr("No parameters loaded. Reload effects or check performance mode. Chat is still available."));
        auto edit = [&](const char *kind, size_t id, json value) {
            auto request = snapshot(runtime, s);
            request["changes"] = json::array({{{"kind", kind}, {"id", id}, {"value", value}}});
            apply(runtime, s, request);
        };
        if (ImGui::CollapsingHeader(ui_label("Techniques").c_str())) {
            for (size_t i = 0; i < s.techniques.size(); ++i) {
                const auto &m = s.techniques[i].metadata;
                const auto label = m["effect"].get<std::string>() + " / " + m["name"].get<std::string>();
                if (!filter.empty() && label.find(filter) == std::string::npos) continue;
                bool enabled = m["value"].get<bool>();
                ImGui::PushID(static_cast<int>(i));
                ImGui::BeginDisabled(m["readonly"].get<bool>());
                const bool changed = ImGui::Checkbox(label.c_str(), &enabled);
                ImGui::EndDisabled(); ImGui::PopID();
                if (changed) edit("technique", i, enabled);
            }
        }
        if (ImGui::CollapsingHeader(ui_label("Parameters").c_str())) {
            for (size_t i = 0; i < s.parameters.size(); ++i) {
                const auto &p = s.parameters[i];
                const auto &m = p.metadata;
                const auto label = m["effect"].get<std::string>() + " / " + m["name"].get<std::string>();
                if (!filter.empty() && label.find(filter) == std::string::npos) continue;
                ImGui::PushID(static_cast<int>(i + s.techniques.size()));
                ImGui::TextUnformatted(label.c_str());
                if (!m["description"].get<std::string>().empty() && ImGui::IsItemHovered()) ImGui::SetTooltip("%s", m["description"].get<std::string>().c_str());
                if (m["readonly"].get<bool>() || p.count == 0 || p.count > 4) {
                    ImGui::TextWrapped(tr("%s (read-only in this panel)"), m["value"].dump().c_str());
                    ImGui::PopID(); continue;
                }
                bool changed = false; json value;
                if (m["type"] == "bool" && p.count == 1) {
                    bool v = m["value"][0].get<bool>(); changed = ImGui::Checkbox(ui_label("Value").c_str(), &v); value = json::array({v});
                } else if (m["type"] == "float") {
                    std::array<float, 4> v{}; for (size_t k = 0; k < p.count; ++k) v[k] = m["value"][k].get<float>();
                    changed = ImGui::InputScalarN(ui_label("Value").c_str(), ImGuiDataType_Float, v.data(), static_cast<int>(p.count), nullptr, nullptr, "%.5f", ImGuiInputTextFlags_EnterReturnsTrue);
                    value = json::array(); for (size_t k = 0; k < p.count; ++k) value.push_back(v[k]);
                } else if (m["type"] == "int") {
                    std::array<int32_t, 4> v{}; for (size_t k = 0; k < p.count; ++k) v[k] = m["value"][k].get<int32_t>();
                    changed = ImGui::InputScalarN(ui_label("Value").c_str(), ImGuiDataType_S32, v.data(), static_cast<int>(p.count), nullptr, nullptr, nullptr, ImGuiInputTextFlags_EnterReturnsTrue);
                    value = json::array(); for (size_t k = 0; k < p.count; ++k) value.push_back(v[k]);
                } else if (m["type"] == "uint") {
                    std::array<uint32_t, 4> v{}; for (size_t k = 0; k < p.count; ++k) v[k] = m["value"][k].get<uint32_t>();
                    changed = ImGui::InputScalarN(ui_label("Value").c_str(), ImGuiDataType_U32, v.data(), static_cast<int>(p.count), nullptr, nullptr, nullptr, ImGuiInputTextFlags_EnterReturnsTrue);
                    value = json::array(); for (size_t k = 0; k < p.count; ++k) value.push_back(v[k]);
                } else ImGui::TextUnformatted(tr("Boolean vectors are editable through the bridge."));
                ImGui::PopID();
                if (changed) edit("parameter", i, value);
            }
        }
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem(ui_label("Shaders").c_str())) {
            ImGui::TextWrapped(tr("Direct3D 11 / 12 pixel shaders. Identified by hash, not by visual purpose: a shared shader can affect multiple objects."));
            if (ImGui::Button(ui_label("Refresh game shaders").c_str())) {
                s.game_shaders = shader_lab::inventory(runtime->get_device());
                auto &shaders = s.game_shaders["shaders"];
                std::sort(shaders.begin(), shaders.end(), [](const json &a, const json &b) { return a["binds"].get<uint64_t>() > b["binds"].get<uint64_t>(); });
            }
            ImGui::SameLine();
            if (ImGui::Button(ui_label("Restore all original shaders").c_str())) { shader_lab::restore_all(runtime->get_device()); s.status = "Replacements disabled at the next game bind."; ++s.revision; }
            if (s.game_shaders.contains("shaders")) {
                ImGui::BeginChild("game_shader_list", ImVec2(0, 170), true);
                for (const auto &entry : s.game_shaders["shaders"]) {
                    const auto hash = entry["hash"].get<std::string>();
                    const auto label = hash.substr(0, 16) + tr(" | uses ") + std::to_string(entry["binds"].get<uint64_t>()) + " | " + entry.value("encoding", std::string("DXBC")) + " | PSO " + std::to_string(entry.value("replaceable_pipelines", size_t(0))) + "/" + std::to_string(entry.value("pipelines", size_t(0))) + (entry["enabled"].get<bool>() ? tr(" | REPLACED") : "");
                    if (ImGui::Selectable(label.c_str(), hash == s.selected_hash)) s.selected_hash = hash;
                }
                ImGui::EndChild();
            }
            if (s.game_shaders.contains("shaders")) for (const auto &entry : s.game_shaders["shaders"]) if (entry["hash"] == s.selected_hash) {
                if (!entry.value("limitation", std::string()).empty()) ImGui::TextWrapped(tr("Limitation: %s"), tr(entry["limitation"].get_ref<const std::string &>().c_str()));
                if (!entry.value("error", std::string()).empty()) ImGui::TextWrapped(tr("Error: %s"), tr(entry["error"].get_ref<const std::string &>().c_str()));
            }
            ImGui::TextWrapped(tr("Selection: %s"), s.selected_hash.empty() ? tr("no shader") : s.selected_hash.c_str());
            if (!s.selected_hash.empty() && ImGui::Button(ui_label("Inspect selected shader").c_str())) {
                auto details = shader_lab::inspect(runtime->get_device(), s.selected_hash);
                s.inspected_hash = s.selected_hash;
                s.shader_inspection = details["reflection"].dump(2) + "\n\n" + details["assembly"].get<std::string>();
            }
            if (!s.shader_inspection.empty() && s.inspected_hash == s.selected_hash && ImGui::CollapsingHeader(ui_label("Signatures, resources and disassembly").c_str())) {
                ImGui::BeginChild("shader_inspection", ImVec2(0, 230), true);
                ImGui::TextUnformatted(s.shader_inspection.c_str());
                ImGui::EndChild();
            }
            if (!s.selected_hash.empty() && ImGui::Button(ui_label("Restore selected shader").c_str())) { shader_lab::enable(runtime->get_device(), s.selected_hash, false); ++s.revision; }
                ImGui::EndTabItem();
            }
            ImGui::EndTabBar();
        }
    } catch (const std::exception &e) { s.status = e.what(); }
}
}
extern "C" __declspec(dllexport) bool AddonInit(HMODULE module, HMODULE reshade_module) {
    if (!reshade::register_addon(module, reshade_module)) return false;
    try {
        addon_module = module;
        session = std::to_string(GetCurrentProcessId()) + "-" + std::to_string(std::random_device{}());
        bridge.start();
        shader_lab::register_events();
        reshade::register_event<reshade::addon_event::init_effect_runtime>(init);
        reshade::register_event<reshade::addon_event::destroy_effect_runtime>(destroy);
        reshade::register_event<reshade::addon_event::reshade_reloaded_effects>(reload);
        reshade::register_event<reshade::addon_event::reshade_present>(present);
        reshade::register_overlay("CyRSAssistant", overlay);
        return true;
    } catch (...) { bridge.stop(); reshade::unregister_addon(module, reshade_module); return false; }
}
extern "C" __declspec(dllexport) void AddonUninit(HMODULE module, HMODULE reshade_module) {
    bridge.stop();
    shader_lab::unregister_events();
    reshade::unregister_overlay("CyRSAssistant", overlay);
    reshade::unregister_event<reshade::addon_event::reshade_present>(present);
    reshade::unregister_event<reshade::addon_event::reshade_reloaded_effects>(reload);
    reshade::unregister_event<reshade::addon_event::destroy_effect_runtime>(destroy);
    reshade::unregister_event<reshade::addon_event::init_effect_runtime>(init);
    runtimes.clear();
    if (companion_process) { CloseHandle(companion_process); companion_process = nullptr; }
    reshade::unregister_addon(module, reshade_module);
}
BOOL APIENTRY DllMain(HMODULE, DWORD, LPVOID) { return TRUE; }
