#!/bin/bash
# test_stage5_gestures.sh - Gesture Integration Test

set -e

RM2_IP="${1:-10.11.99.1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/../config"

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo "=========================================="
echo "Stage 5: Gesture Integration Test"
echo "=========================================="
echo ""

# Deploy configs
echo -e "${BLUE}Deploying gesture configs...${NC}"
scp -q "$CONFIG_DIR/symbol_ui_activation.conf" root@$RM2_IP:/opt/etc/
scp -q "$CONFIG_DIR/symbol_ui_main.conf" root@$RM2_IP:/opt/etc/
echo -e "${GREEN}✓ Deployed${NC}"
echo ""

# Start activation service manually
echo -e "${BLUE}Starting activation listener...${NC}"
ssh root@$RM2_IP "nohup /opt/bin/genie_lamp /opt/etc/symbol_ui_activation.conf >/dev/null 2>&1 &"
sleep 2
echo -e "${GREEN}✓ Running${NC}"
echo ""

echo "=========================================="
echo "MANUAL GESTURE TESTS"
echo "=========================================="
echo ""
echo -e "${YELLOW}Test 1: Activation Gesture${NC}"
echo "  1. Place all 5 fingers on RM2 screen"
echo "  2. Tap simultaneously"
echo "  3. Green corner indicator should appear"
echo ""
read -p "Press Enter after trying gesture..."

if ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo -e "${GREEN}✓ Activation gesture works${NC}"
    echo ""
    
    echo -e "${YELLOW}Test 2: UI Gestures${NC}"
    echo "  1. Tap with 4 fingers anywhere"
    echo "  2. Palette should appear on right"
    echo ""
    read -p "Press Enter after trying..."
    
    echo ""
    echo -e "${YELLOW}Test 3: Deactivation${NC}"
    echo "  1. Swipe down with 4 fingers"
    echo "  2. Everything should clear"
    echo "  3. Green corner disappears"
    echo ""
    read -p "Press Enter after trying..."
    
    if ! ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
        echo -e "${GREEN}✓ Deactivation gesture works${NC}"
    else
        echo -e "${RED}✗ Still in component mode${NC}"
        echo "  Manually deactivate: ssh root@$RM2_IP /opt/bin/symbol_ui_mode deactivate"
    fi
else
    echo -e "${RED}✗ Activation gesture failed${NC}"
    echo "  Check: genie_lamp running, config correct"
fi

# Cleanup
echo ""
echo -e "${BLUE}Stopping test services...${NC}"
ssh root@$RM2_IP "pkill -f genie_lamp" 2>/dev/null || true

echo ""
echo "=========================================="
echo -e "${GREEN}Stage 5: COMPLETE${NC}"
echo "=========================================="
echo ""
echo "If all gestures worked, proceed to stage 6"
echo "Next: ./test_stage6_full.sh $RM2_IP"
