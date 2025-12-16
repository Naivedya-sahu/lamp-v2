#!/bin/bash
#
# symbol_ui_controller - Component UI controller (bash version)
# Simplified version without Python - uses jq for JSON parsing
#

set -e

# Configuration
LIBRARY_FILE="/opt/etc/symbol_library.json"
STATE_FILE="/home/root/.symbol_ui_state.json"
LAMP_BIN="/opt/bin/lamp"

# Screen dimensions
SCREEN_WIDTH=1404
SCREEN_HEIGHT=1872

# UI layout
UI_PANEL_WIDTH=400
UI_PANEL_X=1004
UI_PANEL_Y=0
UI_PANEL_HEIGHT=$SCREEN_HEIGHT

CANVAS_WIDTH=1004
CANVAS_HEIGHT=$SCREEN_HEIGHT

UI_ITEM_HEIGHT=100
UI_VISIBLE_ITEMS=16
UI_MARGIN=30

# Check if jq is available
if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq not found. Install with: opkg install jq" >&2
    exit 1
fi

# Initialize state file if doesn't exist
if [ ! -f "$STATE_FILE" ]; then
    cat > "$STATE_FILE" << 'EOF'
{
  "palette_visible": false,
  "selected_component": null,
  "scroll_offset": 0,
  "rotation": 0,
  "scale": 1.0,
  "history": []
}
EOF
fi

# Read state value
get_state() {
    local key="$1"
    jq -r ".$key" "$STATE_FILE" 2>/dev/null || echo "null"
}

# Update state value
set_state() {
    local key="$1"
    local value="$2"
    
    # Create temp file
    local tmp=$(mktemp)
    
    # Update JSON
    if [[ "$value" =~ ^[0-9]+\.?[0-9]*$ ]] || [ "$value" = "true" ] || [ "$value" = "false" ] || [ "$value" = "null" ]; then
        # Number, boolean, or null - no quotes
        jq ".$key = $value" "$STATE_FILE" > "$tmp"
    else
        # String - needs quotes
        jq ".$key = \"$value\"" "$STATE_FILE" > "$tmp"
    fi
    
    mv "$tmp" "$STATE_FILE"
}

# Get component list
get_components() {
    jq -r '.components | keys[]' "$LIBRARY_FILE" 2>/dev/null | sort
}

# Count components
count_components() {
    get_components | wc -l
}

# Get component at index
get_component_at() {
    local idx=$1
    get_components | sed -n "$((idx + 1))p"
}

# Toggle palette visibility
toggle_palette() {
    local visible=$(get_state "palette_visible")
    
    if [ "$visible" = "true" ]; then
        # Hide palette
        set_state "palette_visible" "false"
        echo "eraser clear $UI_PANEL_X $UI_PANEL_Y $SCREEN_WIDTH $SCREEN_HEIGHT"
    else
        # Show palette
        set_state "palette_visible" "true"
        render_palette
    fi
}

