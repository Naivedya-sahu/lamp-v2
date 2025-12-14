# Tools Directory

Utilities for lamp-v2 development.

## font_to_header.py

Convert OTF/TTF fonts to C header files for embedding in rmkit applications.

### Usage

```bash
python3 tools/font_to_header.py INPUT.otf OUTPUT.h [FONT_NAME]
```

### Example

```bash
# Convert font
python3 tools/font_to_header.py MyFont.otf src/symbol_selector/font_embed.h SymbolFont

# Output will be in rmkit style:
# - Define: FONT_EMBED_NAME assets::SymbolFont_otf
# - Define: FONT_EMBED_LEN assets::SymbolFont_otf_len
# - Array: unsigned char SymbolFont_otf[] = {...}
```

### Integration with rmkit

Once generated, include the header in your rmkit app:

```cpp
#include "font_embed.h"

// Use with stb_truetype
stbtext::get_text_size("Hello", 24, FONT_EMBED_NAME, FONT_EMBED_LEN);
```

## Upcoming Tools

- `symbol_renderer.py` - Pre-render symbols for quick loading
- `circuit_validator.py` - Validate circuit connectivity
- `export_to_svg.py` - Export placed circuit to SVG
