#!/bin/bash
# Font Text Renderer
# Renders text using SVG font glyphs

FONT_DIR="/home/user/lamp-v2/assets/font"
CHAR_WIDTH=25  # Approximate character width for spacing
CHAR_HEIGHT=40 # Approximate character height

# Render a single character
render_char() {
    local char="$1"
    local x="$2"
    local y="$3"
    local scale="${4:-0.5}"  # Default smaller scale for text

    # Map character to font file
    local font_file="$FONT_DIR/segoe path_${char}.svg"

    if [ ! -f "$font_file" ]; then
        echo "# Character '$char' not available" >&2
        return 1
    fi

    # Render using svg2lamp
    bash /home/user/lamp-v2/scripts/svg2lamp.sh "$font_file" "$x" "$y" "$scale"
}

# Render text string
render_text() {
    local text="$1"
    local x="$2"
    local y="$3"
    local scale="${4:-0.5}"

    local char_spacing=$(echo "$CHAR_WIDTH * $scale" | bc 2>/dev/null || echo "12")
    char_spacing=$(printf "%.0f" "$char_spacing" 2>/dev/null || echo "${char_spacing%.*}")

    local current_x=$x
    local i=0

    while [ $i -lt ${#text} ]; do
        local char="${text:$i:1}"

        # Convert to uppercase for font lookup
        char=$(echo "$char" | tr '[:lower:]' '[:upper:]')

        # Skip spaces
        if [ "$char" = " " ]; then
            current_x=$((current_x + char_spacing))
            i=$((i + 1))
            continue
        fi

        # Render character
        render_char "$char" "$current_x" "$y" "$scale"

        # Advance position
        current_x=$((current_x + char_spacing))
        i=$((i + 1))
    done
}

# Main
if [ $# -lt 3 ]; then
    echo "Usage: $0 <text> <x> <y> [scale]"
    echo "Example: $0 'RESISTOR' 1000 1400 0.5"
    exit 1
fi

render_text "$1" "$2" "$3" "$4"
