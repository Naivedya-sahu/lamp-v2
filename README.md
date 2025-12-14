# lamp-v2 - Circuit Drawing for reMarkable 2

Native circuit schematic tool for RM2 e-ink tablet.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Setup and testing
- **[FONT_GUIDE.md](FONT_GUIDE.md)** - Font integration (OTF→TTF fix)
- **[RM2FB_NOTES.md](RM2FB_NOTES.md)** - Framebuffer setup for UI apps

## Quick Test

```bash
# Test component rendering (no rm2fb needed)
bash src/draw_component.sh assets/components/R.svg \
  --width 200 --height 100 --x 500 --y 500 --dry-run

# Test fonts (standalone, no rm2fb needed)
cd src/font_test && make && ./font_test

# Test gestures (requires rm2fb on RM2)
cd resources/rmkit && ln -sf ../../src/genie_test src/ && make genie_test
```

## Status

✅ **Complete:**
- 16 SVG circuit symbols
- High-fidelity SVG to relative coordinates
- Component rendering with bounding box handling
- Font validation tool (standalone)
- Gesture control test
- rm2fb submodule added

🚧 **In Progress:**
- Symbol Selector app (manual placement)
- Font integration

## Requirements

### On Development Machine:
- Python 3.9+ with svgpathtools, numpy, scipy
- g++ for building tools
- arm-linux-gnueabihf-g++ for RM2 cross-compilation

### On RM2 Device:
- **rm2fb** (for UI apps like genie_test)
  - Install via Toltec: `opkg install rm2fb`
  - Or build from `resources/rm2fb/`
  - See [RM2FB_NOTES.md](RM2FB_NOTES.md)
- **lamp** binary (for component rendering)
- SSH access (via Toltec or manual setup)

## Architecture

**Manual Symbol Placement:**
- Bottom-right symbol palette
- Tap to select, tap to place
- Gesture controls
- Simple JSON file format

## Submodules

```bash
# After cloning, init submodules
git submodule update --init --recursive

# Currently included:
# - resources/rm2fb: remarkable2-framebuffer
# - resources/rmkit: rmkit UI framework (already present)
```

## File Structure

```
lamp-v2/
├── README.md             # This file
├── QUICKSTART.md         # Setup guide
├── FONT_GUIDE.md         # Font integration
├── RM2FB_NOTES.md        # Framebuffer setup
├── assets/components/    # 16 SVG symbols
├── src/
│   ├── genie_test/      # Gesture test (needs rm2fb)
│   ├── font_test/       # Font validation (standalone)
│   └── symbol_selector/ # Main app (WIP)
├── resources/
│   ├── rm2fb/           # Framebuffer submodule
│   └── rmkit/           # UI framework
└── tools/
    └── font_to_lamp.py  # Font converter
```

## Components Available

R, C, L, D, ZD, GND, VDC, VAC, OPAMP, NPN_BJT, PNP_BJT, N_MOSFET, P_MOSFET, P_CAP, SW_OP, SW_CL
