# ELXNK - Electronic Component Drawing System for reMarkable 2
# Contextual Dataset for Development

## PROJECT OVERVIEW

**Name**: Elxnk (Electronic Ink)
**Purpose**: Native circuit schematic drawing tool for reMarkable 2 e-ink tablet
**Platform**: reMarkable 2 (ARM Linux, e-ink display, touch input)
**Language**: C++ (genie_lamp), Bash (utilities), Python (tools)

## SYSTEM ARCHITECTURE

### Core Components:

1. **lamp** - Drawing Engine
   - Location: `resources/rmkit/src/lamp/`
   - Modified version with erase support
   - Accepts pen commands via stdin
   - Commands: `pen down X Y`, `pen move X Y`, `pen up`, `erase on/off`
   - Draws directly to framebuffer
   - No rm2fb dependency for basic drawing

2. **genie_lamp** - Gesture Detection System
   - Location: `src/genie_lamp/`
   - Standalone C++ (no rmkit UI dependencies)
   - Reads touch events from `/dev/input/event2`
   - Multi-touch gesture detection
   - Config-driven command execution
   - Systemd service integration

3. **Component Library** - SVG Asset Management
   - Location: `assets/components/`
   - 16 electronic components as SVG files
   - Components: R, C, L, D, ZD, GND, VDC, VAC, OPAMP, NPN_BJT, PNP_BJT,
                 N_MOSFET, P_MOSFET, P_CAP, SW_OP, SW_CL

4. **Font System** - Text Rendering
   - Location: `assets/font/`
   - SVG-based font glyphs (A-Z, 0-9)
   - Segoe UI based paths
   - Scalable vector rendering

5. **UI State Machine** - Component Selection Interface
   - Location: `scripts/ui_state.sh`
   - Bottom-right UI box (1000,1400 to 1404,1872)
   - Paginated component list (5 items/page, 4 pages)
   - Preview mode for selected components
   - State persistence in `/tmp/genie_ui/`

## DEVELOPMENT TIMELINE

### Phase 1: Foundation (Initial Commits)
- lamp integration from rmkit
- Basic SVG component library
- Font system setup
- rm2fb submodule investigation

### Phase 2: Gesture System (Dec 15-16)
- Created standalone genie_lamp (no rmkit UI)
- Removed framebuffer::get() dependencies
- Config file support for gestures
- Systemd service integration
- 3-finger tap demo (square drawing)

### Phase 3: UI System (Dec 17)
- SVG to lamp converter (svg2lamp.sh)
- Component library manager
- Font text renderer
- State machine UI
- Gesture-driven navigation
- Test rendering system

## KEY TECHNICAL DECISIONS

### 1. No rm2fb Dependency for Core Functions
**Rationale**: rm2fb adds complexity and isn't needed for lamp drawing
**Implementation**: lamp draws directly to framebuffer
**Benefit**: Simpler deployment, fewer dependencies

### 2. Standalone genie_lamp
**Problem**: rmkit UI framework caused undefined reference errors
**Solution**: Rewrote as pure C++ using only Linux input API
**Result**: 254 lines of code, no complex dependencies

### 3. Bash-Based Utilities
**Constraint**: No jq available on reMarkable 2
**Solution**: Use sed/awk/grep for parsing
**Implementation**: SVG path parsing, config management, state machine

