#!/bin/bash
#
# Component test with labels - Bottom right display area
# Tests both drawing and text rendering
#
# Usage: ./test_components_labeled.sh [RM2_IP]

set -e

RM2_IP="${1:-10.11.99.1}"
LAMP="/opt/bin/lamp"

echo "=========================================="
echo "Component Test with Labels"
echo "=========================================="
echo "Target: $RM2_IP"
echo ""

# Helper function
lamp_cmd() {
    echo "$1" | ssh root@$RM2_IP "$LAMP"
}

# Test connection
if ! ssh root@$RM2_IP "test -x $LAMP" 2>/dev/null; then
    echo "Error: Cannot connect to $RM2_IP or lamp not found"
    exit 1
fi
echo "✓ Connected"
echo ""

# Draw bounding box for test area
echo "Drawing test area box..."
lamp_cmd "pen rectangle 850 1600 1350 1850"

sleep 0.5

# RESISTOR (top left in box)
echo "Drawing resistor..."
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

# Label: R
lamp_cmd "pen down 1110 1640"
lamp_cmd "pen move 1110 1660"
lamp_cmd "pen move 1120 1660"
lamp_cmd "pen move 1120 1650"
lamp_cmd "pen move 1110 1650"
lamp_cmd "pen move 1120 1660"
lamp_cmd "pen up"

sleep 0.5

# CAPACITOR (bottom left in box)
echo "Drawing capacitor..."
lamp_cmd "pen line 900 1730 990 1730"
lamp_cmd "pen line 990 1690 990 1770"
lamp_cmd "pen line 1010 1690 1010 1770"
lamp_cmd "pen line 1010 1730 1100 1730"

# Label: C
lamp_cmd "pen down 1120 1720"
lamp_cmd "pen move 1110 1720"
lamp_cmd "pen move 1110 1740"
lamp_cmd "pen move 1120 1740"
lamp_cmd "pen up"

sleep 0.5

# GROUND (right side in box)
echo "Drawing ground..."
lamp_cmd "pen line 1200 1650 1200 1710"
lamp_cmd "pen line 1170 1710 1230 1710"
lamp_cmd "pen line 1178 1725 1222 1725"
lamp_cmd "pen line 1185 1740 1215 1740"
lamp_cmd "pen line 1192 1755 1208 1755"

# Label: GND
lamp_cmd "pen down 1240 1680"
lamp_cmd "pen move 1240 1700"
lamp_cmd "pen move 1245 1695"
lamp_cmd "pen move 1250 1700"
lamp_cmd "pen move 1255 1695"
lamp_cmd "pen move 1260 1700"
lamp_cmd "pen move 1260 1680"
lamp_cmd "pen up"

sleep 0.5

# Title text at top of box
echo "Adding title..."
lamp_cmd "pen down 900 1615"
lamp_cmd "pen move 900 1625"
lamp_cmd "pen move 905 1625"
lamp_cmd "pen move 905 1620"
lamp_cmd "pen move 900 1620"
lamp_cmd "pen move 905 1625"
lamp_cmd "pen up"

# E
lamp_cmd "pen down 910 1615"
lamp_cmd "pen move 910 1625"
lamp_cmd "pen move 915 1625"
lamp_cmd "pen up"
lamp_cmd "pen line 910 1620 915 1620"

# S
lamp_cmd "pen down 925 1615"
lamp_cmd "pen move 920 1615"
lamp_cmd "pen move 920 1620"
lamp_cmd "pen move 925 1620"
lamp_cmd "pen move 925 1625"
lamp_cmd "pen move 920 1625"
lamp_cmd "pen up"

# T
lamp_cmd "pen line 930 1615 940 1615"
lamp_cmd "pen line 935 1615 935 1625"

echo ""
echo "✓ All components drawn with labels!"
echo ""
echo "Components visible in bottom right test box:"
echo "  [R]  Resistor - zigzag pattern"
echo "  [C]  Capacitor - parallel plates"
echo "  [GND] Ground - stacked lines"
echo ""
echo "Press Enter to test eraser..."
read

echo ""
echo "Testing eraser fill..."
lamp_cmd "eraser fill 850 1600 1350 1850 8"
echo "✓ Area erased"

sleep 1

echo ""
echo "Testing eraser clear (dense)..."
lamp_cmd "pen rectangle 900 1650 1100 1750"
sleep 0.5
lamp_cmd "eraser clear 900 1650 1100 1750"
echo "✓ Dense erase complete"

echo ""
echo "=========================================="
echo "✓ Test Complete!"
echo "=========================================="
echo ""
echo "Tested:"
echo "  ✓ Component drawing (resistor, capacitor, ground)"
echo "  ✓ Text labels"
echo "  ✓ Eraser fill (spacing: 8px)"
echo "  ✓ Eraser clear (spacing: 3px)"
echo ""
echo "Fallback system verified!"
