#!/bin/bash
#
# SVG Gallery viewer for reMarkable 2
# Automatically cycles through SVG files, displays each one, then erases
#
# Usage: ./svg_gallery.sh [directory] [scale] [RM2_IP] [delay]
#
# Examples:
#   ./svg_gallery.sh                                    # Use default ./examples/svg_symbols
#   ./svg_gallery.sh ./examples/svg_symbols/Digital    # Use Digital subfolder
#   ./svg_gallery.sh ./examples/svg_symbols 10         # Use scale 10x
#   ss  # 3 second delay

# Configuration
SVG_DIR="${1:-.examples/svg_symbols}"
SCALE="${2:-}"
RM2_IP="${3:-10.11.99.1}"
DELAY="${4:-2}"  # Default 2 second delay between symbols
LAMP="/opt/bin/lamp"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse help flag
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    cat << 'EOF'
SVG Gallery - reMarkable 2 Automatic Viewer

Usage: ./svg_gallery.sh [directory] [scale] [RM2_IP] [delay]

Arguments:
  directory   Path to SVG folder (default: ./examples/svg_symbols)
  scale       Scale factor (default: auto-scale)
  RM2_IP      reMarkable 2 IP address (default: 10.11.99.1)
  delay       Delay in seconds between symbols (default: 2)

Examples:
  ./svg_gallery.sh                                    # Auto-scale, 2s delay
  ./svg_gallery.sh ./examples/svg_symbols/Digital    # Digital gates, 2s delay
  ./svg_gallery.sh ./examples/svg_symbols 10         # Scale 10x, 2s delay
  ./svg_gallery.sh ./examples/svg_symbols 5 10.11.99.1 5  # 5x scale, 5s delay

How it works:
  - Automatically finds all SVG files in directory (alphabetically sorted)
  - Converts each SVG to pen commands
  - Sends to RM2 and waits for it to complete drawing
  - Waits specified delay seconds
  - Erases the screen
  - Moves to next SVG
  - Repeats until all SVGs shown

EOF
    exit 0
fi

# Check if directory exists
if [ ! -d "$SVG_DIR" ]; then
    echo -e "${RED}Error: Directory '$SVG_DIR' not found${NC}"
    exit 1
fi

# Count SVG files
SVG_COUNT=$(find "$SVG_DIR" -name "*.svg" -type f | wc -l)
if [ "$SVG_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: No SVG files found in '$SVG_DIR'${NC}"
    exit 1
fi

echo "=========================================="
echo "SVG Gallery - reMarkable 2 Auto Viewer"
echo "=========================================="
echo -e "${BLUE}Directory:${NC} $SVG_DIR"
echo -e "${BLUE}Found SVGs:${NC} $SVG_COUNT files"
echo -e "${BLUE}Scale:${NC} ${SCALE:-auto}"
echo -e "${BLUE}Delay:${NC} ${DELAY}s per symbol"
echo -e "${BLUE}Target:${NC} $RM2_IP"
echo ""

# Test SSH connection
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

# Function to draw SVG
draw_svg() {
    local svg_file="$1"
    local index="$2"
    local total="$3"
    
    # Get filename without path
    local filename=$(basename "$svg_file")
    
    echo -ne "${CYAN}[$index/$total]${NC} ${YELLOW}$filename${NC} ... "
    
    # Build Python command
    local py_cmd="python3 svg_to_lamp_improved.py '$svg_file'"
    [ -n "$SCALE" ] && py_cmd="$py_cmd $SCALE"
    
    # Generate pen commands
    local pen_commands=$(eval $py_cmd 2>&1)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to convert${NC}"
        return 1
    fi
    
    # Extract bounds from the first line if present
    LAST_BOUNDS=$(echo "$pen_commands" | grep -m1 "^# BOUNDS" | sed 's/^# BOUNDS //')
    
    # Extract only pen commands (skip comments)
    pen_commands=$(echo "$pen_commands" | grep -E "^(pen|finger|sleep|DRAWING)" || true)
    
    if [ -z "$pen_commands" ]; then
        echo -e "${RED}✗ No pen commands generated${NC}"
        return 1
    fi
    
    # Count commands
    local cmd_count=$(echo "$pen_commands" | wc -l)
    
    # Send to RM2
    echo "$pen_commands" | ssh root@$RM2_IP "$LAMP" 2>/dev/null
    local ssh_result=$?
    
    if [ $ssh_result -eq 0 ]; then
        echo -e "${GREEN}✓ ($cmd_count commands)${NC}"
        return 0
    else
        echo -e "${RED}✗ Send failed${NC}"
        return 1
    fi
}

# Function to erase screen
erase_screen() {
    # Use the bounds from the last drawn SVG if available
    if [ -n "$LAST_BOUNDS" ]; then
        echo "eraser fill $LAST_BOUNDS 8" | ssh root@$RM2_IP "$LAMP" 2>/dev/null || true
    else
        # Fallback: just send finger up (does nothing, but safe)
        echo "finger up" | ssh root@$RM2_IP "$LAMP" 2>/dev/null || true
    fi
}

# Get sorted list of SVG files
mapfile -t svg_files < <(find "$SVG_DIR" -name "*.svg" -type f | sort)

# Gallery loop - automatically cycle through all SVGs
total=${#svg_files[@]}
current=0

echo "Starting automatic gallery (press Ctrl+C to stop)..."
echo ""

while [ $current -lt $total ]; do
    svg_file="${svg_files[$current]}"
    index=$((current + 1))
    
    # Draw the SVG
    if draw_svg "$svg_file" "$index" "$total"; then
        # Wait for specified delay
        echo -e "${BLUE}Waiting ${DELAY}s...${NC}"
        sleep "$DELAY"
        
        # Erase the screen
        echo -ne "${BLUE}Erasing...${NC} "
        erase_screen
        echo -e "${GREEN}✓${NC}"
        echo ""
    fi
    
    current=$((current + 1))
done

echo "=========================================="
echo -e "${GREEN}✓ Gallery complete! All $total symbols displayed.${NC}"
echo "=========================================="
