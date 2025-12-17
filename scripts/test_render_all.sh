#!/bin/bash
# Test script to render all components and fonts
# Tests rendering and erasing functionality

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

COMPONENT_DIR="$PROJECT_ROOT/assets/components"
FONT_DIR="$PROJECT_ROOT/assets/font"
DELAY=2  # Seconds between renders

echo "=== Component Rendering Test ==="
echo "This will render all components and fonts, then erase them"
echo ""

# Test components
echo "Testing Components..."
COMPONENTS=$(ls -1 "$COMPONENT_DIR"/*.svg 2>/dev/null)

x=100
y=100
count=0

for svg_file in $COMPONENTS; do
    name=$(basename "$svg_file" .svg)
    echo "Rendering: $name at ($x, $y)"

    # Render component
    bash "$SCRIPT_DIR/svg2lamp.sh" "$svg_file" "$x" "$y" "1.0" | /opt/bin/lamp

    # Also render its name
    bash "$SCRIPT_DIR/font_render.sh" "$name" "$x" "$((y + 50))" "0.4" | /opt/bin/lamp

    # Wait a bit
    sleep "$DELAY"

    # Erase
    echo "Erasing: $name"
    {
        echo "erase on"
        bash "$SCRIPT_DIR/svg2lamp.sh" "$svg_file" "$x" "$y" "1.0"
        bash "$SCRIPT_DIR/font_render.sh" "$name" "$x" "$((y + 50))" "0.4"
        echo "erase off"
    } | /opt/bin/lamp

    # Move to next position
    count=$((count + 1))
    if [ $((count % 4)) -eq 0 ]; then
        x=100
        y=$((y + 150))
    else
        x=$((x + 200))
    fi

    sleep 0.5
done

echo ""
echo "=== Font Rendering Test ==="

# Test alphabet
ALPHABET="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
x=100
y=800

echo "Rendering alphabet: $ALPHABET"
bash "$SCRIPT_DIR/font_render.sh" "$ALPHABET" "$x" "$y" "0.5" | /opt/bin/lamp

sleep "$DELAY"

echo "Erasing alphabet"
{
    echo "erase on"
    bash "$SCRIPT_DIR/font_render.sh" "$ALPHABET" "$x" "$y" "0.5"
    echo "erase off"
} | /opt/bin/lamp

echo ""
echo "=== Test Complete ==="
echo "All components and fonts rendered and erased successfully!"
