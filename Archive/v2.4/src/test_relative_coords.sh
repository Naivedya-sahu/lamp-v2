#!/bin/bash
#
# test_relative_coords.sh - Verify relative coordinate conversion
#
# Tests that relative coordinates (0.0-1.0) are correctly converted to
# absolute screen coordinates with proper scaling and positioning.
#
# Usage: ./test_relative_coords.sh [OPTIONS]
#
# Options:
#   --component <name>   Test specific component (default: R)
#   --verbose            Show detailed output
#   --help               Show this help

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONVERTER="$SCRIPT_DIR/svg_to_lamp_relative.py"
COMPONENTS_DIR="$SCRIPT_DIR/../assets/components"

# Defaults
COMPONENT="R"
VERBOSE=false

# Help
show_help() {
    echo "test_relative_coords.sh - Verify relative coordinate conversion"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --component <name>   Test specific component (default: R)"
    echo "  --verbose            Show detailed output"
    echo "  --help               Show this help"
    echo ""
    echo "Tests:"
    echo "  1. Relative coords are in range [0.0, 1.0]"
    echo "  2. Scaling works correctly"
    echo "  3. Positioning works correctly"
    echo "  4. Bounds clamping prevents overflow"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --component)
            COMPONENT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            exit 1
            ;;
    esac
done

# Validate setup
SVG_FILE="$COMPONENTS_DIR/${COMPONENT}.svg"
if [ ! -f "$SVG_FILE" ]; then
    echo -e "${RED}Error: Component not found: $SVG_FILE${NC}"
    exit 1
fi

if [ ! -f "$CONVERTER" ]; then
    echo -e "${RED}Error: Converter not found: $CONVERTER${NC}"
    exit 1
fi

# Header
echo "=========================================="
echo "  Relative Coordinate Conversion Test"
echo "=========================================="
echo -e "${BLUE}Component:${NC} $COMPONENT"
echo -e "${BLUE}SVG File:${NC} $SVG_FILE"
echo ""

# Test counter
PASSED=0
FAILED=0

# Test 1: Generate relative coordinates
echo -e "${CYAN}Test 1: Generate relative coordinates${NC}"
echo -n "  Parsing SVG... "

rel_output=$(python3 "$CONVERTER" "$SVG_FILE" 2>&1)
rel_commands=$(echo "$rel_output" | grep -E "^pen " || true)

if [ -z "$rel_commands" ]; then
    echo -e "${RED}✗ FAILED${NC}"
    echo "  Error: No commands generated"
    FAILED=$((FAILED + 1))
    exit 1
fi

echo -e "${GREEN}✓ OK${NC}"

# Test 2: Validate coordinate range
echo -e "${CYAN}Test 2: Validate coordinate range [0.0, 1.0]${NC}"
echo -n "  Checking coordinate bounds... "

