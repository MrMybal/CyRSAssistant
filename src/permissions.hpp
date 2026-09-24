#pragma once
#include "protocol.hpp"

namespace cyrs {
// An approval belongs to one exact operation, prompt and policy revision.
struct Permissions {
    int mode = 0; // Automatic, ask, full ReShade access.
    uint64_t epoch = 0, next_id = 0;
    json request = nullptr;

    void invalidate() { request = nullptr; ++epoch; }
    void set_mode(int value) {
        require(value >= 0 && value <= 2, "Unknown permission mode");
        mode = value; invalidate();
    }
    json issue(uint64_t prompt, const std::string &action, const json &payload, const std::string &summary) {
        require(request.is_null() || request.value("status", "") != "pending", "An approval is already pending");
        require(payload.is_object() && payload.dump().size() <= 100000 && summary.size() <= 2048, "Permission preview too large");
        request = {{"id", ++next_id}, {"epoch", epoch}, {"prompt_id", prompt}, {"action", action},
                   {"payload", payload}, {"summary", summary}, {"status", mode == 1 ? "pending" : "approved"}};
        return request;
    }
    void decide(uint64_t id, bool allow) {
        require(!request.is_null() && request.at("id") == id && request.at("epoch") == epoch && request.at("status") == "pending", "Approval expired or already answered");
        request["status"] = allow ? "approved" : "denied";
    }
    void consume(uint64_t id, uint64_t prompt, const std::string &action, const json &payload) {
        require(!request.is_null() && request.at("id") == id && request.at("epoch") == epoch && request.at("prompt_id") == prompt && request.at("status") == "approved", "Action not approved or approval expired");
        require(request.at("action") == action && request.at("payload") == payload, "Approved action changed");
        request["status"] = "consumed";
    }
    json snapshot() const { return {{"mode", mode}, {"epoch", epoch}, {"request", request}}; }
};
inline bool permissioned_write(const std::string &method) {
    return method == "apply_patch" || method == "generate_effect" || method == "replace_game_shader" ||
        method == "enable_game_shader" || method == "restore_game_shaders" || method == "restore_generated_effect" ||
        method == "reload_effects" || method == "undo" || method == "save_preset";
}
}
