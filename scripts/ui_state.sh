#!/bin/bash
# UI State Machine for Component Selection
# Manages state and draws UI in bottom-right corner

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# UI Configuration
UI_X=1000              # Left edge of UI box
UI_Y=1400              # Top edge of UI box
UI_WIDTH=404           # Width of UI box
UI_HEIGHT=472          # Height of UI box
ITEMS_PER_PAGE=5       # How many items to show per page
TEXT_SCALE=0.4         # Scale for text rendering
COMPONENT_SCALE=0.8    # Scale for component preview

# State file locations
STATE_DIR="/tmp/genie_ui"
STATE_FILE="$STATE_DIR/state.txt"
COMPONENT_LIST="$STATE_DIR/components.txt"

# Initialize state
init_state() {
    mkdir -p "$STATE_DIR"

    # Build component list
    bash "$SCRIPT_DIR/component_library.sh" build

    # Initialize state file if doesn't exist
    if [ ! -f "$STATE_FILE" ]; then
        echo "page=0" > "$STATE_FILE"
        echo "selected=0" >> "$STATE_FILE"
        echo "mode=list" >> "$STATE_FILE"
    fi
}

# Read state variable
get_state() {
    local key="$1"
    grep "^${key}=" "$STATE_FILE" 2>/dev/null | cut -d= -f2
}

# Set state variable
set_state() {
    local key="$1"
    local value="$2"

    if grep -q "^${key}=" "$STATE_FILE" 2>/dev/null; then
        sed -i "s/^${key}=.*/${key}=${value}/" "$STATE_FILE"
    else
        echo "${key}=${value}" >> "$STATE_FILE"
    fi
}

# Get total component count
get_total_count() {
    wc -l < "$COMPONENT_LIST" 2>/dev/null || echo "0"
}

# Get total pages
get_total_pages() {
    local total=$(get_total_count)
    echo $(( (total + ITEMS_PER_PAGE - 1) / ITEMS_PER_PAGE ))
}

# Clear UI area
clear_ui() {
    # Draw a filled rectangle to clear the area (use erase mode in lamp)
    echo "erase on" | /opt/bin/lamp
    echo "pen down $UI_X $UI_Y" | /opt/bin/lamp
    echo "pen move $((UI_X + UI_WIDTH)) $UI_Y" | /opt/bin/lamp
    echo "pen move $((UI_X + UI_WIDTH)) $((UI_Y + UI_HEIGHT))" | /opt/bin/lamp
    echo "pen move $UI_X $((UI_Y + UI_HEIGHT))" | /opt/bin/lamp
    echo "pen move $UI_X $UI_Y" | /opt/bin/lamp
    echo "pen up" | /opt/bin/lamp
    echo "erase off" | /opt/bin/lamp
}

# Draw UI border
draw_border() {
    {
        echo "pen down $UI_X $UI_Y"
        echo "pen move $((UI_X + UI_WIDTH)) $UI_Y"
        echo "pen move $((UI_X + UI_WIDTH)) $((UI_Y + UI_HEIGHT))"
        echo "pen move $UI_X $((UI_Y + UI_HEIGHT))"
        echo "pen move $UI_X $UI_Y"
        echo "pen up"
    } | /opt/bin/lamp
}

# Draw component list
draw_list() {
    local page=$(get_state page)
    local selected=$(get_state selected)
    local total=$(get_total_count)

    local start_index=$((page * ITEMS_PER_PAGE))
    local y_offset=$((UI_Y + 50))
    local line_height=60

    # Draw page info
    local current_page=$((page + 1))
    local total_pages=$(get_total_pages)
    bash "$SCRIPT_DIR/font_render.sh" "PG ${current_page}/${total_pages}" $((UI_X + 10)) $((UI_Y + 10)) 0.3 | /opt/bin/lamp

    # Draw list items
    for i in $(seq 0 $((ITEMS_PER_PAGE - 1))); do
        local index=$((start_index + i))
        [ $index -ge $total ] && break

        # Get component name
        local name=$(bash "$SCRIPT_DIR/component_library.sh" get "$index")

        # Highlight if selected
        if [ $index -eq $selected ]; then
            echo "> " > /tmp/prefix.txt
        else
            echo "  " > /tmp/prefix.txt
        fi

        # Draw item
        local text="$(cat /tmp/prefix.txt)$((index + 1)) $name"
        bash "$SCRIPT_DIR/font_render.sh" "$text" $((UI_X + 10)) "$y_offset" "$TEXT_SCALE" | /opt/bin/lamp

        y_offset=$((y_offset + line_height))
    done
}

