#!/bin/bash
#
# test_component_render.sh - End-to-end component rendering test
#
# Tests the complete pipeline: SVG → relative coords → absolute coords → RM2
# Can run in dry-run mode (no RM2 required) or full mode (requires RM2).
#
# Usage: ./test_component_render.sh [OPTIONS]
#
# Options:
#   --rm2 <ip>           RM2 IP address (enables actual rendering)
#   --dry-run            Test without sending to RM2 (default)
#   --component <name>   Test specific component (default: all)
#   --gallery            Render all components in a grid layout
#   --help               Show this help

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRAW_SCRIPT="$SCRIPT_DIR/draw_component.sh"
COMPONENTS_DIR="$SCRIPT_DIR/../assets/components"

# Defaults
RM2_IP=""
DRY_RUN=true
COMPONENT=""
GALLERY=false

# Help
show_help() {
    echo "test_component_render.sh - End-to-end component rendering test"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --rm2 <ip>           RM2 IP address (enables actual rendering)"
    echo "  --dry-run            Test without sending to RM2 (default)"
    echo "  --component <name>   Test specific component (default: test suite)"
    echo "  --gallery            Render all components in a grid layout"
    echo "  --help               Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                           # Dry run with test suite"
    echo "  $0 --component R             # Dry run single component"
    echo "  $0 --rm2 10.11.99.1          # Full test with RM2"
    echo "  $0 --rm2 10.11.99.1 --gallery # Render component gallery"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --rm2)
            RM2_IP="$2"
            DRY_RUN=false
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            RM2_IP=""
            shift
            ;;
        --component)
            COMPONENT="$2"
            shift 2
            ;;
        --gallery)
            GALLERY=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            exit 1
            ;;
    esac
done

# Validate setup
if [ ! -f "$DRAW_SCRIPT" ]; then
    echo -e "${RED}Error: Draw script not found: $DRAW_SCRIPT${NC}"
    exit 1
fi

if [ ! -d "$COMPONENTS_DIR" ]; then
    echo -e "${RED}Error: Components directory not found: $COMPONENTS_DIR${NC}"
    exit 1
fi

# Header
echo "=========================================="
echo "  Component Rendering Test"
echo "=========================================="
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Mode: Dry Run (no RM2 required)${NC}"
else
    echo -e "${BLUE}Mode: Full Test${NC}"
    echo -e "${BLUE}Target: $RM2_IP${NC}"
fi
echo ""

# Test counters
PASSED=0
FAILED=0

# Gallery mode
if [ "$GALLERY" = true ]; then
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Gallery mode requires --rm2 flag${NC}"
        exit 1
    fi

    echo -e "${MAGENTA}Gallery Mode: Rendering component grid${NC}"
    echo ""

    # Define grid layout (4 columns)
    COL_WIDTH=300
    ROW_HEIGHT=250
    START_X=100
    START_Y=100

    components=(R C L D ZD GND VDC VAC OPAMP NPN_BJT PNP_BJT N_MOSFET P_MOSFET P_CAP SW_OP SW_CL)

    row=0
    col=0

    for comp in "${components[@]}"; do
        svg_file="$COMPONENTS_DIR/${comp}.svg"
        if [ ! -f "$svg_file" ]; then
            continue
        fi

        x=$((START_X + col * COL_WIDTH))
        y=$((START_Y + row * ROW_HEIGHT))

        echo -e "${CYAN}Rendering $comp at ($x, $y)...${NC}"

        "$DRAW_SCRIPT" "$svg_file" --width 200 --x $x --y $y --rm2 "$RM2_IP" 2>&1 | grep -E "(✓|✗|Error)" || true

        col=$((col + 1))
        if [ $col -ge 4 ]; then
            col=0
            row=$((row + 1))
        fi

        sleep 0.5
    done

    echo ""
    echo -e "${GREEN}✓ Gallery rendered!${NC}"
    echo "Check your reMarkable 2 screen"
    exit 0
fi

