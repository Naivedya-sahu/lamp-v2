#!/usr/bin/env python3
"""
Layer 3: Circuit Placer & Renderer
Auto-placement algorithm with blocked structure and wire routing
Converts complete circuit to pen commands with scaling
"""

import json
import sys
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set
from netlist_parser import NetlistParser, Circuit, NetlistComponent

@dataclass
class PlacedComponent:
    """Component with placement information"""
    reference: str
    component_type: str
    x: float
    y: float
    rotation: int = 0  # 0, 90, 180, 270 degrees
    pin_positions: List[Tuple[float, float]] = field(default_factory=list)

@dataclass
class Wire:
    """Wire connection between two pins"""
    net_name: str
    points: List[Tuple[float, float]]  # Path points for routing

class CircuitPlacer:
    """Automatic circuit placement with blocked structure"""
    
    # Component spacing constants (in SVG units)
    COMPONENT_SPACING_X = 200
    COMPONENT_SPACING_Y = 200
    GRID_SIZE = 50
    
    def __init__(self, component_library_path: Path):
        # Load component library
        with open(component_library_path, 'r') as f:
            self.library = json.load(f)
        
        self.placed_components: List[PlacedComponent] = []
        self.wires: List[Wire] = []
        self.circuit: Circuit = None
    
    def place_circuit(self, circuit: Circuit) -> Tuple[List[PlacedComponent], List[Wire]]:
        """Place all components and route wires"""
        self.circuit = circuit
        
        # Step 1: Topological ordering for left-to-right flow
        ordered_components = self._topological_sort()
        
        # Step 2: Place components in blocked structure
        self._place_components_blocked(ordered_components)
        
        # Step 3: Route wires between components
        self._route_wires()
        
        return self.placed_components, self.wires
    
    def _topological_sort(self) -> List[NetlistComponent]:
        """
        Sort components for left-to-right signal flow
        Priority: Voltage sources -> Components -> Ground
        """
        voltage_sources = []
        components = []
        grounds = []
        
        for comp in self.circuit.components:
            if comp.component_type in ['VDC', 'VAC', 'IDC']:
                voltage_sources.append(comp)
            elif comp.component_type == 'GND':
                grounds.append(comp)
            else:
                components.append(comp)
        
        # Order: sources, then components by connectivity, then grounds
        return voltage_sources + components + grounds
    
    def _place_components_blocked(self, components: List[NetlistComponent]):
        """Place components in organized blocked structure"""
        # Determine circuit complexity and layout pattern
        num_components = len(components)
        
        # Calculate grid dimensions (prefer horizontal layout)
        if num_components <= 3:
            cols = num_components
            rows = 1
        elif num_components <= 6:
            cols = 3
            rows = 2
        else:
            cols = math.ceil(math.sqrt(num_components * 1.5))
            rows = math.ceil(num_components / cols)
        
        # Place components in grid
        for idx, comp in enumerate(components):
            row = idx // cols
            col = idx % cols
            
            # Calculate position
            x = col * self.COMPONENT_SPACING_X
            y = row * self.COMPONENT_SPACING_Y
            
            # Determine optimal rotation based on connectivity
            rotation = self._determine_rotation(comp, col, cols)
            
            # Get component dimensions and pins from library
            comp_data = self.library.get(comp.component_type, {})
            pins = comp_data.get('pins', [])
            
            # Calculate absolute pin positions after placement and rotation
            pin_positions = self._calculate_pin_positions(
                pins, x, y, rotation
            )
            
            placed = PlacedComponent(
                reference=comp.reference,
                component_type=comp.component_type,
                x=x,
                y=y,
                rotation=rotation,
                pin_positions=pin_positions
            )
            
            self.placed_components.append(placed)
    
    def _determine_rotation(self, comp: NetlistComponent, col: int, total_cols: int) -> int:
        """Determine optimal component rotation"""
        # Voltage sources on left: face right (0°)
        if comp.component_type in ['VDC', 'VAC', 'IDC'] and col == 0:
            return 0
        
        # Ground symbols at bottom: face down (270°)
        if comp.component_type == 'GND':
            return 270
        
        # OpAmps: typically face right
        if comp.component_type == 'OPAMP':
            return 0
        
        # Default: horizontal orientation
        return 0
    
    def _calculate_pin_positions(
        self, 
        pins: List[Dict], 
        x: float, 
        y: float, 
        rotation: int
    ) -> List[Tuple[float, float]]:
        """Calculate absolute pin positions after placement and rotation"""
        positions = []
        
        for pin in pins:
            px, py = pin['x'], pin['y']
            
            # Apply rotation
            if rotation == 90:
                px, py = -py, px
            elif rotation == 180:
                px, py = -px, -py
            elif rotation == 270:
                px, py = py, -px
            
            # Apply translation
            px += x
            py += y
            
            positions.append((px, py))
        
        return positions
    
    def _route_wires(self):
        """Route wires between connected pins"""
        for net in self.circuit.nets:
            # Skip single-pin nets
            if len(net.components) < 2:
                continue
            
            # Get all pin positions for this net
            pin_positions = []
            for comp_ref, pin_idx in net.components:
                placed = self._find_placed_component(comp_ref)
                if placed and pin_idx < len(placed.pin_positions):
                    pin_positions.append(placed.pin_positions[pin_idx])
            
            # Route wire through all pins
            if len(pin_positions) >= 2:
                wire = self._route_orthogonal(net.name, pin_positions)
                self.wires.append(wire)
    
    def _find_placed_component(self, reference: str) -> PlacedComponent:
        """Find placed component by reference"""
        for comp in self.placed_components:
            if comp.reference == reference:
                return comp
        return None
    
    def _route_orthogonal(self, net_name: str, pins: List[Tuple[float, float]]) -> Wire:
        """Route wire using orthogonal (Manhattan) routing"""
        if len(pins) < 2:
            return Wire(net_name=net_name, points=[])
        
        # Simple orthogonal routing: connect pins with L-shaped paths
        points = []
        
        for i in range(len(pins) - 1):
            x1, y1 = pins[i]
            x2, y2 = pins[i + 1]
            
            # Add starting point
            if i == 0:
                points.append((x1, y1))
            
            # L-shaped routing (horizontal then vertical)
            # Choose direction based on which is longer
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            
            if dx > dy:
                # Horizontal-first routing
                points.append((x2, y1))
                points.append((x2, y2))
            else:
                # Vertical-first routing
                points.append((x1, y2))
                points.append((x2, y2))
        
        return Wire(net_name=net_name, points=points)
    
    def calculate_bounds(self) -> Tuple[float, float, float, float]:
        """Calculate bounding box of entire circuit"""
        if not self.placed_components:
            return (0, 0, 0, 0)
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        # Check all component bounds
        for comp in self.placed_components:
            comp_data = self.library.get(comp.component_type, {})
            bounds = comp_data.get('bounds', [0, 0, 0, 0])
            
            # Apply placement offset
            local_min_x, local_min_y, local_max_x, local_max_y = bounds
            min_x = min(min_x, comp.x + local_min_x)
            min_y = min(min_y, comp.y + local_min_y)
            max_x = max(max_x, comp.x + local_max_x)
            max_y = max(max_y, comp.y + local_max_y)
        
        # Check all wire points
        for wire in self.wires:
            for x, y in wire.points:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        
        return (min_x, min_y, max_x, max_y)

