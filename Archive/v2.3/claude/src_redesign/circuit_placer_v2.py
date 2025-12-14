#!/usr/bin/env python3
"""
Optimal Circuit Router - Axis Extension + Minimal Corners
Extends wires along component axes, then takes shortest path
"""

import json
import sys
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from netlist_parser import NetlistParser, Circuit

SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

@dataclass
class PlacedComponent:
    """Component placement"""
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


class OptimalRouter:
    """Smart routing with axis extension and minimal bends"""
    
    RECT_WIDTH = 800
    RECT_HEIGHT = 500
    
    # How far to extend wires along component axis
    AXIS_EXTENSION = 100
    
    def __init__(self, library_path: Path):
        with open(library_path, 'r') as f:
            self.library = json.load(f)
        
        self.placed_components: List[PlacedComponent] = []
        self.wires: List[Wire] = []
        self.circuit: Circuit = None
    
    def route_circuit(self, circuit: Circuit):
        """Main routing"""
        self.circuit = circuit
        
        sources, passives, _ = self._categorize_components()
        self._place_rectangular_loop(sources, passives)
        self._calculate_pin_positions()
        self._route_all_nets()
        
        return self.placed_components, self.wires
    
    def _categorize_components(self):
        """Categorize components"""
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
        """Place components around rectangle"""
        print(f"\nPlacing components:")
        
        edges = [
            {'name': 'TOP', 'x': self.RECT_WIDTH/2, 'y': 0, 'rot': 0},
            {'name': 'RIGHT', 'x': self.RECT_WIDTH, 'y': self.RECT_HEIGHT/2, 'rot': 90},
            {'name': 'BOTTOM', 'x': self.RECT_WIDTH/2, 'y': self.RECT_HEIGHT, 'rot': 0},
        ]
        
        # Place voltage source on LEFT
        for source in sources:
            placed = PlacedComponent(
                reference=source.reference,
                comp_type=source.comp_type,
                anchor_x=0,
                anchor_y=self.RECT_HEIGHT / 2,
                rotation=0,
                edge='LEFT'
            )
            self.placed_components.append(placed)
            print(f"  {source.reference}: LEFT")
        
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
            print(f"  {comp.reference}: {edge['name']}")
    
    def _calculate_pin_positions(self):
        """Calculate pin positions"""
        for placed in self.placed_components:
            comp_def = self.library.get(placed.comp_type)
            if not comp_def:
                continue
            
            pins = comp_def.get('pins', [])
            placed.pin_positions = []
            
            for pin in pins:
                dx, dy = pin['dx'], pin['dy']
                dx_rot, dy_rot = self._rotate(dx, dy, placed.rotation)
                abs_x = placed.anchor_x + dx_rot
                abs_y = placed.anchor_y + dy_rot
                placed.pin_positions.append((abs_x, abs_y))
    
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
    
    def _route_all_nets(self):
        """Route all nets"""
        print(f"\nRouting nets:")
        
        for net_name, net in self.circuit.nets.items():
            if len(net.pins) < 2:
                continue
            
            # Get pin data
            pin_data = []
            for ref, pin_num in net.pins:
                placed = self._find_placed(ref)
                if placed and pin_num - 1 < len(placed.pin_positions):
                    pin_pos = placed.pin_positions[pin_num - 1]
                    pin_data.append({
                        'component': placed,
                        'edge': placed.edge,
                        'pos': pin_pos
                    })
            
            if len(pin_data) < 2:
                continue
            
            # Route with axis extension and smart corners
            waypoints = self._route_optimal(pin_data)
            
            wire = Wire(net_name=net_name, points=waypoints)
            self.wires.append(wire)
            print(f"  {net_name}: {len(waypoints)} waypoints")
    
    def _route_optimal(self, pin_data: List[Dict]) -> List[Tuple[float, float]]:
        """
        Optimal routing strategy:
        1. Extend from pin1 along its component's axis
        2. Find shortest connection to pin2's axis extension
        3. Extend to pin2
        
        Key: Only add corners if they actually reduce path length
        """
        waypoints = []
        
        for i in range(len(pin_data) - 1):
            data1 = pin_data[i]
            data2 = pin_data[i + 1]
            
            x1, y1 = data1['pos']
            x2, y2 = data2['pos']
            edge1 = data1['edge']
            edge2 = data2['edge']
            
            if i == 0:
                waypoints.append((x1, y1))
            
            # Get axis extension points
            ext1 = self._get_axis_extension(x1, y1, edge1, towards=(x2, y2))
            ext2 = self._get_axis_extension(x2, y2, edge2, towards=(x1, y1))
            
            # Strategy: Connect the two extension points optimally
            if edge1 == edge2:
                # Same edge: direct connection along edge
                waypoints.append(ext1)
                waypoints.append(ext2)
            
            elif self._are_adjacent_edges(edge1, edge2):
                # Adjacent edges: single corner connection
                corner = self._get_corner_between_edges(edge1, edge2, ext1, ext2)
                if corner:
                    waypoints.append(ext1)
                    waypoints.append(corner)
                    waypoints.append(ext2)
                else:
                    # Direct L-connection
                    waypoints.append(ext1)
                    waypoints.append((ext2[0], ext1[1]))
                    waypoints.append(ext2)
            
            else:
                # Opposite edges: need two corners
                corners = self._get_two_corners(edge1, edge2, ext1, ext2)
                waypoints.append(ext1)
                for corner in corners:
                    waypoints.append(corner)
                waypoints.append(ext2)
            
            waypoints.append((x2, y2))
        
        return self._remove_duplicates(waypoints)
    
    def _get_axis_extension(self, x: float, y: float, edge: str, 
                           towards: Tuple[float, float]) -> Tuple[float, float]:
        """
        Extend pin along component's natural axis
        
        Direction depends on which way we're heading
        """
        tx, ty = towards
        
        if edge == 'TOP':
            # Component is horizontal - extend horizontally
            if tx > x:
                return (x + self.AXIS_EXTENSION, y)
            else:
                return (x - self.AXIS_EXTENSION, y)
        
        elif edge == 'BOTTOM':
            # Component is horizontal - extend horizontally
            if tx > x:
                return (x + self.AXIS_EXTENSION, y)
            else:
                return (x - self.AXIS_EXTENSION, y)
        
        elif edge == 'RIGHT':
            # Component is vertical - extend vertically
            if ty > y:
                return (x, y + self.AXIS_EXTENSION)
            else:
                return (x, y - self.AXIS_EXTENSION)
        
        elif edge == 'LEFT':
            # Component is vertical - extend vertically
            if ty > y:
                return (x, y + self.AXIS_EXTENSION)
            else:
                return (x, y - self.AXIS_EXTENSION)
        
        return (x, y)
    
    def _are_adjacent_edges(self, edge1: str, edge2: str) -> bool:
        """Check if two edges are adjacent (share a corner)"""
        adjacent_pairs = [
            ('LEFT', 'TOP'), ('TOP', 'LEFT'),
            ('TOP', 'RIGHT'), ('RIGHT', 'TOP'),
            ('RIGHT', 'BOTTOM'), ('BOTTOM', 'RIGHT'),
            ('BOTTOM', 'LEFT'), ('LEFT', 'BOTTOM')
        ]
        return (edge1, edge2) in adjacent_pairs
    
    def _get_corner_between_edges(self, edge1: str, edge2: str, 
                                   ext1: Tuple[float, float], 
                                   ext2: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """Get the corner point between two adjacent edges"""
        x1, y1 = ext1
        x2, y2 = ext2
        
        # The corner is simply the L-connection point
        if edge1 in ['TOP', 'BOTTOM'] and edge2 in ['LEFT', 'RIGHT']:
            return (x2, y1)
        elif edge1 in ['LEFT', 'RIGHT'] and edge2 in ['TOP', 'BOTTOM']:
            return (x1, y2)
        
        return None
    
    def _get_two_corners(self, edge1: str, edge2: str,
                        ext1: Tuple[float, float],
                        ext2: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Get two corner points for opposite edge connections
        
        Choose the shortest path around the rectangle
        """
        x1, y1 = ext1
        x2, y2 = ext2
        
        corners = []
        
        if edge1 == 'LEFT' and edge2 == 'RIGHT':
            # LEFT to RIGHT: go via top or bottom
            if y1 < self.RECT_HEIGHT / 2:
                # Go via top
                corners = [(x1, 0), (x2, 0)]
            else:
                # Go via bottom
                corners = [(x1, self.RECT_HEIGHT), (x2, self.RECT_HEIGHT)]
        
        elif edge1 == 'RIGHT' and edge2 == 'LEFT':
            # RIGHT to LEFT: go via top or bottom
            if y1 < self.RECT_HEIGHT / 2:
                corners = [(x1, 0), (x2, 0)]
            else:
                corners = [(x1, self.RECT_HEIGHT), (x2, self.RECT_HEIGHT)]
        
        elif edge1 == 'TOP' and edge2 == 'BOTTOM':
            # TOP to BOTTOM: go via left or right
            if x1 < self.RECT_WIDTH / 2:
                corners = [(0, y1), (0, y2)]
            else:
                corners = [(self.RECT_WIDTH, y1), (self.RECT_WIDTH, y2)]
        
        elif edge1 == 'BOTTOM' and edge2 == 'TOP':
            # BOTTOM to TOP: go via left or right
            if x1 < self.RECT_WIDTH / 2:
                corners = [(0, y1), (0, y2)]
            else:
                corners = [(self.RECT_WIDTH, y1), (self.RECT_WIDTH, y2)]
        
        return corners
    
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
        """Find component"""
        for p in self.placed_components:
            if p.reference == reference:
                return p
        return None


class CircuitRenderer:
    """Render to pen commands"""
    
    MARGIN = 100
    
    def __init__(self, library_path: Path):
        with open(library_path, 'r') as f:
            self.library = json.load(f)
    
    def render(self, placed_components, wires, scale=None):
        """Render"""
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
        
        commands = [f"# Optimal-Routed Circuit"]
        
        for comp in placed_components:
            commands.extend(self._render_component(comp, scale, offset_x, offset_y))
        
        for wire in wires:
            commands.extend(self._render_wire(wire, scale, offset_x, offset_y))
        
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
            return [f"# ERROR: {placed.comp_type}"]
        
        commands = [f"# {placed.reference}"]
        
        for cmd in comp_def.get('pen_commands', []):
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
        """Rotate"""
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
        print("Usage: python3 circuit_placer_optimal.py <netlist> <library.json>")
        sys.exit(1)
    
    netlist_path = Path(sys.argv[1])
    library_path = Path(sys.argv[2])
    
    parser = NetlistParser()
    circuit = parser.parse_file(netlist_path)
    parser.print_summary()
    
    router = OptimalRouter(library_path)
    placed, wires = router.route_circuit(circuit)
    
    renderer = CircuitRenderer(library_path)
    commands = renderer.render(placed, wires)
    
    print("=" * 60)
    for cmd in commands:
        print(cmd)


if __name__ == '__main__':
    main()