# Single component test
if [ -n "$COMPONENT" ]; then
    svg_file="$COMPONENTS_DIR/${COMPONENT}.svg"

    if [ ! -f "$svg_file" ]; then
        echo -e "${RED}Error: Component not found: $svg_file${NC}"
        exit 1
    fi

    echo -e "${CYAN}Testing component: $COMPONENT${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo "Running: draw_component.sh --dry-run"
        "$DRAW_SCRIPT" "$svg_file" --scale 100 --x 500 --y 800 --dry-run

        # Check if output file was created
        output_file="${COMPONENT}_absolute.lamp"
        if [ -f "$output_file" ]; then
            echo ""
            echo -e "${GREEN}✓ Test passed!${NC}"
            echo "Output: $output_file"
            cmd_count=$(wc -l < "$output_file")
            echo "Commands: $cmd_count"
            echo ""
            echo "Sample commands:"
            head -10 "$output_file"
            rm "$output_file"
        else
            echo -e "${RED}✗ Test failed: No output file generated${NC}"
            exit 1
        fi
    else
        echo "Running: draw_component.sh --rm2 $RM2_IP"
        "$DRAW_SCRIPT" "$svg_file" --scale 100 --x 500 --y 800 --rm2 "$RM2_IP"
        echo ""
        echo -e "${GREEN}✓ Component rendered on RM2${NC}"
    fi

    exit 0
fi

# Test suite (dry-run mode)
echo -e "${CYAN}Running test suite...${NC}"
echo ""

# Test 1: Basic rendering
echo -e "${BLUE}Test 1: Basic rendering (R.svg)${NC}"
svg_file="$COMPONENTS_DIR/R.svg"
if [ -f "$svg_file" ]; then
    if "$DRAW_SCRIPT" "$svg_file" --scale 100 --dry-run >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "  ${YELLOW}⊘ SKIPPED${NC} (R.svg not found)"
fi

# Test 2: Scaling
echo -e "${BLUE}Test 2: Scaling (scale=200)${NC}"
if [ -f "$svg_file" ]; then
    if "$DRAW_SCRIPT" "$svg_file" --scale 200 --dry-run >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "  ${YELLOW}⊘ SKIPPED${NC}"
fi

# Test 3: Positioning
echo -e "${BLUE}Test 3: Positioning (x=500, y=800)${NC}"
if [ -f "$svg_file" ]; then
    if "$DRAW_SCRIPT" "$svg_file" --x 500 --y 800 --dry-run >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "  ${YELLOW}⊘ SKIPPED${NC}"
fi

# Test 4: Width/Height sizing
echo -e "${BLUE}Test 4: Width/Height sizing (200x200)${NC}"
if [ -f "$svg_file" ]; then
    if "$DRAW_SCRIPT" "$svg_file" --width 200 --height 200 --dry-run >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "  ${YELLOW}⊘ SKIPPED${NC}"
fi

# Test 5: Show pins
echo -e "${BLUE}Test 5: Show pins flag${NC}"
if [ -f "$svg_file" ]; then
    if "$DRAW_SCRIPT" "$svg_file" --show-pins --dry-run >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "  ${YELLOW}⊘ SKIPPED${NC}"
fi

# Test 6: Complex component (OPAMP)
echo -e "${BLUE}Test 6: Complex component (OPAMP.svg)${NC}"
svg_file="$COMPONENTS_DIR/OPAMP.svg"
if [ -f "$svg_file" ]; then
    if "$DRAW_SCRIPT" "$svg_file" --scale 150 --dry-run >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "  ${YELLOW}⊘ SKIPPED${NC} (OPAMP.svg not found)"
fi

# Test 7: All components exist and parse
echo -e "${BLUE}Test 7: All components parse successfully${NC}"
all_passed=true
for svg in "$COMPONENTS_DIR"/*.svg; do
    if [ -f "$svg" ]; then
        comp_name=$(basename "$svg" .svg)
        if ! "$DRAW_SCRIPT" "$svg" --dry-run >/dev/null 2>&1; then
            echo -e "  ${RED}✗ Failed: $comp_name${NC}"
            all_passed=false
        fi
    fi
done

if [ "$all_passed" = true ]; then
    echo -e "  ${GREEN}✓ PASSED${NC} (all components parsed)"
    PASSED=$((PASSED + 1))
else
    echo -e "  ${RED}✗ FAILED${NC} (some components failed)"
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed:${NC} $FAILED"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    if [ "$DRY_RUN" = true ]; then
        echo "To test with actual RM2:"
        echo "  $0 --rm2 10.11.99.1"
        echo ""
        echo "To render component gallery:"
        echo "  $0 --rm2 10.11.99.1 --gallery"
    fi
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
