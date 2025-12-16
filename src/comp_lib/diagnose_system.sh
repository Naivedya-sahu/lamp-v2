#!/bin/bash
# diagnose_system.sh - Comprehensive system diagnostic

set -e

RM2_IP="${1:-10.11.99.1}"

echo "=========================================="
echo "Component Library System Diagnostics"
echo "=========================================="
echo "Target: $RM2_IP"
echo ""

# Section 1: Connectivity
echo "=== 1. CONNECTIVITY ==="
if ssh -o ConnectTimeout=5 root@$RM2_IP "echo OK" >/dev/null 2>&1; then
    echo "✓ SSH connection works"
else
    echo "✗ SSH connection failed"
    exit 1
fi
echo ""

# Section 2: Required Binaries
echo "=== 2. REQUIRED BINARIES ==="
check_binary() {
    local name=$1
    local path=$2
    if ssh root@$RM2_IP "test -x $path"; then
        echo "✓ $name exists at $path"
        return 0
    else
        echo "✗ $name missing at $path"
        return 1
    fi
}

check_binary "lamp" "/opt/bin/lamp"
check_binary "genie_lamp" "/opt/bin/genie_lamp"
check_binary "symbol_ui_mode" "/opt/bin/symbol_ui_mode"
check_binary "symbol_ui_controller" "/opt/bin/symbol_ui_controller"
echo ""

# Section 3: Configuration Files
echo "=== 3. CONFIGURATION FILES ==="
check_file() {
    local name=$1
    local path=$2
    if ssh root@$RM2_IP "test -f $path"; then
        size=$(ssh root@$RM2_IP "du -h $path | cut -f1")
        echo "✓ $name exists ($size)"
        return 0
    else
        echo "✗ $name missing"
        return 1
    fi
}

check_file "Library" "/opt/etc/symbol_library.json"
check_file "Activation config" "/opt/etc/symbol_ui_activation.conf"
check_file "Main config" "/opt/etc/symbol_ui_main.conf"
echo ""

# Section 4: Service Files
echo "=== 4. SYSTEMD SERVICE FILES ==="
check_file "Activation service" "/etc/systemd/system/symbol_ui_activation.service"
check_file "Main service" "/etc/systemd/system/symbol_ui_main.service"
echo ""

# Section 5: Dependencies
echo "=== 5. DEPENDENCIES ==="
if ssh root@$RM2_IP "command -v jq >/dev/null 2>&1"; then
    version=$(ssh root@$RM2_IP "jq --version" 2>/dev/null || echo "unknown")
    echo "✓ jq installed ($version)"
else
    echo "✗ jq not installed"
    echo "  Install: ssh root@$RM2_IP 'opkg update && opkg install jq'"
fi

if ssh root@$RM2_IP "command -v systemctl >/dev/null 2>&1"; then
    echo "✓ systemctl available"
else
    echo "✗ systemctl not available"
fi
echo ""

# Section 6: Services Status
echo "=== 6. SERVICE STATUS ==="
echo "Activation service:"
if ssh root@$RM2_IP "systemctl is-active --quiet symbol_ui_activation.service" 2>/dev/null; then
    echo "  ✓ ACTIVE"
else
    echo "  ✗ INACTIVE"
fi

echo "Main service:"
if ssh root@$RM2_IP "systemctl is-active --quiet symbol_ui_main.service" 2>/dev/null; then
    echo "  ✓ ACTIVE"
else
    echo "  ✗ INACTIVE (expected when Component Mode not active)"
fi
echo ""

# Section 7: Running Processes
echo "=== 7. RUNNING PROCESSES ==="
echo "genie_lamp processes:"
genie_count=$(ssh root@$RM2_IP "ps aux | grep -v grep | grep genie_lamp | wc -l")
if [ "$genie_count" -gt 0 ]; then
    echo "  Found $genie_count process(es)"
    ssh root@$RM2_IP "ps aux | grep -v grep | grep genie_lamp" | sed 's/^/  /'
