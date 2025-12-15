#!/usr/bin/env python3
"""
Build Component Library - Extract component metadata from SVG files

Generates unified component library JSON containing:
- Bounding boxes
- Pin positions (relative 0.0-1.0 coordinates)
- Component dimensions
- Default orientations

Usage:
    python3 build_component_library.py assets/components/ > src/component_library.json
"""

import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple
import re

class ComponentLibraryBuilder:
    """Extract component metadata from SVG files"""

    # Component type classifications for ECE circuits
    COMPONENT_TYPES = {
        'R': {'name': 'Resistor', 'category': 'passive', 'default_orientation': 'horizontal'},
        'C': {'name': 'Capacitor', 'category': 'passive', 'default_orientation': 'horizontal'},
        'L': {'name': 'Inductor', 'category': 'passive', 'default_orientation': 'horizontal'},
        'D': {'name': 'Diode', 'category': 'semiconductor', 'default_orientation': 'horizontal'},
        'ZD': {'name': 'Zener Diode', 'category': 'semiconductor', 'default_orientation': 'horizontal'},
        'VDC': {'name': 'DC Voltage Source', 'category': 'source', 'default_orientation': 'vertical', 'polarity': True},
        'VAC': {'name': 'AC Voltage Source', 'category': 'source', 'default_orientation': 'vertical'},
        'GND': {'name': 'Ground', 'category': 'reference', 'default_orientation': 'down', 'single_pin': True},
        'OPAMP': {'name': 'Operational Amplifier', 'category': 'active', 'default_orientation': 'horizontal'},
        'NPN_BJT': {'name': 'NPN Transistor', 'category': 'semiconductor', 'default_orientation': 'vertical'},
        'PNP_BJT': {'name': 'PNP Transistor', 'category': 'semiconductor', 'default_orientation': 'vertical'},
        'N_MOSFET': {'name': 'N-Channel MOSFET', 'category': 'semiconductor', 'default_orientation': 'vertical'},
        'P_MOSFET': {'name': 'P-Channel MOSFET', 'category': 'semiconductor', 'default_orientation': 'vertical'},
        'P_CAP': {'name': 'Polarized Capacitor', 'category': 'passive', 'default_orientation': 'vertical', 'polarity': True},
        'SW_OP': {'name': 'Switch (Open)', 'category': 'passive', 'default_orientation': 'horizontal'},
        'SW_CL': {'name': 'Switch (Closed)', 'category': 'passive', 'default_orientation': 'horizontal'},
    }

    def __init__(self, components_dir: Path):
        self.components_dir = Path(components_dir)
        self.library = {
            'metadata': {
                'version': '2.0',
                'coordinate_system': 'relative_0_1',
                'description': 'Unified component library for ECE circuit rendering',
                'pin_format': 'relative coordinates in range [0.0, 1.0]'
            },
            'components': {}
        }

    def build(self) -> Dict:
        """Build complete component library"""
        svg_files = sorted(self.components_dir.glob('*.svg'))

        for svg_file in svg_files:
            if svg_file.parent.name == 'old':
                continue

            component_id = svg_file.stem
            if component_id not in self.COMPONENT_TYPES:
                print(f"Warning: Unknown component type: {component_id}", file=sys.stderr)
                continue

            print(f"Processing {component_id}...", file=sys.stderr)
            component_data = self._extract_component_data(svg_file, component_id)
            self.library['components'][component_id] = component_data

        return self.library

    def _extract_component_data(self, svg_file: Path, component_id: str) -> Dict:
        """Extract all metadata from a single SVG component"""
        tree = ET.parse(svg_file)
        root = tree.getroot()

        # Get component type info
        type_info = self.COMPONENT_TYPES[component_id]

        # Extract viewBox for dimensions
        viewbox = root.get('viewBox', '')
        if viewbox:
            parts = viewbox.split()
            if len(parts) == 4:
                min_x, min_y, width, height = map(float, parts)
            else:
                min_x, min_y = 0, 0
                width = float(root.get('width', '100'))
                height = float(root.get('height', '100'))
        else:
            min_x, min_y = 0, 0
            width = float(root.get('width', '100'))
            height = float(root.get('height', '100'))

        # Extract pin circles
        pins = self._extract_pins(root, width, height, min_x, min_y)

        # Build component data
        component_data = {
            'name': type_info['name'],
            'category': type_info['category'],
            'svg_file': f'assets/components/{component_id}.svg',
            'bbox': {
                'width': width,
                'height': height
            },
            'pins': pins,
            'default_orientation': type_info['default_orientation'],
            'rotations': [0, 90, 180, 270]
        }

        # Add optional metadata
        if 'polarity' in type_info:
            component_data['polarity'] = type_info['polarity']
        if 'single_pin' in type_info:
            component_data['single_pin'] = type_info['single_pin']

        return component_data

    def _extract_pins(self, root, bbox_width: float, bbox_height: float,
                     min_x: float, min_y: float) -> List[Dict]:
        """Extract pin positions from SVG circles with id='pin*'"""
        pins = []

        for elem in root.iter():
            elem_id = elem.get('id', '')

            # Look for pin circles
            if 'pin' in elem_id.lower():
                tag = elem.tag.split('}')[-1]

                if tag == 'circle':
                    cx = float(elem.get('cx', 0))
                    cy = float(elem.get('cy', 0))
                elif tag == 'path':
                    # Extract circle center from path (used by some SVGs)
                    d = elem.get('d', '')
                    # Look for pattern like "M x,y A ..." which indicates circle center
                    match = re.search(r'[Mm]\s*([\d.-]+)[,\s]+([\d.-]+)', d)
                    if match:
                        cx = float(match.group(1))
                        cy = float(match.group(2))
                    else:
                        continue
                else:
                    continue

                # Convert to relative coordinates [0.0, 1.0]
                rel_x = (cx - min_x) / bbox_width if bbox_width > 0 else 0.5
                rel_y = (cy - min_y) / bbox_height if bbox_height > 0 else 0.5

                # Clamp to [0, 1]
                rel_x = max(0.0, min(1.0, rel_x))
                rel_y = max(0.0, min(1.0, rel_y))

                # Determine pin direction based on position
                angle = self._determine_pin_angle(rel_x, rel_y)

                # Extract pin number from id (pin1, pin2, etc.)
                pin_num_match = re.search(r'pin(\d+)', elem_id.lower())
                pin_num = pin_num_match.group(1) if pin_num_match else str(len(pins) + 1)

                pin_data = {
                    'id': pin_num,
                    'name': elem_id,
                    'x': round(rel_x, 6),
                    'y': round(rel_y, 6),
                    'angle': angle
                }

                pins.append(pin_data)

        # Sort pins by ID for consistency
        pins.sort(key=lambda p: int(p['id']))

        return pins

    def _determine_pin_angle(self, rel_x: float, rel_y: float) -> int:
        """
        Determine pin connection angle based on position

        Angles (degrees):
        - 0: Points right (East)
        - 90: Points up (North)
        - 180: Points left (West)
        - 270: Points down (South)
        """
        # Determine which edge the pin is closest to
        distances = {
            'left': rel_x,           # Distance from left edge
            'right': 1.0 - rel_x,    # Distance from right edge
            'top': rel_y,            # Distance from top edge
            'bottom': 1.0 - rel_y    # Distance from bottom edge
        }

        closest_edge = min(distances, key=distances.get)

        # Map edge to angle (direction wire would go FROM component)
        angle_map = {
            'left': 180,     # Pin on left, wire goes left
            'right': 0,      # Pin on right, wire goes right
            'top': 90,       # Pin on top, wire goes up
            'bottom': 270    # Pin on bottom, wire goes down
        }

        return angle_map[closest_edge]

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 build_component_library.py <components_directory>", file=sys.stderr)
        print("Example: python3 build_component_library.py assets/components/", file=sys.stderr)
        sys.exit(1)

    components_dir = Path(sys.argv[1])

    if not components_dir.exists():
        print(f"Error: Directory not found: {components_dir}", file=sys.stderr)
        sys.exit(1)

    builder = ComponentLibraryBuilder(components_dir)
    library = builder.build()

    print(f"Built library with {len(library['components'])} components", file=sys.stderr)
    print("", file=sys.stderr)

    # Output JSON to stdout
    print(json.dumps(library, indent=2))

if __name__ == '__main__':
    main()
