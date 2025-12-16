#!/bin/bash
# test_stage2_connectivity.sh - Test RM2 connection and lamp/genie_lamp

set -e

RM2_IP="${1:-10.11.99.1}"

echo "=========================================="
echo "Stage 2: RM2 Connectivity Test"
echo "=========================================="
echo "Target: $RM2_IP"
echo ""

# Test 1: SSH
echo "Test 1: SSH Connection"
if ssh -o ConnectTimeout=5 root@$RM2_IP "echo OK" >/dev/null 2>&1; then
    echo "✓ SSH works"
else
    echo "✗ SSH failed - check IP and SSH enabled"
    exit 1
fi
echo ""

# Test 2: Lamp
echo "Test 2: Lamp Executable"
if ssh root@$RM2_IP "test -x /opt/bin/lamp"; then
    echo "✓ Lamp exists"
    echo "  Testing render (check RM2 screen)..."
    ssh root@$RM2_IP 'echo "pen rectangle 500 500 900 900" | /opt/bin/lamp'
    read -p "  Did rectangle appear? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "✓ Lamp renders"
        ssh root@$RM2_IP 'echo "eraser clear 500 500 900 900" | /opt/bin/lamp'
    else
        echo "✗ Lamp rendering failed"
        exit 1
    fi
else
    echo "✗ Lamp not found at /opt/bin/lamp"
    exit 1
fi
echo ""

# Test 3: Genie_lamp
echo "Test 3: Genie_lamp Executable"
if ssh root@$RM2_IP "test -x /opt/bin/genie_lamp"; then
    echo "✓ Genie_lamp exists"
else
    echo "✗ Genie_lamp not found"
    echo "  Build: cd src/genie_lamp && ./build.sh"
    exit 1
fi
echo ""

echo "=========================================="
echo "Stage 2: PASSED ✓"
echo "=========================================="
echo "Ready for Stage 3: Mode Manager Test"
