#!/bin/bash
# SVG to lamp converter
# Extracts path data from SVG and converts to lamp commands

if [ $# -lt 1 ]; then
    echo "Usage: $0 <svg_file> [offset_x] [offset_y] [scale]"
    echo "Example: $0 R.svg 1000 1400 1.0"
    exit 1
fi

SVG_FILE="$1"
OFFSET_X="${2:-0}"
OFFSET_Y="${3:-0}"
SCALE="${4:-1.0}"

if [ ! -f "$SVG_FILE" ]; then
    echo "Error: File $SVG_FILE not found"
    exit 1
fi

# Extract path data from SVG
# Look for d="..." attribute in path elements
PATH_DATA=$(grep -o 'd="[^"]*"' "$SVG_FILE" | sed 's/d="//;s/"$//')

if [ -z "$PATH_DATA" ]; then
    echo "Error: No path data found in $SVG_FILE" >&2
    exit 1
fi

# Simple path parser - converts SVG path to lamp commands
# This handles M (moveto), L (lineto), H (horizontal), V (vertical), C (curve)
# For curves, we approximate with straight lines

convert_path() {
    local path="$1"
    local in_path=false

    # Replace path commands with newlines for easier parsing
    echo "$path" | sed 's/M/\nM/g; s/L/\nL/g; s/H/\nH/g; s/V/\nV/g; s/C/\nC/g; s/c/\nc/g; s/m/\nm/g; s/l/\nl/g' | while read -r cmd; do
        # Skip empty lines
        [ -z "$cmd" ] && continue

        # Extract command letter and coordinates
        CMD_LETTER=$(echo "$cmd" | head -c 1)
        COORDS=$(echo "$cmd" | cut -c 2- | tr ',' ' ')

        case "$CMD_LETTER" in
            M|m)
                # Move to - pen up, move, pen down
                set -- $COORDS
                if [ "$CMD_LETTER" = "M" ]; then
                    # Absolute coordinates
                    X=$(echo "$1 * $SCALE + $OFFSET_X" | bc 2>/dev/null || echo "$1")
                    Y=$(echo "$2 * $SCALE + $OFFSET_Y" | bc 2>/dev/null || echo "$2")
                else
                    # Relative - for simplicity, treat as absolute
                    X=$(echo "$1 * $SCALE + $OFFSET_X" | bc 2>/dev/null || echo "$1")
                    Y=$(echo "$2 * $SCALE + $OFFSET_Y" | bc 2>/dev/null || echo "$2")
                fi
                # Round to integer
                X=$(printf "%.0f" "$X" 2>/dev/null || echo "${X%.*}")
                Y=$(printf "%.0f" "$Y" 2>/dev/null || echo "${Y%.*}")
                echo "pen up"
                echo "pen move $X $Y"
                echo "pen down"
                ;;
            L|l)
                # Line to
                set -- $COORDS
                while [ $# -ge 2 ]; do
                    X=$(echo "$1 * $SCALE + $OFFSET_X" | bc 2>/dev/null || echo "$1")
                    Y=$(echo "$2 * $SCALE + $OFFSET_Y" | bc 2>/dev/null || echo "$2")
                    X=$(printf "%.0f" "$X" 2>/dev/null || echo "${X%.*}")
                    Y=$(printf "%.0f" "$Y" 2>/dev/null || echo "${Y%.*}")
                    echo "pen move $X $Y"
                    shift 2
                done
                ;;
            H|h)
                # Horizontal line
                X=$(echo "$COORDS * $SCALE + $OFFSET_X" | bc 2>/dev/null || echo "$COORDS")
                X=$(printf "%.0f" "$X" 2>/dev/null || echo "${X%.*}")
                echo "pen move $X \$LAST_Y"
                ;;
            V|v)
                # Vertical line
                Y=$(echo "$COORDS * $SCALE + $OFFSET_Y" | bc 2>/dev/null || echo "$COORDS")
                Y=$(printf "%.0f" "$Y" 2>/dev/null || echo "${Y%.*}")
                echo "pen move \$LAST_X $Y"
                ;;
            C|c)
                # Cubic bezier - approximate with end point
                set -- $COORDS
                # Take last two coordinates (end point)
                while [ $# -gt 2 ]; do shift; done
                X=$(echo "$1 * $SCALE + $OFFSET_X" | bc 2>/dev/null || echo "$1")
                Y=$(echo "$2 * $SCALE + $OFFSET_Y" | bc 2>/dev/null || echo "$2")
                X=$(printf "%.0f" "$X" 2>/dev/null || echo "${X%.*}")
                Y=$(printf "%.0f" "$Y" 2>/dev/null || echo "${Y%.*}")
                echo "pen move $X $Y"
                ;;
        esac
    done
    echo "pen up"
}

convert_path "$PATH_DATA"
