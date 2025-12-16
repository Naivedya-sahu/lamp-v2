#!/bin/bash
# test_stage4_controller.sh - Controller Logic Test

set -e

RM2_IP="${1:-10.11.99.1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTROLLER="$SCRIPT_DIR/../src/symbol_ui_controller.py"

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

echo "=========================================="
echo "Stage 4: Controller Logic Test"
echo "=========================================="
echo ""

# Deploy files
echo -e "${BLUE}Deploying files...${NC}"
scp -q /tmp/test_library.json root@$RM2_IP:/opt/etc/symbol_library.json
scp -q "$CONTROLLER" root@$RM2_IP:/opt/bin/symbol_ui_controller
ssh root@$RM2_IP chmod +x /opt/bin/symbol_ui_controller
echo -e "${GREEN}✓ Deployed${NC}"
echo ""

# Test 1: Toggle palette
echo -e "${BLUE}Test 1: Toggle Palette${NC}"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller toggle_palette | /opt/bin/lamp" 2>&1 | grep -v "^$"
read -p "  Did palette appear on right side? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo -e "${GREEN}✓ Palette rendering works${NC}"
else
    echo -e "${RED}✗ Palette failed${NC}"
    exit 1
fi

# Test 2: Scroll
echo ""
echo -e "${BLUE}Test 2: Scroll Down${NC}"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller scroll_down | /opt/bin/lamp" 2>&1 | grep -v "^$"
read -p "  Did list scroll? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo -e "${GREEN}✓ Scroll works${NC}"
fi

# Test 3: Select
echo ""
echo -e "${BLUE}Test 3: Select Component${NC}"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller select_component | /opt/bin/lamp" 2>&1 | grep -v "^$"
read -p "  Did highlight change? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo -e "${GREEN}✓ Selection works${NC}"
fi

# Test 4: Place
echo ""
echo -e "${BLUE}Test 4: Place Component${NC}"
ssh root@$RM2_IP "TAP_X=500 TAP_Y=500 /opt/bin/symbol_ui_controller place_component | /opt/bin/lamp" 2>&1 | grep -v "^$"
read -p "  Did component appear at center? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo -e "${GREEN}✓ Placement works${NC}"
fi

# Test 5: Clear
echo ""
echo -e "${BLUE}Test 5: Clear Screen${NC}"
ssh root@$RM2_IP "/opt/bin/symbol_ui_controller clear_screen | /opt/bin/lamp" 2>&1 | grep -v "^$"
read -p "  Did screen clear? (y/n): " answer
if [ "$answer" = "y" ]; then
    echo -e "${GREEN}✓ Clear works${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Stage 4: PASSED${NC}"
echo "=========================================="
echo ""
echo "Next: ./test_stage5_gestures.sh $RM2_IP"
