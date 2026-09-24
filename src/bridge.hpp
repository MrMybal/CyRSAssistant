#pragma once
#include "protocol.hpp"
#include <Windows.h>
#include <chrono>
#include <deque>
#include <future>
#include <memory>
#include <mutex>
#include <thread>

namespace cyrs {
struct Request {
    json body;
    std::promise<json> result;
    std::chrono::steady_clock::time_point deadline;
};
class Bridge {
public:
    void start();
    void stop();
    std::shared_ptr<Request> take(uint64_t runtime);
    const std::string &name() const { return name_; }
private:
    void run();
    bool transfer(HANDLE pipe, void *data, DWORD size, bool write);
    HANDLE stop_ = nullptr;
    std::thread thread_;
    std::mutex mutex_;
    std::deque<std::shared_ptr<Request>> queue_;
    std::string name_;
};
}
