#!/usr/bin/env python3
"""
Netlist Parser - Simplified 2-Pin Component Format
Parses simple netlists: COMP_TYPE REF NODE1 NODE2 [VALUE]
Example: R R1 N1 N2 10k
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Component:
    """Component instance from netlist"""
    reference: str      # R1, C2, V1
    comp_type: str      # R, C, VDC
    node1: str          # First node
    node2: str          # Second node
    value: str = ""     # 10k, 100nF, 5V

@dataclass
class Net:
    """Electrical connection between nodes"""
    name: str
    pins: List[tuple]  # [(ref, pin_num), ...]

@dataclass
class Circuit:
    """Complete circuit definition"""
    components: List[Component] = field(default_factory=list)
    nets: Dict[str, Net] = field(default_factory=dict)


class NetlistParser:
    """Parse simplified netlist format"""
    
    # Component type mapping
    COMP_TYPE_MAP = {
        'R': 'R',
        'C': 'C',
        'L': 'L',
        'D': 'D',
        'ZD': 'ZD',
        'V': 'VDC',
        'VAC': 'VAC',
        'VDC': 'VDC',
        'P_CAP': 'P_CAP',
        'GND': 'GND'
    }
    
    def __init__(self):
        self.circuit = Circuit()
    
    def parse_file(self, netlist_path: Path) -> Circuit:
        """Parse netlist file"""
        with open(netlist_path, 'r') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('*') or line.startswith('.'):
                continue
            
            # Parse component line
            try:
                self._parse_line(line)
            except Exception as e:
                print(f"Warning: Line {line_num}: {e}")
        
        # Build nets
        self._build_nets()
        
        return self.circuit
    
    def _parse_line(self, line: str):
        """
        Parse line format: COMP_TYPE REF NODE1 NODE2 [VALUE]
        Examples:
          R R1 N1 N2 10k
          C C1 N2 GND 100nF
          VDC V1 VIN GND 5V
        """
        parts = line.split()
        
        if len(parts) < 4:
            raise ValueError(f"Invalid format: {line}")
        
        comp_type = parts[0].upper()
        reference = parts[1]
        node1 = parts[2]
        node2 = parts[3]
        value = parts[4] if len(parts) > 4 else ""
        
        # Map component type
        mapped_type = self.COMP_TYPE_MAP.get(comp_type, comp_type)
        
        # Normalize ground nodes
        if node1 in ['0', 'gnd', 'GND']:
            node1 = 'GND'
        if node2 in ['0', 'gnd', 'GND']:
            node2 = 'GND'
        
        component = Component(
            reference=reference,
            comp_type=mapped_type,
            node1=node1,
            node2=node2,
            value=value
        )
        
        self.circuit.components.append(component)
    
    def _build_nets(self):
        """Build net connectivity from components"""
        for comp in self.circuit.components:
            # Add pin1 to node1 net
            if comp.node1 not in self.circuit.nets:
                self.circuit.nets[comp.node1] = Net(name=comp.node1, pins=[])
            self.circuit.nets[comp.node1].pins.append((comp.reference, 1))
            
            # Add pin2 to node2 net
            if comp.node2 not in self.circuit.nets:
                self.circuit.nets[comp.node2] = Net(name=comp.node2, pins=[])
            self.circuit.nets[comp.node2].pins.append((comp.reference, 2))
    
    def print_summary(self):
        """Print circuit summary"""
        print("=" * 60)
        print("NETLIST SUMMARY")
        print("=" * 60)
        print(f"\nComponents ({len(self.circuit.components)}):")
        for comp in self.circuit.components:
            value_str = f" = {comp.value}" if comp.value else ""
            print(f"  {comp.reference:8s} ({comp.comp_type:10s}): {comp.node1} -- {comp.node2}{value_str}")
        
        print(f"\nNets ({len(self.circuit.nets)}):")
        for net_name, net in self.circuit.nets.items():
            connections = [f"{ref}.{pin}" for ref, pin in net.pins]
            print(f"  {net_name:10s}: {' -- '.join(connections)}")
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 netlist_parser.py <netlist_file>")
        print("\nNetlist format: COMP_TYPE REF NODE1 NODE2 [VALUE]")
        print("Example:")
        print("  * RC Filter")
        print("  VDC V1 VIN GND 5V")
        print("  R R1 VIN VOUT 10k")
        print("  C C1 VOUT GND 100nF")
        sys.exit(1)
    
    netlist_path = Path(sys.argv[1])
    
    if not netlist_path.exists():
        print(f"ERROR: File not found: {netlist_path}")
        sys.exit(1)
    
    parser = NetlistParser()
    circuit = parser.parse_file(netlist_path)
    parser.print_summary()


if __name__ == '__main__':
    main()
