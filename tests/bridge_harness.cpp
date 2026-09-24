#include "bridge.hpp"
#include <atomic>
#include <iostream>
int main() {
    cyrs::Bridge bridge;
    bridge.start();
    std::atomic<bool> done = false;
    std::thread pump([&] {
        unsigned processed = 0;
        while (!done.load()) {
            if (auto request = bridge.take(1)) {
                ++processed;
                request->result.set_value({{"ok", true}, {"echo", request->body}, {"processed", processed}});
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    });
    std::cout << bridge.name() << std::endl;
    std::cin.get();
    done = true;
    pump.join();
    bridge.stop();
    return 0;
}
