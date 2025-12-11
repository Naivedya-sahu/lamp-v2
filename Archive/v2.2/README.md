# lamp-v2 🧹

Enhanced version of [rmkit's lamp](https://github.com/rmkit-dev/rmkit) with **programmatic eraser support** and **custom component library** for reMarkable tablets.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![reMarkable](https://img.shields.io/badge/reMarkable-2-green.svg)](https://remarkable.com/)

## Features

### Eraser Support
- 🎨 Full eraser tool emulation via `BTN_TOOL_RUBBER` events
- 🔄 Dynamic self-clearing UI - menus erase and redraw themselves
- 🎭 Smooth transitions and animations
- ✅ Native integration - xochitl recognizes all strokes
- 📱 No rm2fb required - works on firmware 3.24+

### Component Library
- 📚 Extract individual symbols from 214-symbol electrical library
- 🔧 Configure visibility: `viewed`, `cycled`, or `hidden`
- 🔄 Cycle through favorite components with buttons
- 💾 Export symbols to individual SVG files
- 🎨 Integration with svg_to_lamp.py for drawing

## Quick Start

```bash
# Build enhanced lamp
./build_lamp_enhanced.sh

# Deploy to reMarkable
scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/

# Test eraser
echo "pen rectangle 100 100 500 500" | lamp
echo "eraser fill 100 100 500 500 15" | lamp

# Component library demo
./examples/component_library_demo.sh
```

## Eraser Commands

```bash
# Erase line
echo "eraser line x1 y1 x2 y2" | lamp

# Erase rectangle
echo "eraser rectangle x1 y1 x2 y2" | lamp

# Fill area with eraser strokes
echo "eraser fill x1 y1 x2 y2 [spacing]" | lamp

# Dense clearing
echo "eraser clear x1 y1 x2 y2" | lamp

# Low-level control
echo "eraser down x y" | lamp
echo "eraser move x y" | lamp
echo "eraser up" | lamp
```

## Component Library

```bash
# Initialize configuration
python3 component_library.py init

# List symbols
python3 component_library.py list

# Configure visibility
python3 component_library.py set g1087 cycled   # resistor
python3 component_library.py set g1263 viewed   # transistor
python3 component_library.py set g6082 hidden   # deprecated

# Export symbols
python3 component_library.py export --visibility cycled --output symbols/

# Draw on tablet
python3 svg_to_lamp.py symbols/g1087.svg 500 800 2.0 | lamp
```

## Utilities

**svg_to_lamp.py** - Convert SVG to lamp commands
```bash
python3 svg_to_lamp.py symbol.svg x y scale | lamp
```

**text_to_lamp.py** - Render text as vector strokes
```bash
python3 text_to_lamp.py "10kΩ" x y size | lamp
```

**component_selector.py** - Interactive component browser
```bash
python3 component_selector.py
# Commands: n (next), p (previous), c (current), e (export), q (quit)
```

## Repository Structure

```
lamp-v2/
├── README.md                           # This file
├── DEV_HISTORY.md                      # Development history
├── INSTALL.md                          # Install/use/uninstall guide
├── component_library.py                # Component library manager
├── component_selector.py               # Interactive selector
├── component_library_config.json       # Symbol configuration
├── svg_to_lamp.py                      # SVG to lamp converter
├── text_to_lamp.py                     # Text renderer
├── build_lamp_enhanced.sh              # Build script
├── test_eraser.sh                      # Eraser tests
├── lamp_eraser.patch                   # Eraser patch
└── examples/
    ├── component_library_demo.sh       # Component library demo
    ├── dynamic_ui_demo.sh              # Dynamic UI demo
    └── svg_symbols/
        ├── Electrical_symbols_library.svg  # 214 symbols
        ├── resistor.svg
        ├── capacitor.svg
        └── ground.svg
```

## Use Cases

### Dynamic Menus
```bash
# Draw menu
echo "pen rectangle 50 1400 350 1850" | lamp

# User selection...

# Transition to new screen
echo "eraser fill 50 1400 350 1850 15" | lamp
echo "pen rectangle 370 1400 670 1850" | lamp
```

### Component Palette
```bash
# Show component
python3 svg_to_lamp.py resistor.svg 700 1600 1.5 | lamp
python3 text_to_lamp.py "10kΩ" 720 1680 0.5 | lamp

# Clear preview area
echo "eraser fill 700 1400 1350 1850 15" | lamp
```

## How It Works

The reMarkable tablet recognizes `BTN_TOOL_RUBBER` events for eraser input. Just like lamp emulates `BTN_TOOL_PEN` for drawing, we emulate `BTN_TOOL_RUBBER` for erasing using the same coordinate system and event injection mechanism.

## Prerequisites

- ARM cross-compiler: `gcc-arm-linux-gnueabihf`, `g++-arm-linux-gnueabihf`
- [okp](https://github.com/raisjn/okp) transpiler
- Python 3.x
- reMarkable tablet (firmware 3.24+)

## Documentation

- **README.md** - This overview
- **DEV_HISTORY.md** - Development timeline and technical notes
- **INSTALL.md** - Complete installation, usage, and testing guide

## Compatibility

| Device | Firmware | Status |
|--------|----------|--------|
| reMarkable 2 | 3.24 | ✅ Tested |
| reMarkable 2 | 3.15-3.23 | ✅ Should work |
| reMarkable 1 | Any | ⚠️ Untested |

## License

MIT License - see LICENSE file.

Electrical symbols library: CC0 Public Domain (Wikimedia Commons)

## Credits

- Based on [rmkit](https://github.com/rmkit-dev/rmkit) by rmkit-dev
- Electrical symbols: Filip Dominec and contributors (Wikimedia Commons)
- Eraser support inspired by reMarkable input event analysis

## Related Projects

- [rmkit](https://github.com/rmkit-dev/rmkit) - Original reMarkable toolkit
- [remarkable-hacks](https://github.com/ddvk/remarkable-hacks) - Patches for xochitl
- [awesome-reMarkable](https://github.com/reHackable/awesome-reMarkable) - Community tools

---

**Made with ❤️ for the reMarkable community**
