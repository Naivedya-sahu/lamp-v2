#!/bin/bash
#
# deploy_comp_lib.sh - Deploy complete Component Library UI system (BASH VERSION)
# No Python3 required - pure bash + jq for RM2 compatibility
#

set -e

RM2_IP="${1:-10.11.99.1}"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Component Library UI Deployment"
echo "=========================================="
echo -e "${BLUE}Target: $RM2_IP${NC}"
echo -e "${BLUE}Version: Bash (no Python3 required)${NC}"
echo ""

# Step 1: Connectivity check
echo -e "${BLUE}Step 1: Testing Connection...${NC}"
if ! ssh -o ConnectTimeout=5 root@$RM2_IP "echo OK" >/dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to $RM2_IP${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Step 2: Check/install jq
echo -e "${BLUE}Step 2: Checking Dependencies...${NC}"
if ! ssh root@$RM2_IP "command -v jq >/dev/null 2>&1"; then
    echo -e "${YELLOW}jq not found - installing via opkg...${NC}"
    ssh root@$RM2_IP "opkg update && opkg install jq" || {
        echo -e "${RED}✗ Failed to install jq${NC}"
        echo "Install manually: ssh root@$RM2_IP 'opkg update && opkg install jq'"
        exit 1
    }
    echo -e "${GREEN}✓ jq installed${NC}"
else
    echo -e "${GREEN}✓ jq available${NC}"
fi
echo ""

# Step 3: Build library
echo -e "${BLUE}Step 3: Building Library...${NC}"
if [ ! -f "/tmp/test_library.json" ]; then
    echo "Building library from assets..."
    python3 build_component_library.py \
        ../../assets/components \
        ../../assets/font \
        /tmp/test_library.json
fi

if [ ! -f "/tmp/test_library.json" ]; then
    echo -e "${RED}✗ Library build failed${NC}"
    exit 1
fi

# Check library size
LIBRARY_SIZE=$(du -h /tmp/test_library.json | cut -f1)
echo -e "${GREEN}✓ Library built ($LIBRARY_SIZE)${NC}"
echo ""

# Step 4: Deploy files
echo -e "${BLUE}Step 4: Deploying Files...${NC}"
ssh root@$RM2_IP "mkdir -p /opt/bin /opt/etc"

# Library
scp -q /tmp/test_library.json root@$RM2_IP:/opt/etc/symbol_library.json
echo -e "${GREEN}✓ symbol_library.json${NC}"

# Mode manager (BASH)
scp -q symbol_ui_mode.sh root@$RM2_IP:/opt/bin/symbol_ui_mode
ssh root@$RM2_IP "chmod +x /opt/bin/symbol_ui_mode"
echo -e "${GREEN}✓ symbol_ui_mode (bash)${NC}"

# Controller (BASH)
scp -q symbol_ui_controller.sh root@$RM2_IP:/opt/bin/symbol_ui_controller
ssh root@$RM2_IP "chmod +x /opt/bin/symbol_ui_controller"
echo -e "${GREEN}✓ symbol_ui_controller (bash)${NC}"

# Configs
scp -q symbol_ui_activation.conf root@$RM2_IP:/opt/etc/
scp -q symbol_ui_main.conf root@$RM2_IP:/opt/etc/
echo -e "${GREEN}✓ Configuration files${NC}"

# Services
scp -q symbol_ui_activation.service root@$RM2_IP:/etc/systemd/system/
scp -q symbol_ui_main.service root@$RM2_IP:/etc/systemd/system/
echo -e "${GREEN}✓ Systemd services${NC}"
echo ""

# Step 5: Setup services
echo -e "${BLUE}Step 5: Configuring Services...${NC}"
ssh root@$RM2_IP "systemctl daemon-reload"
ssh root@$RM2_IP "systemctl enable symbol_ui_activation.service"
ssh root@$RM2_IP "systemctl start symbol_ui_activation.service"
sleep 2

if ssh root@$RM2_IP "systemctl is-active --quiet symbol_ui_activation.service"; then
    echo -e "${GREEN}✓ Activation service running${NC}"
else
    echo -e "${YELLOW}⚠ Service may not be running${NC}"
    echo "Check logs: ssh root@$RM2_IP journalctl -u symbol_ui_activation.service -n 20"
fi
echo ""

# Step 6: Verification
echo -e "${BLUE}Step 6: Verification...${NC}"
FILES=(
    "/opt/etc/symbol_library.json"
    "/opt/bin/symbol_ui_mode"
    "/opt/bin/symbol_ui_controller"
    "/opt/etc/symbol_ui_activation.conf"
    "/opt/etc/symbol_ui_main.conf"
)

for file in "${FILES[@]}"; do
    if ssh root@$RM2_IP "test -f $file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file"
    fi
done
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "System Type: Bash (no Python3 dependency)"
echo "Dependencies: jq (for JSON parsing)"
echo ""
echo "Usage:"
echo "  1. On RM2: 5-finger tap to activate Component Mode"
echo "  2. Green corner appears (bottom-right 34×34px)"
echo "  3. 4-finger tap to show palette"
echo "  4. 3-finger swipes to scroll"
echo "  5. 2-finger tap in palette to select"
echo "  6. 2-finger tap in canvas to place"
echo "  7. 4-finger swipe down to exit mode"
echo ""
echo "Troubleshooting:"
echo "  Status:  ssh root@$RM2_IP /opt/bin/symbol_ui_mode status"
echo "  Logs:    ssh root@$RM2_IP journalctl -u symbol_ui_activation.service -f"
echo "  Restart: ssh root@$RM2_IP systemctl restart symbol_ui_activation.service"
echo ""
echo "Known Limitations:"
echo "  - No font rendering yet (component names shown as comments)"
echo "  - Simplified coordinate transforms"
echo "  - Requires jq package (installed automatically)"
echo ""