### 4. Dynamic Path Resolution
**Problem**: Hardcoded paths break deployment
**Solution**: Scripts detect their location and calculate project root
**Pattern**:
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
```

### 5. State Machine for UI
**Design**: Store state in /tmp/genie_ui/
**Variables**: page (current page), selected (item index), mode (list/preview)
**Commands**: init, redraw, next_page, prev_page, next_item, prev_item, select
**Benefit**: Stateless gesture handlers, easy debugging

## FILE STRUCTURE

```
lamp-v2/
├── assets/
│   ├── components/          # 16 SVG electronic symbols
│   │   ├── R.svg           # Resistor
│   │   ├── C.svg           # Capacitor
│   │   └── ...
│   ├── font/               # A-Z, 0-9 SVG glyphs
│   │   ├── segoe path_A.svg
│   │   └── ...
│   └── testing-utilities/   # RM2 test scripts
│       ├── rm2_diagnostic.sh
│       └── test_crosscompile.sh
│
├── src/
│   └── genie_lamp/         # Gesture detector
│       ├── main.cpp        # Standalone implementation
│       ├── Makefile        # Simple ARM cross-compile
│       ├── genie_lamp.conf # Example gesture config
│       ├── ui.conf         # UI control gestures
│       └── genie_lamp.service # Systemd service
│
├── scripts/                # Utility scripts
│   ├── svg2lamp.sh        # SVG → lamp converter
│   ├── component_library.sh # Component manager
│   ├── font_render.sh     # Text renderer
│   ├── ui_state.sh        # State machine
│   └── test_render_all.sh # Test script
│
├── resources/
│   └── rmkit/             # UI framework (lamp source)
│       └── src/lamp/      # Drawing engine
│
├── BUILD_INSTRUCTIONS.txt  # Genie build guide
├── UI_SYSTEM_README.txt    # UI system documentation
└── README.md              # Project overview
```

## GESTURE SYSTEM

### Config Format:
```
gesture=tap
fingers=3
command=echo "test" | /opt/bin/lamp
```

### Active Gestures (ui.conf):
- 4-finger tap: Show/Refresh UI
- 2-finger tap: Next Page
- 3-finger tap: Select Component (toggle preview)
- 5-finger tap: Next Item

## STATE MACHINE FLOW

```
[INIT]
  ↓
Build component list from assets/components/
  ↓
Create state file: page=0, selected=0, mode=list
  ↓
[IDLE] ← Wait for gesture
  ↓
Gesture detected → Update state → Redraw UI
  ↓
┌─────────────────────────────────┐
│ [LIST MODE]                     │
│ - Draw UI box border            │
│ - Show page indicator          │
│ - List current page items      │
│ - Highlight selected item      │
└─────────────────────────────────┘
  ↓ (select gesture)
┌─────────────────────────────────┐
│ [PREVIEW MODE]                  │
│ - Draw list (as above)         │
│ - Render selected component    │
│   in preview area              │
└─────────────────────────────────┘
  ↓ (select again)
Back to LIST MODE
```

## DRAWING PIPELINE

```
SVG File → svg2lamp.sh → lamp commands → lamp binary → framebuffer → screen
   ↓           ↓              ↓
