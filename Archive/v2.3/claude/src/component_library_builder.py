#!/usr/bin/env python3
"""
Layer 1: Component Library Builder
Converts all SVG symbols to pen commands with anchor point metadata
Generates a header file for circuit assembly
"""

import xml.etree.ElementTree as ET
import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import subprocess

@dataclass
class Pin:
    """Pin with ID and coordinates"""
    id: str
    x: float
    y: float

@dataclass
class Component:
    """Component with pen commands and pin locations"""
    name: str
    width: float
    height: float
    pins: List[Pin]
    pen_commands: List[str]
    bounds: Tuple[float, float, float, float]  # min_x, min_y, max_x, max_y

class ComponentLibraryBuilder:
    """Builds component library from SVG files"""
    
    def __init__(self, components_dir: str):
        self.components_dir = Path(components_dir)
        self.components: Dict[str, Component] = {}
        
    def extract_pins_from_svg(self, svg_path: Path) -> List[Pin]:
        """Extract pin anchor points from SVG"""
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        pins = []
        for elem in root.iter():
            tag = elem.tag.split('}')[-1]
            if tag == 'circle':
                pin_id = elem.get('id', '')
                if pin_id.startswith('pin'):
                    cx = float(elem.get('cx', 0))
                    cy = float(elem.get('cy', 0))
                    
                    # Apply transforms if present
                    transform = elem.get('transform', '')
                    if transform:
                        cx, cy = self._apply_transform(cx, cy, transform)
                    
                    # Check parent transforms
                    parent = self._find_parent(root, elem)
                    while parent is not None:
                        parent_transform = parent.get('transform', '')
                        if parent_transform:
                            cx, cy = self._apply_transform(cx, cy, parent_transform)
                        parent = self._find_parent(root, parent)
                    
                    pins.append(Pin(id=pin_id, x=cx, y=cy))
        
        # Sort by pin number
        pins.sort(key=lambda p: int(re.search(r'\d+', p.id).group()) if re.search(r'\d+', p.id) else 0)
        return pins
    
    def _find_parent(self, root, elem):
        """Find parent element in tree"""
        for parent in root.iter():
            if elem in list(parent):
                return parent
        return None
    
    def _apply_transform(self, x: float, y: float, transform: str) -> Tuple[float, float]:
        """Apply SVG transform to coordinates"""
        # Parse matrix transform: matrix(a, b, c, d, e, f)
        matrix_match = re.search(r'matrix\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)', transform)
        if matrix_match:
            a, b, c, d, e, f = map(float, matrix_match.groups())
            new_x = a * x + c * y + e
            new_y = b * x + d * y + f
            return new_x, new_y
        
        # Parse translate transform
        translate_match = re.search(r'translate\(([-\d.]+)(?:,\s*([-\d.]+))?\)', transform)
        if translate_match:
            tx = float(translate_match.group(1))
            ty = float(translate_match.group(2)) if translate_match.group(2) else 0
            return x + tx, y + ty
        
        return x, y
    
    def svg_to_pen_commands(self, svg_path: Path) -> Tuple[List[str], Tuple[float, float, float, float]]:
        """Convert SVG to pen commands using existing converter"""
        # Use the existing svg_to_lamp_svgpathtools.py converter
        converter_path = Path(__file__).parent / 'svg_to_lamp_smart.py'
        
        result = subprocess.run(
            ['python3', str(converter_path), str(svg_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error converting {svg_path}: {result.stderr}", file=sys.stderr)
            return [], (0, 0, 0, 0)
        
        # Parse pen commands and bounds
        lines = result.stdout.strip().split('\n')
        pen_commands = []
        bounds = None
        
        for line in lines:
            if line.startswith('# BOUNDS'):
                parts = line.split()
                bounds = tuple(map(float, parts[2:6]))
            elif line.strip() and not line.startswith('#'):
                pen_commands.append(line)
        
        # If no bounds in output, calculate from pen commands
        if not bounds:
            bounds = self._calculate_bounds_from_commands(pen_commands)
        
        return pen_commands, bounds
    
    def _calculate_bounds_from_commands(self, commands: List[str]) -> Tuple[float, float, float, float]:
        """Calculate bounds from pen commands"""
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for cmd in commands:
            parts = cmd.split()
            if len(parts) >= 3:
                try:
                    x, y = float(parts[-2]), float(parts[-1])
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
                except ValueError:
                    continue
        
        if min_x == float('inf'):
            return (0, 0, 0, 0)
        
        return (min_x, min_y, max_x, max_y)
    
    def build_component(self, svg_path: Path) -> Component:
        """Build complete component from SVG"""
        # Extract component name from filename
        name = svg_path.stem
        
        # Get SVG dimensions
        tree = ET.parse(svg_path)
        root = tree.getroot()
        width = float(root.get('width', 100))
        height = float(root.get('height', 100))
        
        # Extract pins
        pins = self.extract_pins_from_svg(svg_path)
        
        # Convert to pen commands
        pen_commands, bounds = self.svg_to_pen_commands(svg_path)
        
        return Component(
            name=name,
            width=width,
            height=height,
            pins=pins,
            pen_commands=pen_commands,
            bounds=bounds
        )
    
    def build_library(self) -> Dict[str, Component]:
        """Build complete component library"""
        svg_files = sorted(self.components_dir.glob('*.svg'))
        
        print(f"Building component library from {len(svg_files)} symbols...")
        
        for svg_file in svg_files:
            try:
                component = self.build_component(svg_file)
                self.components[component.name] = component
                print(f"  ✓ {component.name}: {len(component.pins)} pins, {len(component.pen_commands)} commands")
            except Exception as e:
                print(f"  ✗ {svg_file.name}: {e}", file=sys.stderr)
        
        return self.components
    
    def export_to_header(self, output_path: Path):
        """Export component library to header file"""
        with open(output_path, 'w') as f:            
            library_dict = {}
            for name, comp in self.components.items():
                library_dict[name] = {
                    'width': comp.width,
                    'height': comp.height,
                    'bounds': comp.bounds,
                    'pins': [{'id': p.id, 'x': p.x, 'y': p.y} for p in comp.pins],
                    'pen_commands': comp.pen_commands
                }
            
            f.write(json.dumps(library_dict, indent=2))
        
        print(f"\n✓ Component library exported to {output_path}")
        print(f"  Total components: {len(self.components)}")
        print(f"  Total pins: {sum(len(c.pins) for c in self.components.values())}")
        print(f"  Total pen commands: {sum(len(c.pen_commands) for c in self.components.values())}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 component_library_builder.py <components_dir> [output_header]")
        print("Example: python3 component_library_builder.py ./components ./component_library.json")
        sys.exit(1)
    
    components_dir = sys.argv[1]
    output_header = sys.argv[2] if len(sys.argv) > 2 else './component_library.json'
    
    builder = ComponentLibraryBuilder(components_dir)
    builder.build_library()
    builder.export_to_header(Path(output_header))

if __name__ == '__main__':
    main()
