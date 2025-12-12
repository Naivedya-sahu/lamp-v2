#!/usr/bin/env python3
"""
Component Library Builder - Fixed to skip pin circles
Converts SVG components to anchor-relative pen commands with centered anchors
Uses svg_to_lamp_smartv2 for intelligent path sampling
"""

import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict
import xml.etree.ElementTree as ET
import re

# Import the smart SVG parser
sys.path.insert(0, str(Path(__file__).parent))
from svg_to_lamp_smartv2 import smart_parse_path

SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

class AnchorRelativeConverter:
    """Convert SVG to anchor-relative coordinate system"""
    
    def __init__(self):
        self.components = {}
    
    def convert_svg_to_component(self, svg_path: Path, component_name: str) -> Dict:
        """
        Convert SVG to component definition with anchor at bounding box center
        Skips pin circles - they are reference points only
        """
        print(f"Processing {component_name} from {svg_path}...")
        
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Step 1: Parse SVG and collect absolute coordinates
        pen_commands_abs = []
        all_points = []
        
        for elem in root.iter():
            tag = elem.tag.split('}')[-1]
            elem_id = elem.get('id', '').lower()
            
            # Skip pin elements - they are reference points only
            is_pin = 'pin' in elem_id
            
            if tag == 'path':
                if is_pin:
                    continue
                    
                d = elem.get('d', '')
                if not d:
                    continue
                
                # Use smart parser with default tolerance
                try:
                    pts = smart_parse_path(d, tolerance=1.0)
                    if not pts:
                        continue
                    
                    # Generate pen commands
                    x0, y0 = pts[0]
                    pen_commands_abs.append(['pen', 'down', x0, y0])
                    all_points.append((x0, y0))
                    
                    for x, y in pts[1:]:
                        pen_commands_abs.append(['pen', 'move', x, y])
                        all_points.append((x, y))
                    
                    pen_commands_abs.append(['pen', 'up'])
                except Exception as e:
                    print(f"  Warning: Failed to parse path: {e}")
                    continue
            
            elif tag == 'circle':
                if is_pin:
                    continue  # Skip pin circles
                    
                cx = float(elem.get('cx', 0))
                cy = float(elem.get('cy', 0))
                r = float(elem.get('r', 0))
                pen_commands_abs.append(['pen', 'circle', cx, cy, r])
                all_points.extend([
                    (cx - r, cy), (cx + r, cy),
                    (cx, cy - r), (cx, cy + r)
                ])
            
            elif tag == 'line':
                if is_pin:
                    continue
                    
                x1 = float(elem.get('x1', 0))
                y1 = float(elem.get('y1', 0))
                x2 = float(elem.get('x2', 0))
                y2 = float(elem.get('y2', 0))
                pen_commands_abs.append(['pen', 'line', x1, y1, x2, y2])
                all_points.extend([(x1, y1), (x2, y2)])
            
            elif tag == 'rect':
                if is_pin:
                    continue
                    
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                w = float(elem.get('width', 0))
                h = float(elem.get('height', 0))
                pen_commands_abs.append(['pen', 'rectangle', x, y, x + w, y + h])
                all_points.extend([
                    (x, y), (x + w, y),
                    (x, y + h), (x + w, y + h)
                ])
        
        if not all_points:
            print(f"  WARNING: No drawable content found in {svg_path}")
            return None
        
        # Step 2: Calculate bounding box
        min_x = min(p[0] for p in all_points)
        max_x = max(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_y = max(p[1] for p in all_points)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Step 3: Calculate center anchor
        anchor_x = (min_x + max_x) / 2.0
        anchor_y = (min_y + max_y) / 2.0
        
        print(f"  Bounds: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})")
        print(f"  Size: {width:.1f} x {height:.1f}")
        print(f"  Anchor: ({anchor_x:.1f}, {anchor_y:.1f})")
        
        # Step 4: Convert all coordinates to anchor-relative
        pen_commands_rel = []
        for cmd in pen_commands_abs:
            cmd_type = cmd[0]
            
            if cmd_type == 'pen':
                action = cmd[1]
                
                if action in ['down', 'move']:
                    x, y = cmd[2], cmd[3]
                    dx = x - anchor_x
                    dy = y - anchor_y
                    pen_commands_rel.append(['pen', action, dx, dy])
                
                elif action == 'circle':
                    cx, cy, r = cmd[2], cmd[3], cmd[4]
                    dx = cx - anchor_x
                    dy = cy - anchor_y
                    pen_commands_rel.append(['pen', 'circle', dx, dy, r])
                
                elif action == 'line':
                    x1, y1, x2, y2 = cmd[2], cmd[3], cmd[4], cmd[5]
                    dx1 = x1 - anchor_x
                    dy1 = y1 - anchor_y
                    dx2 = x2 - anchor_x
                    dy2 = y2 - anchor_y
                    pen_commands_rel.append(['pen', 'line', dx1, dy1, dx2, dy2])
                
                elif action == 'rectangle':
                    x1, y1, x2, y2 = cmd[2], cmd[3], cmd[4], cmd[5]
                    dx1 = x1 - anchor_x
                    dy1 = y1 - anchor_y
                    dx2 = x2 - anchor_x
                    dy2 = y2 - anchor_y
                    pen_commands_rel.append(['pen', 'rectangle', dx1, dy1, dx2, dy2])
                
                elif action == 'up':
                    pen_commands_rel.append(['pen', 'up'])
        
        # Step 5: Define pins (component-specific logic)
        pins = self._detect_pins(component_name, width, height)
        
        # Convert to component definition
        component_def = {
            "width": width,
            "height": height,
            "anchor": {"x": 0.0, "y": 0.0},
            "pins": pins,
            "pen_commands": pen_commands_rel
        }
        
        print(f"  Generated {len(pen_commands_rel)} pen commands")
        print(f"  Defined {len(pins)} pins")
        
        return component_def
    
    def _detect_pins(self, component_name: str, width: float, height: float) -> List[Dict]:
        """Define pin positions relative to anchor"""
        pins = []
        
        # Default 2-pin horizontal layout
        if component_name in ['R', 'C', 'L', 'D', 'ZD']:
            pins = [
                {"id": "pin1", "dx": -width / 2.0, "dy": 0.0},
                {"id": "pin2", "dx": width / 2.0, "dy": 0.0}
            ]
        
        # Vertical 2-pin
        elif component_name in ['VDC', 'VAC', 'P_CAP']:
            pins = [
                {"id": "pin1", "dx": 0.0, "dy": -height / 2.0},
                {"id": "pin2", "dx": 0.0, "dy": height / 2.0}
            ]
        
        # Single pin
        elif component_name == 'GND':
            pins = [
                {"id": "pin1", "dx": 0.0, "dy": -height / 2.0}
            ]
        
        # 3-pin transistors
        elif component_name in ['NPN_BJT', 'PNP_BJT', 'N_MOSFET', 'P_MOSFET']:
            pins = [
                {"id": "pin1", "dx": -width / 2.0, "dy": -height / 4.0},
                {"id": "pin2", "dx": width / 2.0, "dy": 0.0},
                {"id": "pin3", "dx": -width / 2.0, "dy": height / 4.0}
            ]
        
        # 5-pin opamp
        elif component_name == 'OPAMP':
            pins = [
                {"id": "pin1", "dx": -width / 2.0, "dy": height / 4.0},
                {"id": "pin2", "dx": -width / 2.0, "dy": -height / 4.0},
                {"id": "pin3", "dx": 0.0, "dy": -height / 2.0},
                {"id": "pin4", "dx": 0.0, "dy": height / 2.0},
                {"id": "pin5", "dx": width / 2.0, "dy": 0.0}
            ]
        
        else:
            # Default: 2-pin horizontal
            pins = [
                {"id": "pin1", "dx": -width / 2.0, "dy": 0.0},
                {"id": "pin2", "dx": width / 2.0, "dy": 0.0}
            ]
        
        return pins
    
    def build_library(self, svg_dir: Path, output_path: Path):
        """Build complete component library"""
        svg_files = list(svg_dir.glob("*.svg"))
        
        if not svg_files:
            print(f"ERROR: No SVG files found in {svg_dir}")
            return
        
        print(f"Found {len(svg_files)} SVG files")
        print("=" * 60)
        
        library = {}
        
        for svg_file in sorted(svg_files):
            component_name = svg_file.stem
            
            try:
                component_def = self.convert_svg_to_component(svg_file, component_name)
                if component_def:
                    library[component_name] = component_def
                print()
            except Exception as e:
                print(f"  ERROR: {e}")
                print()
        
        # Write library to JSON
        with open(output_path, 'w') as f:
            json.dump(library, f, indent=2)
        
        print("=" * 60)
        print(f"Component library saved to: {output_path}")
        print(f"Total components: {len(library)}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 component_library_builder.py <svg_directory> <output.json>")
        print("Example: python3 component_library_builder.py ../assets/components component_library.json")
        sys.exit(1)
    
    svg_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    if not svg_dir.exists():
        print(f"ERROR: Directory not found: {svg_dir}")
        sys.exit(1)
    
    converter = AnchorRelativeConverter()
    converter.build_library(svg_dir, output_path)


if __name__ == '__main__':
    main()
