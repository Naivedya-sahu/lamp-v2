#!/usr/bin/env python3
"""
Circuit Builder - Generates lamp commands for drawing circuits with proper netlist
Uses component definitions with anchor points for connections
"""

import sys
import json
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import List, Tuple, Dict
from component_definitions import ComponentLibrary, ComponentDefinition, PlacedComponent, Circuit, AnchorPoint


class SVGComponentRenderer:
    """Renders SVG components to lamp commands with coordinate transformation"""

    def __init__(self, library_svg_path: str):
        self.library_svg_path = library_svg_path
        self.tree = ET.parse(library_svg_path)
        self.root = self.tree.getroot()
        self.svg_groups = {}
        self._extract_groups()

    def _extract_groups(self):
        """Extract all SVG groups"""
        for elem in self.root.iter():
            if elem.tag.endswith('}g') or elem.tag == 'g':
                group_id = elem.get('id')
                if group_id and group_id.startswith('g'):
                    self.svg_groups[group_id] = elem

    def get_group_bbox(self, group_id: str) -> Dict[str, float]:
        """Calculate bounding box for a group"""
        elem = self.svg_groups.get(group_id)
        if not elem:
            return {'x': 0, 'y': 0, 'width': 0, 'height': 0}

        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        for child in elem.iter():
            if 'path' in child.tag:
                d = child.get('d', '')
                coords = self._extract_coords_from_path(d)
                for x, y in coords:
                    min_x, max_x = min(min_x, x), max(max_x, x)
                    min_y, max_y = min(min_y, y), max(max_y, y)

        return {
            'x': min_x if min_x != float('inf') else 0,
            'y': min_y if min_y != float('inf') else 0,
            'width': max_x - min_x if max_x != float('-inf') else 0,
            'height': max_y - min_y if max_y != float('-inf') else 0
        }

    def _extract_coords_from_path(self, d: str) -> List[Tuple[float, float]]:
        """Extract coordinate pairs from SVG path data, including negatives"""
        coords = []
        numbers = re.findall(r'-?\d+\.?\d*', d)
        for i in range(0, len(numbers) - 1, 2):
            try:
                coords.append((float(numbers[i]), float(numbers[i + 1])))
            except (ValueError, IndexError):
                continue
        return coords

    def render_component_to_lamp(self, group_id: str, target_x: float, target_y: float,
                                  target_width: float, target_height: float) -> List[str]:
        """
        Render SVG component to lamp commands with scaling and translation

        Args:
            group_id: SVG group ID
            target_x, target_y: Target position
            target_width, target_height: Target size (for fixed block sizing)
        """
        elem = self.svg_groups.get(group_id)
        if not elem:
            return [f"# Error: Group {group_id} not found"]

        # Get original bounding box
        bbox = self.get_group_bbox(group_id)

        # Calculate scale factors
        if bbox['width'] > 0 and bbox['height'] > 0:
            scale_x = target_width / bbox['width']
            scale_y = target_height / bbox['height']
            scale = min(scale_x, scale_y)  # Maintain aspect ratio
        else:
            scale = 1.0

        # Calculate offset to center in target box
        offset_x = target_x - bbox['x'] * scale + (target_width - bbox['width'] * scale) / 2
        offset_y = target_y - bbox['y'] * scale + (target_height - bbox['height'] * scale) / 2

        # Generate lamp commands
        commands = []
        commands.append(f"# Component {group_id} at ({target_x}, {target_y})")

        for child in elem.iter():
            tag = child.tag.split('}')[-1]

            if tag == 'path':
                cmds = self._parse_path_to_lamp(child, scale, offset_x, offset_y)
                commands.extend(cmds)
            elif tag == 'line':
                cmds = self._parse_line_to_lamp(child, scale, offset_x, offset_y)
                commands.extend(cmds)
            elif tag == 'rect':
                cmds = self._parse_rect_to_lamp(child, scale, offset_x, offset_y)
                commands.extend(cmds)
            elif tag == 'circle':
                cmds = self._parse_circle_to_lamp(child, scale, offset_x, offset_y)
                commands.extend(cmds)

        return commands

    def _transform_point(self, x: float, y: float, scale: float, offset_x: float, offset_y: float) -> Tuple[int, int]:
        """Transform SVG coordinates to lamp coordinates"""
        return (
            int(x * scale + offset_x),
            int(y * scale + offset_y)
        )

    def _parse_path_to_lamp(self, elem, scale: float, offset_x: float, offset_y: float) -> List[str]:
        """Parse SVG path to lamp commands"""
        d = elem.get('d', '')
        if not d:
            return []

        commands = []
        path_cmds = re.findall(r'([MLHVZmlhvz])([^MLHVZmlhvz]*)', d)

        current_x, current_y = 0.0, 0.0
        start_x, start_y = 0.0, 0.0
        pen_down = False

        for cmd, coords in path_cmds:
            coords = coords.strip()
            if not coords and cmd.upper() not in ['Z']:
                continue

            nums = [float(n) for n in re.findall(r'-?\d+\.?\d*', coords)]

            if cmd == 'M':  # Move to (absolute)
                if pen_down:
                    commands.append("pen up")
                    pen_down = False
                current_x, current_y = nums[0], nums[1]
                start_x, start_y = current_x, current_y

            elif cmd == 'm':  # Move to (relative)
                if pen_down:
                    commands.append("pen up")
                    pen_down = False
                current_x += nums[0]
                current_y += nums[1]
                start_x, start_y = current_x, current_y

            elif cmd in ['L', 'l']:  # Line to
                for i in range(0, len(nums), 2):
                    if cmd == 'L':
                        next_x, next_y = nums[i], nums[i+1]
                    else:
                        next_x = current_x + nums[i]
                        next_y = current_y + nums[i+1]

                    if not pen_down:
                        x1, y1 = self._transform_point(current_x, current_y, scale, offset_x, offset_y)
                        commands.append(f"pen down {x1} {y1}")
                        pen_down = True

                    x2, y2 = self._transform_point(next_x, next_y, scale, offset_x, offset_y)
                    commands.append(f"pen move {x2} {y2}")
                    current_x, current_y = next_x, next_y

            elif cmd in ['H', 'h']:  # Horizontal line
                for num in nums:
                    next_x = num if cmd == 'H' else current_x + num
                    next_y = current_y

                    if not pen_down:
                        x1, y1 = self._transform_point(current_x, current_y, scale, offset_x, offset_y)
                        commands.append(f"pen down {x1} {y1}")
                        pen_down = True

                    x2, y2 = self._transform_point(next_x, next_y, scale, offset_x, offset_y)
                    commands.append(f"pen move {x2} {y2}")
                    current_x = next_x

            elif cmd in ['V', 'v']:  # Vertical line
                for num in nums:
                    next_x = current_x
                    next_y = num if cmd == 'V' else current_y + num

                    if not pen_down:
                        x1, y1 = self._transform_point(current_x, current_y, scale, offset_x, offset_y)
                        commands.append(f"pen down {x1} {y1}")
                        pen_down = True

                    x2, y2 = self._transform_point(next_x, next_y, scale, offset_x, offset_y)
                    commands.append(f"pen move {x2} {y2}")
                    current_y = next_y

            elif cmd in ['Z', 'z']:  # Close path
                if pen_down:
                    x2, y2 = self._transform_point(start_x, start_y, scale, offset_x, offset_y)
                    commands.append(f"pen move {x2} {y2}")
                    commands.append("pen up")
                    pen_down = False

        if pen_down:
            commands.append("pen up")

        return commands

    def _parse_line_to_lamp(self, elem, scale: float, offset_x: float, offset_y: float) -> List[str]:
        """Parse SVG line to lamp commands"""
        x1 = float(elem.get('x1', 0))
        y1 = float(elem.get('y1', 0))
        x2 = float(elem.get('x2', 0))
        y2 = float(elem.get('y2', 0))

        x1_t, y1_t = self._transform_point(x1, y1, scale, offset_x, offset_y)
        x2_t, y2_t = self._transform_point(x2, y2, scale, offset_x, offset_y)

        return [f"pen line {x1_t} {y1_t} {x2_t} {y2_t}"]

    def _parse_rect_to_lamp(self, elem, scale: float, offset_x: float, offset_y: float) -> List[str]:
        """Parse SVG rectangle to lamp commands"""
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        w = float(elem.get('width', 0))
        h = float(elem.get('height', 0))

        x1, y1 = self._transform_point(x, y, scale, offset_x, offset_y)
        x2, y2 = self._transform_point(x + w, y + h, scale, offset_x, offset_y)

        return [f"pen rectangle {x1} {y1} {x2} {y2}"]

    def _parse_circle_to_lamp(self, elem, scale: float, offset_x: float, offset_y: float) -> List[str]:
        """Parse SVG circle to lamp commands"""
        cx = float(elem.get('cx', 0))
        cy = float(elem.get('cy', 0))
        r = float(elem.get('r', 0))

        cx_t, cy_t = self._transform_point(cx, cy, scale, offset_x, offset_y)
        r_t = int(r * scale)

        return [f"pen circle {cx_t} {cy_t} {r_t}"]


