#!/usr/bin/env python3
"""Quick script to build anchor-relative component library"""

import sys
from pathlib import Path

# Add project files to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, "/mnt/project")

from component_library_builder import AnchorRelativeConverter

svg_dir = Path(__file__).parent / "assets" / "components"
output_path = Path(__file__).parent / "src" / "component_library_anchor.json"

converter = AnchorRelativeConverter()
converter.build_library(svg_dir, output_path)

print(f"\nLibrary saved to: {output_path}")
