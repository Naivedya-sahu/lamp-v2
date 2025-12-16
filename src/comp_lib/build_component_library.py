#!/usr/bin/env python3
"""
build_component_library.py - Build complete component and font library
Creates JSON library with lamp pen commands for all SVG assets
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List

def svg_to_lamp_commands(svg_path: Path, scale: int = 1, x: int = 0, y: int = 0, tolerance: float = 1.0) -> List[str]:
    """Convert SVG to lamp pen commands using svg_to_lamp.sh"""
    script_dir = Path(__file__).parent
    svg_to_lamp = script_dir / "svg_to_lamp.sh"
    
    if not svg_to_lamp.exists():
        raise FileNotFoundError(f"svg_to_lamp.sh not found at {svg_to_lamp}")
    
    # Build command with all arguments (script expects them in order)
    cmd = [
        "bash", str(svg_to_lamp),
        str(svg_path),
        str(scale),
        str(x),
        str(y),
        str(tolerance)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Parse commands line by line
        commands = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        return commands
    except subprocess.CalledProcessError as e:
        print(f"Error converting {svg_path.name}: {e.stderr}", file=sys.stderr)
        return []

def build_component_library(components_dir: Path) -> Dict:
    """Build library from components directory"""
    library = {}
    
    svg_files = sorted(components_dir.glob("*.svg"))
    if not svg_files:
        print(f"Warning: No SVG files found in {components_dir}", file=sys.stderr)
        return library
    
    print(f"Processing {len(svg_files)} component SVG files...")
    
    for svg_file in svg_files:
        component_name = svg_file.stem
        print(f"  {component_name}...", end=" ", flush=True)
        
        # Convert at unit scale for relative coordinates
        commands = svg_to_lamp_commands(svg_file, scale=1, tolerance=1.0)
        
        if commands:
            library[component_name] = {
                "type": "component",
                "source": str(svg_file.name),
                "commands": commands,
                "command_count": len(commands)
            }
            print(f"✓ ({len(commands)} commands)")
        else:
            print(f"✗ (failed)")
    
    return library

def build_font_library(font_dir: Path) -> Dict:
    """Build library from font directory"""
    library = {}
    
    svg_files = sorted(font_dir.glob("*.svg"))
    if not svg_files:
        print(f"Warning: No SVG files found in {font_dir}", file=sys.stderr)
        return library
    
    print(f"Processing {len(svg_files)} font glyph SVG files...")
    
    for svg_file in svg_files:
        # Extract character from filename
        # Format: "segoe path_X.svg" where X is the character
        stem = svg_file.stem
        if "_" in stem:
            char = stem.split("_")[-1]
        else:
            char = stem
        
        print(f"  '{char}'...", end=" ", flush=True)
        
        # Convert at unit scale for relative coordinates
        commands = svg_to_lamp_commands(svg_file, scale=1, tolerance=1.5)
        
        if commands:
            library[char] = {
                "type": "glyph",
                "char": char,
                "source": str(svg_file.name),
                "commands": commands,
                "command_count": len(commands)
            }
            print(f"✓ ({len(commands)} commands)")
        else:
            print(f"✗ (failed)")
    
    return library

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 build_component_library.py <components_dir> <font_dir> <output.json>")
        print("\nExample:")
        print("  python3 build_component_library.py ../../assets/components ../../assets/font library.json")
        sys.exit(1)
    
    components_dir = Path(sys.argv[1])
    font_dir = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    
    if not components_dir.exists():
        print(f"Error: Components directory not found: {components_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not font_dir.exists():
        print(f"Error: Font directory not found: {font_dir}", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 60)
    print("Building Component and Font Library")
    print("=" * 60)
    print()
    
    # Build components
    print("COMPONENTS:")
    components = build_component_library(components_dir)
    print()
    
    # Build font glyphs
    print("FONT GLYPHS:")
    font = build_font_library(font_dir)
    print()
    
    # Combine into single library
    library = {
        "components": components,
        "font": font,
        "stats": {
            "component_count": len(components),
            "glyph_count": len(font),
            "total_entries": len(components) + len(font)
        }
    }
    
    # Write library to JSON
    with open(output_path, 'w') as f:
        json.dump(library, f, indent=2)
    
    print("=" * 60)
    print(f"Library saved to: {output_path}")
    print(f"Components: {len(components)}")
    print(f"Glyphs: {len(font)}")
    print(f"Total entries: {len(components) + len(font)}")
    print("=" * 60)

if __name__ == '__main__':
    main()
