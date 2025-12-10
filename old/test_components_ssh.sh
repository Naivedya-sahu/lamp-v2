#!/bin/bash
#
# Test script: Draw 3 component symbols at bottom right of RM2 screen
# Fallback system using direct lamp commands (no Python dependencies)
#
# Usage: ./test_components_ssh.sh [RM2_IP]
#
# reMarkable 2 screen: 1404x1872 pixels
# Bottom right area: x=900-1300, y=1600-1850

set -e

# Configuration
RM2_IP="${1:-10.11.99.1}"
LAMP_BIN="/opt/bin/lamp"

# Component positions (bottom right area)
RESISTOR_X=900
RESISTOR_Y=1650
RESISTOR_SCALE=2.0

CAPACITOR_X=900
CAPACITOR_Y=1730
CAPACITOR_SCALE=2.0

GROUND_X=1050
GROUND_Y=1650
GROUND_SCALE=1.5

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Component Test: Bottom Right Display"
echo "=========================================="
echo "Target: $RM2_IP"
echo "Position: Bottom right corner"
echo ""

# Test connection
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh root@$RM2_IP "test -x $LAMP_BIN" 2>/dev/null; then
    echo "Error: Cannot connect to RM2 or lamp not found at $LAMP_BIN"
    echo "Please check:"
    echo "  1. RM2 is connected (USB: 10.11.99.1 or WiFi IP)"
    echo "  2. lamp binary is deployed to $LAMP_BIN"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Function to draw resistor (zigzag pattern)
draw_resistor() {
    local base_x=$1
    local base_y=$2
    local scale=$3

    echo -e "${BLUE}Drawing resistor...${NC}"

    # Scale coordinates
    local s=$scale

    # Resistor path: zigzag pattern
    # Original: M 0 20 L 20 20 L 25 10 L 35 30 L 45 10 L 55 30 L 65 10 L 75 30 L 80 20 L 100 20

    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen down $base_x $base_y
pen move $((base_x + $(echo "20 * $s" | bc | cut -d. -f1))) $base_y
pen move $((base_x + $(echo "25 * $s" | bc | cut -d. -f1))) $((base_y - $(echo "10 * $s" | bc | cut -d. -f1)))
pen move $((base_x + $(echo "35 * $s" | bc | cut -d. -f1))) $((base_y + $(echo "10 * $s" | bc | cut -d. -f1)))
pen move $((base_x + $(echo "45 * $s" | bc | cut -d. -f1))) $((base_y - $(echo "10 * $s" | bc | cut -d. -f1)))
pen move $((base_x + $(echo "55 * $s" | bc | cut -d. -f1))) $((base_y + $(echo "10 * $s" | bc | cut -d. -f1)))
pen move $((base_x + $(echo "65 * $s" | bc | cut -d. -f1))) $((base_y - $(echo "10 * $s" | bc | cut -d. -f1)))
pen move $((base_x + $(echo "75 * $s" | bc | cut -d. -f1))) $((base_y + $(echo "10 * $s" | bc | cut -d. -f1)))
pen move $((base_x + $(echo "80 * $s" | bc | cut -d. -f1))) $base_y
pen move $((base_x + $(echo "100 * $s" | bc | cut -d. -f1))) $base_y
pen up
EOF
    echo -e "${GREEN}✓ Resistor drawn${NC}"
}

# Function to draw capacitor (two parallel plates)
draw_capacitor() {
    local base_x=$1
    local base_y=$2
    local scale=$3

    echo -e "${BLUE}Drawing capacitor...${NC}"

    local s=$scale

    # Left lead
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen line $base_x $base_y $((base_x + $(echo "45 * $s" | bc | cut -d. -f1))) $base_y
EOF

    # Left plate (vertical line)
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen line $((base_x + $(echo "45 * $s" | bc | cut -d. -f1))) $((base_y - $(echo "20 * $s" | bc | cut -d. -f1))) $((base_x + $(echo "45 * $s" | bc | cut -d. -f1))) $((base_y + $(echo "20 * $s" | bc | cut -d. -f1)))
EOF

    # Right plate (vertical line)
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen line $((base_x + $(echo "55 * $s" | bc | cut -d. -f1))) $((base_y - $(echo "20 * $s" | bc | cut -d. -f1))) $((base_x + $(echo "55 * $s" | bc | cut -d. -f1))) $((base_y + $(echo "20 * $s" | bc | cut -d. -f1)))
EOF

    # Right lead
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen line $((base_x + $(echo "55 * $s" | bc | cut -d. -f1))) $base_y $((base_x + $(echo "100 * $s" | bc | cut -d. -f1))) $base_y
EOF

    echo -e "${GREEN}✓ Capacitor drawn${NC}"
}

