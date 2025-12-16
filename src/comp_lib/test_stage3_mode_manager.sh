#!/bin/bash
# test_stage3_mode_manager.sh - Test mode activation manager

set -e

RM2_IP="${1:-10.11.99.1}"

echo "=========================================="
echo "Stage 3: Mode Manager Test"
echo "=========================================="
echo ""

# Deploy mode manager
echo "Deploying mode manager..."
scp -q symbol_ui_mode.py root@$RM2_IP:/opt/bin/symbol_ui_mode
ssh root@$RM2_IP chmod +x /opt/bin/symbol_ui_mode
echo "✓ Deployed"
echo ""

# Test 1: Activation
echo "Test 1: Mode Activation"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode activate"
if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo "✓ Mode file created"
    read -p "  Check RM2 bottom-right for green corner. Visible? (y/n): " answer
    if [ "$answer" != "y" ]; then
        echo "⚠ Visual indicator may not be working"
    fi
else
    echo "✗ Mode activation failed"
    exit 1
fi
echo ""

# Test 2: Deactivation
echo "Test 2: Mode Deactivation"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode deactivate"
if ! ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo "✓ Mode file removed"
    read -p "  Green corner disappeared? (y/n): " answer
    if [ "$answer" != "y" ]; then
        echo "⚠ Visual cleanup may not be working"
    fi
else
    echo "✗ Mode deactivation failed"
    exit 1
fi
echo ""

# Test 3: Toggle
echo "Test 3: Mode Toggle"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode toggle"
if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo "✓ Toggle activated"
    ssh root@$RM2_IP "/opt/bin/symbol_ui_mode toggle"
    if ! ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
        echo "✓ Toggle deactivated"
    fi
else
    echo "✗ Toggle failed"
    exit 1
fi
echo ""

echo "=========================================="
echo "Stage 3: PASSED ✓"
echo "=========================================="
echo "Ready for Stage 4: Controller Test"
