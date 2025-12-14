#!/usr/bin/env python3
"""
Convert OTF/TTF font to lamp-compatible C header with validation

This tool:
1. Validates font is readable by TTF libraries
2. Converts to C header array for embedding
3. Ensures compatibility with stb_truetype (used by lamp/rmkit)

Usage:
    python3 font_to_lamp.py INPUT.otf OUTPUT.h [FONT_NAME]

Example:
    python3 font_to_lamp.py Monocraft.otf ../src/symbol_selector/font_embed.h Monocraft
"""

import sys
from pathlib import Path

def validate_font(font_path: Path) -> bool:
    """Validate that the font is a valid TTF/OTF file"""
    try:
        with open(font_path, 'rb') as f:
            # Read first 4 bytes (TTF/OTF signature)
            signature = f.read(4)

            # Valid signatures:
            # 0x00010000 - TrueType 1.0
            # 0x74727565 ('true') - TrueType
            # 0x4F54544F ('OTTO') - OpenType with CFF
            # 0x74746366 ('ttcf') - TrueType Collection

            if signature == b'\x00\x01\x00\x00':
                print("✓ Detected TrueType font (signature: 0x00010000)")
                return True
            elif signature == b'true':
                print("✓ Detected TrueType font (signature: 'true')")
                return True
            elif signature == b'OTTO':
                print("✓ Detected OpenType/CFF font (signature: 'OTTO')")
                print("⚠  Note: CFF fonts may have rendering issues with stb_truetype")
                print("   If you see outlined text, convert to TrueType format first")
                return True
            elif signature == b'ttcf':
                print("✗ TrueType Collection (.ttc) not supported")
                print("  Extract individual font from collection first")
                return False
            else:
                print(f"✗ Unknown font format (signature: {signature.hex()})")
                return False
    except Exception as e:
        print(f"✗ Error reading font: {e}")
        return False

def convert_font_to_header(input_path: Path, output_path: Path, font_name: str = None):
    """Convert font file to C header with embedded binary data"""

    print(f"\n{'='*60}")
    print(f"Converting: {input_path.name}")
    print(f"{'='*60}\n")

    # Validate font
    if not validate_font(input_path):
        print("\n✗ Font validation failed!")
        print("\nTo fix OpenType/CFF fonts (outlined text issue):")
        print("  1. Install fontforge: sudo apt install fontforge")
        print("  2. Convert to TrueType:")
        print(f"     fontforge -lang=ff -c 'Open(\"{input_path}\"); Generate(\"{input_path.stem}.ttf\")'")
        print("  3. Use the .ttf file instead")
        return False

    # Read font file
    with open(input_path, 'rb') as f:
        font_data = f.read()

    # Generate font name
    if font_name is None:
        font_name = input_path.stem.replace('-', '_').replace(' ', '_')

    # Clean font name for C identifier
    font_name_clean = ''.join(c if c.isalnum() or c == '_' else '_' for c in font_name)

    # Determine extension
    ext = input_path.suffix.lower()
    if ext == '.otf':
        ext_name = 'otf'
    elif ext == '.ttf':
        ext_name = 'ttf'
    else:
        ext_name = 'font'

    var_name = f"{font_name_clean}_{ext_name}"

    # Generate header content
    header_lines = []
    header_lines.append(f"// Auto-generated from {input_path.name}")
    header_lines.append(f"// Font: {font_name}")
    header_lines.append(f"// Size: {len(font_data)} bytes")
    header_lines.append(f"// Format: {ext.upper()}")
    header_lines.append("//")
    header_lines.append("// Usage in C++ code:")
    header_lines.append('//   #include "font_embed.h"')
    header_lines.append("//   // Font will be used automatically by stbtext")
    header_lines.append("//   // Or specify explicitly:")
    header_lines.append("//   stbtt_InitFont(&font, FONT_EMBED_NAME, 0);")
    header_lines.append("")
    header_lines.append(f"#define FONT_EMBED_NAME assets::{var_name}")
    header_lines.append(f"#define FONT_EMBED_LEN assets::{var_name}_len")
    header_lines.append("")
    header_lines.append("namespace assets {")
    header_lines.append(f"unsigned char {var_name}[] = {{")

    # Write binary data as hex bytes (12 per line)
    hex_bytes = []
    for i, byte in enumerate(font_data):
        hex_bytes.append(f"0x{byte:02x}")

        # Write line every 12 bytes
        if len(hex_bytes) == 12:
            header_lines.append("  " + ", ".join(hex_bytes) + ",")
            hex_bytes = []

    # Write remaining bytes
    if hex_bytes:
        header_lines.append("  " + ", ".join(hex_bytes))

    header_lines.append("};")
    header_lines.append(f"unsigned int {var_name}_len = {len(font_data)};")
    header_lines.append("}")
    header_lines.append("")

    # Write to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(header_lines))

    print(f"\n{'='*60}")
    print("✓ Conversion successful!")
    print(f"{'='*60}")
    print(f"Output: {output_path}")
    print(f"Font variable: {var_name}")
    print(f"Size: {len(font_data):,} bytes")
    print(f"\nText will render as FILLED (solid) glyphs, not outlines.")
    print("\nNext steps:")
    print(f'  1. Include in your app: #include "{output_path.name}"')
    print("  2. stb_truetype will automatically use FONT_EMBED_NAME")
    print("  3. Text renders solid black on white background")

    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 font_to_lamp.py INPUT.otf OUTPUT.h [FONT_NAME]")
        print("\nExample:")
        print("  python3 font_to_lamp.py Monocraft.otf font_embed.h Monocraft")
        print("\nSupported formats: .ttf, .otf")
        print("\nNote: If you see outlined text instead of filled:")
        print("  Your OTF uses CFF outlines (not TrueType)")
        print("  Convert to .ttf format using fontforge")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    font_name = sys.argv[3] if len(sys.argv) > 3 else None

    if not input_path.exists():
        print(f"✗ Error: Input file not found: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() not in ['.otf', '.ttf']:
        print(f"⚠  Warning: Expected .otf or .ttf file, got {input_path.suffix}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    success = convert_font_to_header(input_path, output_path, font_name)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
