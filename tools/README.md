# Development Tools

## font_to_lamp.py

Convert fonts to lamp-compatible C headers with validation.

**Usage:**
```bash
python3 font_to_lamp.py INPUT.ttf OUTPUT.h [NAME]
```

**Features:**
- ✓ Validates font format (TTF/OTF)
- ⚠ Detects CFF fonts (cause outlined text)
- ✓ Suggests conversion to TTF if needed
- ✓ Creates stb_truetype-compatible header

**Example:**
```bash
python3 font_to_lamp.py \
  ../resources/Monocraft.ttf \
  ../src/symbol_selector/font_embed.h \
  Monocraft
```

## Important: OTF vs TTF

**stb_truetype only fully supports TrueType outlines.**

- ✓ `.ttf` files → Filled glyphs
- ✓ `.otf` (TrueType-based) → Filled glyphs  
- ⚠ `.otf` (CFF-based) → **Outlined glyphs only**

**If you get outlined text, convert OTF to TTF:**
```bash
fontforge -lang=ff -c 'Open("Font.otf"); Generate("Font.ttf")'
```

See **[FONT_GUIDE.md](../FONT_GUIDE.md)** for details.
