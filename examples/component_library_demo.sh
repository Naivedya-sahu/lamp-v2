#!/bin/bash
#
# Component Library Demo Script
# Demonstrates the custom electrical component library system
#

set -e

echo "=========================================="
echo "ELECTRICAL COMPONENT LIBRARY DEMO"
echo "=========================================="
echo ""

# Paths
LIBRARY="examples/svg_symbols/Electrical_symbols_library.svg"
CONFIG="component_library_config.json"
EXPORT_DIR="exported_symbols"

# 1. Initialize the library
echo "Step 1: Initializing component library..."
python3 component_library.py --library "$LIBRARY" --config "$CONFIG" init
echo ""

# 2. List all symbols
echo "Step 2: Listing all available symbols..."
python3 component_library.py --library "$LIBRARY" --config "$CONFIG" list | head -20
echo "... (showing first 20 symbols)"
echo ""

# 3. Configure some symbols for cycling
echo "Step 3: Configuring symbols for different visibility modes..."
echo "  - Setting g1087 to 'cycled' (resistor)"
python3 component_library.py --library "$LIBRARY" --config "$CONFIG" set g1087 cycled

echo "  - Setting g1092 to 'cycled' (capacitor)"
python3 component_library.py --library "$LIBRARY" --config "$CONFIG" set g1092 cycled

echo "  - Setting g1058 to 'cycled' (inductor)"
python3 component_library.py --library "$LIBRARY" --config "$CONFIG" set g1058 cycled

echo "  - Setting g6082 to 'hidden'"
python3 component_library.py --library "$LIBRARY" --config "$CONFIG" set g6082 hidden
echo ""

# 4. List cycled symbols
echo "Step 4: Showing symbols marked for cycling..."
python3 component_library.py --library "$LIBRARY" --config "$CONFIG" list --visibility cycled
echo ""

# 5. Export cycled symbols
echo "Step 5: Exporting cycled symbols to individual SVG files..."
python3 component_library.py --library "$LIBRARY" --config "$CONFIG" export \
    --visibility cycled --output "$EXPORT_DIR"
echo ""

# 6. Show what was exported
echo "Step 6: Exported files:"
ls -lh "$EXPORT_DIR/" 2>/dev/null || echo "  (no files exported yet)"
echo ""

# 7. Demo: Convert one symbol to lamp commands
echo "Step 7: Converting a symbol to lamp drawing commands..."
if [ -f "$EXPORT_DIR/g1087.svg" ]; then
    echo "  Generating commands for resistor (g1087) at position (500, 800), scale 2.0"
    echo "  Command: python3 svg_to_lamp.py $EXPORT_DIR/g1087.svg 500 800 2.0"
    echo ""
    echo "  Output (first 10 lines):"
    python3 svg_to_lamp.py "$EXPORT_DIR/g1087.svg" 500 800 2.0 | head -10
    echo "  ..."
fi
echo ""

echo "=========================================="
echo "DEMO COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit $CONFIG to customize which symbols are cycled/hidden/viewed"
echo "  2. Run 'python3 component_selector.py' for interactive mode"
echo "  3. Use exported SVG files with svg_to_lamp.py for drawing"
echo ""
echo "Example drawing command:"
echo "  python3 svg_to_lamp.py $EXPORT_DIR/g1087.svg 500 800 2.0 | lamp"
echo ""
