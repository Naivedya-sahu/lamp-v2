#!/usr/bin/env python3
"""
Convert OTF/TTF font file to C header for embedding in rmkit apps

Usage:
    python3 font_to_header.py input.otf output.h [FONT_NAME]

Example:
    python3 font_to_header.py MyFont.otf src/symbol_selector/font_embed.h MyFont

Output format (rmkit style):
    #define FONT_EMBED_NAME assets::MyFont_ttf
    #define FONT_EMBED_LEN assets::MyFont_ttf_len

    namespace assets {
    unsigned char MyFont_ttf[] = {
      0x00, 0x01, 0x00, 0x00, ...
    };
    unsigned int MyFont_ttf_len = 12345;
    }
"""

import sys
from pathlib import Path

def convert_font_to_header(input_path: Path, output_path: Path, font_name: str = None):
    """Convert font file to C header with embedded binary data"""

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
    with open(output_path, 'w') as f:
        f.write('\n'.join(header_lines))

    print(f"✓ Converted {input_path.name} → {output_path}")
    print(f"  Font name: {font_name}")
    print(f"  Variable: {var_name}")
    print(f"  Size: {len(font_data):,} bytes")
    print(f"\nTo use in C++ code:")
    print(f'  #include "{output_path.name}"')
    print(f"  stbtext::get_text_size(text, size, FONT_EMBED_NAME, FONT_EMBED_LEN);")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 font_to_header.py INPUT.otf OUTPUT.h [FONT_NAME]")
        print("\nExample:")
        print("  python3 font_to_header.py MyFont.otf font_embed.h MyFont")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    font_name = sys.argv[3] if len(sys.argv) > 3 else None

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() not in ['.otf', '.ttf']:
        print(f"Warning: Expected .otf or .ttf file, got {input_path.suffix}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    convert_font_to_header(input_path, output_path, font_name)

if __name__ == '__main__':
    main()
