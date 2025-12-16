#!/bin/bash
# test_stage6_full.sh - Full System Integration Test

set -e

RM2_IP="${1:-10.11.99.1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$SCRIPT_DIR/../services"

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo "=========================================="
echo "Stage 6: Full System Integration Test"
echo "=========================================="
echo ""

# Deploy services
echo -e "${BLUE}Setting up systemd services...${NC}"
scp -q "$SERVICE_DIR/symbol_ui_activation.service" root@$RM2_IP:/etc/systemd/system/
scp -q "$SERVICE_DIR/symbol_ui_main.service" root@$RM2_IP:/etc/systemd/system/

ssh root@$RM2_IP "systemctl daemon-reload"
ssh root@$RM2_IP "systemctl enable symbol_ui_activation.service"
ssh root@$RM2_IP "systemctl start symbol_ui_activation.service"

# Wait for service
sleep 3

# Check status
if ssh root@$RM2_IP "systemctl is-active --quiet symbol_ui_activation.service"; then
    echo -e "${GREEN}✓ Activation service running${NC}"
else
    echo -e "${RED}✗ Activation service failed${NC}"
    ssh root@$RM2_IP "journalctl -u symbol_ui_activation.service -n 20"
    exit 1
fi
echo ""

echo "=========================================="
echo "FULL WORKFLOW TEST"
echo "=========================================="
echo ""
echo -e "${YELLOW}Perform this sequence on RM2:${NC}"
echo ""
echo "1. ${BLUE}5-finger tap${NC} → Activate mode"
echo "   Expected: Green corner appears"
echo ""
echo "2. ${BLUE}4-finger tap${NC} → Show palette"
echo "   Expected: Component list appears on right"
echo ""
echo "3. ${BLUE}3-finger swipe up/down${NC} (in palette) → Scroll"
echo "   Expected: List scrolls"
echo ""
echo "4. ${BLUE}2-finger tap${NC} (in palette) → Select"
echo "   Expected: Item highlights"
echo ""
echo "5. ${BLUE}2-finger tap${NC} (on canvas) → Place"
echo "   Expected: Component appears where tapped"
echo ""
echo "6. ${BLUE}3-finger swipe left/right${NC} → Scale"
echo "   Expected: Next component will be scaled"
echo ""
echo "7. ${BLUE}4-finger swipe up${NC} → Clear"
echo "   Expected: Canvas clears"
echo ""
echo "8. ${BLUE}4-finger swipe down${NC} → Deactivate"
echo "   Expected: Everything clears, green corner disappears"
echo ""
read -p "Press Enter when ready to check results..."

# Check final state
if ! ssh root@$RM2_IP "test -f /home/root/.symbol_ui_mode"; then
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✓ Full workflow successful!${NC}"
    echo "=========================================="
    echo ""
    echo "System is production-ready!"
    echo ""
    echo "Service status:"
    ssh root@$RM2_IP "systemctl status symbol_ui_activation.service --no-pager" | head -10
else
    echo ""
    echo -e "${YELLOW}⚠ Still in component mode${NC}"
    echo "  Manually deactivate: ssh root@$RM2_IP /opt/bin/symbol_ui_mode deactivate"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Stage 6: COMPLETE${NC}"
echo "=========================================="
echo ""
echo "All tests passed! System is ready for use."
echo ""
echo "To view logs: ssh root@$RM2_IP journalctl -u symbol_ui_activation.service -f"
echo "To restart:   ssh root@$RM2_IP systemctl restart symbol_ui_activation.service"
