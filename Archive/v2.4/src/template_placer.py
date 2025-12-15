#!/usr/bin/env python3
"""
Template-Based Circuit Placer for ECE Circuits

Detects common circuit topologies and applies optimal template layouts:
- Series circuits (filters, resonant circuits)
- Parallel circuits (voltage/current dividers)
- Amplifier configurations (CE, CC, CB, op-amp)
- Oscillators (Wien, Colpitts, Hartley)

Designed for scalability to complex ECE circuits.
"""

import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
import math

@dataclass
class Pin:
    """Pin with absolute position"""
    component_ref: str
    pin_id: str
    x: float
    y: float
    angle: int  # Wire direction angle

@dataclass
class PlacedComponent:
    """Component with absolute placement"""
    reference: str  # R1, C1, V1, etc.
    component_type: str  # R, C, VDC, etc.
    x: float  # Center position X
    y: float  # Center position Y
    width: float  # Actual width in pixels
    height: float  # Actual height in pixels
    rotation: int = 0  # 0, 90, 180, 270
    pins: List[Pin] = field(default_factory=list)

@dataclass
class Net:
    """Electrical net connecting pins"""
    name: str
    pins: List[Tuple[str, str]]  # List of (component_ref, pin_id)

@dataclass
class Circuit:
    """Complete circuit definition"""
    components: List[Dict] = field(default_factory=list)  # From netlist
    nets: List[Net] = field(default_factory=list)

class TopologyDetector:
    """Detect circuit topology patterns"""

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.node_graph = self._build_node_graph()

    def _build_node_graph(self) -> Dict[str, List[Tuple[str, str]]]:
        """Build graph of node connectivity"""
        graph = defaultdict(list)

        for net in self.circuit.nets:
            # Each net connects multiple component pins
            for comp_ref, pin_id in net.pins:
                graph[net.name].append((comp_ref, pin_id))

        return dict(graph)

    def detect_topology(self) -> str:
        """
        Detect main circuit topology

        Returns:
            'series', 'parallel', 'voltage_divider', 'amplifier',
            'oscillator', 'mixed', or 'unknown'
        """
        # Count nodes and component types
        num_nets = len(self.circuit.nets)
        num_components = len(self.circuit.components)

        # Classify components
        sources = []
        passives = []
        active = []
        ground_nets = []

        for comp in self.circuit.components:
            comp_type = comp['component_type']
            if comp_type in ['VDC', 'VAC', 'IDC']:
                sources.append(comp)
            elif comp_type in ['R', 'C', 'L']:
                passives.append(comp)
            elif comp_type in ['OPAMP', 'NPN_BJT', 'PNP_BJT', 'N_MOSFET', 'P_MOSFET']:
                active.append(comp)
            elif comp_type == 'GND':
                # Find ground nets
                for net in self.circuit.nets:
                    for comp_ref, _ in net.pins:
                        if comp_ref == comp['reference']:
                            ground_nets.append(net.name)

        # Detection heuristics
        if len(active) > 0:
            # Has active components - likely amplifier or oscillator
            if len(active) == 1 and active[0]['component_type'] == 'OPAMP':
                return 'opamp_circuit'
            elif len(passives) >= 3:
                return 'oscillator'
            else:
                return 'amplifier'

        elif len(sources) == 1 and len(passives) >= 2:
            # One source, multiple passives
            if self._is_series_topology():
                if len(passives) == 2 and passives[0]['component_type'] == 'R' and passives[1]['component_type'] == 'C':
                    return 'rc_filter'
                elif len(passives) == 2 and passives[0]['component_type'] == 'R' and passives[1]['component_type'] == 'L':
                    return 'rl_filter'
                elif len(passives) == 3:
                    return 'rlc_filter'
                else:
                    return 'series'
            elif self._is_parallel_topology():
                return 'parallel'
            elif self._is_voltage_divider():
                return 'voltage_divider'

        return 'series'  # Default to series layout

    def _is_series_topology(self) -> bool:
        """Check if circuit is series (linear chain)"""
        # In series, most nodes have degree 2 (two connections)
        node_degrees = defaultdict(int)

        for net in self.circuit.nets:
            node_degrees[net.name] = len(net.pins)

        # Series: mostly degree-2 nodes
        degree_2_count = sum(1 for d in node_degrees.values() if d == 2)
        return degree_2_count >= len(node_degrees) * 0.6

    def _is_parallel_topology(self) -> bool:
        """Check if circuit has parallel branches"""
        # Parallel: some nodes have degree > 2
        for net in self.circuit.nets:
            if len(net.pins) > 2:
                return True
        return False

    def _is_voltage_divider(self) -> bool:
        """Check if circuit is a voltage divider (two series resistors)"""
        resistors = [c for c in self.circuit.components if c['component_type'] == 'R']
        if len(resistors) != 2:
            return False

        # Check if they're in series between source and ground
        return self._is_series_topology()


