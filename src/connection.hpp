#pragma once
#include <filesystem>

// Credentials are session-only. Never serialize this object into the public inventory.
struct Connection {
    int provider = 0;
    std::array<char, 1024> endpoint{};
    std::array<char, 160> model{};
    std::array<char, 512> key{};
    uint64_t epoch = 0;
    bool wanted = false;
    ULONGLONG heartbeat = 0, started = 0;
    std::string phase = "disconnected", message = "Choose a provider, then click Connect.";
};
HMODULE addon_module = nullptr;
HANDLE companion_process = nullptr;

bool connected(const Connection &c) {
    return c.wanted && c.phase == "ready" && c.heartbeat && GetTickCount64() - c.heartbeat < 10000;
}
void launch_companion(const std::string &pipe_name, const std::string &language) {
    if (companion_process && WaitForSingleObject(companion_process, 0) == WAIT_TIMEOUT) return;
    if (companion_process) { CloseHandle(companion_process); companion_process = nullptr; }
    wchar_t path[32768]{};
    GetModuleFileNameW(addon_module, path, 32768);
    const auto executable = std::filesystem::path(path).parent_path() / L"CyRSAssistantCompanion.exe";
    if (!std::filesystem::is_regular_file(executable)) throw std::runtime_error("CyRSAssistantCompanion.exe is missing next to the add-on. Reinstall the complete package.");
    const std::wstring pipe(pipe_name.begin(), pipe_name.end());
    std::wstring command = L"\"" + executable.wstring() + L"\" --pipe \"" + pipe + L"\"";
    STARTUPINFOW startup{}; startup.cb = sizeof(startup);
    PROCESS_INFORMATION process{};
    if (!CreateProcessW(executable.c_str(), command.data(), nullptr, nullptr, FALSE, CREATE_NO_WINDOW, nullptr,
        executable.parent_path().c_str(), &startup, &process))
    {
        char message[512]{};
        std::snprintf(message, sizeof(message), i18n::translate(language, "Cannot start the local service (Windows %lu)."), GetLastError());
        throw std::runtime_error(message);
    }
    CloseHandle(process.hThread); companion_process = process.hProcess;
}
