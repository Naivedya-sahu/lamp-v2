#!/bin/bash
# Component Library Manager
# Lists and renders electronic components

COMPONENT_DIR="/home/user/lamp-v2/assets/components"
STATE_DIR="/tmp/genie_ui"
COMPONENT_LIST="$STATE_DIR/components.txt"

# Initialize
mkdir -p "$STATE_DIR"

# Build component list
build_component_list() {
    ls -1 "$COMPONENT_DIR"/*.svg 2>/dev/null | while read -r file; do
        basename "$file" .svg
    done | sort > "$COMPONENT_LIST"
}

# Get component count
get_count() {
    wc -l < "$COMPONENT_LIST" 2>/dev/null || echo "0"
}

# Get component by index (0-based)
get_component() {
    local index=$1
    sed -n "$((index + 1))p" "$COMPONENT_LIST"
}

# Get component file path
get_component_path() {
    local name="$1"
    echo "$COMPONENT_DIR/$name.svg"
}

# Render component at position
render_component() {
    local name="$1"
    local x="$2"
    local y="$3"
    local scale="${4:-1.0}"

    local svg_file=$(get_component_path "$name")

    if [ ! -f "$svg_file" ]; then
        echo "Error: Component $name not found" >&2
        return 1
    fi

    # Use svg2lamp converter
    bash /home/user/lamp-v2/scripts/svg2lamp.sh "$svg_file" "$x" "$y" "$scale"
}

# List all components
list_components() {
    cat "$COMPONENT_LIST" 2>/dev/null
}

# Main command dispatcher
case "${1:-list}" in
    build)
        build_component_list
        echo "Built component list: $(get_count) components"
        ;;
    count)
        get_count
        ;;
    get)
        get_component "$2"
        ;;
    path)
        get_component_path "$2"
        ;;
    render)
        render_component "$2" "$3" "$4" "$5"
        ;;
    list)
        list_components
        ;;
    *)
        echo "Usage: $0 {build|count|get INDEX|path NAME|render NAME X Y [SCALE]|list}"
        exit 1
        ;;
esac
