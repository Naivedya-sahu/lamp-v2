#!/bin/bash
# test_stage1_library.sh - Library Build Validation
# Tests SVG converter and library builder

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/../build"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Stage 1: Library Build Validation"
echo "=========================================="
echo ""

# Test 1: Check required files exist
echo -e "${BLUE}Test 1: Required Files${NC}"
required_files=(
    "$BUILD_DIR/svg_to_lamp.sh"
    "$BUILD_DIR/build_library.py"
    "$PROJECT_ROOT/assets/components"
    "$PROJECT_ROOT/assets/font"
)

all_exist=true
for file in "${required_files[@]}"; do
    if [ -e "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
        all_exist=false
    fi
done

if [ "$all_exist" = false ]; then
    echo -e "${RED}ERROR: Required files missing${NC}"
    exit 1
fi
echo ""

# Test 2: SVG converter works
echo -e "${BLUE}Test 2: SVG Converter${NC}"
test_svg="$PROJECT_ROOT/assets/components/R.svg"

if [ ! -f "$test_svg" ]; then
    echo -e "${RED}✗ Test SVG not found: $test_svg${NC}"
    exit 1
fi

bash "$BUILD_DIR/svg_to_lamp.sh" "$test_svg" 10 500 800 > /tmp/test_R.txt 2>&1

if [ -s /tmp/test_R.txt ]; then
    lines=$(wc -l < /tmp/test_R.txt)
    echo -e "${GREEN}✓ SVG converter works${NC}"
    echo "  Generated $lines commands"
    echo "  Sample:"
    head -3 /tmp/test_R.txt | sed 's/^/    /'
else
    echo -e "${RED}✗ SVG converter failed${NC}"
    cat /tmp/test_R.txt
    exit 1
fi
echo ""

# Test 3: Library builder works
echo -e "${BLUE}Test 3: Library Builder${NC}"
python3 "$BUILD_DIR/build_library.py" \
    "$PROJECT_ROOT/assets/components" \
    "$PROJECT_ROOT/assets/font" \
    /tmp/test_library.json

if [ -f /tmp/test_library.json ]; then
    echo -e "${GREEN}✓ Library builder works${NC}"
    
    if command -v jq >/dev/null 2>&1; then
        comp_count=$(jq -r '.stats.component_count' /tmp/test_library.json)
        glyph_count=$(jq -r '.stats.glyph_count' /tmp/test_library.json)
        total=$(jq -r '.stats.total_entries' /tmp/test_library.json)
        echo "  Components: $comp_count"
        echo "  Glyphs: $glyph_count"
        echo "  Total: $total"
    else
        echo "  (Install jq for detailed stats)"
        ls -lh /tmp/test_library.json
    fi
else
    echo -e "${RED}✗ Library builder failed${NC}"
    exit 1
fi
echo ""

# Test 4: JSON validity
echo -e "${BLUE}Test 4: JSON Validity${NC}"
if command -v jq >/dev/null 2>&1; then
    if jq empty /tmp/test_library.json 2>/dev/null; then
        echo -e "${GREEN}✓ JSON is valid${NC}"
    else
        echo -e "${RED}✗ JSON is invalid${NC}"
        jq . /tmp/test_library.json 2>&1 | head -20
        exit 1
    fi
else
    if python3 -m json.tool /tmp/test_library.json >/dev/null 2>&1; then
        echo -e "${GREEN}✓ JSON is valid (via python)${NC}"
    else
        echo -e "${RED}✗ JSON is invalid${NC}"
        python3 -m json.tool /tmp/test_library.json 2>&1 | head -20
        exit 1
    fi
fi
echo ""

echo "=========================================="
echo -e "${GREEN}Stage 1: PASSED${NC}"
echo "=========================================="
echo ""
echo "Next step: ./test_stage2_connectivity.sh [RM2_IP]"
