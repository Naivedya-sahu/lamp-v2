# lamp-v2 - Circuit Drawing for reMarkable 2

Native circuit schematic tool for RM2 e-ink tablet.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Setup and testing guide
- **[FONT_GUIDE.md](FONT_GUIDE.md)** - Font integration (OTF→TTF, outlined text fix)

## Quick Test

```bash
# Test component rendering
bash src/draw_component.sh assets/components/R.svg \
  --width 200 --height 100 --x 500 --y 500 --dry-run

# Test gestures
cd resources/rmkit && ln -sf ../../src/genie_test src/ && make genie_test

# Test fonts
cd resources/rmkit && ln -sf ../../src/font_test src/ && make font_test
```

## Status

✅ **Complete:**
- 16 SVG circuit symbols (R, C, L, OPAMP, etc.)
- High-fidelity SVG to relative coordinates
- Component rendering with bounding box handling
- Gesture control test (genie)
- Font integration with validation

🚧 **In Progress:**
- Symbol Selector app (manual placement)
- Gesture-based symbol palette

## Architecture

**Manual Symbol Placement:**
- Bottom-right symbol palette
- Tap to select, tap to place
- Gesture controls for copy/delete/rotate
- Simple JSON file format
- No complex auto-layout needed

## Tech Stack

- **Language**: Python 3.9+, C++ (rmkit)
- **Framework**: rmkit (native RM2)
- **Graphics**: stb_truetype, SVG paths
- **Target**: reMarkable 2 (1404×1872)

## File Structure

```
lamp-v2/
├── QUICKSTART.md         # Setup guide
├── FONT_GUIDE.md         # Font integration
├── assets/components/    # 16 SVG symbols
├── src/
│   ├── genie_test/      # Gesture test app
│   ├── font_test/       # Font rendering test
│   └── symbol_selector/ # Main app (WIP)
└── tools/
    └── font_to_lamp.py  # Font converter
```

## Components Available

R, C, L, D, ZD, GND, VDC, VAC, OPAMP, NPN_BJT, PNP_BJT, N_MOSFET, P_MOSFET, P_CAP, SW_OP, SW_CL
