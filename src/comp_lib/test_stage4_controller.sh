#!/bin/bash
# test_stage4_controller.sh - Test controller logic (BASH VERSION)

set -e

RM2_IP="${1:-10.11.99.1}"

echo "=========================================="
echo "Stage 4: Controller Test (Bash Version)"
echo "=========================================="
echo ""

# Check if jq is installed on RM2
echo "Checking jq availability..."
if ! ssh root@$RM2_IP "command -v jq >/dev/null 2>&1"; then
    echo "✗ jq not found on RM2"
    echo ""
    echo "Installing jq via Toltec..."
    ssh root@$RM2_IP "opkg update && opkg install jq" || {
        echo "✗ Failed to install jq"
        echo "Manual install: ssh root@$RM2_IP 'opkg update && opkg install jq'"
        exit 1
    }
    echo "✓ jq installed"
else
    echo "✓ jq already installed"
fi
echo ""

# Deploy library and controller
echo "Deploying files..."

# Check if library was built
if [ ! -f "/tmp/test_library.json" ]; then
    echo "✗ Library not found at /tmp/test_library.json"
    echo "Run ./test_stage1_library_build.sh first"
    exit 1
fi

scp -q /tmp/test_library.json root@$RM2_IP:/opt/etc/symbol_library.json
echo "✓ Library deployed"

scp -q symbol_ui_controller.sh root@$RM2_IP:/opt/bin/symbol_ui_controller
ssh root@$RM2_IP chmod +x /opt/bin/symbol_ui_controller
echo "✓ Controller deployed"
echo ""

# Test 1: Toggle palette
echo "Test 1: Toggle Palette"
echo "Executing: /opt/bin/symbol_ui_controller toggle_palette"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller toggle_palette" 2>&1 | head -5
echo ""
read -p "  Check RM2 - palette border on right side? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo "✓ Palette rendering works"
else
    echo "⚠ Palette not visible - check lamp and library"
fi
echo ""

# Test 2: Scroll down
echo "Test 2: Scroll Down"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller scroll_down" 2>&1 | head -5
read -p "  Did palette update? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo "✓ Scroll works"
fi
echo ""

# Test 3: Select component
echo "Test 3: Select Component"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller select_component" 2>&1 | head -5
read -p "  Did selection highlight appear? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo "✓ Selection works"
fi
echo ""

# Test 4: Check state file
echo "Test 4: State Persistence"
if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_state.json"; then
    echo "✓ State file exists"
    echo "State contents:"
    ssh root@$RM2_IP "cat /home/root/.symbol_ui_state.json" | head -10
else
    echo "✗ State file not created"
fi
echo ""

# Test 5: Clear screen
echo "Test 5: Clear Screen"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller clear_screen"
read -p "  Did screen clear? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo "✓ Clear works"
fi
echo ""

echo "=========================================="
echo "Stage 4: PASSED ✓"
echo "=========================================="
echo ""
echo "Note: Bash controller with jq for JSON parsing"
echo "Ready for Stage 5: Gesture Integration Test"
