# lamp-v2 Quick Start

Complete guide for circuit drawing on reMarkable 2.

## Setup

### 1. Install Dependencies
```bash
pip3 install svgpathtools numpy scipy
```

### 2. Convert Font (when Monocraft.otf is available)
```bash
python3 tools/font_to_header.py resources/Monocraft.otf src/symbol_selector/font_embed.h
```

## Test Components

### Draw Single Component
```bash
# Render resistor at 500x500, size 200x100
bash src/draw_component.sh assets/components/R.svg \
  --width 200 --height 100 --x 500 --y 500 --dry-run

# Show pins for debugging
bash src/draw_component.sh assets/components/OPAMP.svg \
  --width 300 --height 200 --x 700 --y 900 --show-pins --dry-run
```

### Deploy to RM2
```bash
# Replace 10.11.99.1 with your RM2 IP
bash src/draw_component.sh assets/components/R.svg \
  --width 200 --height 100 --x 500 --y 500 --rm2 10.11.99.1
```

## Test Gestures (Genie)

### 1. Build Test App
```bash
cd resources/rmkit
ln -sf ../../src/genie_test src/
make genie_test
```

### 2. Deploy to RM2
```bash
scp src/build/genie_test root@10.11.99.1:/home/root/
ssh root@10.11.99.1 './genie_test'
```

### 3. Test Gestures
- **2-finger swipe left**: Should show "SWIPE LEFT"
- **2-finger swipe right**: Should show "SWIPE RIGHT"
- **2-finger swipe up**: Should show "SWIPE UP"
- **2-finger swipe down**: Should show "SWIPE DOWN"
- **2-finger tap**: Should show "TWO FINGER TAP"

## Symbol Selector (Coming Soon)

Manual symbol placement tool with gesture control.

### Features
- Bottom-right symbol palette
- Tap to select, tap to place
- Gesture-based controls
- Manual wiring

### Build (once implemented)
```bash
cd src/symbol_selector
make
scp symbol_selector root@10.11.99.1:/home/root/
```

## File Structure

```
lamp-v2/
├── assets/components/        # 16 SVG symbols
├── src/
│   ├── svg_to_lamp_relative.py    # SVG → relative coords
│   ├── draw_component.sh          # Render to RM2
│   ├── genie_test/               # Gesture test app
│   └── symbol_selector/          # Main app (WIP)
├── tools/font_to_header.py   # Font converter
└── QUICKSTART.md            # This file
```

## Available Components

R, C, L, D, ZD, GND, VDC, VAC, OPAMP, NPN_BJT, PNP_BJT, N_MOSFET, P_MOSFET, P_CAP, SW_OP, SW_CL

## Troubleshooting

**Symbols missing strokes?**
→ Install: `pip3 install svgpathtools`

**Can't connect to RM2?**
→ Check IP in Settings → Storage → USB web interface
→ Enable SSH via Toltec

**Out of bounds rendering?**
→ Fixed - circuits auto-fit screen

## Next Steps

1. Upload Monocraft.otf to resources/
2. Convert font: `python3 tools/font_to_header.py resources/Monocraft.otf src/symbol_selector/font_embed.h`
3. Test gestures with genie_test
4. Build symbol selector
