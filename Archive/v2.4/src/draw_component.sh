#!/bin/bash
#
# draw_component.sh - Send SVG component to reMarkable 2
#
# Converts SVG to relative coordinates, scales to absolute position, and renders on RM2.
#
# Usage: ./draw_component.sh <svg_file> [OPTIONS]
#
# Options:
#   --scale <factor>     Scale factor (default: 1.0)
#   --x <pos>            X position in pixels (default: 0)
#   --y <pos>            Y position in pixels (default: 0)
#   --width <px>         Width in pixels (overrides scale)
#   --height <px>        Height in pixels (overrides scale)
#   --show-pins          Show pin circles for testing
#   --tolerance <val>    Simplification tolerance (default: 1.0)
#   --rm2 <ip>           RM2 IP address (default: 10.11.99.1)
#   --dry-run            Generate commands without sending
#   --help               Show this help
#
# Examples:
#   ./draw_component.sh assets/components/R.svg
#   ./draw_component.sh assets/components/R.svg --scale 100 --x 500 --y 800
#   ./draw_component.sh assets/components/OPAMP.svg --width 200 --height 200 --x 600 --y 400
#   ./draw_component.sh assets/components/C.svg --show-pins --dry-run

set -e

# Default values
SCALE=1.0
POS_X=0
POS_Y=0
WIDTH=""
HEIGHT=""
SHOW_PINS=false
TOLERANCE=1.0
RM2_IP="10.11.99.1"
LAMP_BIN="/opt/bin/lamp"
DRY_RUN=false
SVG_FILE=""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONVERTER="$SCRIPT_DIR/svg_to_lamp_relative.py"

# Help function
show_help() {
    echo "draw_component.sh - Send SVG component to reMarkable 2"
    echo ""
    echo "Usage: $0 <svg_file> [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --scale <factor>     Scale factor (default: 1.0)"
    echo "  --x <pos>            X position in pixels (default: 0)"
    echo "  --y <pos>            Y position in pixels (default: 0)"
    echo "  --width <px>         Width in pixels (overrides scale)"
    echo "  --height <px>        Height in pixels (overrides scale)"
    echo "  --show-pins          Show pin circles for testing"
    echo "  --tolerance <val>    Simplification tolerance (default: 1.0)"
    echo "  --rm2 <ip>           RM2 IP address (default: 10.11.99.1)"
    echo "  --dry-run            Generate commands without sending"
    echo "  --help               Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 R.svg --scale 100 --x 500 --y 800"
    echo "  $0 OPAMP.svg --width 200 --height 200 --x 600 --y 400"
    echo "  $0 C.svg --show-pins --dry-run"
    echo ""
    echo "reMarkable 2 screen: 1404 x 1872 pixels"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --scale)
            SCALE="$2"
            shift 2
            ;;
        --x)
            POS_X="$2"
            shift 2
            ;;
        --y)
            POS_Y="$2"
            shift 2
            ;;
        --width)
            WIDTH="$2"
            shift 2
            ;;
        --height)
            HEIGHT="$2"
            shift 2
            ;;
        --show-pins)
            SHOW_PINS=true
            shift
            ;;
        --tolerance)
            TOLERANCE="$2"
            shift 2
            ;;
        --rm2)
            RM2_IP="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            if [ -z "$SVG_FILE" ]; then
                SVG_FILE="$1"
            else
                echo -e "${RED}Error: Multiple SVG files specified${NC}"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [ -z "$SVG_FILE" ]; then
    echo -e "${RED}Error: No SVG file specified${NC}"
    echo "Use --help for usage information"
    exit 1
fi

# Check if SVG file exists
if [ ! -f "$SVG_FILE" ]; then
    echo -e "${RED}Error: SVG file not found: $SVG_FILE${NC}"
    exit 1
fi

# Check if converter exists
if [ ! -f "$CONVERTER" ]; then
    echo -e "${RED}Error: Converter not found: $CONVERTER${NC}"
    exit 1
fi

# Header
echo "=========================================="
echo "  Draw Component - reMarkable 2"
echo "=========================================="
echo -e "${BLUE}SVG File:${NC} $SVG_FILE"
echo -e "${BLUE}Position:${NC} ($POS_X, $POS_Y)"
if [ -n "$WIDTH" ] || [ -n "$HEIGHT" ]; then
    echo -e "${BLUE}Size:${NC} ${WIDTH:-auto} x ${HEIGHT:-auto} pixels"
else
    echo -e "${BLUE}Scale:${NC} $SCALE"
fi
echo -e "${BLUE}Show Pins:${NC} $SHOW_PINS"
echo -e "${BLUE}Tolerance:${NC} $TOLERANCE"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Mode:${NC} Dry run (no sending)"
else
    echo -e "${BLUE}Target:${NC} $RM2_IP"
fi
echo ""

# Test SSH connection (skip for dry run)
if [ "$DRY_RUN" = false ]; then
    echo -e "${BLUE}Testing SSH connection...${NC}"
    if ! ssh -o ConnectTimeout=3 root@$RM2_IP "test -x $LAMP_BIN" 2>/dev/null; then
        echo -e "${RED}Error: Cannot connect to $RM2_IP or lamp not found${NC}"
        echo "Please check:"
        echo "  1. RM2 is connected (USB: 10.11.99.1 or WiFi IP)"
        echo "  2. lamp binary is deployed to $LAMP_BIN"
        exit 1
    fi
    echo -e "${GREEN}✓ Connected${NC}"
    echo ""
fi

