#!/bin/bash
#
# test_svg_parser.sh - Test SVG parsing for all components
#
# Tests the svg_to_lamp_relative.py converter on all component SVG files.
# Validates that each component can be parsed and generates valid commands.
#
# Usage: ./test_svg_parser.sh [OPTIONS]
#
# Options:
#   --component <name>   Test specific component (e.g., R, C, OPAMP)
#   --show-pins          Include pin circles in parsing
#   --verbose            Show full command output
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
COMPONENT=""
SHOW_PINS=false
VERBOSE=false

# Help
show_help() {
    echo "test_svg_parser.sh - Test SVG parsing for all components"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --component <name>   Test specific component (e.g., R, C, OPAMP)"
    echo "  --show-pins          Include pin circles in parsing"
    echo "  --verbose            Show full command output"
    echo "  --help               Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                          # Test all components"
    echo "  $0 --component R            # Test only R.svg"
    echo "  $0 --show-pins --verbose    # Test all with pins, verbose output"
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
        --show-pins)
            SHOW_PINS=true
            shift
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
if [ ! -f "$CONVERTER" ]; then
    echo -e "${RED}Error: Converter not found: $CONVERTER${NC}"
    exit 1
fi

if [ ! -d "$COMPONENTS_DIR" ]; then
    echo -e "${RED}Error: Components directory not found: $COMPONENTS_DIR${NC}"
    exit 1
fi

# Header
echo "=========================================="
echo "  SVG Parser Test"
echo "=========================================="
echo -e "${BLUE}Converter:${NC} $CONVERTER"
echo -e "${BLUE}Components:${NC} $COMPONENTS_DIR"
echo -e "${BLUE}Show Pins:${NC} $SHOW_PINS"
echo -e "${BLUE}Verbose:${NC} $VERBOSE"
echo ""

# Build converter options
CONV_OPTS="--tolerance 1.0"
if [ "$SHOW_PINS" = true ]; then
    CONV_OPTS="$CONV_OPTS --show-pins"
fi

# Get list of components to test
if [ -n "$COMPONENT" ]; then
    SVG_FILES=("$COMPONENTS_DIR/${COMPONENT}.svg")
    if [ ! -f "${SVG_FILES[0]}" ]; then
        echo -e "${RED}Error: Component not found: ${COMPONENT}.svg${NC}"
        exit 1
    fi
else
    SVG_FILES=("$COMPONENTS_DIR"/*.svg)
fi

# Test counters
TOTAL=0
PASSED=0
FAILED=0

# Test each component
for svg_file in "${SVG_FILES[@]}"; do
    # Skip if it's a directory or doesn't exist
    if [ ! -f "$svg_file" ]; then
        continue
    fi

    component_name=$(basename "$svg_file" .svg)
    TOTAL=$((TOTAL + 1))

    echo -ne "${BLUE}Testing $component_name...${NC} "

    # Run converter
    output=$(python3 "$CONVERTER" "$svg_file" $CONV_OPTS 2>&1)
    exit_code=$?

    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
        if [ "$VERBOSE" = true ]; then
            echo "$output" | head -20
        else
            echo "  Error: Converter failed (use --verbose for details)"
        fi
        continue
    fi

    # Extract commands and statistics
    commands=$(echo "$output" | grep -E "^pen " || true)
    cmd_count=$(echo "$commands" | wc -l)
    stats=$(echo "$output" | grep "^#" || true)

    if [ -z "$commands" ]; then
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
        echo "  Error: No pen commands generated"
        continue
    fi

    # Validate command format
    invalid_cmds=$(echo "$commands" | grep -Ev "^pen (down|move|up)" || true)
    if [ -n "$invalid_cmds" ]; then
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
        echo "  Error: Invalid command format"
        if [ "$VERBOSE" = true ]; then
            echo "$invalid_cmds" | head -5
        fi
        continue
    fi

    # Validate coordinate ranges (should be 0.0-1.0 for relative)
    invalid_coords=$(echo "$commands" | grep -E "pen (down|move)" | awk '{
        if ($3 < 0 || $3 > 1 || $4 < 0 || $4 > 1) {
            print "Invalid coords: " $0
        }
    }')

    if [ -n "$invalid_coords" ]; then
        echo -e "${YELLOW}⚠ WARNING${NC}"
        PASSED=$((PASSED + 1))
        echo "  Coordinates outside [0.0, 1.0] range"
        if [ "$VERBOSE" = true ]; then
            echo "$invalid_coords" | head -5
        fi
    else
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    fi

    # Show details if verbose
    if [ "$VERBOSE" = true ]; then
        echo "$stats" | sed 's/^#/  /'
        echo "  Commands: $cmd_count"
        echo "  First 3 commands:"
        echo "$commands" | head -3 | sed 's/^/    /'
        echo ""
    else
        # Show compact summary
        bounds=$(echo "$stats" | grep "Bounds:" | sed 's/^# //')
        size=$(echo "$stats" | grep "Size:" | sed 's/^# //')
        echo "  $bounds | $size | $cmd_count cmds"
    fi
done

# Summary
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo -e "${BLUE}Total:${NC} $TOTAL"
echo -e "${GREEN}Passed:${NC} $PASSED"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed:${NC} $FAILED"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
