#include "bridge.hpp"
#include <sddl.h>
#include <array>
#include <map>

namespace cyrs {
void Bridge::start() {
    name_ = "\\\\.\\pipe\\CyRSAssistant-" + std::to_string(GetCurrentProcessId());
    stop_ = CreateEventW(nullptr, TRUE, FALSE, nullptr);
    if (!stop_) throw std::runtime_error("Cannot create bridge stop event");
    thread_ = std::thread([this] { run(); });
}
void Bridge::stop() {
    if (!stop_) return;
    SetEvent(stop_);
    if (thread_.joinable()) thread_.join();
    CloseHandle(stop_);
    stop_ = nullptr;
    std::lock_guard<std::mutex> lock(mutex_);
    queue_.clear();
}
std::shared_ptr<Request> Bridge::take(uint64_t runtime) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto it = queue_.begin(); it != queue_.end();) {
        if ((*it)->deadline < std::chrono::steady_clock::now()) { it = queue_.erase(it); continue; }
        if (!(*it)->body.contains("runtime") || (*it)->body["runtime"] == runtime) {
            auto result = *it;
            queue_.erase(it);
            return result;
        }
        ++it;
    }
    return {};
}
bool Bridge::transfer(HANDLE pipe, void *data, DWORD size, bool write) {
    while (size) {
        OVERLAPPED operation{};
        operation.hEvent = CreateEventW(nullptr, TRUE, FALSE, nullptr);
        if (!operation.hEvent) return false;
        DWORD count = 0;
        BOOL ok = write ? WriteFile(pipe, data, size, &count, &operation) : ReadFile(pipe, data, size, &count, &operation);
        if (!ok && GetLastError() == ERROR_IO_PENDING) {
            HANDLE events[] = {stop_, operation.hEvent};
            if (WaitForMultipleObjects(2, events, FALSE, 30000) == WAIT_OBJECT_0 + 1)
                ok = GetOverlappedResult(pipe, &operation, &count, FALSE);
            else {
                CancelIoEx(pipe, &operation);
                GetOverlappedResult(pipe, &operation, &count, TRUE);
                ok = FALSE;
            }
        }
        CloseHandle(operation.hEvent);
        if (!ok || !count) return false;
        data = static_cast<char *>(data) + count;
        size -= count;
    }
    return true;
}
void Bridge::run() {
    // Restrict access to the actual user SID, not all authenticated users.
    HANDLE token = nullptr;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &token)) return;
    DWORD bytes = 0;
    GetTokenInformation(token, TokenUser, nullptr, 0, &bytes);
    std::vector<char> storage(bytes);
    if (!GetTokenInformation(token, TokenUser, storage.data(), bytes, &bytes)) { CloseHandle(token); return; }
    CloseHandle(token);
    LPWSTR sid = nullptr;
    if (!ConvertSidToStringSidW(reinterpret_cast<TOKEN_USER *>(storage.data())->User.Sid, &sid)) return;
    const std::wstring sddl = L"D:P(A;;GA;;;" + std::wstring(sid) + L")";
    LocalFree(sid);
    PSECURITY_DESCRIPTOR descriptor = nullptr;
    if (!ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl.c_str(), SDDL_REVISION_1, &descriptor, nullptr)) return;
    SECURITY_ATTRIBUTES security{sizeof(security), descriptor, FALSE};
    std::map<std::string, std::pair<json, json>> cache;
    std::deque<std::string> order;
    size_t cache_bytes = 0;
    while (WaitForSingleObject(stop_, 0) != WAIT_OBJECT_0) {
        HANDLE pipe = CreateNamedPipeA(name_.c_str(), PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED | FILE_FLAG_FIRST_PIPE_INSTANCE,
            PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS, 1, 65536, 65536, 0, &security);
        if (pipe == INVALID_HANDLE_VALUE) break;
        OVERLAPPED connection{};
        connection.hEvent = CreateEventW(nullptr, TRUE, FALSE, nullptr);
        BOOL connected = ConnectNamedPipe(pipe, &connection);
        const auto error = GetLastError();
        if (!connected && error == ERROR_PIPE_CONNECTED) connected = TRUE;
        else if (!connected && error == ERROR_IO_PENDING) {
            HANDLE events[] = {stop_, connection.hEvent};
            if (WaitForMultipleObjects(2, events, FALSE, INFINITE) == WAIT_OBJECT_0 + 1) {
                DWORD ignored = 0;
                connected = GetOverlappedResult(pipe, &connection, &ignored, FALSE);
            } else {
                CancelIoEx(pipe, &connection);
                DWORD ignored = 0;
                GetOverlappedResult(pipe, &connection, &ignored, TRUE);
            }
        }
        CloseHandle(connection.hEvent);
        uint32_t length = 0;
        if (connected && transfer(pipe, &length, sizeof(length), false) && length > 0 && length <= 1024 * 1024) {
            std::string input(length, '\0');
            if (transfer(pipe, input.data(), length, false)) {
                json response;
                try {
                    const auto body = json::parse(input);
                    require(body.at("protocol") == 1, "Unsupported protocol version");
                    const auto id = body.at("request_id").get<std::string>();
                    require(!id.empty() && id.size() <= 100, "Invalid request id");
                    const auto previous = cache.find(id);
                    if (previous != cache.end()) {
                        require(previous->second.first == body, "Request id reused with a different payload");
                        response = previous->second.second;
                    } else {
                        auto request = std::make_shared<Request>();
                        request->body = body;
                        request->deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
                        auto result = request->result.get_future();
                        {
                            std::lock_guard<std::mutex> lock(mutex_);
                            while (!queue_.empty() && queue_.front()->deadline < std::chrono::steady_clock::now()) queue_.pop_front();
                            require(queue_.size() < 32, "Command queue is full");
                            queue_.push_back(request);
                        }
                        while (WaitForSingleObject(stop_, 0) != WAIT_OBJECT_0 &&
                            result.wait_for(std::chrono::milliseconds(20)) != std::future_status::ready &&
                            std::chrono::steady_clock::now() < request->deadline) {}
                        response = result.wait_for(std::chrono::milliseconds(0)) == std::future_status::ready ? result.get() :
                            json{{"ok", false}, {"error", "Runtime timeout; read state before retrying"}};
                        response["request_id"] = id;
                        // Polling state must not retain hundreds of full inventories in the game.
                        const auto method = body.at("method").get<std::string>();
                        if (method != "get_state" && method != "list_sessions" && method != "capture_frame" && method != "get_connection" && method != "connection_status" && method != "connect_provider" && method != "list_game_shaders" && method != "inspect_game_shader") {
                            cache_bytes += body.dump().size() + response.dump().size();
                            cache[id] = {body, response};
                            order.push_back(id);
                            while (order.size() > 256 || (cache_bytes > 16 * 1024 * 1024 && order.size() > 1)) {
                                const auto &entry = cache.at(order.front());
                                cache_bytes -= entry.first.dump().size() + entry.second.dump().size();
                                cache.erase(order.front()); order.pop_front();
                            }
                        }
                    }
                } catch (const std::exception &e) { response = {{"ok", false}, {"error", e.what()}}; }
                auto output = response.dump(-1, ' ', false, json::error_handler_t::replace);
                if (output.size() > 8 * 1024 * 1024)
                    output = R"({"ok":false,"error":"Runtime inventory exceeds the 8 MiB response limit"})";
                length = static_cast<uint32_t>(output.size());
                if (length <= 8 * 1024 * 1024 && transfer(pipe, &length, sizeof(length), true) &&
                    transfer(pipe, const_cast<char *>(output.data()), length, true)) {
                    // DisconnectNamedPipe discards unread bytes. Wait for receipt, cancellably.
                    char acknowledgement = 0;
                    transfer(pipe, &acknowledgement, 1, false);
                }
            }
        }
        DisconnectNamedPipe(pipe);
        CloseHandle(pipe);
    }
    LocalFree(descriptor);
}
}
