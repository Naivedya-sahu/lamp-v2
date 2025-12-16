#!/bin/bash
#
# svg_to_lamp.sh - Universal SVG to lamp command converter
# Converts any SVG (component or font glyph) to lamp pen commands
#
# Usage: ./svg_to_lamp.sh <svg_file> [scale] [x] [y] [tolerance]
#

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <svg_file> [scale] [x] [y] [tolerance]"
    echo ""
    echo "Arguments:"
    echo "  svg_file   - Path to SVG file (required)"
    echo "  scale      - Scale factor (default: auto)"
    echo "  x          - X offset in pixels (default: auto-center)"
    echo "  y          - Y offset in pixels (default: auto-center)"
    echo "  tolerance  - Simplification tolerance (default: 1.0)"
    echo ""
    echo "Output: lamp pen commands to stdout"
    echo ""
    echo "Examples:"
    echo "  $0 R.svg                         # Auto-scale and center"
    echo "  $0 R.svg 10 500 800              # Scale 10x at (500,800)"
    echo "  $0 'segoe path_A.svg' 5 100 200  # Font glyph"
    exit 1
fi

SVG_FILE="$1"
SCALE="${2:-}"
OFFSET_X="${3:-}"
OFFSET_Y="${4:-}"
TOLERANCE="${5:-1.0}"

# Check if SVG file exists
if [ ! -f "$SVG_FILE" ]; then
    echo "Error: SVG file '$SVG_FILE' not found" >&2
    exit 1
fi

# Find the Python script (look in parent directories)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT=""

# Check multiple locations
for location in \
    "$SCRIPT_DIR/svg_to_lamp_smartv2.py" \
    "$SCRIPT_DIR/../svg_to_lamp_smartv2.py" \
    "$SCRIPT_DIR/../../svg_to_lamp_smartv2.py" \
    "$(dirname "$SCRIPT_DIR")/svg_to_lamp_smartv2.py"
do
    if [ -f "$location" ]; then
        PY_SCRIPT="$location"
        break
    fi
done

if [ -z "$PY_SCRIPT" ]; then
    echo "Error: svg_to_lamp_smartv2.py not found" >&2
    echo "Searched in:" >&2
    echo "  $SCRIPT_DIR" >&2
    echo "  Parent directories" >&2
    exit 1
fi

# Build command with arguments
CMD="python3 '$PY_SCRIPT' '$SVG_FILE'"
[ -n "$SCALE" ] && CMD="$CMD $SCALE"
[ -n "$OFFSET_X" ] && CMD="$CMD $OFFSET_X"
[ -n "$OFFSET_Y" ] && CMD="$CMD $OFFSET_Y"
CMD="$CMD $TOLERANCE"

# Execute and filter out comments
eval $CMD 2>/dev/null | grep -E "^(pen|finger|sleep|eraser)" || {
    echo "Error: Failed to convert SVG" >&2
    exit 1
}
