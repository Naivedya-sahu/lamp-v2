#!/bin/bash
#
# Draw all components from library in a grid layout
# Useful for testing and visual verification of the component library
#
# Usage: ./test_library.sh [RM2_IP]

set -e

RM2_IP="${1:-10.11.99.1}"
LAMP="/opt/bin/lamp"
LIBRARY="component_library.json"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Component Library Test - Grid Layout"
echo "=========================================="
echo -e "${BLUE}Target:${NC} $RM2_IP"
echo ""

# Check if library exists
if [ ! -f "$LIBRARY" ]; then
    echo -e "${RED}Error: Component library '$LIBRARY' not found${NC}"
    exit 1
fi

# Test connection
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh root@$RM2_IP "test -x $LAMP" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to $RM2_IP${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"
echo ""

# Generate grid layout and send all components
echo -e "${BLUE}Drawing all components in grid layout...${NC}"
python3 << EOF | ssh root@$RM2_IP "$LAMP"
import json
import sys

# reMarkable 2 screen dimensions
SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

# Grid layout parameters
COLS = 4
MARGIN = 50

# Read library
with open("$LIBRARY", "r") as f:
    library = json.load(f)

# Sort components for consistent layout
components = sorted(library.items())
total = len(components)

print(f"# Drawing {total} components in {COLS} columns", file=sys.stderr)

# Calculate max dimensions per component for proper spacing
max_widths = []
max_heights = []
for i, (name, comp) in enumerate(components):
    bounds = comp.get("bounds", [0, 0, 100, 100])
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    max_widths.append(width)
    max_heights.append(height)

# Find max width and height to ensure no clipping
max_comp_width = max(max_widths) if max_widths else 100
max_comp_height = max(max_heights) if max_heights else 100

# Calculate spacing based on actual component sizes with padding
PADDING = 40  # Space between components
SPACING_X = int(max_comp_width + PADDING)
SPACING_Y = int(max_comp_height + PADDING)

# Ensure grid fits on screen, scale down if necessary
available_width = SCREEN_WIDTH - 2 * MARGIN
available_height = SCREEN_HEIGHT - 2 * MARGIN
needed_width = COLS * SPACING_X
needed_height = ((total + COLS - 1) // COLS) * SPACING_Y

scale = 1.0
if needed_width > available_width or needed_height > available_height:
    scale_x = available_width / needed_width
    scale_y = available_height / needed_height
    scale = min(scale_x, scale_y, 1.0)
    SPACING_X = int(SPACING_X * scale)
    SPACING_Y = int(SPACING_Y * scale)
    print(f"# Scaling grid by {scale:.2f} to fit on screen", file=sys.stderr)

START_X = MARGIN + SPACING_X // 2
START_Y = MARGIN + SPACING_Y // 2

print(f"# Grid spacing: {SPACING_X}x{SPACING_Y}, Scale: {scale:.2f}", file=sys.stderr)

# Draw grid of components
row = 0
col = 0

for name, comp in components:
    # Calculate position in grid
    x = START_X + col * SPACING_X
    y = START_Y + row * SPACING_Y
    
    # Get bounds and calculate anchor (center of bounding box)
    bounds = comp.get("bounds", [0, 0, 100, 100])
    anchor_x = (bounds[0] + bounds[2]) / 2
    anchor_y = (bounds[1] + bounds[3]) / 2
    
    # Apply grid scale to component
    comp_scale = scale * 0.9  # Additional 10% reduction for safety margin
    
    # Transform and output pen commands
    for cmd_str in comp.get("pen_commands", []):
        # Parse command string
        parts = cmd_str.strip().split()
        
        if len(parts) < 2:
            continue
        
        tool = parts[0]
        action = parts[1]
        
        if action == "up":
            print(f"{tool} {action}")
        elif action in ["down", "move"] and len(parts) >= 4:
            px = int((int(parts[2]) - anchor_x) * comp_scale + x)
            py = int((int(parts[3]) - anchor_y) * comp_scale + y)
            print(f"{tool} {action} {px} {py}")
        elif action == "line" and len(parts) >= 6:
            x1 = int((int(parts[2]) - anchor_x) * comp_scale + x)
            y1 = int((int(parts[3]) - anchor_y) * comp_scale + y)
            x2 = int((int(parts[4]) - anchor_x) * comp_scale + x)
            y2 = int((int(parts[5]) - anchor_y) * comp_scale + y)
            print(f"{tool} {action} {x1} {y1} {x2} {y2}")
        elif action == "rectangle" and len(parts) >= 6:
            x1 = int((int(parts[2]) - anchor_x) * comp_scale + x)
            y1 = int((int(parts[3]) - anchor_y) * comp_scale + y)
            x2 = int((int(parts[4]) - anchor_x) * comp_scale + x)
            y2 = int((int(parts[5]) - anchor_y) * comp_scale + y)
            print(f"{tool} {action} {x1} {y1} {x2} {y2}")
        elif action == "circle" and len(parts) >= 5:
            cx = int((int(parts[2]) - anchor_x) * comp_scale + x)
            cy = int((int(parts[3]) - anchor_y) * comp_scale + y)
            r = int(int(parts[4]) * comp_scale)
            print(f"{tool} {action} {cx} {cy} {r}")
    
    # Draw small label circle at anchor point for reference
    print(f"pen circle {x} {y} 3")
    
    print(f"# {name} at ({x}, {y})", file=sys.stderr)
    
    # Move to next position
    col += 1
    if col >= COLS:
        col = 0
        row += 1

print(f"# Grid complete: {row + 1} rows, {COLS} columns", file=sys.stderr)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Grid layout complete!${NC}"
    echo ""
    echo "All components drawn in ${COLS}x${ROWS} grid"
    echo "Check your reMarkable 2 screen"
else
    echo ""
    echo -e "${RED}✗ Error drawing grid${NC}"
    exit 1
fi
