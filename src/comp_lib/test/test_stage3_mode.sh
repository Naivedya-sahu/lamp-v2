#!/bin/bash
# test_stage3_mode.sh - Mode Manager Test

set -e

RM2_IP="${1:-10.11.99.1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE_SCRIPT="$SCRIPT_DIR/../src/symbol_ui_mode.py"

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

echo "=========================================="
echo "Stage 3: Mode Manager Test"
echo "=========================================="
echo ""

# Deploy mode manager
echo -e "${BLUE}Deploying mode manager...${NC}"
scp -q "$MODE_SCRIPT" root@$RM2_IP:/opt/bin/symbol_ui_mode
ssh root@$RM2_IP chmod +x /opt/bin/symbol_ui_mode
echo -e "${GREEN}✓ Deployed${NC}"
echo ""

# Test 1: Activation
echo -e "${BLUE}Test 1: Mode Activation${NC}"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode activate" 2>&1 | grep -v "^$"
if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo -e "${GREEN}✓ Mode file created${NC}"
    echo "  Check RM2 bottom-right corner for green indicator"
    read -p "  Did green corner appear? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo -e "${GREEN}✓ Visual indicator works${NC}"
    fi
else
    echo -e "${RED}✗ Mode activation failed${NC}"
    exit 1
fi

# Test 2: Deactivation
echo ""
echo -e "${BLUE}Test 2: Mode Deactivation${NC}"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode deactivate" 2>&1 | grep -v "^$"
if ! ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo -e "${GREEN}✓ Mode file removed${NC}"
    read -p "  Did corner disappear? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo -e "${GREEN}✓ Visual cleanup works${NC}"
    fi
else
    echo -e "${RED}✗ Deactivation failed${NC}"
    exit 1
fi

# Test 3: Toggle
echo ""
echo -e "${BLUE}Test 3: Toggle Function${NC}"
ssh root@$RM2_IP "/opt/bin/symbol_ui_mode toggle" >/dev/null 2>&1
if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo -e "${GREEN}✓ Toggle activated${NC}"
    ssh root@$RM2_IP "/opt/bin/symbol_ui_mode toggle" >/dev/null 2>&1
    if ! ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
        echo -e "${GREEN}✓ Toggle deactivated${NC}"
    fi
else
    echo -e "${RED}✗ Toggle failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Stage 3: PASSED${NC}"
echo "=========================================="
echo ""
echo "Next: ./test_stage4_controller.sh $RM2_IP"
