#!/usr/bin/env python3
"""
Component Definition System with Anchor Points and Fixed Block Sizes
Defines standard electrical components with connection points for circuit netlists
"""

import json
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class AnchorPoint:
    """Connection point on a component"""
    name: str  # e.g., "left", "right", "top", "bottom", "anode", "cathode"
    x: float   # Relative position within component (0.0 to 1.0)
    y: float   # Relative position within component (0.0 to 1.0)
    net: str = ""  # Network name (for netlist), e.g., "VCC", "GND", "N1"

    def get_absolute_pos(self, comp_x: float, comp_y: float, width: float, height: float) -> Tuple[float, float]:
        """Get absolute position based on component placement"""
        return (comp_x + self.x * width, comp_y + self.y * height)


@dataclass
class ComponentDefinition:
    """Definition of a component type with standardized size and anchor points"""
    name: str
    category: str  # "passive", "source", "semiconductor", "logic", "connector"
    width: float   # Standard width in pixels
    height: float  # Standard height in pixels
    anchors: List[AnchorPoint]
    svg_group_ids: List[str]  # Possible group IDs from library
    symbol: str  # Circuit symbol (R, C, L, V, etc.)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'category': self.category,
            'width': self.width,
            'height': self.height,
            'anchors': [{'name': a.name, 'x': a.x, 'y': a.y, 'net': a.net} for a in self.anchors],
            'svg_group_ids': self.svg_group_ids,
            'symbol': self.symbol
        }

    @staticmethod
    def from_dict(data):
        """Create from dictionary"""
        anchors = [AnchorPoint(**a) for a in data['anchors']]
        return ComponentDefinition(
            name=data['name'],
            category=data['category'],
            width=data['width'],
            height=data['height'],
            anchors=anchors,
            svg_group_ids=data['svg_group_ids'],
            symbol=data['symbol']
        )


