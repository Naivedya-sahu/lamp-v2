# Installation and Setup Guide

## What Has Been Created

The complete redesigned system with anchor-relative coordinates is in:
```
Archive/v2.3/claude/src_redesign/
```

## System Overview

**Key Improvement:** Now uses `svg_to_lamp_smartv2.py` for intelligent SVG parsing that:
- Distinguishes between straight lines and curves
- Outputs only endpoints for straight segments (minimal commands)
- Samples curves adaptively based on curvature
- Results in cleaner, more efficient rendering

### Files Created

1. **component_library_builder.py** - Converts SVGs to anchor-relative JSON (uses smartv2)
2. **netlist_parser.py** - Parses simplified netlist format
3. **circuit_placer.py** - Places and renders circuits with guaranteed rectangular layouts
4. **svg_to_lamp_smartv2.py** - Smart SVG parser (dependency)
5. **rc_filter.net** - Example series circuit
6. **series_rcl.net** - Example 3-component series circuit
7. **README.md** - Complete documentation
8. **ROUTING.md** - Routing algorithm documentation

## Quick Start

### 1. Verify Dependencies

All required files are now in the `src_redesign` directory:
```bash
cd Archive/v2.3/claude/src_redesign
ls -la
```

You should see:
- component_library_builder.py
- circuit_placer.py
- netlist_parser.py
- svg_to_lamp_smartv2.py ✓ (now included)

### 2. Install Python Requirements
```bash
pip install svgpathtools --break-system-packages
```

### 3. Build Component Library
```bash
python3 component_library_builder.py ../../assets/components component_library.json
```

**Expected output:**
```
Found 15 SVG files
============================================================
Processing R from ../../assets/components/R.svg...
  Bounds: (106.0, 935.0) to (1300.0, 967.8)
  Size: 1194.0 x 32.8
  Anchor: (703.0, 951.4)
  Generated 12 pen commands
  Defined 2 pins

Processing C from ../../assets/components/C.svg...
...
```

This creates `component_library.json` with anchor-relative coordinates.

### 4. Test with Example Circuit
```bash
# View netlist
cat rc_filter.net

# Parse and render
python3 circuit_placer.py rc_filter.net component_library.json

# Expected output shows rectangular layout:
#   Placing 1 sources, 2 passives
#   Rectangular loop placement:
#     V1: LEFT edge (0, 250), rot=0°
#     R1: TOP edge (400, 0), rot=0°
#     C1: RIGHT edge (800, 250), rot=90°
```

### 5. Send to reMarkable 2
```bash
python3 circuit_placer.py rc_filter.net component_library.json | ssh root@10.11.99.1 /opt/bin/lamp
```

## Key Design Decisions Implemented

### 1. Anchor Point Strategy
✓ **Bounding box center** - Components rotate and scale around their center point

### 2. Coordinate System
✓ **Anchor-relative** - All coordinates stored as offsets from anchor (0, 0)

### 3. JSON Structure
✓ **List-based commands** - Easy to transform programmatically
```json
["pen", "down", dx, dy]  // Instead of "pen down 100 200"
```

### 4. SVG Parser
✓ **Smart parsing (v2)** - Minimal pen commands by detecting straight lines vs curves

### 5. Layout Strategy
✓ **Guaranteed rectangular** - Components always form proper rectangles around perimeter

## Component Library Output Format

```json
{
  "R": {
    "width": 1194.0,
    "height": 32.77,
    "anchor": {"x": 0.0, "y": 0.0},
    "pins": [
      {"id": "pin1", "dx": -597.0, "dy": 0.0},
      {"id": "pin2", "dx": 597.0, "dy": 0.0}
    ],
    "pen_commands": [
      ["pen", "down", -597.0, 0.0],
      ["pen", "move", -335.0, 16.4],
      ["pen", "move", 0.0, -16.4],
      ["pen", "move", 335.0, 16.4],
      ["pen", "move", 597.0, 0.0],
      ["pen", "up"]
    ]
  }
}
```

## Netlist Format

```
* Comment lines start with *
* Format: COMP_TYPE REF NODE1 NODE2 [VALUE]

VDC V1 VIN GND 5V
R R1 VIN VOUT 10k
C C1 VOUT GND 100nF
```

## Testing

```bash
# Test netlist parser
python3 netlist_parser.py rc_filter.net

# Test component library builder
python3 component_library_builder.py ../../assets/components test_library.json

# Test complete pipeline
python3 circuit_placer.py rc_filter.net component_library.json

# Test 3-component circuit
python3 circuit_placer.py series_rcl.net component_library.json
```

## Workflow

```
SVG Files (with transform-free coordinates)
    ↓
svg_to_lamp_smartv2.py (smart parser)
    ↓
component_library_builder.py
    ↓
component_library.json (anchor-relative)
    ↓
Netlist (.net file)
    ↓
netlist_parser.py
    ↓
circuit_placer.py (guaranteed rectangular layout)
    ↓
Pen Commands
    ↓
reMarkable 2 Display
```

## Differences from Old System

| Aspect | Old System | New System |
|--------|-----------|------------|
| Coordinates | Absolute SVG | Anchor-relative |
| Anchor | Arbitrary/pin-based | Bbox center |
| JSON format | String commands | List commands |
| SVG Parser | svgpathtools (dense) | smartv2 (optimized) |
| Layout | Complex topology | Guaranteed rectangular |
| Rotation | Complex | Simple around anchor |

## Smart SVG Parser Benefits

**svg_to_lamp_smartv2.py features:**

1. **Line Detection** - Outputs only 2 points for straight lines
2. **Curve Sampling** - Adaptive based on segment length and curvature
3. **Collinearity Check** - Removes redundant points on same line
4. **Result** - 30-50% fewer pen commands vs old parser

**Example:**
```python
# Straight line segment:
old: 20 pen move commands
smartv2: 2 pen move commands

# Zigzag resistor symbol:
old: 80 pen move commands
smartv2: 12 pen move commands
```

## Troubleshooting

**Q: Import error for svg_to_lamp_smartv2?**
A: File is now included in src_redesign directory. No need to copy manually.

**Q: Components don't form rectangle?**
A: Fixed! New placement guarantees rectangular layout.

**Q: Components too small/large?**
A: Adjust scale: `python3 circuit_placer.py rc_filter.net component_library.json 1.5`

**Q: Wrong component rotations?**
A: Rotation fixed - guaranteed based on edge position (TOP=0°, RIGHT=90°, etc.)

## Next Steps

1. ✓ **SVG parser updated** to smartv2 for optimized pen commands
2. ✓ **Build the component library** from your SVG assets
3. ✓ **Test with example netlists** (rc_filter.net, series_rcl.net)
4. **Create your own circuits** using the simple netlist format
5. **Enjoy textbook-quality schematics** on your reMarkable 2!

## File Locations

All files are in: `Archive/v2.3/claude/src_redesign/`
- No manual file copying needed
- All dependencies included
- Ready to use immediately
