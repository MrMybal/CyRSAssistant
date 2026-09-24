#include "protocol.hpp"
#include <iostream>
using namespace cyrs;
int main() {
    int failures = 0, checks = 0;
    const auto state = json::parse(R"({"session":"test","runtime":1,"generation":2,"revision":3,"parameters":[{"id":0,"type":"float","readonly":false,"value":[0.5],"min":0,"max":1},{"id":1,"type":"uint","readonly":false,"value":[1]},{"id":2,"type":"bool","readonly":true,"value":[false]}],"techniques":[{"id":0,"value":false}]})");
    const auto valid = json::parse(R"({"session":"test","runtime":1,"generation":2,"revision":3,"changes":[{"kind":"parameter","id":0,"value":[0.7]}]})");
    auto test = [&](const char *name, json request, bool accept) {
        ++checks;
        bool accepted = true;
        try { validate_patch(state, request); } catch (const std::exception &) { accepted = false; }
        if (accepted != accept) { std::cerr << "FAIL: " << name << '\n'; ++failures; }
    };
    test("valid", valid, true);
    auto p = valid; p["generation"] = 1; test("stale generation", p, false);
    p = valid; p["revision"] = 2; test("stale revision", p, false);
    p = valid; p["runtime"] = 2; test("wrong runtime", p, false);
    p = valid; p["session"] = "other"; test("wrong session", p, false);
    p = valid; p["changes"][0]["id"] = 99u; test("unknown parameter", p, false);
    p = valid; p["changes"][0]["value"] = json::array({2}); test("bound", p, false);
    p = valid; p["changes"][0]["value"] = json::array({true}); test("bool is not numeric", p, false);
    p = valid; p["changes"][0]["value"] = json::array({0.2, 0.4}); test("shape", p, false);
    p = valid; p["changes"].push_back(p["changes"][0]); test("duplicate", p, false);
    p = valid; p["changes"][0]["id"] = 1u; p["changes"][0]["value"] = json::array({-1}); test("uint underflow", p, false);
    p["changes"][0]["value"] = json::array({4294967296ULL}); test("uint overflow", p, false);
    p["changes"][0]["value"] = json::array({1.5}); test("uint fractional", p, false);
    p["changes"][0]["value"] = json::array({4294967295ULL}); test("uint maximum", p, true);
    p = valid; p["changes"][0]["id"] = 2u; p["changes"][0]["value"] = json::array({true}); test("dynamic uniform", p, false);
    p = valid; p["changes"][0] = {{"kind", "technique"}, {"id", 0u}, {"value", true}}; test("technique toggle", p, true);
    p["changes"][0]["value"] = 1; test("technique type", p, false);
    std::cout << checks << " protocol checks, " << failures << " failures\n";
    return failures ? 1 : 0;
}
