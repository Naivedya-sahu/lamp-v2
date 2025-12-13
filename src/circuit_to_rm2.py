#!/usr/bin/env python3
"""
Complete Circuit Pipeline: Netlist → Placement → Routing → RM2 Rendering

End-to-end pipeline for ECE circuit schematics:
1. Parse SPICE netlist
2. Detect circuit topology
3. Place components using templates
4. Route wires with Manhattan routing
5. Render to reMarkable 2

Usage:
    python3 circuit_to_rm2.py examples/rc_filter.net [OPTIONS]
"""

import sys
import json
import subprocess
from pathlib import Path
import argparse
from typing import List, Dict

# Import our modules
sys.path.insert(0, str(Path(__file__).parent))
from netlist_to_json import NetlistParser
from template_placer import TopologyDetector, TemplatePlacer, Circuit, Net
from manhattan_router import ManhattanRouter

class CircuitRenderer:
    """Render placed and routed circuit to RM2"""

    SCREEN_WIDTH = 1404
    SCREEN_HEIGHT = 1872

    def __init__(self, component_library_path: Path, draw_script_path: Path):
        self.library_path = component_library_path
        self.draw_script = draw_script_path

        with open(component_library_path) as f:
            self.library = json.load(f)['components']

    def render(self, placed_circuit: Dict, rm2_ip: str = None, dry_run: bool = False) -> List[str]:
        """
        Render circuit to pen commands

        Returns list of lamp commands
        """
        commands = []

        # Calculate scaling to fit screen
        scale = self._calculate_scale(placed_circuit['components'])

        print(f"Rendering at scale: {scale:.2f}x", file=sys.stderr)

        # Render components
        for comp in placed_circuit['components']:
            comp_commands = self._render_component(comp, scale, rm2_ip, dry_run)
            commands.extend(comp_commands)

        # Render wires
        for wire in placed_circuit.get('wires', []):
            wire_commands = self._render_wire(wire, scale)
            commands.extend(wire_commands)

        return commands

    def _calculate_scale(self, components: List[Dict]) -> float:
        """Calculate scale factor to fit circuit on screen"""
        if not components:
            return 1.0

        # Find bounding box
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for comp in components:
            pos = comp['position']
            size = comp['size']

            min_x = min(min_x, pos['x'] - size['width']/2)
            max_x = max(max_x, pos['x'] + size['width']/2)
            min_y = min(min_y, pos['y'] - size['height']/2)
            max_y = max(max_y, pos['y'] + size['height']/2)

        # Add wires to bounds
        # (Simplified - wires already considered in placement)

        circuit_width = max_x - min_x
        circuit_height = max_y - min_y

        # Calculate scale with margins
        margin = 100
        scale_x = (self.SCREEN_WIDTH - 2 * margin) / circuit_width if circuit_width > 0 else 1.0
        scale_y = (self.SCREEN_HEIGHT - 2 * margin) / circuit_height if circuit_height > 0 else 1.0

        # Use smaller scale to fit both dimensions
        scale = min(scale_x, scale_y, 2.0)  # Cap at 2x

        return scale

    def _render_component(self, comp: Dict, scale: float, rm2_ip: str = None,
                         dry_run: bool = False) -> List[str]:
        """Render single component using draw_component.sh"""
        commands = []

        comp_type = comp['type']
        svg_file = self.library[comp_type]['svg_file']
        pos = comp['position']
        size = comp['size']

        # Calculate scaled position and size
        scaled_x = int(pos['x'] * scale)
        scaled_y = int(pos['y'] * scale)
        scaled_width = int(size['width'] * scale)
        scaled_height = int(size['height'] * scale)

        # Build command
        cmd = [
            str(self.draw_script),
            svg_file,
            '--width', str(scaled_width),
            '--height', str(scaled_height),
            '--x', str(scaled_x),
            '--y', str(scaled_y)
        ]

        if dry_run:
            cmd.append('--dry-run')
        elif rm2_ip:
            cmd.extend(['--rm2', rm2_ip])

        print(f"Drawing {comp['reference']} ({comp_type}) at ({scaled_x}, {scaled_y})", file=sys.stderr)

        # Execute draw command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Warning: Failed to draw {comp['reference']}: {result.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"Error drawing {comp['reference']}: {e}", file=sys.stderr)

        return commands

    def _render_wire(self, wire: Dict, scale: float) -> List[str]:
        """Render wire path"""
        commands = []
        path = wire['path']

        if len(path) < 2:
            return commands

        # Start wire
        first = path[0]
        commands.append(f"pen down {int(first['x'] * scale)} {int(first['y'] * scale)}")

        # Draw segments
        for point in path[1:]:
            commands.append(f"pen move {int(point['x'] * scale)} {int(point['y'] * scale)}")

        commands.append("pen up")

        return commands