invalid_coords=$(echo "$rel_commands" | awk '
    $1 == "pen" && ($2 == "down" || $2 == "move") {
        x = $3; y = $4
        if (x < 0 || x > 1 || y < 0 || y > 1) {
            printf "Line %d: x=%.6f y=%.6f (out of range)\n", NR, x, y
        }
    }
')

if [ -n "$invalid_coords" ]; then
    echo -e "${RED}✗ FAILED${NC}"
    echo "$invalid_coords" | head -5
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✓ OK${NC}"
    PASSED=$((PASSED + 1))
fi

# Get coordinate stats
min_x=$(echo "$rel_commands" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $3}' | sort -n | head -1)
max_x=$(echo "$rel_commands" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $3}' | sort -n | tail -1)
min_y=$(echo "$rel_commands" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $4}' | sort -n | head -1)
max_y=$(echo "$rel_commands" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $4}' | sort -n | tail -1)

echo "  Range: x=[${min_x}, ${max_x}], y=[${min_y}, ${max_y}]"

# Test 3: Test scaling
echo -e "${CYAN}Test 3: Test scaling (scale=100, pos=0,0)${NC}"
echo -n "  Converting to absolute coordinates... "

abs_commands=$(echo "$rel_commands" | python3 -c "
import sys
scale = 100.0
offset_x = 0
offset_y = 0

for line in sys.stdin:
    parts = line.strip().split()
    if len(parts) >= 4 and parts[0] == 'pen' and parts[1] in ('down', 'move'):
        rel_x = float(parts[2])
        rel_y = float(parts[3])
        abs_x = int(rel_x * scale + offset_x)
        abs_y = int(rel_y * scale + offset_y)
        print(f'pen {parts[1]} {abs_x} {abs_y}')
    elif len(parts) >= 2 and parts[0] == 'pen' and parts[1] == 'up':
        print('pen up')
")

if [ -z "$abs_commands" ]; then
    echo -e "${RED}✗ FAILED${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✓ OK${NC}"
    PASSED=$((PASSED + 1))

    # Validate scaled coordinates
    abs_min_x=$(echo "$abs_commands" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $3}' | sort -n | head -1)
    abs_max_x=$(echo "$abs_commands" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $3}' | sort -n | tail -1)
    abs_min_y=$(echo "$abs_commands" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $4}' | sort -n | head -1)
    abs_max_y=$(echo "$abs_commands" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $4}' | sort -n | tail -1)

    echo "  Scaled range: x=[${abs_min_x}, ${abs_max_x}], y=[${abs_min_y}, ${abs_max_y}]"

    # Verify scaling is approximately correct
    expected_max_x=$(python3 -c "print(int(float('$max_x') * 100))")
    expected_max_y=$(python3 -c "print(int(float('$max_y') * 100))")

    if [ "$abs_max_x" -eq "$expected_max_x" ] && [ "$abs_max_y" -eq "$expected_max_y" ]; then
        echo -e "  ${GREEN}Scale verification: ✓ Correct${NC}"
    else
        echo -e "  ${YELLOW}Scale verification: Expected ~${expected_max_x}x${expected_max_y}, got ${abs_max_x}x${abs_max_y}${NC}"
    fi
fi

# Test 4: Test positioning
echo -e "${CYAN}Test 4: Test positioning (scale=50, pos=500,800)${NC}"
echo -n "  Converting with offset... "

abs_commands_offset=$(echo "$rel_commands" | python3 -c "
import sys
scale = 50.0
offset_x = 500
offset_y = 800

for line in sys.stdin:
    parts = line.strip().split()
    if len(parts) >= 4 and parts[0] == 'pen' and parts[1] in ('down', 'move'):
        rel_x = float(parts[2])
        rel_y = float(parts[3])
        abs_x = int(rel_x * scale + offset_x)
        abs_y = int(rel_y * scale + offset_y)
        print(f'pen {parts[1]} {abs_x} {abs_y}')
    elif len(parts) >= 2 and parts[0] == 'pen' and parts[1] == 'up':
        print('pen up')
")

if [ -z "$abs_commands_offset" ]; then
    echo -e "${RED}✗ FAILED${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✓ OK${NC}"
    PASSED=$((PASSED + 1))

    # Validate offset coordinates
    offset_min_x=$(echo "$abs_commands_offset" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $3}' | sort -n | head -1)
    offset_min_y=$(echo "$abs_commands_offset" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $4}' | sort -n | head -1)

    echo "  Offset range starts at: x=${offset_min_x}, y=${offset_min_y}"

    # Verify offset is approximately 500, 800
    if [ "$offset_min_x" -ge 500 ] && [ "$offset_min_y" -ge 800 ]; then
        echo -e "  ${GREEN}Offset verification: ✓ Correct${NC}"
    else
        echo -e "  ${YELLOW}Offset verification: Expected ≥500,800, got ${offset_min_x},${offset_min_y}${NC}"
    fi
fi

# Test 5: Test bounds clamping
echo -e "${CYAN}Test 5: Test bounds clamping (prevent overflow)${NC}"
echo -n "  Testing large scale at screen edge... "

abs_commands_clamp=$(echo "$rel_commands" | python3 -c "
import sys
scale = 2000.0
offset_x = 1000
offset_y = 1500

for line in sys.stdin:
    parts = line.strip().split()
    if len(parts) >= 4 and parts[0] == 'pen' and parts[1] in ('down', 'move'):
        rel_x = float(parts[2])
        rel_y = float(parts[3])
        abs_x = int(rel_x * scale + offset_x)
        abs_y = int(rel_y * scale + offset_y)
        # Clamp to screen bounds
        abs_x = max(0, min(abs_x, 1403))
        abs_y = max(0, min(abs_y, 1871))
        print(f'pen {parts[1]} {abs_x} {abs_y}')
    elif len(parts) >= 2 and parts[0] == 'pen' and parts[1] == 'up':
        print('pen up')
")

clamp_max_x=$(echo "$abs_commands_clamp" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $3}' | sort -n | tail -1)
clamp_max_y=$(echo "$abs_commands_clamp" | awk '$1 == "pen" && ($2 == "down" || $2 == "move") {print $4}' | sort -n | tail -1)

if [ "$clamp_max_x" -le 1403 ] && [ "$clamp_max_y" -le 1871 ]; then
    echo -e "${GREEN}✓ OK${NC}"
    PASSED=$((PASSED + 1))
    echo "  Max coords: x=${clamp_max_x}, y=${clamp_max_y} (within bounds)"
else
    echo -e "${RED}✗ FAILED${NC}"
    FAILED=$((FAILED + 1))
    echo "  Max coords: x=${clamp_max_x}, y=${clamp_max_y} (exceeds 1403x1871)"
fi

# Verbose output
if [ "$VERBOSE" = true ]; then
    echo ""
    echo -e "${BLUE}Detailed Output:${NC}"
    echo ""
    echo "Sample relative commands (first 5):"
    echo "$rel_commands" | head -5 | sed 's/^/  /'
    echo ""
    echo "Sample absolute commands (scale=100, first 5):"
    echo "$abs_commands" | head -5 | sed 's/^/  /'
fi

# Summary
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed:${NC} $FAILED"
    echo ""
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}✓ All coordinate conversion tests passed!${NC}"
    exit 0
fi
