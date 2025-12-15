#!/usr/bin/env python3
"""
Textbook-Standard Circuit Placer
===================================
Follows IEEE/ANSI schematic conventions:
- LEFT→RIGHT signal flow (sources left, loads right)
- TOP→BOTTOM voltage hierarchy (V+ top, GND bottom)
- Series circuits: horizontal chain
- Parallel circuits: vertical branches
- Orthogonal (Manhattan) routing only
- Minimal wire crossings
"""

import json
import sys
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set

SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

@dataclass
class PlacedComponent:
    """Component with placement info"""
    reference: str
    comp_type: str
    x: float
    y: float
    rotation: int = 0  # 0, 90, 180, 270
    pin_positions: List[Tuple[float, float]] = field(default_factory=list)

@dataclass
class Wire:
    """Wire with waypoints"""
    net_name: str
    waypoints: List[Tuple[float, float]]


class TextbookCircuitPlacer:
    """
    Topology-aware placement following textbook standards
    """
    
    # Spacing constants (SVG units)
    COMPONENT_SPACING_H = 250  # Horizontal spacing
    COMPONENT_SPACING_V = 200  # Vertical spacing
    RAIL_HEIGHT = 150  # Source to first component
    
    def __init__(self, library_path: Path):
        with open(library_path, 'r') as f:
            self.library = json.load(f)
        
        self.placed_components: List[PlacedComponent] = []
        self.wires: List[Wire] = []
        self.circuit = None
    
    def place_circuit(self, circuit):
        """Main placement entry"""
        self.circuit = circuit
        
        # Detect topology
        topology = self._detect_topology()
        print(f"\nDetected topology: {topology}")
        
        # Place based on topology
        if topology == "SERIES":
            self._place_series()
        elif topology == "PARALLEL":
            self._place_parallel()
        else:
            self._place_generic_grid()
        
        # Calculate pin positions
        self._calculate_all_pin_positions()
        
        # Route wires
        self._route_all_wires()
        
        return self.placed_components, self.wires
    
    def _detect_topology(self) -> str:
        """
        Detect circuit topology:
        - SERIES: Each intermediate node connects exactly 2 components (chain)
        - PARALLEL: All passives share same input/output nodes (bus)
        - GENERIC: Complex topology
        """
        sources = [c for c in self.circuit.components if c.comp_type in ['VDC', 'VAC']]
        passives = [c for c in self.circuit.components if c.comp_type not in ['VDC', 'VAC', 'GND']]
        grounds = [c for c in self.circuit.components if c.comp_type == 'GND']
        
        if not sources or not passives:
            return "GENERIC"
        
        # Check for series: each intermediate node has exactly 2 connections
        node_connections = {}
        for comp in self.circuit.components:
            for node in [comp.node1, comp.node2]:
                if node == 'GND':
                    continue
                node_connections[node] = node_connections.get(node, 0) + 1
        
        # Series: intermediate nodes have exactly 2 connections
        intermediate_nodes = [n for n in node_connections if node_connections[n] == 2]
        if len(intermediate_nodes) == len(passives) - 1:
            return "SERIES"
        
        # Check for parallel: all passives share two common nodes
        if len(passives) >= 2:
            # Get nodes from first passive
            first_nodes = {passives[0].node1, passives[0].node2}
            # Check if all other passives share these nodes
            all_share = all(
                {p.node1, p.node2} == first_nodes 
                for p in passives[1:]
            )
            if all_share:
                return "PARALLEL"
        
        return "GENERIC"
    
    def _place_series(self):
        """
        Place series circuit horizontally (textbook RC filter style):
        [V+]---[R1]---[R2]---[R3]---+
                                    |
                                  [GND]
        """
        print("Placing series circuit...")
        
        sources = [c for c in self.circuit.components if c.comp_type in ['VDC', 'VAC']]
        passives = [c for c in self.circuit.components if c.comp_type not in ['VDC', 'VAC', 'GND']]
        grounds = [c for c in self.circuit.components if c.comp_type == 'GND']
        
        x = 0
        y = self.RAIL_HEIGHT
        
        # Place voltage source on left (vertical orientation)
        if sources:
            source = sources[0]
            self.placed_components.append(PlacedComponent(
                reference=source.reference,
                comp_type=source.comp_type,
                x=x,
                y=y,
                rotation=0
            ))
            print(f"  {source.reference}: LEFT vertical at ({x}, {y})")
        
        # Build series chain starting from source output
        if sources and passives:
            chain = self._build_series_chain(sources[0], passives)
            
            x += self.COMPONENT_SPACING_H
            
            # Place components horizontally
            for comp in chain:
                self.placed_components.append(PlacedComponent(
                    reference=comp.reference,
                    comp_type=comp.comp_type,
                    x=x,
                    y=y,
                    rotation=0
                ))
                print(f"  {comp.reference}: HORIZONTAL at ({x}, {y})")
                x += self.COMPONENT_SPACING_H
        
        # Place ground at end (bottom)
        if grounds:
            ground = grounds[0]
            self.placed_components.append(PlacedComponent(
                reference=ground.reference,
                comp_type=ground.comp_type,
                x=x - self.COMPONENT_SPACING_H,  # Align with last component
                y=y + self.COMPONENT_SPACING_V,
                rotation=0
            ))
            print(f"  {ground.reference}: BOTTOM at ({x - self.COMPONENT_SPACING_H}, {y + self.COMPONENT_SPACING_V})")
    
    def _build_series_chain(self, source, passives):
        """Build component chain following connectivity"""
        chain = []
        remaining = set(passives)
        current_node = source.node2  # Start at source output
        
        while remaining:
            # Find component connected to current node
            found = None
            for comp in remaining:
                if comp.node1 == current_node:
                    found = comp
                    current_node = comp.node2
                    break
                elif comp.node2 == current_node:
                    found = comp
                    current_node = comp.node1
                    break
            
            if found:
                chain.append(found)
                remaining.remove(found)
            else:
                # No connection found, add remaining arbitrarily
                chain.extend(list(remaining))
                break
        
        return chain
    
    def _place_parallel(self):
        """
        Place parallel circuit vertically (textbook voltage divider style):
        [V+]---+---[R1]---+
               |          |
               +---[R2]---+
               |          |
               +---[R3]---+
               |          |
              GND        GND
        """
        print("Placing parallel circuit...")
        
        sources = [c for c in self.circuit.components if c.comp_type in ['VDC', 'VAC']]
        passives = [c for c in self.circuit.components if c.comp_type not in ['VDC', 'VAC', 'GND']]
        grounds = [c for c in self.circuit.components if c.comp_type == 'GND']
        
        x_source = 0
        x_passives = self.COMPONENT_SPACING_H * 2
        y_start = self.RAIL_HEIGHT
        
        # Place source on left
        if sources:
            source = sources[0]
            self.placed_components.append(PlacedComponent(
                reference=source.reference,
                comp_type=source.comp_type,
                x=x_source,
                y=y_start,
                rotation=0
            ))
            print(f"  {source.reference}: LEFT at ({x_source}, {y_start})")
        
        # Place passives vertically
        y = y_start
        for comp in passives:
            self.placed_components.append(PlacedComponent(
                reference=comp.reference,
                comp_type=comp.comp_type,
                x=x_passives,
                y=y,
                rotation=0
            ))
            print(f"  {comp.reference}: BRANCH at ({x_passives}, {y})")
            y += self.COMPONENT_SPACING_V
        
        # Place ground on right
        if grounds:
            ground = grounds[0]
            self.placed_components.append(PlacedComponent(
                reference=ground.reference,
                comp_type=ground.comp_type,
                x=x_passives + self.COMPONENT_SPACING_H,
                y=y_start + (len(passives) - 1) * self.COMPONENT_SPACING_V // 2,
                rotation=0
            ))
            print(f"  {ground.reference}: RIGHT at ({x_passives + self.COMPONENT_SPACING_H}, {y_start + (len(passives) - 1) * self.COMPONENT_SPACING_V // 2})")
    
    def _place_generic_grid(self):
        """Fallback: simple grid placement"""
        print("Placing generic grid...")
        
        x, y = 0, 0
        for comp in self.circuit.components:
            self.placed_components.append(PlacedComponent(
                reference=comp.reference,
                comp_type=comp.comp_type,
                x=x,
                y=y,
                rotation=0
            ))
            x += self.COMPONENT_SPACING_H
            if x > self.COMPONENT_SPACING_H * 4:
                x = 0
                y += self.COMPONENT_SPACING_V
    
    def _calculate_all_pin_positions(self):
        """Calculate absolute pin positions for all components"""
        for placed in self.placed_components:
            comp_def = self.library.get(placed.comp_type)
            if not comp_def:
                continue
            
            pins = comp_def.get('pins', [])
            placed.pin_positions = []
            
            for pin in pins:
                dx, dy = pin['dx'], pin['dy']
                
                # Apply rotation
                if placed.rotation == 90:
                    dx, dy = -dy, dx
                elif placed.rotation == 180:
                    dx, dy = -dx, -dy
                elif placed.rotation == 270:
                    dx, dy = dy, -dx
                
                # Apply translation
                abs_x = placed.x + dx
                abs_y = placed.y + dy
                placed.pin_positions.append((abs_x, abs_y))
    
    def _route_all_wires(self):
        """Route all nets with orthogonal routing"""
        print(f"\nRouting nets:")
        
        for net_name, net in self.circuit.nets.items():
            if len(net.pins) < 2:
                continue
            
            # Get all pin positions for this net
            pin_data = []
            for ref, pin_num in net.pins:
                placed = self._find_placed(ref)
                if placed and pin_num - 1 < len(placed.pin_positions):
                    pin_pos = placed.pin_positions[pin_num - 1]
                    pin_data.append((ref, pin_pos))
            
            if len(pin_data) < 2:
                continue
            
            # Simple orthogonal routing
            waypoints = self._route_orthogonal(pin_data)
            
            self.wires.append(Wire(net_name=net_name, waypoints=waypoints))
            print(f"  {net_name}: {len(waypoints)} waypoints")
    
    def _route_orthogonal(self, pin_data: List[Tuple[str, Tuple[float, float]]]) -> List[Tuple[float, float]]:
        """
        Simple orthogonal routing between pins
        Uses L-shaped connections (3 waypoints max per segment)
        """
        waypoints = []
        
        for i in range(len(pin_data) - 1):
            ref1, (x1, y1) = pin_data[i]
            ref2, (x2, y2) = pin_data[i + 1]
            
            if i == 0:
                waypoints.append((x1, y1))
            
            # Determine routing direction: horizontal-first or vertical-first
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            
            if dx > dy:
                # Horizontal-first (standard for series circuits)
                waypoints.append((x2, y1))
            else:
                # Vertical-first (standard for parallel circuits)
                waypoints.append((x1, y2))
            
            waypoints.append((x2, y2))
        
        # Remove duplicate consecutive points
        return self._remove_duplicates(waypoints)
    
    def _remove_duplicates(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove consecutive duplicate points"""
        if not points:
            return []
        
        result = [points[0]]
        for p in points[1:]:
            if abs(p[0] - result[-1][0]) > 0.1 or abs(p[1] - result[-1][1]) > 0.1:
                result.append(p)
        
        return result
    
    def _find_placed(self, reference: str):
        """Find placed component by reference"""
        for p in self.placed_components:
            if p.reference == reference:
                return p
        return None


class CircuitRenderer:
    """Render circuit to pen commands"""
    
    MARGIN = 100
    
    def __init__(self, library_path: Path):
        with open(library_path, 'r') as f:
            self.library = json.load(f)
    
    def render(self, placed_components, wires, scale=None):
        """Render to pen commands with auto-scaling"""
        bounds = self._calc_bounds(placed_components, wires)
        min_x, min_y, max_x, max_y = bounds
        
        circuit_width = max_x - min_x
        circuit_height = max_y - min_y
        
        # Auto-scale to fit screen
        if scale is None:
            scale_x = (SCREEN_WIDTH - 2 * self.MARGIN) / circuit_width if circuit_width > 0 else 1
            scale_y = (SCREEN_HEIGHT - 2 * self.MARGIN) / circuit_height if circuit_height > 0 else 1
            scale = min(scale_x, scale_y, 3.0)
        
        # Center on screen
        scaled_width = circuit_width * scale
        scaled_height = circuit_height * scale
        offset_x = (SCREEN_WIDTH - scaled_width) / 2 - min_x * scale
        offset_y = (SCREEN_HEIGHT - scaled_height) / 2 - min_y * scale
        
        print(f"\nRendering: scale={scale:.2f}x, bounds=({min_x:.0f}, {min_y:.0f}, {max_x:.0f}, {max_y:.0f})\n")
        
        commands = [
            "# Textbook-Style Circuit",
            f"# Scale: {scale:.2f}x, Size: {scaled_width:.0f}x{scaled_height:.0f}px"
        ]
        
        # Render components
        for comp in placed_components:
            commands.append(f"# {comp.reference} ({comp.comp_type})")
            commands.extend(self._render_component(comp, scale, offset_x, offset_y))
        
        # Render wires
        for wire in wires:
            commands.append(f"# Net: {wire.net_name}")
            commands.extend(self._render_wire(wire, scale, offset_x, offset_y))
        
        return commands
    
    def _calc_bounds(self, components, wires):
        """Calculate circuit bounding box"""
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for comp in components:
            for x, y in comp.pin_positions:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
        
        for wire in wires:
            for x, y in wire.waypoints:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
        
        return (min_x, min_y, max_x, max_y)
    
    def _render_component(self, placed, scale, offset_x, offset_y):
        """Render component pen commands"""
        comp_def = self.library.get(placed.comp_type)
        if not comp_def:
            return [f"# ERROR: Unknown component {placed.comp_type}"]
        
        commands = []
        
        for cmd in comp_def.get('pen_commands', []):
            if not isinstance(cmd, list) or len(cmd) < 2:
                continue
            
            action = cmd[1]
            
            if action == 'up':
                commands.append('pen up')
            
            elif action in ['down', 'move'] and len(cmd) >= 4:
                dx, dy = cmd[2], cmd[3]
                dx_rot, dy_rot = self._rotate(dx, dy, placed.rotation)
                x = placed.x + dx_rot
                y = placed.y + dy_rot
                sx = int(x * scale + offset_x)
                sy = int(y * scale + offset_y)
                commands.append(f'pen {action} {sx} {sy}')
            
            elif action == 'circle' and len(cmd) >= 5:
                dx, dy, r = cmd[2], cmd[3], cmd[4]
                dx_rot, dy_rot = self._rotate(dx, dy, placed.rotation)
                x = placed.x + dx_rot
                y = placed.y + dy_rot
                sx = int(x * scale + offset_x)
                sy = int(y * scale + offset_y)
                sr = int(r * scale)
                commands.append(f'pen circle {sx} {sy} {sr}')
            
            elif action == 'line' and len(cmd) >= 6:
                dx1, dy1, dx2, dy2 = cmd[2], cmd[3], cmd[4], cmd[5]
                dx1_rot, dy1_rot = self._rotate(dx1, dy1, placed.rotation)
                dx2_rot, dy2_rot = self._rotate(dx2, dy2, placed.rotation)
                x1 = placed.x + dx1_rot
                y1 = placed.y + dy1_rot
                x2 = placed.x + dx2_rot
                y2 = placed.y + dy2_rot
                sx1 = int(x1 * scale + offset_x)
                sy1 = int(y1 * scale + offset_y)
                sx2 = int(x2 * scale + offset_x)
                sy2 = int(y2 * scale + offset_y)
                commands.append(f'pen line {sx1} {sy1} {sx2} {sy2}')
        
        return commands
    
    def _render_wire(self, wire, scale, offset_x, offset_y):
        """Render wire waypoints"""
        if len(wire.waypoints) < 2:
            return []
        
        commands = []
        
        x, y = wire.waypoints[0]
        sx = int(x * scale + offset_x)
        sy = int(y * scale + offset_y)
        commands.append(f'pen down {sx} {sy}')
        
        for x, y in wire.waypoints[1:]:
            sx = int(x * scale + offset_x)
            sy = int(y * scale + offset_y)
            commands.append(f'pen move {sx} {sy}')
        
        commands.append('pen up')
        
        return commands
    
    def _rotate(self, dx, dy, rotation):
        """Apply rotation to offset"""
        if rotation == 0:
            return dx, dy
        elif rotation == 90:
            return -dy, dx
        elif rotation == 180:
            return -dx, -dy
        elif rotation == 270:
            return dy, -dx
        return dx, dy


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 circuit_placer_textbook.py <netlist> <component_library.json>")
        print("\nExample:")
        print("  python3 circuit_placer_textbook.py rc_filter.net component_library.json")
        sys.exit(1)
    
    # Import netlist parser
    sys.path.insert(0, str(Path(__file__).parent.parent / "Archive" / "v2.3" / "claude" / "src"))
    from netlist_parser import NetlistParser
    
    netlist_path = Path(sys.argv[1])
    library_path = Path(sys.argv[2])
    
    # Parse netlist
    parser = NetlistParser()
    circuit = parser.parse_file(netlist_path)
    parser.print_summary()
    
    # Place circuit
    placer = TextbookCircuitPlacer(library_path)
    placed, wires = placer.place_circuit(circuit)
    
    # Render
    renderer = CircuitRenderer(library_path)
    commands = renderer.render(placed, wires)
    
    # Output
    print("=" * 60)
    for cmd in commands:
        print(cmd)


if __name__ == '__main__':
    main()
