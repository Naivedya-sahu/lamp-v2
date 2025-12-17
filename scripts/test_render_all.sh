#!/bin/bash
# Test script to render all components and fonts
# Tests rendering and erasing functionality

COMPONENT_DIR="/home/user/lamp-v2/assets/components"
FONT_DIR="/home/user/lamp-v2/assets/font"
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
    bash /home/user/lamp-v2/scripts/svg2lamp.sh "$svg_file" "$x" "$y" "1.0" | /opt/bin/lamp

    # Also render its name
    bash /home/user/lamp-v2/scripts/font_render.sh "$name" "$x" "$((y + 50))" "0.4" | /opt/bin/lamp

    # Wait a bit
    sleep "$DELAY"

    # Erase
    echo "Erasing: $name"
    {
        echo "erase on"
        bash /home/user/lamp-v2/scripts/svg2lamp.sh "$svg_file" "$x" "$y" "1.0"
        bash /home/user/lamp-v2/scripts/font_render.sh "$name" "$x" "$((y + 50))" "0.4"
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
bash /home/user/lamp-v2/scripts/font_render.sh "$ALPHABET" "$x" "$y" "0.5" | /opt/bin/lamp

sleep "$DELAY"

echo "Erasing alphabet"
{
    echo "erase on"
    bash /home/user/lamp-v2/scripts/font_render.sh "$ALPHABET" "$x" "$y" "0.5"
    echo "erase off"
} | /opt/bin/lamp

echo ""
echo "=== Test Complete ==="
echo "All components and fonts rendered and erased successfully!"
