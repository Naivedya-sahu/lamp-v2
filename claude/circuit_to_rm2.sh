#!/bin/bash
#
# Circuit to reMarkable 2 Pipeline
# Complete 4-layer system for drawing circuits from netlists
#
# Usage: ./circuit_to_rm2.sh <netlist_file> [scale] [RM2_IP] [optimize]
#

set -e

# Configuration
COMPONENTS_DIR="${COMPONENTS_DIR:-./components}"
LIBRARY_FILE="./component_library.json"
NETLIST_FILE="$1"
SCALE="${2:-auto}"
RM2_IP="${3:-10.11.99.1}"
OPTIMIZE="${4:-raw}"  # 'optimize' or 'raw'
LAMP="/opt/bin/lamp"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Usage check
if [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ -z "$NETLIST_FILE" ]; then
    cat << 'EOF'
Circuit to reMarkable 2 - Complete Pipeline

Usage: ./circuit_to_rm2.sh <netlist_file> [scale] [RM2_IP] [optimize]

Arguments:
  netlist_file    LTSpice-format netlist file (required)
  scale          Scale factor (default: auto)
  RM2_IP         reMarkable 2 IP (default: 10.11.99.1)
  optimize       'optimize' or 'raw' (default: raw)

Example netlist format (save as circuit.net):
  * Simple RC Circuit
  V1 N1 0 5V
  R1 N1 N2 10k
  C1 N2 0 100nF

Examples:
  ./circuit_to_rm2.sh circuit.net              # Auto-scale, raw commands
  ./circuit_to_rm2.sh circuit.net 2.0          # 2x scale
  ./circuit_to_rm2.sh circuit.net auto 10.11.99.1 optimize  # Optimized

Pipeline Layers:
  Layer 1: Component Library Builder (SVG → pen commands + pins)
  Layer 2: Netlist Parser (netlist → circuit graph)
  Layer 3: Circuit Placer (auto-placement + routing)
  Layer 4: Transmission (send to reMarkable 2)

EOF
    exit 0
fi

echo "=========================================="
echo "Circuit to reMarkable 2 Pipeline"
echo "=========================================="
echo -e "${BLUE}Netlist:${NC} $NETLIST_FILE"
echo -e "${BLUE}Scale:${NC} ${SCALE}"
echo -e "${BLUE}Target:${NC} $RM2_IP"
echo -e "${BLUE}Mode:${NC} $OPTIMIZE"
echo ""

# Check if netlist exists
if [ ! -f "$NETLIST_FILE" ]; then
    echo -e "${RED}Error: Netlist file not found: $NETLIST_FILE${NC}"
    exit 1
fi

# Check if components directory exists
if [ ! -d "$COMPONENTS_DIR" ]; then
    echo -e "${RED}Error: Components directory not found: $COMPONENTS_DIR${NC}"
    exit 1
fi

# Test SSH connection
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh root@$RM2_IP "test -x $LAMP" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to $RM2_IP or lamp not found${NC}"
    echo "Please check:"
    echo "  1. RM2 is connected (USB: 10.11.99.1 or WiFi IP)"
    echo "  2. lamp binary is deployed to $LAMP"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# ============================================================
# LAYER 1: Build Component Library (if not exists or stale)
# ============================================================
REBUILD_LIBRARY=0

if [ ! -f "$LIBRARY_FILE" ]; then
    echo -e "${CYAN}[Layer 1] Component library not found${NC}"
    REBUILD_LIBRARY=1
elif [ "$COMPONENTS_DIR" -nt "$LIBRARY_FILE" ]; then
    echo -e "${CYAN}[Layer 1] Components directory updated${NC}"
    REBUILD_LIBRARY=1
fi

if [ $REBUILD_LIBRARY -eq 1 ]; then
    echo -e "${BLUE}Building component library...${NC}"
    python3 ./component_library_builder.py "$COMPONENTS_DIR" "$LIBRARY_FILE"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Component library build failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Component library ready${NC}"
else
    echo -e "${GREEN}✓ Component library up to date${NC}"
fi
echo ""

# ============================================================
# LAYER 2 & 3: Parse Netlist, Place Circuit, Render
# ============================================================
echo -e "${CYAN}[Layer 2 & 3] Parsing netlist and placing circuit...${NC}"

SCALE_ARG=""
if [ "$SCALE" != "auto" ]; then
    SCALE_ARG="$SCALE"
fi

PEN_COMMANDS=$(python3 circuit_placer.py "$NETLIST_FILE" "$LIBRARY_FILE" $SCALE_ARG 2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Circuit placement failed${NC}"
    echo "$PEN_COMMANDS"
    exit 1
fi

# Extract only pen commands (skip comments and summary)
PEN_COMMANDS_CLEAN=$(echo "$PEN_COMMANDS" | grep -E "^(pen|finger|sleep)" || true)

if [ -z "$PEN_COMMANDS_CLEAN" ]; then
    echo -e "${RED}✗ No pen commands generated${NC}"
    echo "$PEN_COMMANDS"
    exit 1
fi

# Count commands
CMD_COUNT=$(echo "$PEN_COMMANDS_CLEAN" | wc -l)
echo -e "${GREEN}✓ Generated $CMD_COUNT pen commands${NC}"
echo ""

# Show summary info
echo "$PEN_COMMANDS" | grep -E "^(Circuit|Placed|Routed|Scale|Output)" || true
echo ""

# ============================================================
# LAYER 4: Optimize (if requested) and Send to RM2
# ============================================================
if [ "$OPTIMIZE" = "optimize" ]; then
    echo -e "${CYAN}[Layer 4] Optimizing pen commands...${NC}"
    
    # Simple optimization: merge consecutive moves, remove redundant ups/downs
    # TODO: Implement actual optimization
    PEN_COMMANDS_FINAL="$PEN_COMMANDS_CLEAN"
    echo -e "${YELLOW}⚠ Optimization not yet implemented, using raw commands${NC}"
else
    PEN_COMMANDS_FINAL="$PEN_COMMANDS_CLEAN"
    echo -e "${BLUE}[Layer 4] Using raw pen commands${NC}"
fi
echo ""

# Preview first/last commands
echo -e "${YELLOW}Preview (first 5 commands):${NC}"
echo "$PEN_COMMANDS_FINAL" | head -5
echo "..."
echo ""

# Send to reMarkable 2
echo -e "${BLUE}Sending to reMarkable 2...${NC}"
echo "$PEN_COMMANDS_FINAL" | ssh root@$RM2_IP "$LAMP"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Circuit drawn successfully!${NC}"
    echo ""
    echo "Commands sent: $CMD_COUNT"
    echo "Check your reMarkable 2 screen"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Error sending commands${NC}"
    exit 1
fi

echo "=========================================="
echo -e "${GREEN}Pipeline Complete${NC}"
echo "=========================================="
