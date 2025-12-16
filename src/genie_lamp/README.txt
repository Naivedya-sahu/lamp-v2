GENIE_LAMP - Standalone Gesture Detector

This is a simplified, standalone version of genie that:
- Has NO rmkit dependencies
- Uses only standard C++ and Linux input API
- Reads touch events directly from /dev/input/event2
- Detects 3-finger tap gesture
- Draws a square via lamp command

BUILD: make
DEPLOY: make install
RUN: ssh root@10.11.99.1 /opt/bin/genie_lamp

The old rmkit-based version is preserved in .old files.
