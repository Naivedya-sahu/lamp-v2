#!/usr/bin/env python3
"""
Fixed Textbook-Standard Circuit Placer
Compatible with LTSpice netlist format
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

@dataclass
class PlacedComponent:
    """Component with placement info"""
    reference: str
    comp_type: str
    x: float
    y: float
    rotation: int = 0
    pin_positions: List[Tuple[float, float]] = field(default_factory=list)

@dataclass
class Wire:
    """Wire with waypoints"""
    net_name: str
    waypoints: List[Tuple[float, float]]


class TextbookCircuitPlacer:
    """
    Topology-aware placement with simple orthogonal routing
    Compatible with LTSpice netlist format
    """
    
    COMPONENT_SPACING_H = 250
    COMPONENT_SPACING_V = 200
    RAIL_HEIGHT = 150
    
    def __init__(self, library_path: Path):
        with open(library_path, 'r') as f:
            self.library = json.load(f)
        
        self.placed_components: List[PlacedComponent] = []
        self.wires: List[Wire] = []
        self.circuit = None
    
    def place_circuit(self, circuit):
        """Main placement entry"""
        self.circuit = circuit
        
        topology = self._detect_topology()
        print(f"\nDetected topology: {topology}")
        
        if topology == "SERIES":
            self._place_series()
        elif topology == "PARALLEL":
            self._place_parallel()
        else:
            self._place_generic_grid()
        
        self._calculate_all_pin_positions()
        self._route_all_wires()
        
        return self.placed_components, self.wires
    
    def _get_comp_nodes(self, comp):
        """Get nodes from component (handles both old and new format)"""
        # LTSpice parser uses 'nodes' list
        if hasattr(comp, 'nodes'):
            return comp.nodes
        # Simplified parser uses node1, node2
        elif hasattr(comp, 'node1') and hasattr(comp, 'node2'):
            return [comp.node1, comp.node2]
        return []
    
    def _get_comp_type(self, comp):
        """Get component type (handles both formats)"""
        if hasattr(comp, 'component_type'):
            return comp.component_type
        elif hasattr(comp, 'comp_type'):
            return comp.comp_type
        return 'R'
    
    def _detect_topology(self) -> str:
        """Detect circuit topology"""
        sources = [c for c in self.circuit.components if self._get_comp_type(c) in ['VDC', 'VAC', 'V']]
        passives = [c for c in self.circuit.components if self._get_comp_type(c) not in ['VDC', 'VAC', 'V', 'GND']]
        
        if not sources or not passives:
            return "GENERIC"
        
        # Check series topology
        node_connections = {}
        for comp in self.circuit.components:
            nodes = self._get_comp_nodes(comp)
            for node in nodes:
                if node in ['0', 'GND']:
                    continue
                node_connections[node] = node_connections.get(node, 0) + 1
        
        intermediate_nodes = [n for n in node_connections if node_connections[n] == 2]
        if len(intermediate_nodes) == len(passives) - 1:
            return "SERIES"
        
        # Check parallel topology
        if len(passives) >= 2:
            first_nodes = set(self._get_comp_nodes(passives[0]))
            first_nodes.discard('0')
            first_nodes.discard('GND')
            
            all_share = all(
                set(self._get_comp_nodes(p)) - {'0', 'GND'} == first_nodes
                for p in passives[1:]
            )
            if all_share:
                return "PARALLEL"
        
        return "GENERIC"
    
    def _place_series(self):
        """Place series circuit horizontally"""
        print("Placing series circuit...")
        
        sources = [c for c in self.circuit.components if self._get_comp_type(c) in ['VDC', 'VAC', 'V']]
        passives = [c for c in self.circuit.components if self._get_comp_type(c) not in ['VDC', 'VAC', 'V', 'GND']]
        
        x, y = 0, self.RAIL_HEIGHT
        
        # Place voltage source
        if sources:
            source = sources[0]
            self.placed_components.append(PlacedComponent(
                reference=source.reference,
                comp_type=self._get_comp_type(source),
                x=x, y=y, rotation=0
            ))
            print(f"  {source.reference}: at ({x}, {y})")
        
        # Build and place series chain
        if sources and passives:
            chain = self._build_series_chain(sources[0], passives)
            x += self.COMPONENT_SPACING_H
            
            for comp in chain:
                self.placed_components.append(PlacedComponent(
                    reference=comp.reference,
                    comp_type=self._get_comp_type(comp),
                    x=x, y=y, rotation=0
                ))
                print(f"  {comp.reference}: at ({x}, {y})")
                x += self.COMPONENT_SPACING_H
    
    def _build_series_chain(self, source, passives):
        """Build component chain following connectivity"""
        chain = []
        remaining = set(passives)
        source_nodes = self._get_comp_nodes(source)
        current_node = source_nodes[1] if len(source_nodes) > 1 else source_nodes[0]
        
        while remaining:
            found = None
            for comp in remaining:
                comp_nodes = self._get_comp_nodes(comp)
                if len(comp_nodes) >= 2:
                    if comp_nodes[0] == current_node:
                        found = comp
                        current_node = comp_nodes[1]
                        break
                    elif comp_nodes[1] == current_node:
                        found = comp
                        current_node = comp_nodes[0]
                        break
            
            if found:
                chain.append(found)
                remaining.remove(found)
            else:
                chain.extend(list(remaining))
                break
        
        return chain
    
    def _place_parallel(self):
        """Place parallel circuit vertically"""
        print("Placing parallel circuit...")
        
        sources = [c for c in self.circuit.components if self._get_comp_type(c) in ['VDC', 'VAC', 'V']]
        passives = [c for c in self.circuit.components if self._get_comp_type(c) not in ['VDC', 'VAC', 'V', 'GND']]
        
        x_source = 0
        x_passives = self.COMPONENT_SPACING_H * 2
        y_start = self.RAIL_HEIGHT
        
        if sources:
            self.placed_components.append(PlacedComponent(
                reference=sources[0].reference,
                comp_type=self._get_comp_type(sources[0]),
                x=x_source, y=y_start, rotation=0
            ))
            print(f"  {sources[0].reference}: at ({x_source}, {y_start})")
        
        y = y_start
        for comp in passives:
            self.placed_components.append(PlacedComponent(
                reference=comp.reference,
                comp_type=self._get_comp_type(comp),
                x=x_passives, y=y, rotation=0
            ))
            print(f"  {comp.reference}: at ({x_passives}, {y})")
            y += self.COMPONENT_SPACING_V
    
    def _place_generic_grid(self):
        """Fallback grid placement"""
        print("Placing generic grid...")
        x, y = 0, 0
        for comp in self.circuit.components:
            self.placed_components.append(PlacedComponent(
                reference=comp.reference,
                comp_type=self._get_comp_type(comp),
                x=x, y=y, rotation=0
            ))
            x += self.COMPONENT_SPACING_H
            if x > self.COMPONENT_SPACING_H * 4:
                x = 0
                y += self.COMPONENT_SPACING_V
    
    def _calculate_all_pin_positions(self):
        """Calculate absolute pin positions"""
        for placed in self.placed_components:
            comp_def = self.library.get(placed.comp_type)
            if not comp_def:
                continue
            
            pins = comp_def.get('pins', [])
            placed.pin_positions = []
            
            for pin in pins:
                dx, dy = pin['dx'], pin['dy']
                
                if placed.rotation == 90:
                    dx, dy = -dy, dx
                elif placed.rotation == 180:
                    dx, dy = -dx, -dy
                elif placed.rotation == 270:
                    dx, dy = dy, -dx
                
                placed.pin_positions.append((placed.x + dx, placed.y + dy))
    
    def _route_all_wires(self):
        """Route all nets"""
        print(f"\nRouting nets:")
        
        # Handle both net formats
        if hasattr(self.circuit, 'nets'):
            if isinstance(self.circuit.nets, list):
                nets = self.circuit.nets
            elif isinstance(self.circuit.nets, dict):
                nets = self.circuit.nets.values()
            else:
                nets = []
        else:
            return
        
        for net in nets:
            # Handle different net formats
            if hasattr(net, 'components'):
                pin_refs = net.components  # LTSpice format
            elif hasattr(net, 'pins'):
                pin_refs = net.pins  # Simplified format
            else:
                continue
            
            if len(pin_refs) < 2:
                continue
            
            # Collect pin positions
            pin_positions = []
            for ref_data in pin_refs:
                if isinstance(ref_data, tuple):
                    ref, pin_idx = ref_data
                else:
                    continue
                
                placed = self._find_placed(ref)
                if placed and pin_idx < len(placed.pin_positions):
                    pin_positions.append(placed.pin_positions[pin_idx])
            
            if len(pin_positions) < 2:
                continue
            
            # Simple orthogonal routing
            waypoints = self._route_simple(pin_positions)
            self.wires.append(Wire(net_name=net.name, waypoints=waypoints))
            print(f"  {net.name}: {len(waypoints)} waypoints")
    
    def _route_simple(self, pins: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Simple L-shaped routing"""
        waypoints = []
        
        for i in range(len(pins) - 1):
            x1, y1 = pins[i]
            x2, y2 = pins[i + 1]
            
            if i == 0:
                waypoints.append((x1, y1))
            
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            
            if dx > dy:
                waypoints.append((x2, y1))
            else:
                waypoints.append((x1, y2))
            
            waypoints.append((x2, y2))
        
        return self._remove_duplicates(waypoints)
    
    def _remove_duplicates(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove consecutive duplicates"""
        if not points:
            return []
        
        result = [points[0]]
        for p in points[1:]:
            if abs(p[0] - result[-1][0]) > 0.1 or abs(p[1] - result[-1][1]) > 0.1:
                result.append(p)
        return result
    
    def _find_placed(self, reference: str):
        """Find placed component"""
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
        """Render to pen commands"""
        bounds = self._calc_bounds(placed_components, wires)
        min_x, min_y, max_x, max_y = bounds
        
        circuit_width = max_x - min_x
        circuit_height = max_y - min_y
        
        if scale is None:
            scale_x = (SCREEN_WIDTH - 2 * self.MARGIN) / circuit_width if circuit_width > 0 else 1
            scale_y = (SCREEN_HEIGHT - 2 * self.MARGIN) / circuit_height if circuit_height > 0 else 1
            scale = min(scale_x, scale_y, 3.0)
        
        scaled_width = circuit_width * scale
        scaled_height = circuit_height * scale
        offset_x = (SCREEN_WIDTH - scaled_width) / 2 - min_x * scale
        offset_y = (SCREEN_HEIGHT - scaled_height) / 2 - min_y * scale
        
        print(f"\nRendering: scale={scale:.2f}x\n")
        
        commands = ["# Textbook Circuit", f"# Scale: {scale:.2f}x"]
        
        for comp in placed_components:
            commands.append(f"# {comp.reference}")
            commands.extend(self._render_component(comp, scale, offset_x, offset_y))
        
        for wire in wires:
            commands.append(f"# {wire.net_name}")
            commands.extend(self._render_wire(wire, scale, offset_x, offset_y))
        
        return commands
    
    def _calc_bounds(self, components, wires):
        """Calculate bounding box"""
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
        """Render component"""
        comp_def = self.library.get(placed.comp_type)
        if not comp_def:
            return [f"# ERROR: Unknown {placed.comp_type}"]
        
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
                commands.append(f'pen {action} {int(x * scale + offset_x)} {int(y * scale + offset_y)}')
            elif action == 'circle' and len(cmd) >= 5:
                dx, dy, r = cmd[2], cmd[3], cmd[4]
                dx_rot, dy_rot = self._rotate(dx, dy, placed.rotation)
                x = placed.x + dx_rot
                y = placed.y + dy_rot
                commands.append(f'pen circle {int(x * scale + offset_x)} {int(y * scale + offset_y)} {int(r * scale)}')
            elif action == 'line' and len(cmd) >= 6:
                dx1, dy1, dx2, dy2 = cmd[2], cmd[3], cmd[4], cmd[5]
                dx1_rot, dy1_rot = self._rotate(dx1, dy1, placed.rotation)
                dx2_rot, dy2_rot = self._rotate(dx2, dy2, placed.rotation)
                commands.append(f'pen line {int((placed.x + dx1_rot) * scale + offset_x)} {int((placed.y + dy1_rot) * scale + offset_y)} {int((placed.x + dx2_rot) * scale + offset_x)} {int((placed.y + dy2_rot) * scale + offset_y)}')
        
        return commands
    
    def _render_wire(self, wire, scale, offset_x, offset_y):
        """Render wire"""
        if len(wire.waypoints) < 2:
            return []
        
        commands = []
        x, y = wire.waypoints[0]
        commands.append(f'pen down {int(x * scale + offset_x)} {int(y * scale + offset_y)}')
        
        for x, y in wire.waypoints[1:]:
            commands.append(f'pen move {int(x * scale + offset_x)} {int(y * scale + offset_y)}')
        
        commands.append('pen up')
        return commands
    
    def _rotate(self, dx, dy, rotation):
        """Rotate offset"""
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
        print("Usage: python3 circuit_placer_textbook_fixed.py <netlist> <component_library.json>")
        sys.exit(1)
    
    # Import the archived LTSpice parser
    sys.path.insert(0, str(Path(__file__).parent.parent / "Archive" / "v2.3" / "claude" / "src"))
    from netlist_parser import NetlistParser
    
    netlist_path = Path(sys.argv[1])
    library_path = Path(sys.argv[2])
    
    parser = NetlistParser()
    circuit = parser.parse_file(netlist_path)
    parser.print_summary()
    
    placer = TextbookCircuitPlacer(library_path)
    placed, wires = placer.place_circuit(circuit)
    
    renderer = CircuitRenderer(library_path)
    commands = renderer.render(placed, wires)
    
    print("=" * 60)
    for cmd in commands:
        print(cmd)


if __name__ == '__main__':
    main()