class ComponentLibrary:
    """Library of standard component definitions"""

    def __init__(self):
        self.components: Dict[str, ComponentDefinition] = {}
        self._init_standard_components()

    def _init_standard_components(self):
        """Initialize standard component definitions"""

        # RESISTOR - 120x48px, horizontal, 2-terminal
        self.add_component(ComponentDefinition(
            name="Resistor",
            category="passive",
            width=120,
            height=48,
            anchors=[
                AnchorPoint("left", 0.0, 0.5),   # Left terminal at middle height
                AnchorPoint("right", 1.0, 0.5)   # Right terminal at middle height
            ],
            svg_group_ids=["g1087", "g1092", "g1263", "g1253"],  # Resistor symbol variations
            symbol="R"
        ))

        # CAPACITOR - 120x48px, horizontal, 2-terminal
        self.add_component(ComponentDefinition(
            name="Capacitor",
            category="passive",
            width=120,
            height=48,
            anchors=[
                AnchorPoint("left", 0.0, 0.5),
                AnchorPoint("right", 1.0, 0.5)
            ],
            svg_group_ids=["g1058", "g1100", "g1136", "g1162"],  # Capacitor symbol variations
            symbol="C"
        ))

        # INDUCTOR - 120x48px, horizontal, 2-terminal
        self.add_component(ComponentDefinition(
            name="Inductor",
            category="passive",
            width=120,
            height=48,
            anchors=[
                AnchorPoint("left", 0.0, 0.5),
                AnchorPoint("right", 1.0, 0.5)
            ],
            svg_group_ids=["g1046", "g1063", "g1081", "g1091"],  # Inductor symbol variations
            symbol="L"
        ))

        # DC VOLTAGE SOURCE - 80x80px, vertical orientation
        self.add_component(ComponentDefinition(
            name="VDC",
            category="source",
            width=80,
            height=80,
            anchors=[
                AnchorPoint("positive", 0.5, 0.0),   # Top terminal (positive)
                AnchorPoint("negative", 0.5, 1.0)    # Bottom terminal (negative)
            ],
            svg_group_ids=["g184", "g188"],  # Voltage source symbols
            symbol="V"
        ))

        # AC VOLTAGE SOURCE - 80x80px
        self.add_component(ComponentDefinition(
            name="VAC",
            category="source",
            width=80,
            height=80,
            anchors=[
                AnchorPoint("positive", 0.5, 0.0),
                AnchorPoint("negative", 0.5, 1.0)
            ],
            svg_group_ids=["g1032"],  # AC source symbols
            symbol="V~"
        ))

        # GROUND - 60x40px
        self.add_component(ComponentDefinition(
            name="Ground",
            category="connector",
            width=60,
            height=40,
            anchors=[
                AnchorPoint("gnd", 0.5, 0.0)  # Connection point at top
            ],
            svg_group_ids=["g1080", "g1080-3"],  # Ground symbols
            symbol="GND"
        ))

        # DIODE - 80x60px, horizontal
        self.add_component(ComponentDefinition(
            name="Diode",
            category="semiconductor",
            width=80,
            height=60,
            anchors=[
                AnchorPoint("anode", 0.0, 0.5),     # Left (anode)
                AnchorPoint("cathode", 1.0, 0.5)    # Right (cathode)
            ],
            svg_group_ids=["g2999", "g3007"],  # Diode symbols
            symbol="D"
        ))

        # WIRE/CONNECTION - flexible size for routing
        self.add_component(ComponentDefinition(
            name="Wire",
            category="connector",
            width=0,  # Flexible
            height=0,
            anchors=[],  # Defined by endpoints
            svg_group_ids=[],
            symbol="-"
        ))

    def add_component(self, comp: ComponentDefinition):
        """Add component to library"""
        self.components[comp.name] = comp
        # Also index by symbol
        self.components[comp.symbol] = comp

    def get_component(self, identifier: str) -> ComponentDefinition:
        """Get component by name or symbol"""
        return self.components.get(identifier)

    def get_by_svg_group(self, group_id: str) -> ComponentDefinition:
        """Find component definition by SVG group ID"""
        for comp in self.components.values():
            if group_id in comp.svg_group_ids:
                return comp
        return None

    def save_to_json(self, filepath: str):
        """Save library to JSON file"""
        data = {
            name: comp.to_dict()
            for name, comp in self.components.items()
            if name == comp.name  # Avoid duplicates (symbol references)
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_json(self, filepath: str):
        """Load library from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.components = {}
        for name, comp_data in data.items():
            comp = ComponentDefinition.from_dict(comp_data)
            self.add_component(comp)


@dataclass
class PlacedComponent:
    """Instance of a component placed in a circuit"""
    ref: str  # Reference designator (R1, C1, etc.)
    component_type: str  # Name or symbol from ComponentDefinition
    x: float  # Placement X coordinate
    y: float  # Placement Y coordinate
    rotation: int = 0  # Rotation angle (0, 90, 180, 270)
    value: str = ""  # Component value (e.g., "10k", "100nF")

    def get_anchor_absolute(self, anchor_name: str, comp_def: ComponentDefinition) -> Tuple[float, float]:
        """Get absolute position of an anchor point"""
        for anchor in comp_def.anchors:
            if anchor.name == anchor_name:
                # TODO: Apply rotation transformation
                return anchor.get_absolute_pos(self.x, self.y, comp_def.width, comp_def.height)
        return None


class Circuit:
    """Circuit design with netlist"""

    def __init__(self, name: str = "Unnamed Circuit"):
        self.name = name
        self.components: List[PlacedComponent] = []
        self.wires: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
        self.nets: Dict[str, List[str]] = {}  # net_name -> [ref.anchor, ...]

    def add_component(self, comp: PlacedComponent):
        """Add component to circuit"""
        self.components.append(comp)

    def add_wire(self, from_pos: Tuple[float, float], to_pos: Tuple[float, float]):
        """Add wire connection"""
        self.wires.append((from_pos, to_pos))

    def connect(self, comp1_ref: str, anchor1: str, comp2_ref: str, anchor2: str, net_name: str = None):
        """Connect two component anchors in netlist"""
        if net_name is None:
            net_name = f"N{len(self.nets) + 1}"

        if net_name not in self.nets:
            self.nets[net_name] = []

        self.nets[net_name].append(f"{comp1_ref}.{anchor1}")
        self.nets[net_name].append(f"{comp2_ref}.{anchor2}")

    def generate_netlist(self) -> str:
        """Generate SPICE-style netlist"""
        lines = [f"* {self.name}"]
        lines.append("")

        # Component definitions
        for comp in self.components:
            # Format: REF node1 node2 value
            # TODO: Map anchors to nets to get node numbers
            lines.append(f"* {comp.ref} (placeholder)")

        lines.append("")
        lines.append(".end")
        return "\n".join(lines)


def create_rc_vdc_circuit(library: ComponentLibrary) -> Circuit:
    """
    Create simple RC circuit with VDC source in series

    Circuit: VDC --- R --- C --- GND
                      |         |
                      +---------+
    """
    circuit = Circuit("RC Circuit with DC Source")

    # Get component definitions
    vdc_def = library.get_component("VDC")
    r_def = library.get_component("R")
    c_def = library.get_component("C")
    gnd_def = library.get_component("GND")

    # Place components
    # VDC at top (200, 100)
    vdc = PlacedComponent(ref="V1", component_type="VDC", x=200, y=100, value="5V")
    circuit.add_component(vdc)

    # Resistor horizontal (300, 200)
    r1 = PlacedComponent(ref="R1", component_type="R", x=300, y=200, value="10k")
    circuit.add_component(r1)

    # Capacitor horizontal (450, 200)
    c1 = PlacedComponent(ref="C1", component_type="C", x=450, y=200, value="100nF")
    circuit.add_component(c1)

    # Ground (540, 280)
    gnd = PlacedComponent(ref="GND1", component_type="GND", x=540, y=280)
    circuit.add_component(gnd)

    # Define netlist connections
    circuit.connect("V1", "positive", "R1", "left", "VCC")
    circuit.connect("R1", "right", "C1", "left", "N1")
    circuit.connect("C1", "right", "GND1", "gnd", "GND")
    circuit.connect("V1", "negative", "GND1", "gnd", "GND")

    return circuit


def main():
    """Demo: Create component library and sample circuit"""
    print("Creating Component Library...")
    library = ComponentLibrary()

    # Save to JSON
    library.save_to_json("component_definitions.json")
    print(f"Saved {len(library.components)} component types to component_definitions.json")

    # List components
    print("\nStandard Components:")
    for name, comp in library.components.items():
        if name == comp.name:  # Avoid symbol duplicates
            print(f"  {comp.symbol:4s} - {comp.name:15s} ({comp.width}x{comp.height}px, {len(comp.anchors)} anchors)")

    # Create sample circuit
    print("\nCreating RC + VDC circuit...")
    circuit = create_rc_vdc_circuit(library)

    print(f"\nCircuit: {circuit.name}")
    print(f"Components: {len(circuit.components)}")
    for comp in circuit.components:
        print(f"  {comp.ref:6s} {comp.component_type:10s} @ ({comp.x}, {comp.y}) = {comp.value}")

    print(f"\nNets:")
    for net_name, connections in circuit.nets.items():
        print(f"  {net_name:8s}: {', '.join(connections)}")


if __name__ == '__main__':
    main()
