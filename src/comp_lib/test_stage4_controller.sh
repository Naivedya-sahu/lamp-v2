#!/bin/bash
# test_stage4_controller.sh - Test controller logic (BASH VERSION - IMPROVED)

set -e

RM2_IP="${1:-10.11.99.1}"

echo "=========================================="
echo "Stage 4: Controller Test (Bash Version)"
echo "=========================================="
echo ""

# Pre-check: Verify stage 1 completed
if [ ! -f "/tmp/test_library.json" ]; then
    echo "⚠ Library not found at /tmp/test_library.json"
    echo ""
    echo "Running Stage 1 first..."
    cd "$(dirname "${BASH_SOURCE[0]}")"
    ./test_stage1_library_build.sh || {
        echo "✗ Stage 1 failed"
        exit 1
    }
    echo ""
fi

# Check if jq is installed on RM2
echo "Checking jq availability..."
if ! ssh root@$RM2_IP "command -v jq >/dev/null 2>&1"; then
    echo "✗ jq not found on RM2"
    echo ""
    echo "Installing jq via opkg..."
    
    # Try to install
    if ssh root@$RM2_IP "opkg update >/dev/null 2>&1 && opkg install jq >/dev/null 2>&1"; then
        echo "✓ jq installed"
    else
        echo "✗ Failed to install jq automatically"
        echo ""
        echo "Manual installation required:"
        echo "  ssh root@$RM2_IP"
        echo "  opkg update"
        echo "  opkg install jq"
        echo ""
        read -p "Install jq manually and press Enter to continue, or Ctrl+C to exit..."
        
        # Verify after manual install
        if ! ssh root@$RM2_IP "command -v jq >/dev/null 2>&1"; then
            echo "✗ jq still not found"
            exit 1
        fi
    fi
else
    echo "✓ jq already installed"
fi
echo ""

# Deploy library and controller
echo "Deploying files..."

scp -q /tmp/test_library.json root@$RM2_IP:/opt/etc/symbol_library.json
echo "✓ Library deployed"

scp -q symbol_ui_controller.sh root@$RM2_IP:/opt/bin/symbol_ui_controller
ssh root@$RM2_IP chmod +x /opt/bin/symbol_ui_controller
echo "✓ Controller deployed"
echo ""

# Verify deployment
echo "Verifying deployment..."
if ssh root@$RM2_IP "test -f /opt/etc/symbol_library.json"; then
    lib_size=$(ssh root@$RM2_IP "du -h /opt/etc/symbol_library.json | cut -f1")
    echo "✓ Library file exists ($lib_size)"
else
    echo "✗ Library file missing"
    exit 1
fi

if ssh root@$RM2_IP "test -x /opt/bin/symbol_ui_controller"; then
    echo "✓ Controller executable"
else
    echo "✗ Controller not executable"
    exit 1
fi
echo ""

# Test 1: Toggle palette
echo "Test 1: Toggle Palette"
echo "Sending command: toggle_palette"

if ssh root@$RM2_IP "/opt/bin/symbol_ui_controller toggle_palette" 2>&1 | head -1 | grep -q "pen"; then
    echo "✓ Controller generates lamp commands"
    echo ""
    read -p "  Check RM2 - palette border on right side (x=1004-1404)? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "✓ Palette rendering works"
    else
        echo "⚠ Palette not visible"
        echo "  Possible causes:"
        echo "  - lamp not rendering properly"
        echo "  - Library empty or corrupt"
    fi
else
    echo "✗ Controller failed to generate commands"
    echo ""
    echo "Error output:"
    ssh root@$RM2_IP "/opt/bin/symbol_ui_controller toggle_palette" 2>&1 | head -10
    exit 1
fi
echo ""

# Test 2: Scroll (if palette visible)
echo "Test 2: Scroll Down"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller scroll_down" 2>&1 | head -1 | grep -q "pen" && {
    echo "✓ Scroll generates commands"
} || {
    echo "⚠ Scroll may not work (expected if list short)"
}
echo ""

