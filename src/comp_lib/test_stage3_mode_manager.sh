#!/bin/bash
# test_stage3_mode_manager.sh - Test mode activation manager (BASH VERSION)

set -e

RM2_IP="${1:-10.11.99.1}"

echo "=========================================="
echo "Stage 3: Mode Manager Test (Bash Version)"
echo "=========================================="
echo ""

# Deploy mode manager (bash version)
echo "Deploying bash mode manager..."
scp -q symbol_ui_mode.sh root@$RM2_IP:/opt/bin/symbol_ui_mode
ssh root@$RM2_IP chmod +x /opt/bin/symbol_ui_mode
echo "✓ Deployed"
echo ""

# Test 1: Activation
echo "Test 1: Mode Activation"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode activate"
sleep 1

if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo "✓ Mode file created"
    read -p "  Check RM2 bottom-right for green corner. Visible? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "✓ Visual indicator works"
    else
        echo "⚠ Visual indicator not visible - check lamp binary"
    fi
else
    echo "✗ Mode activation failed"
    exit 1
fi
echo ""

# Test 2: Deactivation
echo "Test 2: Mode Deactivation"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode deactivate"
sleep 1

if ! ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo "✓ Mode file removed"
    read -p "  Green corner disappeared? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "✓ Visual cleanup works"
    else
        echo "⚠ Visual cleanup issue - check lamp binary"
    fi
else
    echo "✗ Mode deactivation failed"
    exit 1
fi
echo ""

# Test 3: Toggle
echo "Test 3: Mode Toggle"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode toggle"
sleep 1

if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo "✓ Toggle activated"
    ssh root@$RM2_IP "/opt/bin/symbol_ui_mode toggle"
    sleep 1
    if ! ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
        echo "✓ Toggle deactivated"
    else
        echo "✗ Toggle deactivation failed"
        exit 1
    fi
else
    echo "✗ Toggle activation failed"
    exit 1
fi
echo ""

# Test 4: Status command
echo "Test 4: Status Command"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode status"
echo ""

echo "=========================================="
echo "Stage 3: PASSED ✓"
echo "=========================================="
echo ""
echo "Note: Bash version deployed (no Python3 required)"
echo "Ready for Stage 4: Controller Test"
