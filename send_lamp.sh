#!/bin/bash
#
# Send raw pen commands to lamp on reMarkable 2
# Uses SVG path data to draw symbols
#
# Usage: ./send_lamp.sh [RM2_IP]
#
# reMarkable 2 screen: 1404x1872 pixels

set -e

# Configuration
RM2_IP="${1:-10.11.99.1}"
LAMP="/opt/bin/lamp"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "SVG Path to Pen Commands"
echo "=========================================="
echo "Target: $RM2_IP"
echo ""

# Test connection
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh root@$RM2_IP "test -x $LAMP" 2>/dev/null; then
    echo "Error: Cannot connect to $RM2_IP or lamp not found"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Function to send raw pen commands
send_pen_commands() {
    local pen_cmds="$1"
    ssh root@$RM2_IP "$LAMP" << 'EOF'
pen down 544 796
pen move 439 796
pen up
pen down 492 1128
pen move 492 1023
pen up
pen down 544 1076
pen move 439 1076
pen up
pen down 317 796
pen move 387 796
pen up
pen down 317 1076
pen move 387 1076
pen up
pen down 387 656
pen move 387 1216
pen move 947 936
pen move 387 656
pen up
pen down 947 936
pen move 1017 936
pen up
pen down 667 796
pen move 667 586
pen up
pen down 667 1076
pen move 667 1286
pen up
EOF
}

echo -e "${BLUE}Drawing R symbol...${NC}"

send_pen_commands

echo -e "${GREEN}✓ R symbol drawn${NC}"