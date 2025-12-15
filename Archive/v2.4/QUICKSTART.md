# Quick Start Guide

## Setup

```bash
pip3 install svgpathtools numpy scipy
```

## Test Components

### Render to Screen
```bash
# Dry run (no RM2 needed)
bash src/draw_component.sh assets/components/R.svg \
  --width 200 --height 100 --x 500 --y 500 --dry-run

# Deploy to RM2
bash src/draw_component.sh assets/components/OPAMP.svg \
  --width 300 --height 200 --x 700 --y 900 --rm2 10.11.99.1
```

## Test Gestures

```bash
cd resources/rmkit
ln -sf ../../src/genie_test src/
make genie_test
scp src/build/genie_test root@10.11.99.1:/home/root/
ssh root@10.11.99.1 './genie_test'
```

**Test:** 2-finger swipes, 2-finger tap

## Test Fonts

```bash
cd src/font_test
make
./font_test

# For RM2 (requires ARM cross-compiler)
make arm
scp font_test.arm root@10.11.99.1:/home/root/font_test
ssh root@10.11.99.1 './font_test'
```

**Expected:** Shows font metrics and validates TrueType outlines

**If CFF/outlines warning:** See [FONT_GUIDE.md](FONT_GUIDE.md) - convert OTF to TTF

## Font Integration

See **[FONT_GUIDE.md](FONT_GUIDE.md)** for complete font setup.

**Quick:**
```bash
# If you have OTF (may cause outlined text)
fontforge -lang=ff -c 'Open("Monocraft.otf"); Generate("Monocraft.ttf")'

# Convert to C header
python3 tools/font_to_lamp.py \
  resources/Monocraft.ttf \
  src/symbol_selector/font_embed.h \
  Monocraft
```

## Components

R, C, L, D, ZD, GND, VDC, VAC, OPAMP, NPN_BJT, PNP_BJT, N_MOSFET, P_MOSFET, P_CAP, SW_OP, SW_CL

## Troubleshooting

**Outlined text instead of filled?**  
→ See [FONT_GUIDE.md](FONT_GUIDE.md) - Convert OTF to TTF

**Component symbols missing strokes?**  
→ Install: `pip3 install svgpathtools`

**Can't connect to RM2?**  
→ Settings → Storage → USB web interface for IP  
→ Install Toltec for SSH access

## File Structure

```
lamp-v2/
├── QUICKSTART.md (this)      # Quick reference
├── FONT_GUIDE.md            # Font troubleshooting
├── assets/components/       # 16 SVG symbols
├── src/
│   ├── genie_test/         # Gesture test
│   ├── font_test/          # Font test
│   └── symbol_selector/    # Main app (WIP)
└── tools/
    └── font_to_lamp.py     # Font converter
```