else
    echo "  ✗ No genie_lamp processes running"
fi
echo ""

# Section 8: Mode State
echo "=== 8. MODE STATE ==="
if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo "✓ Component Mode: ACTIVE"
else
    echo "  Component Mode: INACTIVE (normal)"
fi

if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_state.json"; then
    echo "✓ State file exists"
else
    echo "  State file: Not created yet (normal)"
fi
echo ""

# Section 9: Test lamp
echo "=== 9. TEST LAMP RENDERING ==="
echo "Drawing test rectangle at (100,100)..."
ssh root@$RM2_IP 'echo "pen rectangle 100 100 200 200" | /opt/bin/lamp' 2>&1 | head -3
read -p "Did rectangle appear on RM2 screen? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo "✓ lamp rendering works"
    ssh root@$RM2_IP 'echo "eraser clear 100 100 200 200" | /opt/bin/lamp' >/dev/null 2>&1
else
    echo "⚠ lamp rendering may not be working"
fi
echo ""

# Section 10: Test mode manager
echo "=== 10. TEST MODE MANAGER ==="
echo "Testing mode activation..."
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode activate" 2>&1 | head -5
sleep 1

if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo "✓ Mode manager works"
    read -p "Green corner visible in bottom-right? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "✓ Visual indicator works"
    else
        echo "⚠ Visual indicator may not be visible"
    fi
    
    # Cleanup
    ssh root@$RM2_IP "/opt/bin/symbol_ui_mode deactivate" >/dev/null 2>&1
else
    echo "✗ Mode manager failed"
fi
echo ""

# Section 11: Test controller (if jq available)
echo "=== 11. TEST CONTROLLER ==="
if ssh root@$RM2_IP "command -v jq >/dev/null 2>&1"; then
    echo "Testing controller..."
    ssh root@$RM2_IP "/opt/bin/symbol_ui_controller toggle_palette" 2>&1 | head -3
    read -p "Did palette border appear? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "✓ Controller works"
        ssh root@$RM2_IP "/opt/bin/symbol_ui_controller clear_screen" >/dev/null 2>&1
    else
        echo "⚠ Controller may not be working"
    fi
else
    echo "⚠ Skipped (jq not installed)"
fi
echo ""

# Section 12: Summary
echo "=========================================="
echo "DIAGNOSTIC SUMMARY"
echo "=========================================="
echo ""

# Count issues
issues=0

ssh root@$RM2_IP "test -x /opt/bin/lamp" || ((issues++))
ssh root@$RM2_IP "test -x /opt/bin/genie_lamp" || ((issues++))
ssh root@$RM2_IP "test -x /opt/bin/symbol_ui_mode" || ((issues++))
ssh root@$RM2_IP "test -x /opt/bin/symbol_ui_controller" || ((issues++))
ssh root@$RM2_IP "test -f /opt/etc/symbol_library.json" || ((issues++))
ssh root@$RM2_IP "command -v jq >/dev/null 2>&1" || ((issues++))

if [ $issues -eq 0 ]; then
    echo "✓ All components present"
    echo "✓ System appears ready"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./test_stage5_service_setup.sh"
    echo "  2. Or: ./deploy_comp_lib.sh (full deployment)"
else
    echo "⚠ Found $issues issue(s)"
    echo ""
    echo "Recommended actions:"
    if ! ssh root@$RM2_IP "command -v jq >/dev/null 2>&1"; then
        echo "  - Install jq: ssh root@$RM2_IP 'opkg update && opkg install jq'"
    fi
    if ! ssh root@$RM2_IP "test -f /opt/etc/symbol_library.json"; then
        echo "  - Deploy library: Run ./test_stage1_library_build.sh first"
    fi
    echo "  - Run full deployment: ./deploy_comp_lib.sh"
fi
echo ""
