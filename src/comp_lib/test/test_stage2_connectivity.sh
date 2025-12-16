#!/bin/bash
# test_stage2_connectivity.sh - RM2 Connectivity Test

set -e

RM2_IP="${1:-10.11.99.1}"

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

echo "=========================================="
echo "Stage 2: RM2 Connectivity Test"
echo "=========================================="
echo "Target: $RM2_IP"
echo ""

# Test 1: SSH
echo -e "${BLUE}Test 1: SSH Connection${NC}"
if ssh -o ConnectTimeout=5 root@$RM2_IP "echo OK" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH works${NC}"
else
    echo -e "${RED}✗ SSH failed${NC}"
    echo "  Check: RM2 powered on, SSH enabled, correct IP"
    exit 1
fi

# Test 2: Lamp
echo -e "${BLUE}Test 2: Lamp Executable${NC}"
if ssh root@$RM2_IP "test -x /opt/bin/lamp"; then
    echo -e "${GREEN}✓ Lamp exists${NC}"
    echo "  Testing rendering..."
    ssh root@$RM2_IP 'echo "pen rectangle 500 500 900 900" | /opt/bin/lamp'
    read -p "  Did rectangle appear on RM2? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo -e "${GREEN}✓ Lamp renders${NC}"
        ssh root@$RM2_IP 'echo "eraser clear 500 500 900 900" | /opt/bin/lamp'
    else
        echo -e "${RED}✗ Lamp rendering failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Lamp not found at /opt/bin/lamp${NC}"
    exit 1
fi

# Test 3: Genie
echo -e "${BLUE}Test 3: Genie_lamp Executable${NC}"
if ssh root@$RM2_IP "test -x /opt/bin/genie_lamp"; then
    echo -e "${GREEN}✓ Genie_lamp exists${NC}"
else
    echo -e "${RED}✗ Genie_lamp not found${NC}"
    echo "  Build: cd src/genie_lamp && ./build.sh"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Stage 2: PASSED${NC}"
echo "=========================================="
echo ""
echo "Next: ./test_stage3_mode.sh $RM2_IP"
