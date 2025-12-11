#!/bin/bash
#
# List all components in the component library
# Shows component names, sizes, and anchor points
#
# Usage: ./list_components.sh

set -e

LIBRARY="component_library.json"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Component Library Contents"
echo "=========================================="

# Check if library exists
if [ ! -f "$LIBRARY" ]; then
    echo -e "${RED}Error: Component library '$LIBRARY' not found${NC}"
    echo "Please run: python3 component_library_builder.py ../components"
    exit 1
fi

# Parse and display library contents
python3 << 'EOF'
import json

with open("component_library.json", "r") as f:
    library = json.load(f)

print(f"\nTotal components: {len(library)}\n")
print(f"{'Component':<15} | {'Width':>6} | {'Height':>6} | {'Commands':>8} | {'Bounds':<25} | {'Pins'}")
print("-" * 100)

for name, comp in sorted(library.items()):
    width = comp.get("width", 0)
    height = comp.get("height", 0)
    num_cmds = len(comp.get("pen_commands", []))
    
    # Format bounds
    bounds = comp.get("bounds", [0, 0, 0, 0])
    bounds_str = f"({bounds[0]:.0f},{bounds[1]:.0f}) to ({bounds[2]:.0f},{bounds[3]:.0f})"
    
    pins = len(comp.get("pins", []))
    
    print(f"{name:<15} | {width:>6.0f} | {height:>6.0f} | {num_cmds:>8} | {bounds_str:<25} | {pins}")

print()
EOF

echo "=========================================="
echo -e "${CYAN}Usage:${NC}"
echo "  ./send_component.sh <name> [scale] [x] [y]"
echo ""
echo -e "${CYAN}Examples:${NC}"
echo "  ./send_component.sh R              # Draw resistor"
echo "  ./send_component.sh NPN_BJT 2      # Draw BJT scaled 2x"
echo "  ./send_component.sh OPAMP 1.5 500 800"
echo "=========================================="