class CircuitRenderer:
    """Renders complete circuits to lamp commands"""

    def __init__(self, component_library: ComponentLibrary, svg_renderer: SVGComponentRenderer):
        self.library = component_library
        self.svg_renderer = svg_renderer

    def render_circuit(self, circuit: Circuit, draw_wires: bool = True, draw_anchors: bool = False) -> str:
        """
        Render circuit to lamp commands

        Args:
            circuit: Circuit to render
            draw_wires: Draw connection wires between anchors
            draw_anchors: Draw anchor point markers (for debugging)
        """
        commands = []
        commands.append(f"# Circuit: {circuit.name}")
        commands.append(f"# Generated by circuit_builder.py")
        commands.append("")

        # Draw each component
        for comp in circuit.components:
            comp_def = self.library.get_component(comp.component_type)
            if not comp_def:
                commands.append(f"# Error: Component type '{comp.component_type}' not found")
                continue

            # Get SVG group ID for this component
            if comp_def.svg_group_ids:
                group_id = comp_def.svg_group_ids[0]  # Use first variant

                # Render component
                comp_commands = self.svg_renderer.render_component_to_lamp(
                    group_id, comp.x, comp.y, comp_def.width, comp_def.height
                )
                commands.extend(comp_commands)

                # Draw anchor points (debugging)
                if draw_anchors:
                    for anchor in comp_def.anchors:
                        ax, ay = anchor.get_absolute_pos(comp.x, comp.y, comp_def.width, comp_def.height)
                        commands.append(f"pen circle {int(ax)} {int(ay)} 3")

                # Add label
                commands.append(f"# {comp.ref} = {comp.value}")
                commands.append("")

        # Draw wires based on netlist
        if draw_wires:
            commands.append("# Wiring")
            drawn_wires = set()

            for net_name, connections in circuit.nets.items():
                # Group connections by net
                # For each net, connect all anchors together
                anchor_positions = []

                for conn in connections:
                    ref, anchor_name = conn.split('.')
                    # Find component
                    comp = next((c for c in circuit.components if c.ref == ref), None)
                    if comp:
                        comp_def = self.library.get_component(comp.component_type)
                        if comp_def:
                            anchor = next((a for a in comp_def.anchors if a.name == anchor_name), None)
                            if anchor:
                                pos = anchor.get_absolute_pos(comp.x, comp.y, comp_def.width, comp_def.height)
                                anchor_positions.append((pos, f"{ref}.{anchor_name}"))

                # Draw wires between consecutive anchors in net
                for i in range(len(anchor_positions) - 1):
                    pos1, name1 = anchor_positions[i]
                    pos2, name2 = anchor_positions[i + 1]

                    wire_key = tuple(sorted([name1, name2]))
                    if wire_key not in drawn_wires:
                        x1, y1 = int(pos1[0]), int(pos1[1])
                        x2, y2 = int(pos2[0]), int(pos2[1])
                        commands.append(f"pen line {x1} {y1} {x2} {y2}  # {net_name}: {name1} -> {name2}")
                        drawn_wires.add(wire_key)

            commands.append("")

        return '\n'.join(commands)


