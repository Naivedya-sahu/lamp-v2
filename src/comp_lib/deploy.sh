#!/bin/bash
#
# deploy.sh - One-command deployment for Component Library System
# Builds library, deploys all files, sets up services
#
# Usage: ./deploy.sh [RM2_IP]
#

set -e

RM2_IP="${1:-10.11.99.1}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
SRC_DIR="$SCRIPT_DIR/src"
CONFIG_DIR="$SCRIPT_DIR/config"
SERVICE_DIR="$SCRIPT_DIR/services"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=========================================="
echo "Component Library System Deployment"
echo "=========================================="
echo ""
echo -e "${BLUE}Target: $RM2_IP${NC}"
echo ""

# Check SSH
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=5 root@$RM2_IP "echo OK" >/dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to $RM2_IP${NC}"
    echo "Check: RM2 powered on, SSH enabled, correct IP"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Step 1: Build library
echo "=========================================="
echo "Step 1: Building Component Library"
echo "=========================================="
echo ""

if [ ! -d "$PROJECT_ROOT/assets/components" ] || [ ! -d "$PROJECT_ROOT/assets/font" ]; then
    echo -e "${RED}Error: Assets directories not found${NC}"
    echo "Expected: $PROJECT_ROOT/assets/components"
    echo "          $PROJECT_ROOT/assets/font"
    exit 1
fi

echo -e "${BLUE}Building library...${NC}"
python3 "$BUILD_DIR/build_library.py" \
    "$PROJECT_ROOT/assets/components" \
    "$PROJECT_ROOT/assets/font" \
    "$SCRIPT_DIR/symbol_library.json"

if [ ! -f "$SCRIPT_DIR/symbol_library.json" ]; then
    echo -e "${RED}Error: Failed to build library${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Library built${NC}"
echo ""

# Step 2: Deploy files
echo "=========================================="
echo "Step 2: Deploying Files to RM2"
echo "=========================================="
echo ""

echo -e "${BLUE}Creating directories...${NC}"
ssh root@$RM2_IP "mkdir -p /opt/bin /opt/etc"

echo -e "${BLUE}Deploying library...${NC}"
scp -q "$SCRIPT_DIR/symbol_library.json" root@$RM2_IP:/opt/etc/
echo -e "${GREEN}✓ symbol_library.json${NC}"

echo -e "${BLUE}Deploying mode manager...${NC}"
scp -q "$SRC_DIR/symbol_ui_mode.py" root@$RM2_IP:/opt/bin/symbol_ui_mode
ssh root@$RM2_IP "chmod +x /opt/bin/symbol_ui_mode"
echo -e "${GREEN}✓ symbol_ui_mode${NC}"

echo -e "${BLUE}Deploying controller...${NC}"
scp -q "$SRC_DIR/symbol_ui_controller.py" root@$RM2_IP:/opt/bin/symbol_ui_controller
ssh root@$RM2_IP "chmod +x /opt/bin/symbol_ui_controller"
echo -e "${GREEN}✓ symbol_ui_controller${NC}"

echo -e "${BLUE}Deploying gesture configs...${NC}"
scp -q "$CONFIG_DIR/symbol_ui_activation.conf" root@$RM2_IP:/opt/etc/
scp -q "$CONFIG_DIR/symbol_ui_main.conf" root@$RM2_IP:/opt/etc/
echo -e "${GREEN}✓ gesture configs${NC}"

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

if ! ssh root@$RM2_IP "test -x /opt/bin/genie_lamp" 2>/dev/null; then
    echo -e "${YELLOW}Warning: genie_lamp not found${NC}"
    echo "  The system requires genie_lamp to function"
    echo "  Build: cd ../genie_lamp && ./build.sh"
fi

if ! ssh root@$RM2_IP "test -x /opt/bin/lamp" 2>/dev/null; then
    echo -e "${YELLOW}Warning: lamp not found${NC}"
    echo "  The system requires lamp to function"
    echo "  Build: cd ../../resources/rmkit && make lamp"
fi

echo ""

# Step 3: Setup services
echo "=========================================="
echo "Step 3: Setting Up Systemd Services"
echo "=========================================="
echo ""

echo -e "${BLUE}Deploying service files...${NC}"
scp -q "$SERVICE_DIR/symbol_ui_activation.service" root@$RM2_IP:/etc/systemd/system/
scp -q "$SERVICE_DIR/symbol_ui_main.service" root@$RM2_IP:/etc/systemd/system/

echo -e "${BLUE}Enabling services...${NC}"
ssh root@$RM2_IP "systemctl daemon-reload"
ssh root@$RM2_IP "systemctl enable symbol_ui_activation.service"
ssh root@$RM2_IP "systemctl start symbol_ui_activation.service"

sleep 2

if ssh root@$RM2_IP "systemctl is-active --quiet symbol_ui_activation.service"; then
    echo -e "${GREEN}✓ Activation service running${NC}"
else
    echo -e "${YELLOW}Warning: Service may not be running${NC}"
    echo "  Check: ssh root@$RM2_IP systemctl status symbol_ui_activation.service"
fi

echo ""

# Step 4: Verification
echo "=========================================="
echo "Step 4: Verification"
echo "=========================================="
echo ""

check_file() {
    if ssh root@$RM2_IP "test -f $1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

echo -e "${BLUE}Checking installed files:${NC}"
check_file "/opt/etc/symbol_library.json"
check_file "/opt/bin/symbol_ui_mode"
check_file "/opt/bin/symbol_ui_controller"
check_file "/opt/etc/symbol_ui_activation.conf"
check_file "/opt/etc/symbol_ui_main.conf"
check_file "/etc/systemd/system/symbol_ui_activation.service"
check_file "/etc/systemd/system/symbol_ui_main.service"

echo ""

# Summary
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "System Status:"

if [ -f "$SCRIPT_DIR/symbol_library.json" ]; then
    if command -v jq >/dev/null 2>&1; then
        comp=$(jq -r '.stats.component_count' "$SCRIPT_DIR/symbol_library.json" 2>/dev/null)
        font=$(jq -r '.stats.glyph_count' "$SCRIPT_DIR/symbol_library.json" 2>/dev/null)
        echo "  Components: ${comp:-N/A}"
        echo "  Font glyphs: ${font:-N/A}"
    fi
fi

service_status=$(ssh root@$RM2_IP 'systemctl is-active symbol_ui_activation.service' 2>/dev/null || echo "unknown")
echo "  Activation service: $service_status"
echo ""

echo "Usage:"
echo "  1. ${BLUE}5-finger tap${NC} anywhere → Activate component mode"
echo "  2. Green corner appears (bottom-right)"
echo "  3. ${BLUE}4-finger tap${NC} → Show component palette"
echo "  4. Use gestures to navigate and place components"
echo "  5. ${BLUE}4-finger swipe down${NC} → Deactivate mode"
echo ""

echo "Troubleshooting:"
echo "  View logs:  ssh root@$RM2_IP journalctl -u symbol_ui_activation.service -f"
echo "  Restart:    ssh root@$RM2_IP systemctl restart symbol_ui_activation.service"
echo "  Status:     ssh root@$RM2_IP systemctl status symbol_ui_activation.service"
echo "  Mode check: ssh root@$RM2_IP /opt/bin/symbol_ui_mode status"
echo ""

echo "Documentation: See README.md for complete gesture guide"
echo ""