# Test 3: Select component
echo "Test 3: Select Component"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller select_component" 2>&1 | head -1 | grep -q "pen" && {
    echo "✓ Selection generates commands"
    read -p "  Did highlight rectangle appear? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "✓ Selection highlighting works"
    fi
} || {
    echo "⚠ Selection generated no commands"
}
echo ""

# Test 4: Check state file
echo "Test 4: State Persistence"
if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_state.json"; then
    echo "✓ State file exists"
    echo ""
    echo "State contents (first 10 lines):"
    ssh root@$RM2_IP "cat /home/root/.symbol_ui_state.json 2>/dev/null | head -10" | sed 's/^/  /'
    echo ""
    
    # Verify state can be read with jq
    if ssh root@$RM2_IP "jq -r '.palette_visible' /home/root/.symbol_ui_state.json" >/dev/null 2>&1; then
        palette_visible=$(ssh root@$RM2_IP "jq -r '.palette_visible' /home/root/.symbol_ui_state.json")
        echo "✓ State is valid JSON"
        echo "  palette_visible: $palette_visible"
    else
        echo "⚠ State file corrupt or invalid JSON"
    fi
else
    echo "✗ State file not created"
    echo "  Controller may not have write permissions"
fi
echo ""

# Test 5: Library parsing
echo "Test 5: Library Parsing"
component_count=$(ssh root@$RM2_IP "jq -r '.components | length' /opt/etc/symbol_library.json" 2>/dev/null || echo "0")
font_count=$(ssh root@$RM2_IP "jq -r '.font | length' /opt/etc/symbol_library.json" 2>/dev/null || echo "0")

if [ "$component_count" -gt 0 ]; then
    echo "✓ Library contains $component_count components"
    echo "  Sample components:"
    ssh root@$RM2_IP "jq -r '.components | keys[]' /opt/etc/symbol_library.json | head -5" | sed 's/^/    /'
else
    echo "✗ No components in library"
fi

if [ "$font_count" -gt 0 ]; then
    echo "✓ Library contains $font_count glyphs"
else
    echo "⚠ No font glyphs in library (optional)"
fi
echo ""

# Test 6: Clear screen
echo "Test 6: Clear Screen"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller clear_screen" 2>&1 | grep -q "eraser clear" && {
    echo "✓ Clear generates erase command"
    read -p "  Did screen clear? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "✓ Clear screen works"
    fi
} || {
    echo "✗ Clear command failed"
}
echo ""

# Test 7: Scale commands
echo "Test 7: Scale Commands"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller scale_up" >/dev/null 2>&1 && {
    new_scale=$(ssh root@$RM2_IP "jq -r '.scale' /home/root/.symbol_ui_state.json" 2>/dev/null || echo "1.0")
    echo "✓ Scale up works (scale now: $new_scale)"
} || {
    echo "⚠ Scale up failed"
}

ssh root@$RM2_IP "/opt/bin/symbol_ui_controller scale_down" >/dev/null 2>&1 && {
    new_scale=$(ssh root@$RM2_IP "jq -r '.scale' /home/root/.symbol_ui_state.json" 2>/dev/null || echo "1.0")
    echo "✓ Scale down works (scale now: $new_scale)"
} || {
    echo "⚠ Scale down failed"
}
echo ""

echo "=========================================="
echo "Stage 4: Controller Test Complete"
echo "=========================================="
echo ""

# Summary
echo "Summary:"
echo "  - Controller deployed and executable: ✓"
echo "  - jq available for JSON parsing: ✓"
echo "  - Library loaded: $component_count components"
echo "  - State management: $([ -f /home/root/.symbol_ui_state.json ] && echo '✓' || echo '✗')"
echo "  - Lamp command generation: ✓"
echo ""
echo "Known Limitations:"
echo "  - No font rendering (component names as comments)"
echo "  - Palette shows borders/highlights only"
echo "  - Component selection works but no text visible"
echo ""
echo "Next Steps:"
echo "  1. Run: ./test_stage5_service_setup.sh (setup systemd)"
echo "  2. Test gestures on actual device"
echo "  3. Or full deployment: ./deploy_comp_lib.sh"
echo ""
