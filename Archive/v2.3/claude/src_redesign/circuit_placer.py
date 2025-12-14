#!/usr/bin/env python3
"""
Circuit Placer - Fixed Perimeter Routing
Wires ALWAYS follow the rectangle perimeter, never cross through center
"""

import json
import sys
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set
from netlist_parser import NetlistParser, Circuit, Component

# reMarkable 2 screen dimensions
SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

@dataclass
class PlacedComponent:
    """Component with placement information"""
    reference: str
    comp_type: str
    anchor_x: float
    anchor_y: float
    rotation: int = 0
    edge: str = ""
    
    pin_positions: List[Tuple[float, float]] = field(default_factory=list)

@dataclass
class Wire:
    """Wire route"""
    net_name: str
    points: List[Tuple[float, float]]


class CircuitPlacer:
    """Textbook-style placement with perimeter-only routing"""
    
    # Rectangle dimensions
    RECT_WIDTH = 800
    RECT_HEIGHT = 500
    
    # Perimeter margin - how far from edge to route wires
    WIRE_MARGIN = 80
    
    def __init__(self, library_path: Path):
        with open(library_path, 'r') as f:
            self.library = json.load(f)
        
        self.placed_components: List[PlacedComponent] = []
        self.wires: List[Wire] = []
        self.circuit: Circuit = None
        
        # Define perimeter routing rails
        self.rails = {
            'TOP': self.WIRE_MARGIN,
            'RIGHT': self.RECT_WIDTH - self.WIRE_MARGIN,
            'BOTTOM': self.RECT_HEIGHT - self.WIRE_MARGIN,
            'LEFT': self.WIRE_MARGIN
        }
    
    def place_circuit(self, circuit: Circuit):
        """Place components"""
        self.circuit = circuit
        
        sources, passives, grounds = self._categorize_components()
        
        print(f"\nPlacing {len(sources)} sources, {len(passives)} passives")
        
        self._place_rectangular_loop(sources, passives)
        self._calculate_pin_positions()
        self._route_perimeter_wires()
        
        return self.placed_components, self.wires
    
    def _categorize_components(self):
        """Separate components"""
        sources = []
        passives = []
        grounds = []
        
        for comp in self.circuit.components:
            if comp.comp_type in ['VDC', 'VAC']:
                sources.append(comp)
            elif comp.comp_type == 'GND':
                grounds.append(comp)
            else:
                passives.append(comp)
        
        return sources, passives, grounds
    
    def _place_rectangular_loop(self, sources, passives):
        """
        Place components around rectangle
        
        CRITICAL: Match rotation to edge orientation
        - TOP edge: horizontal component (0°)
        - RIGHT edge: vertical component (90°)  
        - BOTTOM edge: horizontal component (0° or 180°)
        - LEFT edge: vertical component (0°)
        """
        print(f"Rectangular placement:")
        
        # Define edges with CORRECT rotations
        edges = [
            {'name': 'TOP', 'x': self.RECT_WIDTH/2, 'y': 0, 'rot': 0},           # horizontal
            {'name': 'RIGHT', 'x': self.RECT_WIDTH, 'y': self.RECT_HEIGHT/2, 'rot': 90},  # vertical
            {'name': 'BOTTOM', 'x': self.RECT_WIDTH/2, 'y': self.RECT_HEIGHT, 'rot': 0},  # horizontal
        ]
        
        # Place voltage source on LEFT edge (vertical orientation)
        for source in sources:
            placed = PlacedComponent(
                reference=source.reference,
                comp_type=source.comp_type,
                anchor_x=0,
                anchor_y=self.RECT_HEIGHT / 2,
                rotation=0,  # VDC/VAC are naturally vertical
                edge='LEFT'
            )
            self.placed_components.append(placed)
            print(f"  {source.reference}: LEFT edge, vertical")
        
        # Place passives
        for idx, comp in enumerate(passives):
            edge = edges[idx % len(edges)]
            
            placed = PlacedComponent(
                reference=comp.reference,
                comp_type=comp.comp_type,
                anchor_x=edge['x'],
                anchor_y=edge['y'],
                rotation=edge['rot'],
                edge=edge['name']
            )
            self.placed_components.append(placed)
            print(f"  {comp.reference}: {edge['name']} edge, rot={edge['rot']}°")
    
    def _calculate_pin_positions(self):
        """Calculate absolute pin positions"""
        for placed in self.placed_components:
            comp_def = self.library.get(placed.comp_type)
            if not comp_def:
                print(f"WARNING: {placed.comp_type} not in library")
                continue
            
            pins = comp_def.get('pins', [])
            placed.pin_positions = []
            
            for pin in pins:
                dx = pin['dx']
                dy = pin['dy']
                
                # Rotate
                dx_rot, dy_rot = self._rotate_point(dx, dy, placed.rotation)
                
                # Translate
                abs_x = placed.anchor_x + dx_rot
                abs_y = placed.anchor_y + dy_rot
                
                placed.pin_positions.append((abs_x, abs_y))
    
    def _rotate_point(self, dx: float, dy: float, rotation: int) -> Tuple[float, float]:
        """Rotate point"""
        if rotation == 0:
            return dx, dy
        elif rotation == 90:
            return -dy, dx
        elif rotation == 180:
            return -dx, -dy
        elif rotation == 270:
            return dy, -dx
        return dx, dy
    
    def _route_perimeter_wires(self):
        """
        Route wires along rectangle perimeter ONLY
        
        Strategy: Connect pins via perimeter routing rails
        - Never cut across the center
        - Always follow the rectangle edges
        """
        print(f"\nRouting {len(self.circuit.nets)} nets:")
        
        for net_name, net in self.circuit.nets.items():
            if len(net.pins) < 2:
                continue
            
            # Get pin locations
            pin_data = []
            for ref, pin_num in net.pins:
                placed = self._find_placed(ref)
                if placed and pin_num - 1 < len(placed.pin_positions):
                    pin_pos = placed.pin_positions[pin_num - 1]
                    pin_data.append({
                        'ref': ref,
                        'edge': placed.edge,
                        'pos': pin_pos,
                        'placed': placed
                    })
            
            if len(pin_data) < 2:
                continue
            
            # Route along perimeter
            waypoints = self._route_along_perimeter(pin_data)
            
            wire = Wire(net_name=net_name, points=waypoints)
            self.wires.append(wire)
            print(f"  {net_name}: {len(waypoints)} waypoints")
    
    def _route_along_perimeter(self, pin_data: List[Dict]) -> List[Tuple[float, float]]:
        """
        Route between pins by following rectangle perimeter
        
        Steps:
        1. Start at pin1
        2. Move to nearest perimeter rail
        3. Follow perimeter to next component's rail
        4. Move from rail to pin2
        """
        waypoints = []
        
        for i in range(len(pin_data) - 1):
            pin1 = pin_data[i]
            pin2 = pin_data[i + 1]
            
            x1, y1 = pin1['pos']
            x2, y2 = pin2['pos']
            edge1 = pin1['edge']
            edge2 = pin2['edge']
            
            if i == 0:
                waypoints.append((x1, y1))
            
            # Get perimeter path from edge1 to edge2
            perimeter_path = self._get_perimeter_path(pin1, pin2)
            waypoints.extend(perimeter_path)
            
            waypoints.append((x2, y2))
        
        return self._remove_duplicates(waypoints)
    
    def _get_perimeter_path(self, pin1_data: Dict, pin2_data: Dict) -> List[Tuple[float, float]]:
        """
        Get path along perimeter from pin1's edge to pin2's edge
        
        Returns waypoints that follow the rectangle perimeter
        """
        edge1 = pin1_data['edge']
        edge2 = pin2_data['edge']
        x1, y1 = pin1_data['pos']
        x2, y2 = pin2_data['pos']
        
        path = []
        
        # Define corner positions (perimeter routing)
        corners = {
            'TOP_LEFT': (self.rails['LEFT'], self.rails['TOP']),
            'TOP_RIGHT': (self.rails['RIGHT'], self.rails['TOP']),
            'BOTTOM_LEFT': (self.rails['LEFT'], self.rails['BOTTOM']),
            'BOTTOM_RIGHT': (self.rails['RIGHT'], self.rails['BOTTOM'])
        }
        
        # Route based on edge combinations
        if edge1 == 'LEFT' and edge2 == 'TOP':
            # LEFT → TOP: go up, then right
            path.append((x1, corners['TOP_LEFT'][1]))
            path.append((x2, corners['TOP_LEFT'][1]))
        
        elif edge1 == 'TOP' and edge2 == 'RIGHT':
            # TOP → RIGHT: go right, then down
            path.append((corners['TOP_RIGHT'][0], y1))
            path.append((corners['TOP_RIGHT'][0], y2))
        
        elif edge1 == 'RIGHT' and edge2 == 'BOTTOM':
            # RIGHT → BOTTOM: go down, then left
            path.append((x1, corners['BOTTOM_RIGHT'][1]))
            path.append((x2, corners['BOTTOM_RIGHT'][1]))
        
        elif edge1 == 'BOTTOM' and edge2 == 'LEFT':
            # BOTTOM → LEFT: go left, then up
            path.append((corners['BOTTOM_LEFT'][0], y1))
            path.append((corners['BOTTOM_LEFT'][0], y2))
        
        elif edge1 == 'LEFT' and edge2 == 'RIGHT':
            # LEFT → RIGHT: go around top
            path.append((x1, corners['TOP_LEFT'][1]))
            path.append(corners['TOP_RIGHT'])
            path.append((corners['TOP_RIGHT'][0], y2))
        
        elif edge1 == 'RIGHT' and edge2 == 'LEFT':
            # RIGHT → LEFT: go around bottom
            path.append((x1, corners['BOTTOM_RIGHT'][1]))
            path.append(corners['BOTTOM_LEFT'])
            path.append((corners['BOTTOM_LEFT'][0], y2))
        
        elif edge1 == 'TOP' and edge2 == 'BOTTOM':
            # TOP → BOTTOM: go around right
            path.append((corners['TOP_RIGHT'][0], y1))
            path.append(corners['BOTTOM_RIGHT'])
            path.append((x2, corners['BOTTOM_RIGHT'][1]))
        
        elif edge1 == 'BOTTOM' and edge2 == 'TOP':
            # BOTTOM → TOP: go around left
            path.append((corners['BOTTOM_LEFT'][0], y1))
            path.append(corners['TOP_LEFT'])
            path.append((x2, corners['TOP_LEFT'][1]))
        
        elif edge1 == edge2:
            # Same edge: direct connection along that edge
            if edge1 in ['TOP', 'BOTTOM']:
                # Horizontal edge
                mid_y = self.rails['TOP'] if edge1 == 'TOP' else self.rails['BOTTOM']
                path.append((x1, mid_y))
                path.append((x2, mid_y))
            else:
                # Vertical edge
                mid_x = self.rails['LEFT'] if edge1 == 'LEFT' else self.rails['RIGHT']
                path.append((mid_x, y1))
                path.append((mid_x, y2))
        
        return path
    
    def _remove_duplicates(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove consecutive duplicates"""
        if not points:
            return []
        
        result = [points[0]]
        for p in points[1:]:
            if abs(p[0] - result[-1][0]) > 0.1 or abs(p[1] - result[-1][1]) > 0.1:
                result.append(p)
        
        return result
    
    def _find_placed(self, reference: str) -> PlacedComponent:
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
        
        # Calculate bounds
        bounds = self._calc_bounds(placed_components, wires)
        min_x, min_y, max_x, max_y = bounds
        circuit_width = max_x - min_x
        circuit_height = max_y - min_y
        
        # Auto-scale
        if scale is None:
            scale_x = (SCREEN_WIDTH - 2 * self.MARGIN) / circuit_width if circuit_width > 0 else 1
            scale_y = (SCREEN_HEIGHT - 2 * self.MARGIN) / circuit_height if circuit_height > 0 else 1
            scale = min(scale_x, scale_y, 3.0)
        
        # Center
        scaled_width = circuit_width * scale
        scaled_height = circuit_height * scale
        offset_x = (SCREEN_WIDTH - scaled_width) / 2 - min_x * scale
        offset_y = (SCREEN_HEIGHT - scaled_height) / 2 - min_y * scale
        
        print(f"\nRendering:")
        print(f"  Scale: {scale:.2f}x")
        
        # Generate commands
        commands = []
        commands.append(f"# Circuit - Scale {scale:.2f}x")
        
        # Render components
        for comp in placed_components:
            cmds = self._render_component(comp, scale, offset_x, offset_y)
            commands.extend(cmds)
        
        # Render wires
        for wire in wires:
            cmds = self._render_wire(wire, scale, offset_x, offset_y)
            commands.extend(cmds)
        
        return commands
    
    def _calc_bounds(self, components, wires):
        """Calculate bounds"""
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for comp in components:
            for x, y in comp.pin_positions:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
        
        for wire in wires:
            for x, y in wire.points:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
        
        return (min_x, min_y, max_x, max_y)
    
    def _render_component(self, placed, scale, offset_x, offset_y):
        """Render component"""
        comp_def = self.library.get(placed.comp_type)
        if not comp_def:
            return [f"# ERROR: {placed.comp_type} not in library"]
        
        pen_cmds = comp_def.get('pen_commands', [])
        commands = [f"# {placed.reference} ({placed.comp_type})"]
        
        for cmd in pen_cmds:
            if not isinstance(cmd, list) or len(cmd) < 2:
                continue
            
            action = cmd[1]
            
            if action == 'up':
                commands.append('pen up')
            
            elif action in ['down', 'move'] and len(cmd) >= 4:
                dx, dy = cmd[2], cmd[3]
                dx_rot, dy_rot = self._rotate(dx, dy, placed.rotation)
                x = placed.anchor_x + dx_rot
                y = placed.anchor_y + dy_rot
                sx = int(x * scale + offset_x)
                sy = int(y * scale + offset_y)
                sx = max(0, min(sx, SCREEN_WIDTH - 1))
                sy = max(0, min(sy, SCREEN_HEIGHT - 1))
                commands.append(f'pen {action} {sx} {sy}')
            
            elif action == 'circle' and len(cmd) >= 5:
                dx, dy, r = cmd[2], cmd[3], cmd[4]
                dx_rot, dy_rot = self._rotate(dx, dy, placed.rotation)
                x = placed.anchor_x + dx_rot
                y = placed.anchor_y + dy_rot
                sx = int(x * scale + offset_x)
                sy = int(y * scale + offset_y)
                sr = int(r * scale)
                commands.append(f'pen circle {sx} {sy} {sr}')
            
            elif action == 'line' and len(cmd) >= 6:
                dx1, dy1, dx2, dy2 = cmd[2], cmd[3], cmd[4], cmd[5]
                dx1_rot, dy1_rot = self._rotate(dx1, dy1, placed.rotation)
                dx2_rot, dy2_rot = self._rotate(dx2, dy2, placed.rotation)
                x1 = placed.anchor_x + dx1_rot
                y1 = placed.anchor_y + dy1_rot
                x2 = placed.anchor_x + dx2_rot
                y2 = placed.anchor_y + dy2_rot
                sx1 = int(x1 * scale + offset_x)
                sy1 = int(y1 * scale + offset_y)
                sx2 = int(x2 * scale + offset_x)
                sy2 = int(y2 * scale + offset_y)
                commands.append(f'pen line {sx1} {sy1} {sx2} {sy2}')
        
        return commands
    
    def _render_wire(self, wire, scale, offset_x, offset_y):
        """Render wire"""
        if len(wire.points) < 2:
            return []
        
        commands = [f'# Wire: {wire.net_name}']
        
        x, y = wire.points[0]
        sx = int(x * scale + offset_x)
        sy = int(y * scale + offset_y)
        commands.append(f'pen down {sx} {sy}')
        
        for x, y in wire.points[1:]:
            sx = int(x * scale + offset_x)
            sy = int(y * scale + offset_y)
            commands.append(f'pen move {sx} {sy}')
        
        commands.append('pen up')
        
        return commands
    
    def _rotate(self, dx, dy, rotation):
        """Rotate point"""
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
        print("Usage: python3 circuit_placer.py <netlist> <library.json> [scale]")
        sys.exit(1)
    
    netlist_path = Path(sys.argv[1])
    library_path = Path(sys.argv[2])
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if not library_path.exists():
        print(f"ERROR: Library not found: {library_path}")
        sys.exit(1)
    
    # Parse netlist
    parser = NetlistParser()
    circuit = parser.parse_file(netlist_path)
    parser.print_summary()
    
    # Place circuit
    placer = CircuitPlacer(library_path)
    placed_components, wires = placer.place_circuit(circuit)
    
    # Render
    renderer = CircuitRenderer(library_path)
    pen_commands = renderer.render(placed_components, wires, scale)
    
    # Output
    print("\n" + "=" * 60)
    print("PEN COMMANDS")
    print("=" * 60)
    for cmd in pen_commands:
        print(cmd)


if __name__ == '__main__':
    main()
