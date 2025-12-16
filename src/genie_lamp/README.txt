GENIE_LAMP - Standalone Gesture Detector

Simplified gesture detector with config file support:
- NO rmkit dependencies
- Uses only standard C++ and Linux input API
- Reads touch events from /dev/input/event2
- Config file at /opt/etc/genie_lamp.conf
- Runs as systemd service

QUICK START:
  make              # Build
  make install      # Deploy binary + config + service
  make enable       # Enable service (start on boot)
  make start        # Start service

CONFIGURATION:
  Edit /opt/etc/genie_lamp.conf to customize gestures

LOGS:
  make logs         # View live logs
  journalctl -u genie_lamp -f

The old rmkit-based version is preserved in .old files.
