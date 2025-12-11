#!/usr/bin/env python3
"""
Layer 2: Netlist Parser
Parses LTSpice-style netlists and creates circuit graph
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple
from enum import Enum

class ComponentType(Enum):
    """Standard LTSpice component prefixes"""
    RESISTOR = 'R'
    CAPACITOR = 'C'
    INDUCTOR = 'L'
    DIODE = 'D'
    VOLTAGE_DC = 'V'
    VOLTAGE_AC = 'VAC'
    CURRENT_DC = 'I'
    TRANSISTOR_NPN = 'Q'  # NPN_BJT
    TRANSISTOR_PNP = 'QP'  # PNP_BJT
    MOSFET_N = 'M'  # N_MOSFET
    MOSFET_P = 'MP'  # P_MOSFET
    OPAMP = 'U'
    SWITCH_OPEN = 'SW_OP'
    SWITCH_CLOSED = 'SW_CL'
    ZENER = 'ZD'
    GND = 'GND'

@dataclass
class NetlistComponent:
    """Component instance from netlist"""
    reference: str  # R1, C2, V1, etc.
    component_type: str  # Mapped to SVG filename (R, C, VDC, etc.)
    nodes: List[str]  # Connected node names
    value: str = ""  # Component value (10k, 100nF, 5V, etc.)
    model: str = ""  # Model name if specified

@dataclass
class NetlistNet:
    """Electrical net (connection between nodes)"""
    name: str
    components: List[Tuple[str, int]]  # List of (component_ref, pin_index)

@dataclass
class Circuit:
    """Complete circuit definition"""
    components: List[NetlistComponent] = field(default_factory=list)
    nets: List[NetlistNet] = field(default_factory=list)
    node_map: Dict[str, NetlistNet] = field(default_factory=dict)

class NetlistParser:
    """Parse LTSpice netlist format"""
    
    # Map LTSpice component types to SVG filenames
    COMPONENT_MAP = {
        'R': 'R',
        'C': 'C',
        'L': 'L',
        'D': 'D',
        'V': 'VDC',
        'VAC': 'VAC',
        'I': 'IDC',
        'Q': 'NPN_BJT',
        'QP': 'PNP_BJT',
        'M': 'N_MOSFET',
        'MP': 'P_MOSFET',
        'U': 'OPAMP',
        'SW_OP': 'SW_OP',
        'SW_CL': 'SW_CL',
        'ZD': 'ZD',
    }
    
    def __init__(self):
        self.circuit = Circuit()
        self.node_counter = 0
    
    def parse_file(self, netlist_path: Path) -> Circuit:
        """Parse netlist file"""
        with open(netlist_path, 'r') as f:
            content = f.read()
        
        return self.parse_text(content)
    
    def parse_text(self, netlist_text: str) -> Circuit:
        """Parse netlist text"""
        lines = netlist_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('*') or line.startswith('.'):
                continue
            
            # Parse component line
            self._parse_component_line(line)
        
        # Build net connectivity
        self._build_nets()
        
        return self.circuit
    
    def _parse_component_line(self, line: str):
        """Parse a single component line"""
        parts = line.split()
        if len(parts) < 2:
            return
        
        reference = parts[0]
        
        # Determine component type from reference prefix
        component_type = self._get_component_type(reference)
        
        # Parse nodes (position depends on component type)
        if component_type == 'GND':
            # Ground: GND node_name
            nodes = [parts[1]]
            value = ""
        elif component_type in ['NPN_BJT', 'PNP_BJT']:
            # Transistor: Q1 C B E model
            nodes = parts[1:4] if len(parts) >= 4 else parts[1:]
            value = ""
            model = parts[4] if len(parts) > 4 else ""
        elif component_type in ['N_MOSFET', 'P_MOSFET']:
            # MOSFET: M1 D G S model
            nodes = parts[1:4] if len(parts) >= 4 else parts[1:]
            value = ""
            model = parts[4] if len(parts) > 4 else ""
        elif component_type == 'OPAMP':
            # OpAmp: U1 + - Vcc Vee Out
            nodes = parts[1:6] if len(parts) >= 6 else parts[1:]
            value = ""
        else:
            # Standard 2-terminal: R1 N1 N2 value
            nodes = parts[1:3] if len(parts) >= 3 else parts[1:]
            value = parts[3] if len(parts) > 3 else ""
        
        component = NetlistComponent(
            reference=reference,
            component_type=component_type,
            nodes=nodes,
            value=value
        )
        
        self.circuit.components.append(component)
    
    def _get_component_type(self, reference: str) -> str:
        """Map reference designator to component type"""
        # Check for special cases first
        if reference == '0' or reference.upper() == 'GND':
            return 'GND'
        
        # Extract prefix (letters before numbers)
        prefix_match = re.match(r'^([A-Za-z]+)', reference)
        if not prefix_match:
            return 'R'  # Default to resistor
        
        prefix = prefix_match.group(1).upper()
        
        # Direct mapping
        if prefix in self.COMPONENT_MAP:
            return self.COMPONENT_MAP[prefix]
        
        # Fallback: use first letter
        first_letter = prefix[0]
        return self.COMPONENT_MAP.get(first_letter, 'R')
    
    def _build_nets(self):
        """Build net connectivity from components"""
        # Create nets for each unique node
        node_to_net = {}
        
        for component in self.circuit.components:
            for pin_idx, node_name in enumerate(component.nodes):
                # Normalize node name (0 and GND are same)
                if node_name == '0' or node_name.upper() == 'GND':
                    node_name = 'GND'
                
                # Create net if it doesn't exist
                if node_name not in node_to_net:
                    net = NetlistNet(name=node_name, components=[])
                    node_to_net[node_name] = net
                    self.circuit.nets.append(net)
                
                # Add component pin to net
                node_to_net[node_name].components.append((component.reference, pin_idx))
        
        self.circuit.node_map = node_to_net
    
    def print_summary(self):
        """Print circuit summary"""
        print("=" * 60)
        print("NETLIST PARSE SUMMARY")
        print("=" * 60)
        print(f"\nComponents ({len(self.circuit.components)}):")
        for comp in self.circuit.components:
            nodes_str = ', '.join(comp.nodes)
            value_str = f" = {comp.value}" if comp.value else ""
            print(f"  {comp.reference:8s} ({comp.component_type:12s}): {nodes_str}{value_str}")
        
        print(f"\nNets ({len(self.circuit.nets)}):")
        for net in self.circuit.nets:
            connections = [f"{ref}.{pin}" for ref, pin in net.components]
            print(f"  {net.name:8s}: {' -- '.join(connections)}")
        print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 netlist_parser.py <netlist_file>")
        print("\nExample netlist format:")
        print("  * Simple RC Circuit")
        print("  V1 N1 0 5V")
        print("  R1 N1 N2 10k")
        print("  C1 N2 0 100nF")
        print()
        sys.exit(1)
    
    netlist_path = Path(sys.argv[1])
    
    if not netlist_path.exists():
        print(f"Error: Netlist file not found: {netlist_path}")
        sys.exit(1)
    
    parser = NetlistParser()
    circuit = parser.parse_file(netlist_path)
    parser.print_summary()

if __name__ == '__main__':
    main()
