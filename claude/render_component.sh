#!/bin/bash
#
# Centralized Component Renderer
# Renders all components with standardized, centered output on RM2
# Fixes issues with off-center rendering and size inconsistency
#
# Usage: ./render_component.sh <component> [RM2_IP]
#

set -e

COMPONENT="${1}"
RM2_IP="${2:-10.11.99.1}"
LAMP="/opt/bin/lamp"

# Use fixed components or fall back to originals
if [ -d "components_fixed" ] && [ -f "components_fixed/${COMPONENT}.svg" ]; then
    COMPONENTS_DIR="components_fixed"
    FIXED_VERSION=true
else
    COMPONENTS_DIR="components"
    FIXED_VERSION=false
fi

# STANDARDIZED SCALES - Tested for centered, uniform rendering
# These produce consistent visual sizes on RM2 screen
declare -A STANDARD_SCALES=(
    # Passive components (horizontal, ~80-90px width)
    ["R"]="8"           # Resistor
    ["C"]="10"          # Capacitor (non-polarized)
    ["L"]="8"           # Inductor
    ["P_CAP"]="10"      # Polarized Capacitor
    
    # Diodes (horizontal, ~80px width)
    ["D"]="10"          # Standard Diode
    ["ZD"]="10"         # Zener Diode
    
    # Active components (larger, ~120px)
    ["OPAMP"]="10"      # Op-Amp
    
    # Power/Ground symbols (vertical, ~60-80px)
    ["GND"]="8"         # Ground
    ["VDC"]="8"         # DC Voltage Source
    ["VAC"]="8"         # AC Voltage Source
)

# Component descriptions
declare -A COMPONENT_DESC=(
    ["R"]="Resistor"
    ["C"]="Capacitor (NP)"
    ["L"]="Inductor"
    ["P_CAP"]="Capacitor (Polarized)"
    ["D"]="Diode"
    ["ZD"]="Zener Diode"
    ["OPAMP"]="Op-Amp"
    ["GND"]="Ground"
    ["VDC"]="DC Source"
    ["VAC"]="AC Source"
)

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Help
if [ "$COMPONENT" = "-h" ] || [ "$COMPONENT" = "--help" ] || [ -z "$COMPONENT" ]; then
    cat << 'HELP'
Centralized Component Renderer

Renders electronic components with standardized, centered positioning.
Fixes off-center rendering and size inconsistency issues.

Usage: ./render_component.sh <component> [RM2_IP]

Available Components:
  R       - Resistor
  C       - Capacitor (non-polarized)
  L       - Inductor
  P_CAP   - Polarized Capacitor
  D       - Diode
  ZD      - Zener Diode
  OPAMP   - Operational Amplifier
  GND     - Ground symbol
  VDC     - DC Voltage Source
  VAC     - AC Voltage Source

Standardized Scales:
  - All components render at visually consistent sizes
  - Proper centering on RM2 screen (1404x1872px)
  - VDC/VAC are now uniform size
  - Diodes and Op-Amps properly centered

Examples:
  ./render_component.sh R              # Render resistor
  ./render_component.sh OPAMP          # Render op-amp
  ./render_component.sh VDC 10.11.99.1 # Render DC source

HELP
    exit 0
fi

# Verify component exists
SVG_FILE="${COMPONENTS_DIR}/${COMPONENT}.svg"
if [ ! -f "$SVG_FILE" ]; then
    echo -e "${RED}Error: Component '${COMPONENT}' not found${NC}"
    echo "Expected: $SVG_FILE"
    echo ""
    echo "Available components:"
    ls -1 "$COMPONENTS_DIR"/*.svg 2>/dev/null | xargs -n1 basename | sed 's/.svg$//' | sort
    exit 1
fi

SCALE="${STANDARD_SCALES[$COMPONENT]}"
if [ -z "$SCALE" ]; then
    echo -e "${YELLOW}Warning: No standard scale for '${COMPONENT}', using 8x${NC}"
    SCALE="8"
fi

DESC="${COMPONENT_DESC[$COMPONENT]}"
[ -z "$DESC" ] && DESC="Component"

echo "=========================================="
echo "Centralized Component Renderer"
echo "=========================================="
echo -e "${CYAN}Component:${NC} $DESC ($COMPONENT)"
echo -e "${CYAN}File:${NC} $SVG_FILE"
if [ "$FIXED_VERSION" = true ]; then
    echo -e "${CYAN}Version:${NC} ${GREEN}Fixed (centered)${NC}"
else
    echo -e "${CYAN}Version:${NC} ${YELLOW}Original${NC}"
fi
echo -e "${CYAN}Scale:${NC} ${SCALE}x (standardized)"
echo -e "${CYAN}Target:${NC} $RM2_IP"
echo ""

# Test connection
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
BOUNDS=$(echo "$PEN_COMMANDS" | grep -m1 "^# BOUNDS" | sed 's/^# BOUNDS //' || true)
PEN_COMMANDS=$(echo "$PEN_COMMANDS" | grep -E "^(pen|finger)" || true)

if [ -z "$PEN_COMMANDS" ]; then
    echo -e "${RED}Error: No pen commands generated${NC}"
    exit 1
fi

CMD_COUNT=$(echo "$PEN_COMMANDS" | wc -l)
echo -e "${GREEN}✓ Generated $CMD_COUNT commands${NC}"
echo ""

# Send to RM2
echo -e "${BLUE}Rendering on RM2...${NC}"
echo "$PEN_COMMANDS" | ssh root@$RM2_IP "$LAMP" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Component rendered successfully${NC}"
    
    # Show erase command
    if [ -n "$BOUNDS" ]; then
        echo ""
        echo -e "${CYAN}To erase:${NC}"
        echo "  echo \"eraser fill $BOUNDS 8\" | ssh root@$RM2_IP \"$LAMP\""
    fi
else
    echo -e "${RED}✗ Rendering failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Rendering complete${NC}"
echo "=========================================="