def create_rc_vdc_series_circuit(library: ComponentLibrary) -> Circuit:
    """
    Create simple RC circuit with VDC source in series

    Circuit topology:
    VDC(+) --- R --- C --- GND
       |                   |
       +-------------------+
    """
    circuit = Circuit("RC Series Circuit with DC Source")

    # Place components for series connection
    # Start at (100, 200) - VDC positive terminal
    vdc = PlacedComponent(ref="V1", component_type="VDC", x=100, y=100, value="5V")
    circuit.add_component(vdc)

    # Resistor to the right (series)
    r1 = PlacedComponent(ref="R1", component_type="R", x=200, y=160, value="10k")
    circuit.add_component(r1)

    # Capacitor to the right of resistor (series)
    c1 = PlacedComponent(ref="C1", component_type="C", x=340, y=160, value="100nF")
    circuit.add_component(c1)

    # Ground at bottom
    gnd = PlacedComponent(ref="GND1", component_type="GND", x=100, y=200)
    circuit.add_component(gnd)

    # Netlist (series connection):
    # VDC(+) connects to R(left) - Net: VCC
    circuit.connect("V1", "positive", "R1", "left", "VCC")

    # R(right) connects to C(left) - Net: N1
    circuit.connect("R1", "right", "C1", "left", "N1")

    # C(right) connects to GND - Net: GND
    circuit.connect("C1", "right", "GND1", "gnd", "GND")

    # VDC(-) connects to GND - Net: GND
    circuit.connect("V1", "negative", "GND1", "gnd", "GND")

    return circuit


