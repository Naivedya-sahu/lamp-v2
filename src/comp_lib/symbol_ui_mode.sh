#!/bin/bash
#
# symbol_ui_mode - Component Mode activation manager (bash version)
# No Python3 required - pure bash for RM2 compatibility
#

set -e

# Configuration
MODE_FILE="/home/root/.symbol_ui_mode"
SERVICE_NAME="symbol_ui_main.service"
LAMP_BIN="/opt/bin/lamp"

# Screen dimensions
SCREEN_WIDTH=1404
SCREEN_HEIGHT=1872

# Visual indicator (bottom-right corner, 34x34px green square)
INDICATOR_X1=$((SCREEN_WIDTH - 34))
INDICATOR_Y1=$((SCREEN_HEIGHT - 34))
INDICATOR_X2=$SCREEN_WIDTH
INDICATOR_Y2=$SCREEN_HEIGHT

is_active() {
    [ -f "$MODE_FILE" ]
}

draw_indicator() {
    echo "pen rectangle $INDICATOR_X1 $INDICATOR_Y1 $INDICATOR_X2 $INDICATOR_Y2" | $LAMP_BIN 2>/dev/null || true
}

erase_indicator() {
    echo "eraser clear $INDICATOR_X1 $INDICATOR_Y1 $INDICATOR_X2 $INDICATOR_Y2" | $LAMP_BIN 2>/dev/null || true
}

activate() {
    if is_active; then
        echo "Already in Component Mode" >&2
        return 0
    fi
    
    echo "Activating Component Mode..." >&2
    
    # Create mode indicator file
    touch "$MODE_FILE"
    
    # Start main UI service
    systemctl start "$SERVICE_NAME" 2>/dev/null || {
        echo "Warning: Failed to start service" >&2
    }
    
    # Small delay for service startup
    sleep 0.5
    
    # Draw visual indicator
    draw_indicator
    
    echo "Component Mode ACTIVE" >&2
}

deactivate() {
    if ! is_active; then
        echo "Already in Normal Mode" >&2
        return 0
    fi
    
    echo "Deactivating Component Mode..." >&2
    
    # Erase visual indicator first (immediate feedback)
    erase_indicator
    
    # Stop main UI service
    systemctl stop "$SERVICE_NAME" 2>/dev/null || {
        echo "Warning: Failed to stop service" >&2
    }
    
    # Remove mode indicator file
    rm -f "$MODE_FILE"
    
    echo "Component Mode INACTIVE" >&2
}

toggle() {
    if is_active; then
        deactivate
    else
        activate
    fi
}

status() {
    if is_active; then
        echo "Component Mode: ACTIVE"
        # Check if service is actually running
        if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
            echo "Main Service: active"
        else
            echo "Main Service: inactive"
        fi
    else
        echo "Component Mode: INACTIVE"
    fi
    
    # Check activation service
    if systemctl is-active --quiet "symbol_ui_activation.service" 2>/dev/null; then
        echo "Activation Service: active"
    else
        echo "Activation Service: inactive"
    fi
}

# Main
if [ $# -lt 1 ]; then
    echo "Usage: symbol_ui_mode {activate|deactivate|toggle|status}" >&2
    echo "" >&2
    echo "Commands:" >&2
    echo "  activate    - Enter Component Mode" >&2
    echo "  deactivate  - Exit Component Mode" >&2
    echo "  toggle      - Switch between modes" >&2
    echo "  status      - Show current mode" >&2
    exit 1
fi

case "$1" in
    activate)
        activate
        ;;
    deactivate)
        deactivate
        ;;
    toggle)
        toggle
        ;;
    status)
        status
        ;;
    *)
        echo "Error: Unknown command '$1'" >&2
        echo "Use: activate, deactivate, toggle, or status" >&2
        exit 1
        ;;
esac
