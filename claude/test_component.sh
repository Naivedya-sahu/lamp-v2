#!/bin/bash
#
# Component Testing Script - Send scaled component to RM2
# Uses web-researched optimal scales for electronic schematic symbols
#
# Usage: ./test_component.sh <component_name> [RM2_IP]
#
# Examples:
#   ./test_component.sh R
#   ./test_component.sh OPAMP 10.11.99.1
#

set -e

# Configuration
COMPONENT="${1}"
RM2_IP="${2:-10.11.99.1}"
LAMP="/opt/bin/lamp"
COMPONENTS_DIR="./components"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Optimal scales based on IEEE 315 and practical RM2 usage
# Scales chosen to produce symbols ~60-120px for typical schematics
declare -A OPTIMAL_SCALES=(
    ["R"]="6"           # 140*0.64 = 90px width
    ["C"]="11"          # 100*1.10 = 110px width  
    ["L"]="6"           # 140*0.64 = 90px width
    ["D"]="6"           # 140*0.57 = 80px width
    ["ZD"]="6"          # Similar to D
    ["P_CAP"]="9"       # Polarized cap, similar to C
    ["OPAMP"]="8"       # 150*0.80 = 120px
    ["GND"]="6"         # 100*0.60 = 60px
    ["VDC"]="4"         # 100*0.40 = 40px (too tall otherwise)
    ["VAC"]="6"         # Similar to VDC but usually bigger
)

# Display descriptions
declare -A COMPONENT_DESC=(
    ["R"]="Resistor (2-terminal passive)"
    ["C"]="Capacitor (non-polarized)"
    ["L"]="Inductor (2-terminal passive)"
    ["D"]="Diode"
    ["ZD"]="Zener Diode"
    ["P_CAP"]="Polarized Capacitor"
    ["OPAMP"]="Operational Amplifier"
    ["GND"]="Ground Symbol"
    ["VDC"]="DC Voltage Source"
    ["VAC"]="AC Voltage Source"
)

# Help
if [ "$COMPONENT" = "-h" ] || [ "$COMPONENT" = "--help" ] || [ -z "$COMPONENT" ]; then
    cat << 'HELP'
Component Tester - Send optimally-scaled components to RM2

Usage: ./test_component.sh <component_name> [RM2_IP]

Available Components:
  R       - Resistor (90px)
  C       - Capacitor (110px)
  L       - Inductor (90px)
  D       - Diode (80px)
  ZD      - Zener Diode (80px)
  P_CAP   - Polarized Capacitor (90px)
  OPAMP   - Op-Amp (120px)
  GND     - Ground (60px)
  VDC     - DC Source (60px)
  VAC     - AC Source (90px)

Scales are based on IEEE 315 standards for tablet schematic drawing.
Target sizes optimized for reMarkable 2's 1404x1872 display.

Examples:
  ./test_component.sh R              # Test resistor with optimal scale
  ./test_component.sh OPAMP          # Test op-amp
  ./test_component.sh D 10.11.99.1   # Test diode on specific IP

HELP
    exit 0
fi

# Check component exists
SVG_FILE="${COMPONENTS_DIR}/${COMPONENT}.svg"
if [ ! -f "$SVG_FILE" ]; then
    echo -e "${RED}Error: Component '$COMPONENT' not found${NC}"
    echo "Expected file: $SVG_FILE"
    echo ""
    echo "Available components:"
    ls -1 "$COMPONENTS_DIR"/*.svg 2>/dev/null | xargs -n1 basename | sed 's/.svg$//' | sed 's/^/  /'
    exit 1
fi

# Get optimal scale
SCALE="${OPTIMAL_SCALES[$COMPONENT]}"
if [ -z "$SCALE" ]; then
    echo -e "${YELLOW}Warning: No optimal scale defined for '$COMPONENT', using default${NC}"
    SCALE="8"
fi

DESC="${COMPONENT_DESC[$COMPONENT]}"
[ -z "$DESC" ] && DESC="Unknown component"

echo "=========================================="
echo "Component Test - $COMPONENT"
echo "=========================================="
echo -e "${CYAN}Component:${NC} $DESC"
echo -e "${CYAN}File:${NC} $SVG_FILE"
echo -e "${CYAN}Scale:${NC} ${SCALE}x (IEEE 315 optimized)"
echo -e "${CYAN}Target:${NC} $RM2_IP"
echo ""

# Test SSH
echo -e "${BLUE}Testing connection...${NC}"
if ! ssh root@$RM2_IP "test -x $LAMP" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to $RM2_IP${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Convert SVG
echo -e "${BLUE}Converting SVG...${NC}"
PEN_COMMANDS=$(python3 svg_to_lamp_smart.py "$SVG_FILE" "$SCALE" 2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Conversion failed${NC}"
    echo "$PEN_COMMANDS"
    exit 1
fi

# Extract bounds and commands
BOUNDS=$(echo "$PEN_COMMANDS" | grep -m1 "^# BOUNDS" | sed 's/^# BOUNDS //')
PEN_COMMANDS=$(echo "$PEN_COMMANDS" | grep -E "^(pen|finger)" || true)

if [ -z "$PEN_COMMANDS" ]; then
    echo -e "${RED}Error: No pen commands generated${NC}"
    exit 1
fi

CMD_COUNT=$(echo "$PEN_COMMANDS" | wc -l)
echo -e "${GREEN}✓ Generated $CMD_COUNT commands${NC}"
echo ""

# Send to RM2
echo -e "${BLUE}Drawing on RM2...${NC}"
echo "$PEN_COMMANDS" | ssh root@$RM2_IP "$LAMP" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Component drawn successfully${NC}"
    echo ""
    
    # Store bounds for erasing
    if [ -n "$BOUNDS" ]; then
        echo "# To erase: echo \"eraser fill $BOUNDS 8\" | ssh root@$RM2_IP \"$LAMP\""
    fi
else
    echo -e "${RED}✗ Drawing failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Test complete for $COMPONENT${NC}"
echo "=========================================="