def main():
    parser = argparse.ArgumentParser(
        description='Complete circuit rendering pipeline: Netlist → RM2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s examples/rc_filter.net --dry-run
  %(prog)s examples/voltage_divider.net --rm2 10.11.99.1
  %(prog)s examples/rlc_series.net --rm2 10.11.99.1 --output circuit.lamp
        """
    )

    parser.add_argument('netlist', help='SPICE netlist file (.net)')
    parser.add_argument('--rm2', metavar='IP', help='RM2 IP address (enables actual rendering)')
    parser.add_argument('--dry-run', action='store_true', help='Test without sending to RM2')
    parser.add_argument('--output', '-o', metavar='FILE', help='Save pen commands to file')
    parser.add_argument('--library', default='src/component_library.json',
                       help='Component library JSON (default: src/component_library.json)')
    parser.add_argument('--draw-script', default='src/draw_component.sh',
                       help='Draw component script (default: src/draw_component.sh)')

    args = parser.parse_args()

    # Validate inputs
    netlist_path = Path(args.netlist)
    if not netlist_path.exists():
        print(f"Error: Netlist not found: {netlist_path}", file=sys.stderr)
        sys.exit(1)

    library_path = Path(args.library)
    if not library_path.exists():
        print(f"Error: Component library not found: {library_path}", file=sys.stderr)
        sys.exit(1)

    draw_script_path = Path(args.draw_script)
    if not draw_script_path.exists():
        print(f"Error: Draw script not found: {draw_script_path}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60, file=sys.stderr)
    print("Circuit Pipeline: Netlist → Placement → Routing → RM2", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Step 1: Parse netlist
    print("\n[1/4] Parsing netlist...", file=sys.stderr)
    netlist_parser = NetlistParser()
    netlist_data = netlist_parser.parse_file(netlist_path)

    print(f"  Components: {len(netlist_data['components'])}", file=sys.stderr)
    print(f"  Nets: {len(netlist_data['nets'])}", file=sys.stderr)

    # Build circuit object
    circuit = Circuit()
    circuit.components = netlist_data['components']
    circuit.nets = [Net(name=n['name'], pins=n['pins']) for n in netlist_data['nets']]

    # Step 2: Detect topology
    print("\n[2/4] Detecting topology...", file=sys.stderr)
    detector = TopologyDetector(circuit)
    topology = detector.detect_topology()
    print(f"  Detected: {topology}", file=sys.stderr)

    # Step 3: Place components
    print("\n[3/4] Placing components...", file=sys.stderr)
    placer = TemplatePlacer(library_path)
    placed_components = placer.place(circuit, topology)
    print(f"  Placed: {len(placed_components)} components", file=sys.stderr)

    # Convert to dict format
    placed_dict = {
        'topology': topology,
        'components': []
    }

    for comp in placed_components:
        placed_dict['components'].append({
            'reference': comp.reference,
            'type': comp.component_type,
            'position': {'x': comp.x, 'y': comp.y},
            'size': {'width': comp.width, 'height': comp.height},
            'rotation': comp.rotation,
            'pins': [
                {
                    'id': pin.pin_id,
                    'position': {'x': pin.x, 'y': pin.y},
                    'angle': pin.angle
                }
                for pin in comp.pins
            ]
        })

    placed_dict['nets'] = [{'name': net.name, 'pins': net.pins} for net in circuit.nets]

    # Step 4: Route wires
    print("\n[4/4] Routing wires...", file=sys.stderr)
    router = ManhattanRouter(grid_size=10)
    router.set_obstacles_from_components(placed_dict['components'])

    wires = []
    for net in placed_dict['nets']:
        wire = router.route_net(net, placed_dict['components'])
        wires.append({
            'net': wire.net_name,
            'path': [{'x': p[0], 'y': p[1]} for p in wire.path]
        })
        print(f"  Routed {wire.net_name}: {len(wire.path)} points", file=sys.stderr)

    placed_dict['wires'] = wires

    # Step 5: Render to RM2
    print("\n[5/5] Rendering circuit...", file=sys.stderr)
    renderer = CircuitRenderer(library_path, draw_script_path)

    if args.dry_run or args.rm2:
        commands = renderer.render(placed_dict, args.rm2, args.dry_run)

        if args.output:
            with open(args.output, 'w') as f:
                f.write('\n'.join(commands))
            print(f"\nSaved commands to: {args.output}", file=sys.stderr)

        print("\n" + "=" * 60, file=sys.stderr)
        print("Circuit rendering complete!", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

        if args.rm2:
            print(f"\nCheck your reMarkable 2 at {args.rm2}", file=sys.stderr)
    else:
        print("\nNo rendering target specified. Use --rm2 or --dry-run", file=sys.stderr)
        print(f"\nTo render: {sys.argv[0]} {args.netlist} --rm2 10.11.99.1", file=sys.stderr)


if __name__ == '__main__':
    main()
