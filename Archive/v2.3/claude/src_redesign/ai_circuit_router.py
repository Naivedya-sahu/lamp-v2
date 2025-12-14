#!/usr/bin/env python3
"""
AI-Powered Circuit Router
Uses Claude API to intelligently route wires along rectangle perimeter
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from netlist_parser import NetlistParser, Circuit

SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

@dataclass
class PlacedComponent:
    """Component with placement"""
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


class AICircuitRouter:
    """AI-powered routing using Claude API"""
    
    RECT_WIDTH = 800
    RECT_HEIGHT = 500
    WIRE_MARGIN = 80
    
    def __init__(self, library_path: Path):
        with open(library_path, 'r') as f:
            self.library = json.load(f)
        
        self.placed_components: List[PlacedComponent] = []
        self.wires: List[Wire] = []
        self.circuit: Circuit = None
        
        self.rails = {
            'TOP': self.WIRE_MARGIN,
            'RIGHT': self.RECT_WIDTH - self.WIRE_MARGIN,
            'BOTTOM': self.RECT_HEIGHT - self.WIRE_MARGIN,
            'LEFT': self.WIRE_MARGIN
        }
    
    def route_circuit(self, circuit: Circuit):
        """Main routing function"""
        self.circuit = circuit
        
        # Place components
        sources, passives, _ = self._categorize_components()
        self._place_rectangular_loop(sources, passives)
        self._calculate_pin_positions()
        
        # Route each net using AI
        self._route_with_ai()
        
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
        
        # Voltage source on LEFT
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
        
        # Passives around perimeter
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
    
    def _route_with_ai(self):
        """Route using Claude API for intelligent path planning"""
        import requests
        
        print(f"\nRouting with AI:")
        
        for net_name, net in self.circuit.nets.items():
            if len(net.pins) < 2:
                continue
            
            # Gather pin data
            pin_data = []
            for ref, pin_num in net.pins:
                placed = self._find_placed(ref)
                if placed and pin_num - 1 < len(placed.pin_positions):
                    pin_pos = placed.pin_positions[pin_num - 1]
                    pin_data.append({
                        'component': ref,
                        'edge': placed.edge,
                        'position': {'x': pin_pos[0], 'y': pin_pos[1]}
                    })
            
            if len(pin_data) < 2:
                continue
            
            # Ask Claude to route this net
            waypoints = self._ask_claude_to_route(net_name, pin_data)
            
            wire = Wire(net_name=net_name, points=waypoints)
            self.wires.append(wire)
            print(f"  {net_name}: {len(waypoints)} waypoints")
    
    def _ask_claude_to_route(self, net_name: str, pin_data: List[Dict]) -> List[Tuple[float, float]]:
        """
        Ask Claude API to generate routing path
        
        Claude will reason about the best way to connect pins following
        the rectangle perimeter without crossing through the center
        """
        import requests
        
        # Build prompt for Claude
        prompt = f"""You are a circuit routing expert. Route a wire between these pins following ONLY the rectangle perimeter.

Rectangle dimensions: {self.RECT_WIDTH} x {self.RECT_HEIGHT}
Routing rails (margins from edges): {self.WIRE_MARGIN}px

Pins to connect:
{json.dumps(pin_data, indent=2)}

CRITICAL RULES:
1. Wires MUST follow the rectangle perimeter - NEVER cut through center
2. Use routing rails at: TOP={self.rails['TOP']}, RIGHT={self.rails['RIGHT']}, BOTTOM={self.rails['BOTTOM']}, LEFT={self.rails['LEFT']}
3. Always take the SHORTEST perimeter path
4. Create waypoints at corners where direction changes

Return ONLY a JSON array of waypoints in format: [{{"x": float, "y": float}}, ...]

Start from first pin, add corner waypoints as needed, end at second pin."""

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=30
            )
            
            data = response.json()
            
            # Extract waypoints from response
            if 'content' in data and len(data['content']) > 0:
                text = data['content'][0].get('text', '').strip()
                
                # Remove markdown backticks if present
                text = text.replace('```json', '').replace('```', '').strip()
                
                waypoints_json = json.loads(text)
                waypoints = [(w['x'], w['y']) for w in waypoints_json]
                
                return waypoints
            
        except Exception as e:
            print(f"    AI routing failed: {e}")
        
        # Fallback to simple direct routing
        return [
            (pin_data[0]['position']['x'], pin_data[0]['position']['y']),
            (pin_data[1]['position']['x'], pin_data[1]['position']['y'])
        ]
    
    def _find_placed(self, reference: str) -> PlacedComponent:
        """Find placed component"""
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
        """Render circuit"""
        
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
        
        print(f"\nRendering: scale={scale:.2f}x")
        
        commands = [f"# AI-Routed Circuit - Scale {scale:.2f}x"]
        
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
            return [f"# ERROR: {placed.comp_type} not found"]
        
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
        print("Usage: python3 ai_circuit_router.py <netlist> <library.json>")
        sys.exit(1)
    
    netlist_path = Path(sys.argv[1])
    library_path = Path(sys.argv[2])
    
    parser = NetlistParser()
    circuit = parser.parse_file(netlist_path)
    
    router = AICircuitRouter(library_path)
    placed_components, wires = router.route_circuit(circuit)
    
    renderer = CircuitRenderer(library_path)
    commands = renderer.render(placed_components, wires)
    
    print("\n" + "=" * 60)
    for cmd in commands:
        print(cmd)


if __name__ == '__main__':
    main()
