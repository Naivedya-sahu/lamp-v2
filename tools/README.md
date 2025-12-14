# Tools

## font_to_header.py

Convert OTF/TTF fonts to C headers for rmkit.

**Usage:**
```bash
python3 font_to_header.py INPUT.otf OUTPUT.h [NAME]
```

**Example:**
```bash
python3 font_to_header.py ../resources/Monocraft.otf ../src/symbol_selector/font_embed.h Monocraft
```

**Output:** C header with embedded font data compatible with stb_truetype.
