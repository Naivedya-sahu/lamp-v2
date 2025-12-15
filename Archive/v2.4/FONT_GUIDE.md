# Font Integration Guide

## Problem: Outlined Text

If you see **hollow/outlined text** instead of solid filled text, your OTF font uses CFF (PostScript) outlines instead of TrueType outlines.

**stb_truetype only supports TrueType outlines** - it will render CFF fonts as outlines only.

## Solution: Convert OTF to TTF

### Option 1: Using FontForge (Recommended)

```bash
# Install fontforge
sudo apt install fontforge

# Convert OTF to TTF
fontforge -lang=ff -c 'Open("Monocraft.otf"); Generate("Monocraft.ttf")'

# Use the .ttf file
python3 tools/font_to_lamp.py resources/Monocraft.ttf src/symbol_selector/font_embed.h
```

### Option 2: Using Online Converter

1. Visit: https://convertio.co/otf-ttf/
2. Upload Monocraft.otf
3. Download converted Monocraft.ttf
4. Use the .ttf file

## Usage

### 1. Convert Font to C Header

```bash
python3 tools/font_to_lamp.py INPUT.ttf OUTPUT.h [NAME]
```

**Example:**
```bash
python3 tools/font_to_lamp.py \
  resources/Monocraft.ttf \
  src/symbol_selector/font_embed.h \
  Monocraft
```

The tool will:
- ✓ Validate font format
- ⚠ Warn if CFF/OTF (may cause outlined text)
- ✓ Convert to C header
- ✓ Create FONT_EMBED_NAME and FONT_EMBED_LEN defines

### 2. Test Font Rendering

```bash
# Build test app
cd resources/rmkit
ln -sf ../../src/font_test src/
make font_test

# Deploy and run
scp src/build/font_test root@10.11.99.1:/home/root/
ssh root@10.11.99.1 './font_test'
```

**Expected:** Text appears **FILLED (solid black)**, not outlined.

### 3. Use in Your App

```cpp
#include "font_embed.h"

// Font is automatically loaded by stbtext::setup_font()
// Just create text widgets normally:

auto label = new ui::Text(100, 100, 400, 50, "Hello World");
label->set_style(ui::Stylesheet().font_size(24));
scene->add(label);
```

## Font Format Reference

| Format | Extension | stb_truetype Support | Rendering |
|--------|-----------|---------------------|-----------|
| TrueType | .ttf | ✓ Full | Filled glyphs |
| OpenType (TrueType) | .otf | ✓ Full | Filled glyphs |
| OpenType (CFF) | .otf | ⚠ Outlines only | Outlined glyphs |
| WOFF/WOFF2 | .woff | ✗ Not supported | - |

## Troubleshooting

**Q: Text appears as outlines, not filled**
A: Your OTF uses CFF outlines. Convert to TTF format (see above).

**Q: How do I know if my OTF is CFF or TrueType?**
A: Run `python3 tools/font_to_lamp.py YOUR.otf OUTPUT.h` - it will detect and warn you.

**Q: Font file is too large**
A: Font files are typically 50-500KB. If larger, consider subsetting (removing unused glyphs).

**Q: Can I use system fonts on RM2?**
A: Yes! Set RMKIT_DEFAULT_FONT environment variable:
```bash
export RMKIT_DEFAULT_FONT=/usr/share/fonts/ttf/noto/NotoMono-Regular.ttf
./your_app
```

## Quick Reference

```bash
# 1. Convert OTF to TTF (if needed)
fontforge -lang=ff -c 'Open("Font.otf"); Generate("Font.ttf")'

# 2. Convert to C header
python3 tools/font_to_lamp.py Font.ttf src/app/font_embed.h

# 3. Test rendering
cd resources/rmkit && ln -sf ../../src/font_test src/ && make font_test

# 4. Deploy
scp src/build/font_test root@10.11.99.1:/home/root/ && ssh root@10.11.99.1 './font_test'
```

## Files

- `tools/font_to_lamp.py` - Font converter with validation
- `src/font_test/` - Font rendering test app
- `resources/rmkit/src/rmkit/fb/stb_text.cpy` - Text rendering engine
