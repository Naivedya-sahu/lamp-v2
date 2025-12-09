#!/bin/bash
#
# Convert SVG to pen commands and send directly to reMarkable 2
# Uses Python script to parse SVG and pipes commands to lamp
#
# Usage: ./svg_to_rm2.sh <svg_file> [scale] [x] [y] [RM2_IP]
#
# Examples:
#   ./svg_to_rm2.sh examples/svg_symbols/R.svg 10
#   ./svg_to_rm2.sh examples/svg_symbols/OPAMP.svg 20 500 800
#   ./svg_to_rm2.sh examples/svg_symbols/R.svg 5 100 200 10.11.99.1

set -e

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <svg_file> [scale] [x] [y] [RM2_IP]"
    echo ""
    echo "Arguments:"
    echo "  svg_file  - Path to SVG file (required)"
    echo "  scale     - Scale factor (default: auto)"
    echo "  x         - X offset in pixels (default: auto-center)"
    echo "  y         - Y offset in pixels (default: auto-center)"
    echo "  RM2_IP    - reMarkable 2 IP address (default: 10.11.99.1)"
    echo ""
    echo "Examples:"
    echo "  $0 symbol.svg                      # Auto-scale and center"
    echo "  $0 symbol.svg 10                   # Scale 10x, auto-center"
    echo "  $0 symbol.svg 10 500 800           # Scale 10x at (500,800)"
    echo "  $0 symbol.svg 10 500 800 10.11.99.1"
    exit 1
fi

# Parse arguments
SVG_FILE="$1"
SCALE="${2:-}"
OFFSET_X="${3:-}"
OFFSET_Y="${4:-}"
RM2_IP="${5:-10.11.99.1}"
LAMP="/opt/bin/lamp"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "SVG to reMarkable 2 Converter"
echo "=========================================="

# Check if SVG file exists
if [ ! -f "$SVG_FILE" ]; then
    echo -e "${RED}Error: SVG file '$SVG_FILE' not found${NC}"
    exit 1
fi

echo -e "${BLUE}SVG File:${NC} $SVG_FILE"
echo -e "${BLUE}Scale:${NC} ${SCALE:-auto}"
echo -e "${BLUE}Position:${NC} ${OFFSET_X:-auto}, ${OFFSET_Y:-auto}"
echo -e "${BLUE}Target:${NC} $RM2_IP"
echo ""

# Test connection
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh root@$RM2_IP "test -x $LAMP" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to $RM2_IP or lamp not found${NC}"
    echo "Please check:"
    echo "  1. RM2 is connected (USB: 10.11.99.1 or WiFi IP)"
    echo "  2. lamp binary is deployed to $LAMP"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Build Python command with arguments
PY_CMD="python3 svg_to_lamp_improved.py '$SVG_FILE'"
[ -n "$SCALE" ] && PY_CMD="$PY_CMD $SCALE"
[ -n "$OFFSET_X" ] && PY_CMD="$PY_CMD $OFFSET_X"
[ -n "$OFFSET_Y" ] && PY_CMD="$PY_CMD $OFFSET_Y"

# Generate pen commands
echo -e "${BLUE}Converting SVG to pen commands...${NC}"
PEN_COMMANDS=$(eval $PY_CMD 2>&1)

# Check if conversion was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to convert SVG${NC}"
    echo "$PEN_COMMANDS"
    exit 1
fi

# Extract only the pen commands (filter out DEBUG lines)
PEN_COMMANDS=$(echo "$PEN_COMMANDS" | grep -E "^(pen|finger|sleep)" || true)

if [ -z "$PEN_COMMANDS" ]; then
    echo -e "${RED}Error: No pen commands generated${NC}"
    exit 1
fi

# Count commands for user feedback
CMD_COUNT=$(echo "$PEN_COMMANDS" | wc -l)
echo -e "${GREEN}✓ Generated $CMD_COUNT pen commands${NC}"
echo ""

# Show first few commands as preview
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
    echo "Commands sent: $CMD_COUNT"
    echo "Check your reMarkable 2 screen"
else
    echo ""
    echo -e "${RED}✗ Error sending commands${NC}"
    exit 1
fi
