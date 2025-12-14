# lamp-v2 - Circuit Drawing for reMarkable 2

Native circuit schematic tool for RM2 e-ink tablet.

## Quick Links

- **[QUICKSTART.md](QUICKSTART.md)** - Complete setup and usage guide
- **Components**: 16 pre-made symbols in `assets/components/`
- **Tools**: Font converter in `tools/`

## Current Status

✅ **Working**:
- SVG to relative coordinates conversion (high fidelity)
- Component rendering to RM2
- 16 standardized symbols (R, C, L, OPAMP, transistors, etc.)
- Bounding box handling (auto-fit screen)

🚧 **In Progress**:
- Symbol Selector app (manual placement tool)
- Gesture controls via genie
- Font integration (awaiting Monocraft.otf)

## Quick Test

```bash
# Test component rendering
bash src/draw_component.sh assets/components/R.svg \
  --width 200 --height 100 --x 500 --y 500 --dry-run

# Test gestures
cd resources/rmkit && ln -sf ../../src/genie_test src/ && make genie_test
```

## Architecture

**Old Approach** (v2.1-v2.3): Auto-layout with topology detection
- Too complex for textbook-style diagrams
- Difficult to control exact placement

**New Approach** (v2.4+): Manual symbol placement
- Bottom-right symbol palette
- Gesture-based controls
- Tap to select, tap to place
- Simple and intuitive

## Tech Stack

- **Language**: Python 3.9+, C++ (rmkit)
- **Framework**: rmkit (native RM2 UI)
- **Graphics**: SVG paths → relative coordinates
- **Font**: stb_truetype
- **Target**: reMarkable 2 (1404×1872)

## Development

See **[QUICKSTART.md](QUICKSTART.md)** for:
- Setup instructions
- Build commands
- Testing procedures
- Troubleshooting

## File Structure

```
lamp-v2/
├── assets/components/      # 16 SVG symbols
├── src/
│   ├── genie_test/        # Gesture test app
│   ├── symbol_selector/   # Main app (WIP)
│   └── *.py, *.sh         # Utilities
├── tools/                 # Development tools
├── QUICKSTART.md         # Setup guide
└── README.md            # This file
```

## License

See repository license file.
