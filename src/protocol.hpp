#pragma once
#include <nlohmann/json.hpp>
#include <cmath>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>

namespace cyrs {
using json = nlohmann::json;
inline void require(bool ok, const char *message) { if (!ok) throw std::runtime_error(message); }

// Validate the whole patch before the runtime writes anything.
inline json validate_patch(const json &state, const json &request) {
    require(request.at("session") == state.at("session"), "Session changed");
    require(request.at("runtime") == state.at("runtime"), "Runtime changed");
    require(request.at("generation") == state.at("generation"), "Effects reloaded; read state again");
    require(request.at("revision") == state.at("revision"), "State changed; read state again");
    const auto &changes = request.at("changes");
    require(changes.is_array() && !changes.empty() && changes.size() <= 64, "Expected 1 to 64 changes");
    std::set<std::string> seen;
    json normalized = json::array();
    for (const auto &change : changes) {
        const auto kind = change.at("kind").get<std::string>();
        require(kind == "parameter" || kind == "technique", "Unknown change kind");
        require(change.at("id").is_number_unsigned(), "Expected unsigned item id");
        const auto id = change.at("id").get<size_t>();
        require(seen.insert(kind + std::to_string(id)).second, "Duplicate target");
        const auto &items = state.at(kind == "parameter" ? "parameters" : "techniques");
        require(id < items.size() && items[id].at("id") == id, "Unknown target");
        const auto &item = items[id];
        const auto &value = change.at("value");
        if (kind == "technique") {
            require(value.is_boolean(), "Technique state must be boolean");
            require(!item.value("readonly", false), "Technique controlled by an annotation");
            normalized.push_back(change);
            continue;
        }
        require(!item.at("readonly").get<bool>(), "Parameter is read-only");
        require(value.is_array() && value.size() == item.at("value").size(), "Incorrect parameter shape");
        json values = json::array();
        const auto type = item.at("type").get<std::string>();
        for (const auto &component : value) {
            if (type == "bool") {
                require(component.is_boolean(), "Expected boolean component");
                values.push_back(component);
                continue;
            }
            require(component.is_number(), "Expected numeric component");
            const double number = component.get<double>();
            require(std::isfinite(number), "Non-finite component");
            if (item.contains("min")) require(number >= item.at("min").get<double>(), "Below annotated minimum");
            if (item.contains("max")) require(number <= item.at("max").get<double>(), "Above annotated maximum");
            if (type == "float") {
                require(std::abs(number) <= std::numeric_limits<float>::max(), "Float overflow");
                values.push_back(static_cast<float>(number));
            } else if (type == "int") {
                require(component.is_number_integer() && number >= INT32_MIN && number <= INT32_MAX, "Expected int32");
                values.push_back(component.get<int32_t>());
            } else {
                require(type == "uint" && component.is_number_integer() && number >= 0 && number <= UINT32_MAX, "Expected uint32");
                values.push_back(component.get<uint32_t>());
            }
        }
        normalized.push_back({{"kind", kind}, {"id", id}, {"value", values}});
    }
    return normalized;
}
}