# Function to draw ground symbol
draw_ground() {
    local base_x=$1
    local base_y=$2
    local scale=$3

    echo -e "${BLUE}Drawing ground...${NC}"

    local s=$scale

    # Vertical line down
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen line $base_x $base_y $base_x $((base_y + $(echo "40 * $s" | bc | cut -d. -f1)))
EOF

    # Horizontal lines (getting shorter)
    local y_offset=$(echo "40 * $s" | bc | cut -d. -f1)

    # Line 1 (longest)
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen line $((base_x - $(echo "20 * $s" | bc | cut -d. -f1))) $((base_y + y_offset)) $((base_x + $(echo "20 * $s" | bc | cut -d. -f1))) $((base_y + y_offset))
EOF

    # Line 2
    y_offset=$(echo "50 * $s" | bc | cut -d. -f1)
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen line $((base_x - $(echo "15 * $s" | bc | cut -d. -f1))) $((base_y + y_offset)) $((base_x + $(echo "15 * $s" | bc | cut -d. -f1))) $((base_y + y_offset))
EOF

    # Line 3
    y_offset=$(echo "60 * $s" | bc | cut -d. -f1)
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen line $((base_x - $(echo "10 * $s" | bc | cut -d. -f1))) $((base_y + y_offset)) $((base_x + $(echo "10 * $s" | bc | cut -d. -f1))) $((base_y + y_offset))
EOF

    # Line 4 (shortest)
    y_offset=$(echo "70 * $s" | bc | cut -d. -f1)
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
pen line $((base_x - $(echo "5 * $s" | bc | cut -d. -f1))) $((base_y + y_offset)) $((base_x + $(echo "5 * $s" | bc | cut -d. -f1))) $((base_y + y_offset))
EOF

    echo -e "${GREEN}✓ Ground drawn${NC}"
}

# Function to clear test area
clear_test_area() {
    echo -e "${YELLOW}Clearing test area...${NC}"
    ssh root@$RM2_IP "$LAMP_BIN" << EOF
eraser fill 850 1600 1350 1850 10
EOF
    echo -e "${GREEN}✓ Area cleared${NC}"
}

# Main test sequence
echo "=========================================="
echo "Test 1: Drawing Components"
echo "=========================================="

draw_resistor $RESISTOR_X $RESISTOR_Y $RESISTOR_SCALE
sleep 1

draw_capacitor $CAPACITOR_X $CAPACITOR_Y $CAPACITOR_SCALE
sleep 1

draw_ground $GROUND_X $GROUND_Y $GROUND_SCALE
sleep 1

echo ""
echo -e "${GREEN}✓ All components drawn successfully!${NC}"
echo ""
echo "Check bottom right corner of RM2 screen"
echo "Press Enter to test eraser..."
read

echo ""
echo "=========================================="
echo "Test 2: Eraser Function"
echo "=========================================="

clear_test_area

echo ""
echo -e "${GREEN}✓ All tests complete!${NC}"
echo ""
echo "Summary:"
echo "  - Resistor position: ($RESISTOR_X, $RESISTOR_Y)"
echo "  - Capacitor position: ($CAPACITOR_X, $CAPACITOR_Y)"
echo "  - Ground position: ($GROUND_X, $GROUND_Y)"
echo "  - All components erased successfully"
echo ""
echo "This script works without Python dependencies!"
echo "Use it as fallback if Python tools fail."