Parse path   M→pen up      Direct
Extract d=   L→pen move    drawing
Scale/offset C→approx      No rm2fb
```

## DEPLOYMENT

### Build on Development Machine:
```bash
cd src/genie_lamp
make  # Requires arm-linux-gnueabihf-g++
```

### Deploy to reMarkable:
```bash
make install  # Copies binary, config, service
make enable   # Enable systemd service
make start    # Start service
```

### File Locations on reMarkable:
- Binary: `/opt/bin/genie_lamp`
- Config: `/opt/etc/genie_lamp.conf` or `/opt/etc/genie_ui.conf`
- Service: `/etc/systemd/system/genie_lamp.service`
- Scripts: `/home/root/lamp-v2/scripts/` (deployed as full directory)
- Assets: `/home/root/lamp-v2/assets/` (components and fonts)

## DEPENDENCIES

### Development Machine:
- arm-linux-gnueabihf-g++ (ARM cross-compiler)
- Python 3.9+ (for tools, not runtime)
- bash, sed, awk, bc (for scripts)

### reMarkable 2:
- Linux kernel with input API
- bash (included in base system)
- systemd (for service management)
- lamp binary (custom build)
- NO jq, NO rm2fb, NO fbink required

## KNOWN ISSUES & LIMITATIONS

1. **SVG Path Parsing**: Only handles M, L, H, V, C commands
   - Curves are approximated with endpoints
   - Complex paths may need simplification

2. **Text Rendering**: Fixed character width
   - No proportional spacing
   - Uppercase only (A-Z, 0-9)

3. **UI Constraints**: Fixed bottom-right position
   - 404x472px box
   - Not repositionable (by design)

4. **Component Scale**: SVG viewBox varies
   - Some components may need manual scale adjustment
   - Default scale works for most

5. **Touch Precision**: Multi-touch can be finicky
   - Gesture cooldown prevents double-triggers
   - 30-frame cooldown between gestures

## TESTING

### Test Rendering:
```bash
bash scripts/test_render_all.sh
```
Renders all 16 components + alphabet, then erases.

### Test UI:
```bash
bash scripts/ui_state.sh init
bash scripts/ui_state.sh redraw
```

### Test Gestures:
Deploy ui.conf and trigger gestures on device.

## FUTURE ENHANCEMENTS

### Planned:
- Swipe gestures for page navigation
- Component rotation
- Wire drawing mode
- Save/load schematics
- Component search/filter

### Under Consideration:
- Multi-component preview
- Undo/redo
- Grid snapping
- Component library extension

## BUILD SYSTEM

### lamp:
Built via rmkit system:
```bash
cd resources/rmkit
make lamp TARGET=rm
```

### genie_lamp:
Standalone Makefile:
```bash
cd src/genie_lamp
make
```

### Scripts:
No build required - deploy as-is.
Ensure executable: `chmod +x scripts/*.sh`

## VERSION CONTROL

**Main Branch**: Development branch
**Feature Branch**: `claude/genie-gesture-detection-fork-czL43`
**New Repo**: Elxnk (context-only, documentation)

## CODE STYLE

### Bash Scripts:
- POSIX-compliant where possible
- Functions use local variables
- Error checking on critical operations
- Comments explain "why", code shows "what"

### C++:
- C++11 standard
- Minimal STL (map, vector, set, string)
- No exceptions in critical paths
- RAII for resource management

### Config Files:
- Key=value format
- Comments start with #
- Blank lines separate entries
- Case-sensitive keys

## PERFORMANCE NOTES

- UI redraw: ~500ms for full refresh
- Component render: ~100-200ms per component
- Text render: ~50ms per character
- Gesture detection: <10ms latency
- State file I/O: negligible (<1ms)

## SECURITY CONSIDERATIONS

- Scripts run as root (systemd service)
- No input validation on config files
- Command injection possible via config
- Intended for trusted single-user device

**Mitigation**: Config files in /opt/etc/ (root-only write)

## DEBUGGING

### Check gesture service:
```bash
systemctl status genie_lamp
journalctl -u genie_lamp -f
```

### Check UI state:
```bash
cat /tmp/genie_ui/state.txt
cat /tmp/genie_ui/components.txt
```

### Test lamp directly:
```bash
echo "pen down 500 500" | lamp
echo "pen move 600 600" | lamp
echo "pen up" | lamp
```

### Verify touch events:
```bash
cat /dev/input/event2 | od -x
```

## REFERENCES

- reMarkable 2 specs: 1404x1872 monochrome e-ink
- Touch device: /dev/input/event2 (multitouch)
- Framebuffer: /dev/fb0 (direct access)
- rmkit: UI framework (not used in core)
- SVG spec: https://www.w3.org/TR/SVG/paths.html

## GLOSSARY

- **lamp**: Drawing engine, accepts pen commands
- **genie_lamp**: Gesture detector daemon
- **component**: Electronic schematic symbol (SVG)
- **glyph**: Individual font character (SVG)
- **state machine**: UI controller (bash script)
- **gesture**: Multi-touch input pattern
- **framebuffer**: Direct screen memory access
- **rm2fb**: reMarkable 2 framebuffer shim (NOT USED)

## CONTACT & CONTRIBUTION

Original repository: lamp-v2
Context repository: Elxnk
Platform: reMarkable 2

---
Generated: 2025-12-17
For: Elxnk context repository
Status: Development complete, deployment ready
