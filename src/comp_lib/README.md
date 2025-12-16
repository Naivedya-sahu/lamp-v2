# Component Library UI System

Interactive gesture-controlled component stamping for reMarkable 2.

**Key Feature**: Operates in dedicated mode to avoid conflicts with Xochitl gestures.

## Quick Start

```bash
# 1. Build and test locally
./test_stage1_library_build.sh

# 2. Deploy to RM2
./deploy_comp_lib.sh 10.11.99.1

# 3. On RM2, use 5-finger tap to activate Component Mode
# 4. Use 4-finger tap to show/hide palette
# 5. Use 4-finger swipe down to exit Component Mode
```

## Architecture

```
NORMAL MODE (default)
├─ Xochitl gestures work normally
├─ genie_lamp (activation listener) running
└─ Waiting for 5-finger tap

COMPONENT MODE (activated by 5-finger tap)
├─ Green corner indicator visible
├─ Main UI gestures active
├─ Component palette available
└─ Xochitl gestures disabled
```

## Files

### Scripts
- `deploy_comp_lib.sh` - One-shot deployment
- `svg_to_lamp.sh` - SVG to lamp converter
- `build_component_library.py` - Library builder
- `test_stage*.sh` - Progressive testing (6 stages)

### Components
- `symbol_ui_mode.py` - Mode activation manager
- `symbol_ui_controller.py` - UI state and rendering

### Configuration
- `symbol_ui_activation.conf` - 5-finger activation gesture
- `symbol_ui_main.conf` - Main UI gestures (conflict-free)
- `symbol_ui_activation.service` - Always-on service
- `symbol_ui_main.service` - On-demand service

## Gesture Map

### Activation (Always Available)
- **5-finger tap** → Enter Component Mode
- **4-finger swipe down** → Exit Component Mode

### Component Mode (When Active)
- **4-finger tap** → Show/hide palette
- **3-finger swipe up/down** (palette zone) → Scroll list
- **2-finger tap** (palette zone) → Select component
- **2-finger tap** (canvas zone) → Place component
- **3-finger swipe left/right** (canvas) → Scale
- **4-finger swipe up** → Clear screen

## Testing

Run tests in order:

```bash
./test_stage1_library_build.sh         # Local validation
./test_stage2_connectivity.sh          # RM2 connection
./test_stage3_mode_manager.sh          # Mode activation
./test_stage4_controller.sh            # UI logic
./test_stage5_gestures.sh              # Gesture integration
./test_stage6_full_system.sh           # Complete workflow
```

## Files on RM2

```
/opt/bin/
├── lamp
├── genie_lamp
├── symbol_ui_mode
└── symbol_ui_controller

/opt/etc/
├── symbol_library.json
├── symbol_ui_activation.conf
└── symbol_ui_main.conf

/etc/systemd/system/
├── symbol_ui_activation.service
└── symbol_ui_main.service
```

## Documentation

- `SYSTEM_ARCHITECTURE.md` - Technical details
- `GESTURE_REFERENCE.md` - Complete gesture guide
- `TROUBLESHOOTING.md` - Common issues

## No Xochitl Conflicts

The system uses:
- 5-finger tap (unique)
- 4-finger gestures (unused by Xochitl)
- 3-finger gestures (unused by Xochitl)
- 2-finger taps (only when mode active)

Xochitl's 2-finger swipes and 3-finger taps are **not used**.
