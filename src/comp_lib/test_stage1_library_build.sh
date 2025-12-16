#!/bin/bash
# test_stage1_library_build.sh - Validate library build process locally

set -e

echo "=========================================="
echo "Stage 1: Library Build Validation"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Test 1: Check for required files
echo "Test 1: Check Required Files"
if [ ! -f "svg_to_lamp.sh" ]; then
    echo "✗ svg_to_lamp.sh not found"
    exit 1
fi
if [ ! -f "build_component_library.py" ]; then
    echo "✗ build_component_library.py not found"
    exit 1
fi
echo "✓ All required files present"
echo ""

# Test 2: Check for assets directories
echo "Test 2: Check Assets Directories"
ASSETS_COMPONENTS="../../assets/components"
ASSETS_FONT="../../assets/font"

if [ ! -d "$ASSETS_COMPONENTS" ]; then
    echo "✗ Components directory not found: $ASSETS_COMPONENTS"
    exit 1
fi
if [ ! -d "$ASSETS_FONT" ]; then
    echo "✗ Font directory not found: $ASSETS_FONT"
    exit 1
fi

COMP_COUNT=$(ls -1 "$ASSETS_COMPONENTS"/*.svg 2>/dev/null | wc -l)
FONT_COUNT=$(ls -1 "$ASSETS_FONT"/*.svg 2>/dev/null | wc -l)

echo "✓ Assets directories found"
echo "  Components: $COMP_COUNT SVG files"
echo "  Fonts: $FONT_COUNT SVG files"
echo ""

# Test 3: Test SVG converter on single file
echo "Test 3: SVG Converter (Single File)"
TEST_SVG="$ASSETS_COMPONENTS/R.svg"
if [ -f "$TEST_SVG" ]; then
    chmod +x svg_to_lamp.sh
    ./svg_to_lamp.sh "$TEST_SVG" 10 500 800 > /tmp/test_R.txt 2>&1
    
    if [ -s /tmp/test_R.txt ]; then
        lines=$(wc -l < /tmp/test_R.txt)
        echo "✓ SVG converter works"
        echo "  Generated $lines commands"
        echo "  Preview:"
        head -3 /tmp/test_R.txt | sed 's/^/    /'
    else
        echo "✗ SVG converter failed"
        cat /tmp/test_R.txt
        exit 1
    fi
else
    echo "✗ Test SVG not found: $TEST_SVG"
    exit 1
fi
echo ""

# Test 4: Build library
echo "Test 4: Library Builder"
chmod +x build_component_library.py
python3 build_component_library.py \
    "$ASSETS_COMPONENTS" \
    "$ASSETS_FONT" \
    /tmp/test_library.json

if [ -f /tmp/test_library.json ]; then
    echo "✓ Library builder works"
    
    # Validate JSON
    if command -v jq >/dev/null 2>&1; then
        comp_count=$(jq -r '.stats.component_count' /tmp/test_library.json)
        glyph_count=$(jq -r '.stats.glyph_count' /tmp/test_library.json)
        total=$(jq -r '.stats.total_entries' /tmp/test_library.json)
        echo "  Components: $comp_count"
        echo "  Glyphs: $glyph_count"
        echo "  Total: $total"
    else
        echo "  (Install jq for detailed stats)"
    fi
    
    file_size=$(du -h /tmp/test_library.json | cut -f1)
    echo "  File size: $file_size"
else
    echo "✗ Library builder failed"
    exit 1
fi
echo ""

# Test 5: JSON validity
echo "Test 5: JSON Validity"
if command -v jq >/dev/null 2>&1; then
    if jq empty /tmp/test_library.json 2>/dev/null; then
        echo "✓ JSON is valid"
    else
        echo "✗ JSON is invalid"
        exit 1
    fi
else
    if python3 -m json.tool /tmp/test_library.json >/dev/null 2>&1; then
        echo "✓ JSON is valid (checked with Python)"
    else
        echo "✗ JSON is invalid"
        exit 1
    fi
fi
echo ""

echo "=========================================="
echo "Stage 1: PASSED ✓"
echo "=========================================="
echo ""
echo "Library built successfully at: /tmp/test_library.json"
echo "Ready for Stage 2: Connectivity Test"