# Build converter command
CONV_CMD="python3 '$CONVERTER' '$SVG_FILE' --tolerance $TOLERANCE"
if [ "$SHOW_PINS" = true ]; then
    CONV_CMD="$CONV_CMD --show-pins"
fi

# Generate relative coordinates
echo -e "${BLUE}Converting SVG to relative coordinates...${NC}"
RELATIVE_CMDS=$(eval $CONV_CMD)

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to convert SVG${NC}"
    echo "$RELATIVE_CMDS"
    exit 1
fi

# Extract only pen commands
RELATIVE_CMDS=$(echo "$RELATIVE_CMDS" | grep -E "^pen " || true)

if [ -z "$RELATIVE_CMDS" ]; then
    echo -e "${RED}Error: No pen commands generated${NC}"
    exit 1
fi

# Count commands
CMD_COUNT=$(echo "$RELATIVE_CMDS" | wc -l)
echo -e "${GREEN}✓ Generated $CMD_COUNT relative pen commands${NC}"
echo ""

# Calculate scaling
# If width/height specified, calculate scale from SVG dimensions
if [ -n "$WIDTH" ] || [ -n "$HEIGHT" ]; then
    echo -e "${BLUE}Calculating scale from dimensions...${NC}"

    # Extract SVG viewBox to get original dimensions
    SVG_WIDTH=$(python3 -c "
import xml.etree.ElementTree as ET
import sys
tree = ET.parse('$SVG_FILE')
root = tree.getroot()
vb = root.get('viewBox', root.get('width', '100'))
if ' ' in vb:
    parts = vb.split()
    print(float(parts[2]) - float(parts[0]))
else:
    print(float(root.get('width', '100').replace('px', '')))
" 2>/dev/null || echo "100")

    SVG_HEIGHT=$(python3 -c "
import xml.etree.ElementTree as ET
import sys
tree = ET.parse('$SVG_FILE')
root = tree.getroot()
vb = root.get('viewBox', root.get('height', '100'))
if ' ' in vb:
    parts = vb.split()
    print(float(parts[3]) - float(parts[1]))
else:
    print(float(root.get('height', '100').replace('px', '')))
" 2>/dev/null || echo "100")

    # Calculate scale to match requested dimensions
    if [ -n "$WIDTH" ]; then
        SCALE_X=$(python3 -c "print($WIDTH / $SVG_WIDTH)")
    else
        SCALE_X=$SCALE
    fi

    if [ -n "$HEIGHT" ]; then
        SCALE_Y=$(python3 -c "print($HEIGHT / $SVG_HEIGHT)")
    else
        SCALE_Y=$SCALE
    fi

    # Use minimum scale to maintain aspect ratio
    SCALE=$(python3 -c "print(min($SCALE_X, $SCALE_Y))")

    # Calculate actual rendered size
    ACTUAL_WIDTH=$(python3 -c "print(int($SVG_WIDTH * $SCALE))")
    ACTUAL_HEIGHT=$(python3 -c "print(int($SVG_HEIGHT * $SCALE))")

    echo -e "${GREEN}✓ Scale: $SCALE (renders as ${ACTUAL_WIDTH}x${ACTUAL_HEIGHT} px)${NC}"
    echo ""
fi

# Convert relative coordinates to absolute
echo -e "${BLUE}Converting to absolute coordinates...${NC}"
ABSOLUTE_CMDS=$(echo "$RELATIVE_CMDS" | python3 -c "
import sys

scale = float('$SCALE')
offset_x = int('$POS_X')
offset_y = int('$POS_Y')

# Read SVG bounds to calculate actual dimensions
svg_width = float('${SVG_WIDTH:-100}')
svg_height = float('${SVG_HEIGHT:-100}')

# Calculate pixel dimensions
width_px = svg_width * scale
height_px = svg_height * scale

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    parts = line.split()
    if len(parts) < 2:
        continue

    if parts[0] == 'pen' and parts[1] in ('down', 'move'):
        if len(parts) >= 4:
            rel_x = float(parts[2])
            rel_y = float(parts[3])

            # Convert relative to absolute
            abs_x = int(rel_x * width_px + offset_x)
            abs_y = int(rel_y * height_px + offset_y)

            # Clamp to screen bounds
            abs_x = max(0, min(abs_x, 1403))
            abs_y = max(0, min(abs_y, 1871))

            print(f'pen {parts[1]} {abs_x} {abs_y}')
    elif parts[0] == 'pen' and parts[1] == 'up':
        print('pen up')
")

if [ -z "$ABSOLUTE_CMDS" ]; then
    echo -e "${RED}Error: Failed to convert to absolute coordinates${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Converted to absolute coordinates${NC}"
echo ""

# Show preview
echo -e "${YELLOW}Preview (first 10 commands):${NC}"
echo "$ABSOLUTE_CMDS" | head -10
if [ $CMD_COUNT -gt 10 ]; then
    echo "..."
    echo -e "${CYAN}(${CMD_COUNT} total commands)${NC}"
fi
echo ""

# Send to RM2 or save to file
if [ "$DRY_RUN" = true ]; then
    OUTPUT_FILE="${SVG_FILE%.svg}_absolute.lamp"
    echo "$ABSOLUTE_CMDS" > "$OUTPUT_FILE"
    echo -e "${GREEN}✓ Commands saved to: $OUTPUT_FILE${NC}"
    echo ""
    echo "To send manually:"
    echo "  cat $OUTPUT_FILE | ssh root@$RM2_IP $LAMP_BIN"
else
    echo -e "${BLUE}Sending to reMarkable 2...${NC}"
    echo "$ABSOLUTE_CMDS" | ssh root@$RM2_IP "$LAMP_BIN"

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
fi
