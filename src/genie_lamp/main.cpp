// Standalone gesture detector for reMarkable 2
// No rmkit dependencies - uses only Linux input API

#include <linux/input.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <map>
#include <vector>
#include <set>

#define TOUCH_DEVICE "/dev/input/event2"
#define MAX_TRACKING_ID 100

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

public:
    SimpleGestureDetector() : current_slot(0), has_pending(false) {
        pending_update.tracking_id = -1;
        pending_update.x = 0;
        pending_update.y = 0;
        pending_update.active = false;
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

            // Check for 3-finger tap
            if (active_ids.size() == 3) {
                detect_three_finger_tap();
            }
        }
    }

    void detect_three_finger_tap() {
        static bool gesture_fired = false;
        static int gesture_cooldown = 0;

        // Cooldown to prevent multiple triggers
        if (gesture_cooldown > 0) {
            gesture_cooldown--;
            return;
        }

        if (!gesture_fired && active_ids.size() == 3) {
            printf("3-finger tap detected!\n");
            run_draw_square_command();
            gesture_fired = true;
            gesture_cooldown = 30; // Cooldown frames
        }

        // Reset when fingers are lifted
        if (active_ids.size() < 3) {
            gesture_fired = false;
        }
    }

    void run_draw_square_command() {
        // Draw a 200x200 square at position (500, 500) using lamp
        const char* command =
            "echo 'pen down 500 500\npen move 900 500\npen move 900 900\npen move 500 900\npen move 500 500\npen up' | /opt/bin/lamp &";

        printf("Running command: %s\n", command);
        int ret = system(command);
        if (ret != 0) {
            fprintf(stderr, "Failed to run command, return code: %d\n", ret);
        }
    }

    int get_active_touch_count() const {
        return active_ids.size();
    }
};

int main(int argc, char** argv) {
    printf("Starting genie_lamp - standalone gesture detector\n");
    printf("Touch device: %s\n", TOUCH_DEVICE);

    int fd = open(TOUCH_DEVICE, O_RDONLY);
    if (fd < 0) {
        perror("Failed to open touch device");
        fprintf(stderr, "Make sure %s exists and is readable\n", TOUCH_DEVICE);
        return 1;
    }

    printf("Successfully opened touch device\n");
    printf("Waiting for 3-finger tap gesture...\n");

    SimpleGestureDetector detector;
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
