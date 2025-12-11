#!/bin/bash
#
# Simple test: Draw 3 components at bottom right using hardcoded coordinates
# Pure bash - no Python, no bc, no external dependencies
#
# Usage: ./test_components_simple.sh [RM2_IP]

set -e

RM2_IP="${1:-10.11.99.1}"
LAMP="/opt/bin/lamp"

echo "=========================================="
echo "Component Test (Bottom Right)"
echo "=========================================="
echo "Target: $RM2_IP"
echo ""

# Test connection
echo "Testing connection..."
if ! ssh root@$RM2_IP "test -x $LAMP" 2>/dev/null; then
    echo "Error: Cannot connect or lamp not found"
    exit 1
fi
echo "✓ Connected"
echo ""

# Function to send lamp commands via SSH
lamp_cmd() {
    echo "$1" | ssh root@$RM2_IP "$LAMP"
}

echo "Drawing resistor (zigzag)..."
# Resistor at (900, 1650), scale 2x
# Zigzag pattern
lamp_cmd "pen down 900 1650"
lamp_cmd "pen move 940 1650"
lamp_cmd "pen move 950 1630"
lamp_cmd "pen move 970 1670"
lamp_cmd "pen move 990 1630"
lamp_cmd "pen move 1010 1670"
lamp_cmd "pen move 1030 1630"
lamp_cmd "pen move 1050 1670"
lamp_cmd "pen move 1060 1650"
lamp_cmd "pen move 1100 1650"
lamp_cmd "pen up"
echo "✓ Resistor drawn"

sleep 1

echo "Drawing capacitor (parallel plates)..."
# Capacitor at (900, 1730), scale 2x
# Left lead
lamp_cmd "pen line 900 1730 990 1730"
# Left plate
lamp_cmd "pen line 990 1690 990 1770"
# Right plate
lamp_cmd "pen line 1010 1690 1010 1770"
# Right lead
lamp_cmd "pen line 1010 1730 1100 1730"
echo "✓ Capacitor drawn"

sleep 1

echo "Drawing ground symbol..."
# Ground at (1050, 1650), scale 1.5x
# Vertical line
lamp_cmd "pen line 1050 1650 1050 1710"
# Horizontal lines (decreasing width)
lamp_cmd "pen line 1020 1710 1080 1710"
lamp_cmd "pen line 1028 1725 1072 1725"
lamp_cmd "pen line 1035 1740 1065 1740"
lamp_cmd "pen line 1042 1755 1058 1755"
echo "✓ Ground drawn"

echo ""
echo "✓ All components drawn!"
echo ""
echo "Components at bottom right corner:"
echo "  - Resistor: (900, 1650)"
echo "  - Capacitor: (900, 1730)"
echo "  - Ground: (1050, 1650)"
echo ""
echo "Press Enter to clear..."
read

echo "Clearing area..."
lamp_cmd "eraser fill 850 1600 1350 1850 10"
echo "✓ Cleared"

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "This script works as fallback when Python fails."
echo "All drawing done with direct lamp commands via SSH."