class CircuitRenderer:
    """Render circuit to pen commands"""
    
    # reMarkable 2 screen dimensions
    SCREEN_WIDTH = 1404
    SCREEN_HEIGHT = 1872
    MARGIN = 100
    
    def __init__(self, component_library_path: Path):
        with open(component_library_path, 'r') as f:
            self.library = json.load(f)
    
    def render(
        self, 
        placed_components: List[PlacedComponent], 
        wires: List[Wire],
        scale: float = None
    ) -> List[str]:
        """Render complete circuit to pen commands"""
        
        # Calculate circuit bounds
        bounds = self._calculate_bounds(placed_components, wires)
        min_x, min_y, max_x, max_y = bounds
        circuit_width = max_x - min_x
        circuit_height = max_y - min_y
        
        # Auto-calculate scale if not provided
        if scale is None:
            scale_x = (self.SCREEN_WIDTH - 2 * self.MARGIN) / circuit_width if circuit_width > 0 else 1
            scale_y = (self.SCREEN_HEIGHT - 2 * self.MARGIN) / circuit_height if circuit_height > 0 else 1
            scale = min(scale_x, scale_y, 5.0)  # Cap at 5x
        
        # Calculate centering offset
        scaled_width = circuit_width * scale
        scaled_height = circuit_height * scale
        offset_x = (self.SCREEN_WIDTH - scaled_width) / 2 - min_x * scale
        offset_y = (self.SCREEN_HEIGHT - scaled_height) / 2 - min_y * scale
        
        print(f"Circuit dimensions: {circuit_width:.1f} x {circuit_height:.1f}")
        print(f"Scale factor: {scale:.2f}x")
        print(f"Output dimensions: {scaled_width:.1f} x {scaled_height:.1f}")
        
        # Render all components
        pen_commands = []
        pen_commands.append(f"# Circuit render: {len(placed_components)} components, {len(wires)} wires")
        pen_commands.append(f"# Scale: {scale:.2f}x, Bounds: {bounds}")
        
        for comp in placed_components:
            commands = self._render_component(comp, scale, offset_x, offset_y)
            pen_commands.extend(commands)
        
        # Render all wires
        for wire in wires:
            commands = self._render_wire(wire, scale, offset_x, offset_y)
            pen_commands.extend(commands)
        
        return pen_commands
    
    def _calculate_bounds(
        self, 
        components: List[PlacedComponent], 
        wires: List[Wire]
    ) -> Tuple[float, float, float, float]:
        """Calculate circuit bounds"""
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for comp in components:
            for x, y in comp.pin_positions:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        
        for wire in wires:
            for x, y in wire.points:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        
        return (min_x, min_y, max_x, max_y)
    
    def _render_component(
        self, 
        comp: PlacedComponent, 
        scale: float, 
        offset_x: float, 
        offset_y: float
    ) -> List[str]:
        """Render single component"""
        comp_data = self.library.get(comp.component_type, {})
        base_commands = comp_data.get('pen_commands', [])
        
        commands = []
        commands.append(f"# Component: {comp.reference} ({comp.component_type})")
        
        for cmd in base_commands:
            # Transform coordinates
            parts = cmd.split()
            if len(parts) < 3:
                continue
            
            command_type = ' '.join(parts[:-2])
            try:
                x = float(parts[-2])
                y = float(parts[-1])
                
                # Apply component placement
                x += comp.x
                y += comp.y
                
                # Apply rotation (TODO: implement if needed)
                
                # Apply scale and screen offset
                x = x * scale + offset_x
                y = y * scale + offset_y
                
                # Clamp to screen bounds
                x = max(0, min(x, self.SCREEN_WIDTH - 1))
                y = max(0, min(y, self.SCREEN_HEIGHT - 1))
                
                commands.append(f"{command_type} {int(x)} {int(y)}")
            except ValueError:
                continue
        
        return commands
    
    def _render_wire(
        self, 
        wire: Wire, 
        scale: float, 
        offset_x: float, 
        offset_y: float
    ) -> List[str]:
        """Render wire"""
        if len(wire.points) < 2:
            return []
        
        commands = []
        commands.append(f"# Wire: {wire.net_name}")
        
        # Draw wire path
        x1, y1 = wire.points[0]
        x1 = int(x1 * scale + offset_x)
        y1 = int(y1 * scale + offset_y)
        commands.append(f"pen down {x1} {y1}")
        
        for x, y in wire.points[1:]:
            x = int(x * scale + offset_x)
            y = int(y * scale + offset_y)
            commands.append(f"pen move {x} {y}")
        
        commands.append("pen up")
        
        return commands

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 circuit_placer.py <netlist_file> <component_library.json> [scale]")
        print("Example: python3 circuit_placer.py rc_circuit.net component_library.json 2.0")
        sys.exit(1)
    
    netlist_path = Path(sys.argv[1])
    library_path = Path(sys.argv[2])
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else None
    
    # Parse netlist
    parser = NetlistParser()
    circuit = parser.parse_file(netlist_path)
    parser.print_summary()
    
    # Place circuit
    placer = CircuitPlacer(library_path)
    placed_components, wires = placer.place_circuit(circuit)
    
    print(f"Placed {len(placed_components)} components")
    print(f"Routed {len(wires)} wires")
    
    # Render to pen commands
    renderer = CircuitRenderer(library_path)
    pen_commands = renderer.render(placed_components, wires, scale)
    
    # Output pen commands
    print("\n" + "=" * 60)
    print("PEN COMMANDS")
    print("=" * 60)
    for cmd in pen_commands:
        print(cmd)

if __name__ == '__main__':
    main()