# Render palette (simplified - no fonts yet)
render_palette() {
    local visible=$(get_state "palette_visible")
    
    if [ "$visible" != "true" ]; then
        return
    fi
    
    # Draw panel border
    echo "pen rectangle $UI_PANEL_X $UI_PANEL_Y $SCREEN_WIDTH $SCREEN_HEIGHT"
    
    # Get current scroll offset
    local scroll=$(get_state "scroll_offset")
    local selected=$(get_state "selected_component")
    
    # Get component list
    local components=($(get_components))
    local total=${#components[@]}
    
    # Calculate visible range
    local end=$((scroll + UI_VISIBLE_ITEMS))
    if [ $end -gt $total ]; then
        end=$total
    fi
    
    # Render component names (simplified - just first 3 letters)
    for ((i=scroll; i<end; i++)); do
        local comp="${components[$i]}"
        local y_pos=$((UI_PANEL_Y + UI_MARGIN + (i - scroll) * UI_ITEM_HEIGHT))
        
        # Highlight selected component
        if [ "$comp" = "$selected" ]; then
            local x1=$((UI_PANEL_X + 10))
            local y1=$((y_pos - 5))
            local x2=$((SCREEN_WIDTH - 10))
            local y2=$((y_pos + 75))
            echo "pen rectangle $x1 $y1 $x2 $y2"
        fi
        
        # Draw component name as simple text marker
        # TODO: Replace with actual font rendering
        local text_x=$((UI_PANEL_X + UI_MARGIN))
        local text_y=$((y_pos + 20))
        echo "# Component: $comp at ($text_x, $text_y)"
    done
    
    # Draw scroll indicator
    if [ $total -gt $UI_VISIBLE_ITEMS ]; then
        local scroll_height=$((UI_VISIBLE_ITEMS * UI_PANEL_HEIGHT / total))
        local scroll_y=$((scroll * UI_PANEL_HEIGHT / total))
        local x1=$((SCREEN_WIDTH - 20))
        local x2=$((SCREEN_WIDTH - 10))
        local y2=$((scroll_y + scroll_height))
        echo "pen rectangle $x1 $scroll_y $x2 $y2"
    fi
}

# Scroll functions
scroll_up() {
    local scroll=$(get_state "scroll_offset")
    if [ "$scroll" -gt 0 ]; then
        scroll=$((scroll - 1))
        set_state "scroll_offset" "$scroll"
        echo "eraser clear $UI_PANEL_X $UI_PANEL_Y $SCREEN_WIDTH $SCREEN_HEIGHT"
        render_palette
    fi
}

scroll_down() {
    local scroll=$(get_state "scroll_offset")
    local total=$(count_components)
    local max=$((total - UI_VISIBLE_ITEMS))
    if [ $max -lt 0 ]; then
        max=0
    fi
    
    if [ "$scroll" -lt "$max" ]; then
        scroll=$((scroll + 1))
        set_state "scroll_offset" "$scroll"
        echo "eraser clear $UI_PANEL_X $UI_PANEL_Y $SCREEN_WIDTH $SCREEN_HEIGHT"
        render_palette
    fi
}

# Select component
select_component() {
    local scroll=$(get_state "scroll_offset")
    local comp=$(get_component_at $scroll)
    
    if [ -n "$comp" ]; then
        set_state "selected_component" "$comp"
        echo "eraser clear $UI_PANEL_X $UI_PANEL_Y $SCREEN_WIDTH $SCREEN_HEIGHT"
        render_palette
    fi
}

# Place component (simplified - no actual component rendering yet)
place_component() {
    local selected=$(get_state "selected_component")
    
    if [ "$selected" = "null" ] || [ -z "$selected" ]; then
        return
    fi
    
    # Get tap coordinates from environment
    local x=${TAP_X:-500}
    local y=${TAP_Y:-500}
    local scale=$(get_state "scale")
    
    # Get component commands from library
    local commands=$(jq -r ".components.\"$selected\".commands[]" "$LIBRARY_FILE" 2>/dev/null)
    
    if [ -z "$commands" ]; then
        echo "# Error: Component $selected not found in library" >&2
        return
    fi
    
    # Transform and output commands
    echo "$commands" | while IFS= read -r cmd; do
        # Parse command and apply transforms
        # This is simplified - full implementation would parse and transform coordinates
        if [[ "$cmd" =~ ^pen\ (down|move)\ ([0-9.-]+)\ ([0-9.-]+) ]]; then
            local action="${BASH_REMATCH[1]}"
            local px="${BASH_REMATCH[2]}"
            local py="${BASH_REMATCH[3]}"
            
            # Apply scale and translate
            px=$(awk "BEGIN {printf \"%.0f\", $px * $scale + $x}")
            py=$(awk "BEGIN {printf \"%.0f\", $py * $scale + $y}")
            
            echo "pen $action $px $py"
        else
            echo "$cmd"
        fi
    done
}

# Cancel selection
cancel_selection() {
    set_state "selected_component" "null"
    echo "eraser clear $UI_PANEL_X $UI_PANEL_Y $SCREEN_WIDTH $SCREEN_HEIGHT"
    render_palette
}

# Clear screen
clear_screen() {
    echo "eraser clear 0 0 $SCREEN_WIDTH $SCREEN_HEIGHT"
    # Reset history (simplified)
    set_state "history" "[]"
}

# Scale functions
scale_up() {
    local scale=$(get_state "scale")
    scale=$(awk "BEGIN {printf \"%.2f\", $scale + 0.25}")
    # Cap at 3.0
    scale=$(awk "BEGIN {if ($scale > 3.0) print 3.0; else print $scale}")
    set_state "scale" "$scale"
}

scale_down() {
    local scale=$(get_state "scale")
    scale=$(awk "BEGIN {printf \"%.2f\", $scale - 0.25}")
    # Min at 0.25
    scale=$(awk "BEGIN {if ($scale < 0.25) print 0.25; else print $scale}")
    set_state "scale" "$scale"
}

# Undo (simplified)
undo() {
    # TODO: Implement proper undo with visual erase
    echo "# Undo not yet implemented" >&2
}

# Main
if [ $# -lt 1 ]; then
    echo "Usage: symbol_ui_controller <command>" >&2
    echo "" >&2
    echo "Commands:" >&2
    echo "  toggle_palette, scroll_up, scroll_down, select_component" >&2
    echo "  place_component, cancel_selection, clear_screen" >&2
    echo "  scale_up, scale_down, undo" >&2
    exit 1
fi

command="$1"

# Check library exists
if [ ! -f "$LIBRARY_FILE" ]; then
    echo "Error: Library not found: $LIBRARY_FILE" >&2
    exit 1
fi

# Execute command and pipe to lamp
case "$command" in
    toggle_palette)
        toggle_palette | $LAMP_BIN
        ;;
    scroll_up)
        scroll_up | $LAMP_BIN
        ;;
    scroll_down)
        scroll_down | $LAMP_BIN
        ;;
    select_component)
        select_component | $LAMP_BIN
        ;;
    place_component)
        place_component | $LAMP_BIN
        ;;
    cancel_selection)
        cancel_selection | $LAMP_BIN
        ;;
    clear_screen)
        clear_screen | $LAMP_BIN
        ;;
    scale_up)
        scale_up
        ;;
    scale_down)
        scale_down
        ;;
    undo)
        undo
        ;;
    *)
        echo "Error: Unknown command: $command" >&2
        exit 1
        ;;
esac