def main():
    """Generate lamp commands for RC+VDC circuit"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode: just verify structure
        print("Testing circuit builder...")
        library = ComponentLibrary()
        circuit = create_rc_vdc_series_circuit(library)

        print(f"Circuit: {circuit.name}")
        print(f"Components: {len(circuit.components)}")
        for comp in circuit.components:
            print(f"  {comp.ref}: {comp.component_type} @ ({comp.x}, {comp.y})")

        print(f"\nNetlist:")
        for net, conns in circuit.nets.items():
            print(f"  {net}: {', '.join(conns)}")

        return

    # Full render mode
    print("Initializing component library...")
    library = ComponentLibrary()

    print("Loading SVG library...")
    svg_path = "examples/svg_symbols/Electrical_symbols_library.svg"
    if not Path(svg_path).exists():
        print(f"Error: SVG library not found at {svg_path}")
        sys.exit(1)

    svg_renderer = SVGComponentRenderer(svg_path)
    circuit_renderer = CircuitRenderer(library, svg_renderer)

    print("Creating RC + VDC series circuit...")
    circuit = create_rc_vdc_series_circuit(library)

    print("Rendering circuit to lamp commands...")
    lamp_commands = circuit_renderer.render_circuit(circuit, draw_wires=True, draw_anchors=False)

    # Output
    output_file = "rc_vdc_circuit.lamp"
    with open(output_file, 'w') as f:
        f.write(lamp_commands)

    print(f"\nGenerated {output_file}")
    print(f"Components: {len(circuit.components)}")
    print(f"Nets: {len(circuit.nets)}")
    print(f"\nTo draw on reMarkable 2:")
    print(f"  cat {output_file} | ssh root@10.11.99.1 lamp")


if __name__ == '__main__':
    main()
