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
    pen down 1133 1479
    pen move 1133 1591
    pen up
    pen down 1133 1647
    pen move 1133 1759
    pen up
    pen down 1245 1591
    pen move 1021 1591
    pen up
    pen down 1245 1647
    pen move 1021 1647
    pen up
EOF
}

echo -e "${BLUE}Drawing R symbol...${NC}"

send_pen_commands

echo -e "${GREEN}✓ R symbol drawn${NC}"