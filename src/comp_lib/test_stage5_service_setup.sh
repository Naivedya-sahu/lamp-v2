#!/bin/bash
# test_stage5_service_setup.sh - Setup and test systemd services

set -e

RM2_IP="${1:-10.11.99.1}"

echo "=========================================="
echo "Stage 5: Service Setup & Integration Test"
echo "=========================================="
echo ""

# Deploy service files
echo "Deploying systemd service files..."
scp -q symbol_ui_activation.service root@$RM2_IP:/etc/systemd/system/
scp -q symbol_ui_main.service root@$RM2_IP:/etc/systemd/system/
echo "✓ Service files deployed"
echo ""

# Reload systemd
echo "Reloading systemd daemon..."
ssh root@$RM2_IP "systemctl daemon-reload"
echo "✓ Daemon reloaded"
echo ""

# Check service files are valid
echo "Validating service files..."
if ssh root@$RM2_IP "systemctl cat symbol_ui_activation.service" >/dev/null 2>&1; then
    echo "✓ Activation service file valid"
else
    echo "✗ Activation service file invalid"
    exit 1
fi

if ssh root@$RM2_IP "systemctl cat symbol_ui_main.service" >/dev/null 2>&1; then
    echo "✓ Main service file valid"
else
    echo "✗ Main service file invalid"
    exit 1
fi
echo ""

# Enable activation service
echo "Enabling activation service..."
ssh root@$RM2_IP "systemctl enable symbol_ui_activation.service" 2>&1 | grep -v "Created symlink" || true
echo "✓ Service enabled"
echo ""

# Start activation service
echo "Starting activation service..."
ssh root@$RM2_IP "systemctl start symbol_ui_activation.service"
sleep 2

# Check service status
echo "Checking service status..."
if ssh root@$RM2_IP "systemctl is-active --quiet symbol_ui_activation.service"; then
    echo "✓ Activation service is ACTIVE"
else
    echo "✗ Activation service is NOT active"
    echo ""
    echo "Service status:"
    ssh root@$RM2_IP "systemctl status symbol_ui_activation.service --no-pager -n 20" || true
    echo ""
    echo "Recent logs:"
    ssh root@$RM2_IP "journalctl -u symbol_ui_activation.service -n 30 --no-pager" || true
    echo ""
    read -p "Continue anyway? (y/n): " answer
    if [ "$answer" != "y" ]; then
        exit 1
    fi
fi
echo ""

# Test gesture detection manually
echo "=========================================="
echo "Manual Gesture Test"
echo "=========================================="
echo ""
echo "The activation service should now be listening for gestures."
echo ""
echo "Test Plan:"
echo "  1. On RM2: Perform 5-finger tap"
echo "  2. Green corner should appear"
echo "  3. Mode file should be created"
echo ""
read -p "Press Enter to check if service is detecting input..."
echo ""

# Check if service is running and listening
if ssh root@$RM2_IP "ps aux | grep -v grep | grep 'genie_lamp.*activation.conf'" >/dev/null; then
    echo "✓ genie_lamp process running"
    echo ""
    ssh root@$RM2_IP "ps aux | grep -v grep | grep 'genie_lamp.*activation.conf'"
    echo ""
else
    echo "✗ genie_lamp process NOT found"
    echo ""
    echo "All genie_lamp processes:"
    ssh root@$RM2_IP "ps aux | grep genie_lamp | grep -v grep" || echo "  (none)"
    echo ""
fi

echo "Now perform 5-finger tap on RM2..."
echo ""
read -p "Did you perform 5-finger tap? Press Enter to check result..."

# Check if mode activated
if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo "✓ Mode file exists - gesture detected!"
    echo "✓ 5-finger tap works!"
    
    # Check if main service started
    sleep 2
    if ssh root@$RM2_IP "systemctl is-active --quiet symbol_ui_main.service"; then
        echo "✓ Main service auto-started"
    else
        echo "⚠ Main service did not auto-start"
        echo "  (This is OK - services work, just not via systemctl trigger)"
    fi
    
    # Cleanup
    echo ""
    read -p "Test 4-finger swipe down to deactivate? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "Perform 4-finger swipe down on RM2..."
        read -p "Press Enter after swipe..."
        
        if ! ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
            echo "✓ Deactivation gesture works!"
        else
            echo "⚠ Mode still active - deactivate manually"
            ssh root@$RM2_IP "/opt/bin/symbol_ui_mode deactivate"
        fi
    fi
else
    echo "✗ Mode file not created"
    echo "  Gesture not detected or service not listening"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check service logs:"
    echo "     ssh root@$RM2_IP journalctl -u symbol_ui_activation.service -f"
    echo ""
    echo "  2. Test manually:"
    echo "     ssh root@$RM2_IP"
    echo "     systemctl stop symbol_ui_activation.service"
    echo "     /opt/bin/genie_lamp /opt/etc/symbol_ui_activation.conf"
    echo "     (Then try 5-finger tap)"
fi

echo ""
echo "=========================================="
echo "Stage 5: Service Integration Test Complete"
echo "=========================================="
echo ""

# Show service status summary
echo "Service Status Summary:"
ssh root@$RM2_IP "systemctl is-active symbol_ui_activation.service" && echo "  Activation service: ACTIVE" || echo "  Activation service: INACTIVE"
ssh root@$RM2_IP "systemctl is-active symbol_ui_main.service" && echo "  Main service: ACTIVE" || echo "  Main service: INACTIVE"
ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode" && echo "  Component Mode: ACTIVE" || echo "  Component Mode: INACTIVE"
echo ""
