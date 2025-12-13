#!/usr/bin/env python3
"""
Convert SPICE netlist (.net) to JSON format

Supports standard SPICE netlist format used in ECE circuits.
"""

import sys
import re
from pathlib import Path
import json
from collections import defaultdict

class NetlistParser:
    """Parse SPICE netlist format"""

    COMPONENT_MAP = {
        'R': 'R',
        'C': 'C',
        'L': 'L',
        'D': 'D',
        'V': 'VDC',
        'I': 'IDC',
        'Q': 'NPN_BJT',
        'M': 'N_MOSFET',
        'U': 'OPAMP',
        'ZD': 'ZD',
    }

    def __init__(self):
        self.components = []
        self.nets = defaultdict(list)

    def parse_file(self, netlist_path: Path) -> dict:
        """Parse netlist file"""
        with open(netlist_path) as f:
            content = f.read()

        return self.parse_text(content)

    def parse_text(self, text: str) -> dict:
        """Parse netlist text"""
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()

            # Skip comments and directives
            if not line or line.startswith('*') or line.startswith('.'):
                continue

            self._parse_component_line(line)

        # Build nets
        self._build_nets()

        return {
            'components': self.components,
            'nets': list(self.nets.values())
        }

    def _parse_component_line(self, line: str):
        """Parse component line: REF N1 N2 [N3 ...] [VALUE]"""
        parts = line.split()
        if len(parts) < 2:
            return

        reference = parts[0]
        component_type = self._get_component_type(reference)

        # Parse based on component type
        if component_type == 'GND':
            nodes = [parts[1]]
            value = ''
        elif component_type in ['NPN_BJT', 'PNP_BJT', 'N_MOSFET', 'P_MOSFET']:
            # 3-terminal device: REF D G S [model]
            nodes = parts[1:4] if len(parts) >= 4 else parts[1:]
            value = parts[4] if len(parts) > 4 else ''
        elif component_type == 'OPAMP':
            # 5-terminal: REF IN+ IN- VCC VEE OUT
            nodes = parts[1:6] if len(parts) >= 6 else parts[1:]
            value = ''
        else:
            # 2-terminal device: REF N1 N2 [VALUE]
            nodes = parts[1:3] if len(parts) >= 3 else parts[1:]
            value = parts[3] if len(parts) > 3 else ''

        component = {
            'reference': reference,
            'component_type': component_type,
            'nodes': nodes,
            'value': value
        }

        self.components.append(component)

    def _get_component_type(self, reference: str) -> str:
        """Map reference to component type"""
        if reference == '0' or reference.upper() == 'GND':
            return 'GND'

        # Extract prefix
        prefix_match = re.match(r'^([A-Za-z]+)', reference)
        if not prefix_match:
            return 'R'

        prefix = prefix_match.group(1).upper()

        # Check component map
        if prefix in self.COMPONENT_MAP:
            return self.COMPONENT_MAP[prefix]

        # Fallback to first letter
        first_letter = prefix[0]
        return self.COMPONENT_MAP.get(first_letter, 'R')

    def _build_nets(self):
        """Build net connectivity"""
        node_to_net = {}

        for comp in self.components:
            for pin_idx, node_name in enumerate(comp['nodes']):
                # Normalize node names
                if node_name == '0' or node_name.upper() == 'GND':
                    node_name = 'GND'

                # Create net if doesn't exist
                if node_name not in node_to_net:
                    net = {
                        'name': node_name,
                        'pins': []
                    }
                    node_to_net[node_name] = net
                    self.nets[node_name] = net

                # Add pin to net
                # For 2-pin components: pin1=node[0], pin2=node[1]
                # For 3-pin: pin1,2,3=nodes[0,1,2]
                pin_id = str(pin_idx + 1)
                node_to_net[node_name]['pins'].append([comp['reference'], pin_id])


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 netlist_to_json.py <netlist.net>", file=sys.stderr)
        print("\nExample netlist:", file=sys.stderr)
        print("  * RC Filter", file=sys.stderr)
        print("  V1 IN 0 5V", file=sys.stderr)
        print("  R1 IN OUT 10k", file=sys.stderr)
        print("  C1 OUT 0 100nF", file=sys.stderr)
        sys.exit(1)

    netlist_path = Path(sys.argv[1])

    if not netlist_path.exists():
        print(f"Error: File not found: {netlist_path}", file=sys.stderr)
        sys.exit(1)

    parser = NetlistParser()
    result = parser.parse_file(netlist_path)

    print(f"Parsed {len(result['components'])} components, {len(result['nets'])} nets", file=sys.stderr)

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
