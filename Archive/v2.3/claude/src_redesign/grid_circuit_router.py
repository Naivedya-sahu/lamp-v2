#!/usr/bin/env python3
"""
Grid-Based Circuit Placer with A* Routing
Like LEGO blocks + pathfinding algorithms
"""

import json
import sys
import heapq
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional
from netlist_parser import NetlistParser, Circuit

SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

@dataclass
class PlacedComponent:
    """Component placement"""
    reference: str
    comp_type: str
    grid_x: int  # Grid position
    grid_y: int
    rotation: int = 0
    edge: str = ""
    world_x: float = 0  # World coordinates (for rendering)
    world_y: float = 0
    pin_positions: List[Tuple[float, float]] = field(default_factory=list)

@dataclass
class Wire:
    """Wire route"""
    net_name: str
    points: List[Tuple[float, float]]


class GridRouter:
    """Grid-based placement and routing"""
    
    # Grid dimensions
    GRID_WIDTH = 40
    GRID_HEIGHT = 30
    CELL_SIZE = 25  # Pixels per grid cell
    
    def __init__(self, library_path: Path):
        with open(library_path, 'r') as f:
            self.library = json.load(f)
        
        self.placed_components: List[PlacedComponent] = []
        self.wires: List[Wire] = []
        self.circuit: Circuit = None
        
        # Grid for obstacle detection
        self.grid = [[False for _ in range(self.GRID_WIDTH)] for _ in range(self.GRID_HEIGHT)]
        
        # Component blocking regions
        self.component_blocks: Dict[str, List[Tuple[int, int]]] = {}
    
    def route_circuit(self, circuit: Circuit):
        """Main routing"""
        self.circuit = circuit
        
        # Step 1: Place components on grid
        sources, passives, _ = self._categorize_components()
        self._place_on_grid(sources, passives)
        
        # Step 2: Mark component regions as blocked
        self._mark_component_blocks()
        
        # Step 3: Calculate world coordinates for pins
        self._calculate_pin_positions()
        
        # Step 4: Route nets using A* pathfinding
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
    
    def _place_on_grid(self, sources, passives):
        """
        Place components on grid in rectangular layout
        
        Grid layout (example 40x30):
            TOP: (20, 5)
            RIGHT: (35, 15)
            BOTTOM: (20, 25)
            LEFT: (5, 15)
        """
        print(f"\nPlacing components on {self.GRID_WIDTH}x{self.GRID_HEIGHT} grid:")
        
        # Define positions on grid
        positions = [
            {'name': 'LEFT', 'gx': 5, 'gy': 15, 'rot': 0},
            {'name': 'TOP', 'gx': 20, 'gy': 5, 'rot': 0},
            {'name': 'RIGHT', 'gx': 35, 'gy': 15, 'rot': 90},
            {'name': 'BOTTOM', 'gx': 20, 'gy': 25, 'rot': 0},
        ]
        
        # Place voltage source
        for source in sources:
            pos = positions[0]
            placed = PlacedComponent(
                reference=source.reference,
                comp_type=source.comp_type,
                grid_x=pos['gx'],
                grid_y=pos['gy'],
                rotation=pos['rot'],
                edge=pos['name']
            )
            self.placed_components.append(placed)
            print(f"  {source.reference}: grid({pos['gx']}, {pos['gy']}) {pos['name']}")
        
        # Place passives
        for idx, comp in enumerate(passives):
            pos = positions[(idx + 1) % len(positions)]
            placed = PlacedComponent(
                reference=comp.reference,
                comp_type=comp.comp_type,
                grid_x=pos['gx'],
                grid_y=pos['gy'],
                rotation=pos['rot'],
                edge=pos['name']
            )
            self.placed_components.append(placed)
            print(f"  {comp.reference}: grid({pos['gx']}, {pos['gy']}) {pos['name']}")
    
    def _mark_component_blocks(self):
        """
        Mark grid cells occupied by components as blocked
        
        Each component blocks a region around its anchor point
        """
        print(f"\nMarking component blocks:")
        
        for placed in self.placed_components:
            comp_def = self.library.get(placed.comp_type)
            if not comp_def:
                continue
            
            # Component size in grid cells (approximate)
            width = comp_def['width']
            height = comp_def['height']
            
            # Size in grid cells
            grid_w = max(2, int(width / self.CELL_SIZE))
            grid_h = max(2, int(height / self.CELL_SIZE))
            
            # Mark cells as blocked
            blocks = []
            for dy in range(-grid_h//2, grid_h//2 + 1):
                for dx in range(-grid_w//2, grid_w//2 + 1):
                    gx = placed.grid_x + dx
                    gy = placed.grid_y + dy
                    
                    if 0 <= gx < self.GRID_WIDTH and 0 <= gy < self.GRID_HEIGHT:
                        self.grid[gy][gx] = True
                        blocks.append((gx, gy))
            
            self.component_blocks[placed.reference] = blocks
            print(f"  {placed.reference}: blocking {len(blocks)} cells")
    
    def _calculate_pin_positions(self):
        """Calculate world coordinates for pins"""
        for placed in self.placed_components:
            comp_def = self.library.get(placed.comp_type)
            if not comp_def:
                continue
            
            # World anchor position
            placed.world_x = placed.grid_x * self.CELL_SIZE
            placed.world_y = placed.grid_y * self.CELL_SIZE
            
            pins = comp_def.get('pins', [])
            placed.pin_positions = []
            
            for pin in pins:
                dx, dy = pin['dx'], pin['dy']
                dx_rot, dy_rot = self._rotate(dx, dy, placed.rotation)
                abs_x = placed.world_x + dx_rot
                abs_y = placed.world_y + dy_rot
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
        """Route all nets using A* pathfinding"""
        print(f"\nRouting with A* pathfinding:")
        
        for net_name, net in self.circuit.nets.items():
            if len(net.pins) < 2:
                continue
            
            # Get pin positions
            pin_data = []
            for ref, pin_num in net.pins:
                placed = self._find_placed(ref)
                if placed and pin_num - 1 < len(placed.pin_positions):
                    pin_world = placed.pin_positions[pin_num - 1]
                    # Convert to grid coordinates
                    pin_grid = (int(pin_world[0] / self.CELL_SIZE), 
                               int(pin_world[1] / self.CELL_SIZE))
                    pin_data.append({
                        'world': pin_world,
                        'grid': pin_grid,
                        'component': ref
                    })
            
            if len(pin_data) < 2:
                continue
            
            # Route using A*
            waypoints = self._route_astar(pin_data)
            
            wire = Wire(net_name=net_name, points=waypoints)
            self.wires.append(wire)
            print(f"  {net_name}: {len(waypoints)} waypoints")
    
    def _route_astar(self, pin_data: List[Dict]) -> List[Tuple[float, float]]:
        """
        A* pathfinding between pins
        
        Temporarily unblock component cells for routing
        """
        all_waypoints = []
        
        for i in range(len(pin_data) - 1):
            start_world = pin_data[i]['world']
            end_world = pin_data[i + 1]['world']
            start_grid = pin_data[i]['grid']
            end_grid = pin_data[i + 1]['grid']
            
            # A* pathfinding on grid
            path_grid = self._astar_pathfind(start_grid, end_grid)
            
            if not path_grid:
                # Fallback: direct line
                all_waypoints.extend([start_world, end_world])
            else:
                # Convert grid path to world coordinates
                path_world = [(gx * self.CELL_SIZE, gy * self.CELL_SIZE) 
                             for gx, gy in path_grid]
                all_waypoints.extend(path_world)
        
        return self._remove_duplicates(all_waypoints)
    
    def _astar_pathfind(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        A* pathfinding algorithm
        
        Returns grid path from start to end
        """
        # Priority queue: (f_score, g_score, position)
        open_set = [(0, 0, start)]
        came_from = {}
        g_score = {start: 0}
        
        while open_set:
            _, current_g, current = heapq.heappop(open_set)
            
            if current == end:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return list(reversed(path))
            
            # Check neighbors (4-connected: up, down, left, right)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                nx, ny = neighbor
                
                # Bounds check
                if not (0 <= nx < self.GRID_WIDTH and 0 <= ny < self.GRID_HEIGHT):
                    continue
                
                # Skip blocked cells (components)
                if self.grid[ny][nx]:
                    continue
                
                # Calculate scores
                tentative_g = current_g + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))
        
        # No path found
        return []
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        """Manhattan distance heuristic"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
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
        
        commands = [f"# Grid-Based Circuit with A* Routing"]
        
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
                x = placed.world_x + dx_rot
                y = placed.world_y + dy_rot
                sx = int(x * scale + offset_x)
                sy = int(y * scale + offset_y)
                commands.append(f'pen {action} {sx} {sy}')
            elif action == 'circle' and len(cmd) >= 5:
                dx, dy, r = cmd[2], cmd[3], cmd[4]
                dx_rot, dy_rot = self._rotate(dx, dy, placed.rotation)
                x = placed.world_x + dx_rot
                y = placed.world_y + dy_rot
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
        print("Usage: python3 grid_circuit_router.py <netlist> <library.json>")
        sys.exit(1)
    
    netlist_path = Path(sys.argv[1])
    library_path = Path(sys.argv[2])
    
    parser = NetlistParser()
    circuit = parser.parse_file(netlist_path)
    parser.print_summary()
    
    router = GridRouter(library_path)
    placed, wires = router.route_circuit(circuit)
    
    renderer = CircuitRenderer(library_path)
    commands = renderer.render(placed, wires)
    
    print("=" * 60)
    for cmd in commands:
        print(cmd)


if __name__ == '__main__':
    main()