class TemplatePlacer:
    """Place components using topology-specific templates"""

    # Spacing constants (pixels)
    COMPONENT_SPACING = 250
    VERTICAL_SPACING = 200
    MARGIN = 150

    def __init__(self, library_path: Path):
        with open(library_path) as f:
            self.library = json.load(f)['components']

    def place(self, circuit: Circuit, topology: str) -> List[PlacedComponent]:
        """Place circuit components based on detected topology"""

        if topology in ['series', 'rc_filter', 'rl_filter', 'rlc_filter']:
            return self._place_series(circuit)
        elif topology == 'voltage_divider':
            return self._place_voltage_divider(circuit)
        elif topology == 'parallel':
            return self._place_parallel(circuit)
        elif topology == 'opamp_circuit':
            return self._place_opamp_circuit(circuit)
        elif topology in ['amplifier', 'oscillator']:
            return self._place_amplifier(circuit)
        else:
            # Fallback to series layout
            return self._place_series(circuit)

    def _place_series(self, circuit: Circuit) -> List[PlacedComponent]:
        """
        Place components in horizontal series layout

        Layout: VDC → R → L → C → GND
                (vertical) (horizontal components) (vertical)
        """
        placed = []

        # Sort components: sources first, then passives, then ground
        sources = [c for c in circuit.components if c['component_type'] in ['VDC', 'VAC']]
        passives = [c for c in circuit.components if c['component_type'] in ['R', 'L', 'C', 'D', 'ZD']]
        grounds = [c for c in circuit.components if c['component_type'] == 'GND']

        ordered = sources + passives + grounds

        # Base Y coordinate (horizontal center line)
        base_y = 400

        # Start X position
        current_x = self.MARGIN

        for comp in ordered:
            comp_type = comp['component_type']
            comp_data = self.library.get(comp_type, {})

            # Determine size and orientation
            if comp_type in ['VDC', 'VAC', 'GND']:
                # Vertical components
                width = comp_data['bbox']['width']
                height = comp_data['bbox']['height']
                rotation = 0
            else:
                # Horizontal components
                width = comp_data['bbox']['width']
                height = comp_data['bbox']['height']
                rotation = 0

            # Place component
            placed_comp = PlacedComponent(
                reference=comp['reference'],
                component_type=comp_type,
                x=current_x + width/2,
                y=base_y,
                width=width,
                height=height,
                rotation=rotation
            )

            # Calculate pin positions
            self._calculate_pin_positions(placed_comp, comp_data)

            placed.append(placed_comp)

            # Advance X position
            current_x += width + self.COMPONENT_SPACING

        return placed

    def _place_voltage_divider(self, circuit: Circuit) -> List[PlacedComponent]:
        """
        Place voltage divider in vertical stack

        Layout:
            VDC (top)
             |
            R1 (middle-top)
             |-- VOUT
            R2 (middle-bottom)
             |
            GND (bottom)
        """
        placed = []

        # Find components
        source = next((c for c in circuit.components if c['component_type'] in ['VDC', 'VAC']), None)
        resistors = [c for c in circuit.components if c['component_type'] == 'R']
        ground = next((c for c in circuit.components if c['component_type'] == 'GND'), None)

        components_ordered = [source] + resistors + ([ground] if ground else [])

        # Center X position
        center_x = 500
        current_y = self.MARGIN

        for comp in components_ordered:
            if not comp:
                continue

            comp_type = comp['component_type']
            comp_data = self.library.get(comp_type, {})

            width = comp_data['bbox']['width']
            height = comp_data['bbox']['height']

            placed_comp = PlacedComponent(
                reference=comp['reference'],
                component_type=comp_type,
                x=center_x,
                y=current_y + height/2,
                width=width,
                height=height,
                rotation=0
            )

            self._calculate_pin_positions(placed_comp, comp_data)
            placed.append(placed_comp)

            current_y += height + self.VERTICAL_SPACING

        return placed

    def _place_parallel(self, circuit: Circuit) -> List[PlacedComponent]:
        """
        Place parallel circuit

        Layout:
                 ┌── R1 ──┐
            VDC──┤        ├── GND
                 └── C1 ──┘
        """
        placed = []

        # Find components
        source = next((c for c in circuit.components if c['component_type'] in ['VDC', 'VAC']), None)
        passives = [c for c in circuit.components if c['component_type'] in ['R', 'C', 'L']]
        ground = next((c for c in circuit.components if c['component_type'] == 'GND'), None)

        # Place source on left
        if source:
            source_data = self.library[source['component_type']]
            placed.append(PlacedComponent(
                reference=source['reference'],
                component_type=source['component_type'],
                x=self.MARGIN,
                y=400,
                width=source_data['bbox']['width'],
                height=source_data['bbox']['height']
            ))
            self._calculate_pin_positions(placed[-1], source_data)

        # Place parallel components vertically stacked
        start_x = self.MARGIN + 300
        start_y = 200

        for i, comp in enumerate(passives):
            comp_data = self.library[comp['component_type']]
            y_pos = start_y + i * self.VERTICAL_SPACING

            placed_comp = PlacedComponent(
                reference=comp['reference'],
                component_type=comp['component_type'],
                x=start_x,
                y=y_pos,
                width=comp_data['bbox']['width'],
                height=comp_data['bbox']['height']
            )
            self._calculate_pin_positions(placed_comp, comp_data)
            placed.append(placed_comp)

        # Place ground on right
        if ground:
            ground_data = self.library['GND']
            placed.append(PlacedComponent(
                reference=ground['reference'],
                component_type='GND',
                x=start_x + 300,
                y=400,
                width=ground_data['bbox']['width'],
                height=ground_data['bbox']['height']
            ))
            self._calculate_pin_positions(placed[-1], ground_data)

        return placed

    def _place_opamp_circuit(self, circuit: Circuit) -> List[PlacedComponent]:
        """Place op-amp based circuit (inverting/non-inverting)"""
        # Simplified: Place op-amp in center, components around it
        return self._place_series(circuit)  # Fallback for now

    def _place_amplifier(self, circuit: Circuit) -> List[PlacedComponent]:
        """Place transistor amplifier circuit"""
        # Simplified: Use series layout
        return self._place_series(circuit)  # Fallback for now

    def _calculate_pin_positions(self, placed_comp: PlacedComponent, comp_data: Dict):
        """Calculate absolute pin positions for placed component"""
        for pin in comp_data.get('pins', []):
            # Get relative pin position [0,1]
            rel_x = pin['x']
            rel_y = pin['y']

            # Convert to absolute based on component placement
            # Apply rotation if needed (TODO: implement rotation)
            abs_x = placed_comp.x - placed_comp.width/2 + rel_x * placed_comp.width
            abs_y = placed_comp.y - placed_comp.height/2 + rel_y * placed_comp.height

            pin_obj = Pin(
                component_ref=placed_comp.reference,
                pin_id=pin['id'],
                x=abs_x,
                y=abs_y,
                angle=pin['angle']
            )

            placed_comp.pins.append(pin_obj)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 template_placer.py <netlist.json> <component_library.json>")
        print("\nExample:")
        print("  python3 template_placer.py circuit.json src/component_library.json")
        sys.exit(1)

    netlist_path = Path(sys.argv[1])
    library_path = Path(sys.argv[2])

    # Load netlist (converted to JSON format)
    with open(netlist_path) as f:
        netlist_data = json.load(f)

    # Build circuit
    circuit = Circuit()
    circuit.components = netlist_data.get('components', [])
    circuit.nets = [Net(name=n['name'], pins=n['pins']) for n in netlist_data.get('nets', [])]

    # Detect topology
    detector = TopologyDetector(circuit)
    topology = detector.detect_topology()
    print(f"Detected topology: {topology}", file=sys.stderr)

    # Place components
    placer = TemplatePlacer(library_path)
    placed_components = placer.place(circuit, topology)

    print(f"Placed {len(placed_components)} components", file=sys.stderr)

    # Output placement result
    output = {
        'topology': topology,
        'components': []
    }

    for comp in placed_components:
        comp_data = {
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
        }
        output['components'].append(comp_data)

    # Add nets for router
    output['nets'] = [{'name': net.name, 'pins': net.pins} for net in circuit.nets]

    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
