#include "permissions.hpp"
#include <functional>
#include <iostream>
using namespace cyrs;
int main() {
    unsigned checks = 0;
    auto rejected = [&](const std::function<void()> &f) { bool failed = false; try { f(); } catch (const std::exception &) { failed = true; } if (!failed) throw std::runtime_error("Expected permission rejection"); ++checks; };
    try {
        Permissions p;
        const json payload = {{"value", 1}};
        auto automatic = p.issue(1, "apply_patch", payload, "Set value");
        require(automatic["status"] == "approved", "Automatic mode should approve"); ++checks;
        p.consume(automatic["id"], 1, "apply_patch", payload); ++checks;
        rejected([&] { p.consume(automatic["id"], 1, "apply_patch", payload); });
        p.set_mode(1);
        auto ask = p.issue(2, "apply_patch", payload, "Set value");
        rejected([&] { p.consume(ask["id"], 2, "apply_patch", payload); });
        p.decide(ask["id"], true);
        rejected([&] { p.consume(ask["id"], 2, "apply_patch", json{{"value", 2}}); });
        rejected([&] { p.consume(ask["id"], 3, "apply_patch", payload); });
        rejected([&] { p.consume(ask["id"], 2, "generate_effect", payload); });
        p.consume(ask["id"], 2, "apply_patch", payload); ++checks;
        auto denied = p.issue(3, "read_effect_source", payload, "Read source");
        p.decide(denied["id"], false);
        rejected([&] { p.consume(denied["id"], 3, "read_effect_source", payload); });
        auto cancelled = p.issue(4, "apply_patch", payload, "Set value");
        p.invalidate();
        rejected([&] { p.decide(cancelled["id"], true); });
        p.set_mode(2);
        auto full = p.issue(5, "generate_effect", payload, "Generate");
        require(full["status"] == "approved", "Full mode should approve"); ++checks;
        p.set_mode(1);
        rejected([&] { p.consume(full["id"], 5, "generate_effect", payload); });
        std::cout << checks << " permission checks passed\n";
        return 0;
    } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