# Draw selected component preview
draw_preview() {
    local selected=$(get_state selected)
    local name=$(bash "$SCRIPT_DIR/component_library.sh" get "$selected")

    [ -z "$name" ] && return

    # Draw in upper area of UI
    local preview_x=$((UI_X + UI_WIDTH / 2 - 50))
    local preview_y=$((UI_Y + 250))

    bash "$SCRIPT_DIR/component_library.sh" render "$name" "$preview_x" "$preview_y" "$COMPONENT_SCALE" | /opt/bin/lamp
}

# Redraw entire UI
redraw() {
    clear_ui
    draw_border
    draw_list

    # Draw preview if in preview mode
    local mode=$(get_state mode)
    if [ "$mode" = "preview" ]; then
        draw_preview
    fi
}

# Navigation: Next page
next_page() {
    local page=$(get_state page)
    local total_pages=$(get_total_pages)
    page=$((page + 1))
    [ $page -ge $total_pages ] && page=$((total_pages - 1))
    set_state page "$page"

    # Adjust selection to be within page
    local selected=$(get_state selected)
    local page_start=$((page * ITEMS_PER_PAGE))
    local total=$(get_total_count)
    local page_end=$((page_start + ITEMS_PER_PAGE - 1))
    [ $page_end -ge $total ] && page_end=$((total - 1))

    if [ $selected -lt $page_start ]; then
        set_state selected "$page_start"
    elif [ $selected -gt $page_end ]; then
        set_state selected "$page_end"
    fi
}

# Navigation: Previous page
prev_page() {
    local page=$(get_state page)
    page=$((page - 1))
    [ $page -lt 0 ] && page=0
    set_state page "$page"

    # Adjust selection
    local selected=$(get_state selected)
    local page_start=$((page * ITEMS_PER_PAGE))
    local page_end=$((page_start + ITEMS_PER_PAGE - 1))

    if [ $selected -lt $page_start ]; then
        set_state selected "$page_start"
    elif [ $selected -gt $page_end ]; then
        set_state selected "$page_end"
    fi
}

# Navigation: Next item
next_item() {
    local selected=$(get_state selected)
    local total=$(get_total_count)
    selected=$((selected + 1))
    [ $selected -ge $total ] && selected=$((total - 1))
    set_state selected "$selected"

    # Auto-advance page if needed
    local page=$(get_state page)
    local page_end=$((page * ITEMS_PER_PAGE + ITEMS_PER_PAGE - 1))
    if [ $selected -gt $page_end ]; then
        next_page
    fi
}

# Navigation: Previous item
prev_item() {
    local selected=$(get_state selected)
    selected=$((selected - 1))
    [ $selected -lt 0 ] && selected=0
    set_state selected "$selected"

    # Auto-go-back page if needed
    local page=$(get_state page)
    local page_start=$((page * ITEMS_PER_PAGE))
    if [ $selected -lt $page_start ]; then
        prev_page
    fi
}

# Select current item (toggle preview)
select_item() {
    local mode=$(get_state mode)
    if [ "$mode" = "list" ]; then
        set_state mode "preview"
    else
        set_state mode "list"
    fi
}

# Main command dispatcher
case "${1:-init}" in
    init)
        init_state
        echo "UI initialized"
        ;;
    redraw)
        redraw
        ;;
    next_page)
        next_page
        redraw
        ;;
    prev_page)
        prev_page
        redraw
        ;;
    next_item)
        next_item
        redraw
        ;;
    prev_item)
        prev_item
        redraw
        ;;
    select)
        select_item
        redraw
        ;;
    state)
        cat "$STATE_FILE"
        ;;
    *)
        echo "Usage: $0 {init|redraw|next_page|prev_page|next_item|prev_item|select|state}"
        exit 1
        ;;
esac
