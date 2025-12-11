#!/bin/bash
#
# Send component from JSON library to reMarkable 2
# Extracts pen commands from component_library.json and sends to lamp
#
# Usage: ./send_component.sh <component_name> [scale] [x] [y] [RM2_IP]
#
# Examples:
#   ./send_component.sh R                    # Auto-scale and center
#   ./send_component.sh NPN_BJT 2 500 800   # Scale 2x at (500,800)
#   ./send_component.sh OPAMP 1.5            # Scale 1.5x, auto-center

set -e

# Check arguments
if [ $# -lt 1 ]; then
    cat << 'EOF'
Usage: ./send_component.sh <component_name> [scale] [x] [y] [RM2_IP]

Arguments:
  component_name - Component name from library (required)
  scale          - Scale factor (default: 1.0)
  x              - X offset in pixels (default: from library anchor)
  y              - Y offset in pixels (default: from library anchor)
  RM2_IP         - reMarkable 2 IP address (default: 10.11.99.1)

Examples:
  ./send_component.sh R                    # Draw resistor at library position
  ./send_component.sh NPN_BJT 2            # Scale BJT 2x
  ./send_component.sh OPAMP 1.5 500 800   # Scale 1.5x at (500,800)
  ./send_component.sh VDC 1 0 0 10.11.99.1

Available components in library:
  R, C, L, D, VDC, VAC, GND, NPN_BJT, PNP_BJT, 
  N_MOSFET, P_MOSFET, OPAMP, P_CAP, ZD, SW_CL, SW_OP

Note: Requires component_library.json in current directory
EOF
    exit 1
fi

# Parse arguments
COMPONENT="$1"
SCALE="${2:-1.0}"
OFFSET_X="${3:-}"
OFFSET_Y="${4:-}"
RM2_IP="${5:-10.11.99.1}"
LAMP="/opt/bin/lamp"
LIBRARY="component_library.json"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Component to reMarkable 2"
echo "=========================================="

# Check if library exists
if [ ! -f "$LIBRARY" ]; then
    echo -e "${RED}Error: Component library '$LIBRARY' not found${NC}"
    echo "Please run: python3 component_library_builder.py ../components"
    exit 1
fi

echo -e "${BLUE}Component:${NC} $COMPONENT"
echo -e "${BLUE}Scale:${NC} $SCALE"
echo -e "${BLUE}Position:${NC} ${OFFSET_X:-auto}, ${OFFSET_Y:-auto}"
echo -e "${BLUE}Target:${NC} $RM2_IP"
echo ""

# Test connection
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh root@$RM2_IP "test -x $LAMP" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to $RM2_IP or lamp not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Extract component from JSON using Python
echo -e "${BLUE}Extracting component from library...${NC}"
PEN_COMMANDS=$(python3 << EOF
import json
import sys
import re

# Read library
with open("$LIBRARY", "r") as f:
    library = json.load(f)

# Check if component exists
if "$COMPONENT" not in library:
    print(f"Error: Component '$COMPONENT' not found in library", file=sys.stderr)
    print(f"Available components: {', '.join(library.keys())}", file=sys.stderr)
    sys.exit(1)

comp = library["$COMPONENT"]

# Get bounds and calculate anchor point (center of bounding box)
bounds = comp.get("bounds", [0, 0, 100, 100])
anchor_x = (bounds[0] + bounds[2]) / 2
anchor_y = (bounds[1] + bounds[3]) / 2

# Parse scale and offsets
scale = float("$SCALE")
offset_x = anchor_x if "$OFFSET_X" == "" else int("$OFFSET_X")
offset_y = anchor_y if "$OFFSET_Y" == "" else int("$OFFSET_Y")

# Transform pen commands
commands = []
for cmd_str in comp.get("pen_commands", []):
    # Parse command string: "pen down 100 200" -> ["pen", "down", "100", "200"]
    parts = cmd_str.strip().split()
    
    if len(parts) < 2:
        continue
    
    tool = parts[0]  # "pen"
    action = parts[1]  # "down", "move", "up", "line", etc.
    
    if action == "up":
        commands.append(cmd_str)
    elif action in ["down", "move"] and len(parts) >= 4:
        x = int((int(parts[2]) - anchor_x) * scale + offset_x)
        y = int((int(parts[3]) - anchor_y) * scale + offset_y)
        commands.append(f"{tool} {action} {x} {y}")
    elif action == "line" and len(parts) >= 6:
        x1 = int((int(parts[2]) - anchor_x) * scale + offset_x)
        y1 = int((int(parts[3]) - anchor_y) * scale + offset_y)
        x2 = int((int(parts[4]) - anchor_x) * scale + offset_x)
        y2 = int((int(parts[5]) - anchor_y) * scale + offset_y)
        commands.append(f"{tool} {action} {x1} {y1} {x2} {y2}")
    elif action == "rectangle" and len(parts) >= 6:
        x1 = int((int(parts[2]) - anchor_x) * scale + offset_x)
        y1 = int((int(parts[3]) - anchor_y) * scale + offset_y)
        x2 = int((int(parts[4]) - anchor_x) * scale + offset_x)
        y2 = int((int(parts[5]) - anchor_y) * scale + offset_y)
        commands.append(f"{tool} {action} {x1} {y1} {x2} {y2}")
    elif action == "circle" and len(parts) >= 5:
        cx = int((int(parts[2]) - anchor_x) * scale + offset_x)
        cy = int((int(parts[3]) - anchor_y) * scale + offset_y)
        r = int(int(parts[4]) * scale)
        commands.append(f"{tool} {action} {cx} {cy} {r}")
    else:
        # Pass through unknown commands unchanged
        commands.append(cmd_str)

# Output commands
for cmd in commands:
    print(cmd)

# Print info to stderr
print(f"Extracted {len(commands)} commands", file=sys.stderr)
print(f"Position: ({offset_x}, {offset_y}), Scale: {scale}x", file=sys.stderr)
EOF
)

# Check if extraction was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to extract component${NC}"
    echo "$PEN_COMMANDS"
    exit 1
fi

# Get command count
CMD_COUNT=$(echo "$PEN_COMMANDS" | wc -l)
echo -e "${GREEN}✓ Extracted $CMD_COUNT commands${NC}"
echo ""

# Show preview
echo -e "${YELLOW}Preview (first 5 commands):${NC}"
echo "$PEN_COMMANDS" | head -5
echo "..."
echo ""

# Send to reMarkable 2
echo -e "${BLUE}Sending to reMarkable 2...${NC}"
echo "$PEN_COMMANDS" | ssh root@$RM2_IP "$LAMP"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Drawing complete!${NC}"
    echo ""
    echo "Component: $COMPONENT"
    echo "Commands sent: $CMD_COUNT"
    echo "Check your reMarkable 2 screen"
else
    echo ""
    echo -e "${RED}✗ Error sending commands${NC}"
    exit 1
fi
