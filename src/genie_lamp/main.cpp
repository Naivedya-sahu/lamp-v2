// Standalone gesture detector for reMarkable 2
// No rmkit dependencies - uses only Linux input API

#include <linux/input.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <fstream>
#include <sstream>
#include <map>
#include <vector>
#include <set>

#define TOUCH_DEVICE "/dev/input/event2"
#define DEFAULT_CONFIG "/opt/etc/genie_lamp.conf"

struct GestureConfig {
    std::string gesture_type;  // "tap"
    int fingers;
    std::string command;

    GestureConfig() : fingers(0) {}
};

struct TouchPoint {
    int tracking_id;
    int x;
    int y;
    bool active;
};

class SimpleGestureDetector {
private:
    std::map<int, TouchPoint> touches;
    int current_slot;
    TouchPoint pending_update;
    bool has_pending;
    std::set<int> active_ids;
    std::vector<GestureConfig> gestures;
    std::map<int, bool> gesture_fired;      // Track if gesture with N fingers fired
    std::map<int, int> gesture_cooldown;    // Cooldown per finger count

public:
    SimpleGestureDetector() : current_slot(0), has_pending(false) {
        pending_update.tracking_id = -1;
        pending_update.x = 0;
        pending_update.y = 0;
        pending_update.active = false;
    }

    void load_config(const char* config_file) {
        std::ifstream file(config_file);
        if (!file.is_open()) {
            fprintf(stderr, "Warning: Could not open config file: %s\n", config_file);
            return;
        }

        GestureConfig current;
        std::string line;
        int gesture_count = 0;

        while (std::getline(file, line)) {
            // Trim whitespace
            size_t start = line.find_first_not_of(" \t\r\n");
            if (start == std::string::npos) {
                // Empty line - end of gesture definition
                if (!current.gesture_type.empty() && !current.command.empty()) {
                    gestures.push_back(current);
                    gesture_count++;
                    current = GestureConfig();
                }
                continue;
            }

            // Skip comments
            if (line[start] == '#') continue;

            line = line.substr(start);
            size_t end = line.find_last_not_of(" \t\r\n");
            if (end != std::string::npos) {
                line = line.substr(0, end + 1);
            }

            // Parse key=value
            size_t eq = line.find('=');
            if (eq == std::string::npos) continue;

            std::string key = line.substr(0, eq);
            std::string value = line.substr(eq + 1);

            if (key == "gesture") {
                current.gesture_type = value;
            } else if (key == "fingers") {
                current.fingers = atoi(value.c_str());
            } else if (key == "command") {
                current.command = value;
            }
        }

        // Don't forget last gesture
        if (!current.gesture_type.empty() && !current.command.empty()) {
            gestures.push_back(current);
            gesture_count++;
        }

        file.close();
        printf("Loaded %d gesture(s) from config\n", gesture_count);
    }

    void process_event(const struct input_event& ev) {
        if (ev.type == EV_ABS) {
            switch (ev.code) {
                case ABS_MT_SLOT:
                    current_slot = ev.value;
                    break;

                case ABS_MT_TRACKING_ID:
                    if (ev.value == -1) {
                        // Touch lifted
                        touches.erase(current_slot);
                        active_ids.erase(current_slot);
                    } else {
                        // New touch
                        pending_update.tracking_id = ev.value;
                        pending_update.active = true;
                        has_pending = true;
                        active_ids.insert(current_slot);
                    }
                    break;

                case ABS_MT_POSITION_X:
                    pending_update.x = ev.value;
                    has_pending = true;
                    break;

                case ABS_MT_POSITION_Y:
                    pending_update.y = ev.value;
                    has_pending = true;
                    break;
            }
        } else if (ev.type == EV_SYN && ev.code == SYN_REPORT) {
            // End of event frame
            if (has_pending && pending_update.active) {
                touches[current_slot] = pending_update;
                pending_update.active = false;
                has_pending = false;
            }

            // Check gestures
            detect_gestures();
        }
    }

    void detect_gestures() {
        int finger_count = active_ids.size();

        // Update cooldowns
        for (auto& pair : gesture_cooldown) {
            if (pair.second > 0) pair.second--;
        }

        // Reset gesture_fired when fingers are lifted
        if (finger_count == 0) {
            gesture_fired.clear();
        }

        // Check each configured gesture
        for (const auto& g : gestures) {
            if (g.gesture_type == "tap" && g.fingers == finger_count) {
                // Check cooldown
                if (gesture_cooldown[finger_count] > 0) continue;

                // Check if not already fired
                if (gesture_fired[finger_count]) continue;

                // Fire the gesture
                printf("%d-finger tap detected!\n", finger_count);
                run_command(g.command);
                gesture_fired[finger_count] = true;
                gesture_cooldown[finger_count] = 30; // Cooldown frames
            }
        }
    }

    void run_command(const std::string& cmd) {
        std::string command = cmd + " &";
        printf("Running: %s\n", command.c_str());

        int ret = system(command.c_str());
        if (ret != 0) {
            fprintf(stderr, "Warning: Command returned %d\n", ret);
        }

        // Small delay to let gesture reset
        usleep(50000);
    }

    int get_gesture_count() const {
        return gestures.size();
    }
};

int main(int argc, char** argv) {
    const char* config_file = DEFAULT_CONFIG;

    // Allow custom config file as argument
    if (argc > 1) {
        config_file = argv[1];
    }

    printf("Starting genie_lamp - standalone gesture detector\n");
    printf("Config file: %s\n", config_file);
    printf("Touch device: %s\n", TOUCH_DEVICE);

    SimpleGestureDetector detector;
    detector.load_config(config_file);

    if (detector.get_gesture_count() == 0) {
        fprintf(stderr, "Error: No gestures configured!\n");
        fprintf(stderr, "Please create a config file at %s\n", config_file);
        return 1;
    }

    int fd = open(TOUCH_DEVICE, O_RDONLY);
    if (fd < 0) {
        perror("Failed to open touch device");
        fprintf(stderr, "Make sure %s exists and is readable\n", TOUCH_DEVICE);
        return 1;
    }

    printf("Successfully opened touch device\n");
    printf("Waiting for gestures...\n");

    struct input_event ev;

    while (true) {
        ssize_t n = read(fd, &ev, sizeof(ev));
        if (n != sizeof(ev)) {
            if (n < 0) {
                perror("Error reading from touch device");
            }
            break;
        }

        detector.process_event(ev);
    }

    close(fd);
    return 0;
}
