#pragma once
#include <Windows.h>
#include <cymcp/core.hpp>
#include <algorithm>
#include <fstream>
#include <regex>
#include <set>
namespace cyrs::sdk {
using namespace cymcp;
inline Json discover_pipes() {
    Json result = Json::array(); WIN32_FIND_DATAW data{};
    HANDLE find = FindFirstFileW(L"\\\\.\\pipe\\CyRSAssistant-*", &data);
    if (find != INVALID_HANDLE_VALUE) {
        do { result.push_back("\\\\.\\pipe\\" + path_utf8(data.cFileName)); } while (FindNextFileW(find, &data));
        FindClose(find);
    }
    std::sort(result.begin(), result.end()); return result;
}
class Pipe {
    std::mutex mutex_;
    std::string name_;
    static void transfer(HANDLE pipe, void* data, DWORD size, bool write, const CallContext& c) {
        auto deadline = Clock::now() + std::chrono::seconds(10);
        while (size) {
            c.cancellation.check(); OVERLAPPED op{}; op.hEvent = CreateEventW(nullptr, TRUE, FALSE, nullptr);
            if (!op.hEvent) throw Error("Transport", "Cannot create pipe event");
            DWORD count = 0; BOOL ok = write ? WriteFile(pipe, data, size, &count, &op) : ReadFile(pipe, data, size, &count, &op);
            if (!ok && GetLastError() == ERROR_IO_PENDING) {
                while (WaitForSingleObject(op.hEvent, 50) == WAIT_TIMEOUT && !c.cancellation.cancelled() && Clock::now() < deadline) {}
                if (c.cancellation.cancelled() || Clock::now() >= deadline) {
                    CancelIoEx(pipe, &op); GetOverlappedResult(pipe, &op, &count, TRUE); CloseHandle(op.hEvent);
                    c.cancellation.check(); throw Error("Timeout", "Bridge timeout; read state before retrying an action");
                }
                ok = GetOverlappedResult(pipe, &op, &count, FALSE);
            }
            CloseHandle(op.hEvent);
            if (!ok || !count) throw Error("Transport", "Add-on disconnected; an action may already have run");
            data = static_cast<char*>(data) + count; size -= count;
        }
    }
  public:
    explicit Pipe(std::string name = {}) : name_(std::move(name)) {}
    Json call(const std::string& method, Json args = Json::object(), const CallContext& c = {}) {
        std::lock_guard lock(mutex_);
        if (name_.empty()) {
            auto pipes = discover_pipes();
            if (pipes.size() != 1) throw Error("InstanceRequired", "Use --pipe: exactly one running add-on must be selected");
            name_ = pipes[0];
        }
        const std::string prefix = R"(\\.\pipe\CyRSAssistant-)";
        if (!name_.starts_with(prefix) || name_.size()==prefix.size() || name_.substr(prefix.size()).find_first_not_of("0123456789")!=std::string::npos)
            throw Error("InvalidArguments", "Expected a local CyRSAssistant named pipe");
        args["protocol"] = 1; args["request_id"] = random_token(16); args["method"] = method;
        const auto bytes = args.dump();
        if (bytes.size() > 1024 * 1024) throw Error("SizeLimit", "Bridge request exceeds 1 MiB");
        HANDLE h = INVALID_HANDLE_VALUE;
        auto deadline = Clock::now() + std::chrono::seconds(3);
        do {
            c.cancellation.check(); h = CreateFileA(name_.c_str(), GENERIC_READ | GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, nullptr);
            if (h != INVALID_HANDLE_VALUE) break;
            if (Clock::now() >= deadline) throw Error("InstanceUnavailable", "Selected add-on is not reachable");
            std::this_thread::sleep_for(std::chrono::milliseconds(25));
        } while (true);
        struct Close { HANDLE h; ~Close() { CloseHandle(h); } } close{h};
        uint32_t length = static_cast<uint32_t>(bytes.size());
        transfer(h, &length, 4, true, c); transfer(h, const_cast<char*>(bytes.data()), length, true, c);
        transfer(h, &length, 4, false, c);
        if (!length || length > 8 * 1024 * 1024) throw Error("SizeLimit", "Invalid bridge response size");
        std::string response(length, '\0'); transfer(h, response.data(), length, false, c);
        char ack = 1; transfer(h, &ack, 1, true, c);
        auto result = parse_json(response, 8 * 1024 * 1024);
        if (!result.value("ok", false)) throw Error("ApplicationError", result.value("error", "Add-on operation failed"));
        return result;
    }
    const std::string& name() const { return name_; }
    std::uint64_t runtime(std::uint64_t requested, const CallContext& c = {}) {
        auto sessions = call("list_sessions", {}, c).at("runtimes");
        if (requested) {
            for (const auto& s : sessions) if (s.at("runtime") == requested) return requested;
            throw Error("InstanceRequired", "Requested runtime does not exist");
        }
        if (sessions.size() != 1) throw Error("InstanceRequired", "Use --runtime when the selected add-on has several runtimes");
        return sessions[0].at("runtime");
    }
    Json state(std::uint64_t runtime, const CallContext& c = {}) { return call("get_state", {{"runtime", runtime}}, c).at("state"); }
};
inline Json source_page(const Json& state, const Json& args, const CallContext& context) {
    const auto name = args.at("file").get<std::string>();
    const auto relative = std::filesystem::u8path(name);
    auto ext = relative.extension().string(); std::transform(ext.begin(), ext.end(), ext.begin(), [](unsigned char c){return char(std::tolower(c));});
    if (name.find_first_of("/\\:") != std::string::npos || (ext != ".fx" && ext != ".fxh")) throw Error("InvalidArguments", "Use an exact FX/FXH filename");
    std::set<std::filesystem::path> matches;
    for (auto entry : state.at("search_paths")) {
        auto value = entry.get<std::string>(); const bool recursive = value.size() >= 3 && value.substr(value.size()-3).find("**") != std::string::npos;
        if (recursive) value.resize(value.size()-3);
        auto root = std::filesystem::u8path(value);
        if (root.is_relative()) root = std::filesystem::u8path(state.at("base_path").get<std::string>()) / root;
        std::error_code ec; root = std::filesystem::weakly_canonical(root, ec);
        if (ec || !std::filesystem::is_directory(root)) continue;
        const auto add = [&](const std::filesystem::path& path) {
            std::error_code error; auto real = std::filesystem::canonical(path, error);
            if (error || !std::filesystem::is_regular_file(real)) return;
            auto delta = real.lexically_relative(root);
            if (!delta.empty() && *delta.begin() != "..") matches.insert(real);
        };
        if (recursive) {
            size_t visited = 0;
            for (const auto& file : std::filesystem::recursive_directory_iterator(root, std::filesystem::directory_options::skip_permission_denied)) {
                context.cancellation.check(); if (++visited > 100000) throw Error("SizeLimit", "Shader directory traversal limit reached");
                if (file.path().filename() == relative) add(file.path());
            }
        } else add(root / relative);
    }
    if (matches.size() != 1) throw Error("AmbiguousSource", "FX source is missing or ambiguous across configured roots");
    std::ifstream file(*matches.begin(), std::ios::binary);
    std::string text(1024 * 1024 + 1, '\0'); file.read(text.data(), text.size()); text.resize(static_cast<size_t>(file.gcount()));
    if (text.size() > 1024 * 1024) throw Error("SizeLimit", "FX source exceeds 1 MiB");
    const auto hash = sha256(text); size_t offset = args.value("offset", size_t(0));
    if (offset > text.size() || (offset < text.size() && (static_cast<unsigned char>(text[offset]) & 0xc0) == 0x80)) throw Error("InvalidArguments", "Offset is not a UTF-8 byte boundary");
    size_t end = std::min(text.size(), offset+24000);
    while (end < text.size() && (static_cast<unsigned char>(text[end]) & 0xc0) == 0x80) --end;
    return {{"file", name}, {"sha256", hash}, {"source", text.substr(offset, end-offset)}, {"offset", offset}, {"bytes", text.size()}, {"next_offset", end < text.size() ? Json(end) : Json(nullptr)}};
}
}
