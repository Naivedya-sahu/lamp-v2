# Phase 3: SVG to Relative Coordinates & Component Rendering

Production-ready tools for converting SVG components to relative lamp commands and deploying to reMarkable 2.

## Overview

Phase 3 provides:
1. **Relative coordinate conversion** - SVG → normalized (0.0-1.0) coordinates
2. **Component rendering system** - Deploy components to RM2 with scaling/positioning
3. **Comprehensive testing suite** - Validate each stage of the pipeline

## Architecture

```
SVG File → svg_to_lamp_relative.py → Relative Commands (0.0-1.0)
                                              ↓
                                    draw_component.sh
                                              ↓
                                    Absolute Commands (pixels)
                                              ↓
                                    SSH → RM2 → lamp
```

## Files

### Core Tools

**`src/svg_to_lamp_relative.py`**
- Converts SVG to relative coordinates (0.0-1.0)
- Intelligent line/curve detection with simplification
- Pin circle filtering (--show-pins flag)
- Output: relative pen commands

**`src/draw_component.sh`**
- Complete component rendering pipeline
- Scale/position components on RM2 screen
- Converts relative → absolute coordinates
- SSH deployment to reMarkable 2

### Testing Suite

**`src/test_svg_parser.sh`**
- Tests SVG parsing for all components
- Validates command generation
- Checks coordinate ranges

**`src/test_relative_coords.sh`**
- Verifies relative coordinate conversion
- Tests scaling and positioning
- Validates bounds clamping

**`src/test_component_render.sh`**
- End-to-end pipeline testing
- Dry-run and live RM2 modes
- Component gallery rendering

## Usage

### Basic Component Rendering

```bash
# Draw resistor at (500, 800) with scale 100
./src/draw_component.sh assets/components/R.svg --scale 100 --x 500 --y 800 --rm2 10.11.99.1

# Draw OPAMP sized 200x200 at (600, 400)
./src/draw_component.sh assets/components/OPAMP.svg --width 200 --height 200 --x 600 --y 400 --rm2 10.11.99.1

# Show pin circles for testing
./src/draw_component.sh assets/components/C.svg --show-pins --rm2 10.11.99.1
```

### Generate Relative Coordinates

```bash
# Basic conversion
python3 src/svg_to_lamp_relative.py assets/components/R.svg

# With pin visualization
python3 src/svg_to_lamp_relative.py assets/components/R.svg --show-pins

# Adjust simplification tolerance
python3 src/svg_to_lamp_relative.py assets/components/R.svg --tolerance 2.0
```

### Testing

```bash
# Test all components parse correctly
./src/test_svg_parser.sh

# Test specific component
./src/test_svg_parser.sh --component R --verbose

# Test coordinate conversion
./src/test_relative_coords.sh

# End-to-end test (dry-run)
./src/test_component_render.sh

# Full test with RM2
./src/test_component_render.sh --rm2 10.11.99.1

# Render component gallery
./src/test_component_render.sh --rm2 10.11.99.1 --gallery
```

## Command Reference

### svg_to_lamp_relative.py

```
Usage: svg_to_lamp_relative.py <svg_file> [OPTIONS]

Options:
  --show-pins          Show pin circles (normally hidden)
  --tolerance <val>    Simplification tolerance (default: 1.0)

Output Format:
  pen down <rel_x> <rel_y>   # rel_x, rel_y in [0.0, 1.0]
  pen move <rel_x> <rel_y>
  pen up
```

### draw_component.sh

```
Usage: draw_component.sh <svg_file> [OPTIONS]

Options:
  --scale <factor>     Scale factor (default: 1.0)
  --x <pos>            X position in pixels (default: 0)
  --y <pos>            Y position in pixels (default: 0)
  --width <px>         Width in pixels (overrides scale)
  --height <px>        Height in pixels (overrides scale)
  --show-pins          Show pin circles for testing
  --tolerance <val>    Simplification tolerance (default: 1.0)
  --rm2 <ip>           RM2 IP address (default: 10.11.99.1)
  --dry-run            Generate commands without sending
```

## Component Library

All normalized SVG components in `assets/components/`:

| Component | Description | Pins |
|-----------|-------------|------|
| R.svg | Resistor | 2 |
| C.svg | Capacitor | 2 |
| L.svg | Inductor | 2 |
| D.svg | Diode | 2 |
| ZD.svg | Zener Diode | 2 |
| GND.svg | Ground | 1 |
| VDC.svg | DC Voltage Source | 2 |
| VAC.svg | AC Voltage Source | 2 |
| OPAMP.svg | Operational Amplifier | 5 |
| NPN_BJT.svg | NPN Transistor | 3 |
| PNP_BJT.svg | PNP Transistor | 3 |
| N_MOSFET.svg | N-Channel MOSFET | 3 |
| P_MOSFET.svg | P-Channel MOSFET | 3 |
| P_CAP.svg | Polarized Capacitor | 2 |
| SW_OP.svg | Switch (Open) | 2 |
| SW_CL.svg | Switch (Closed) | 2 |

## Coordinate System

### Relative Coordinates (0.0-1.0)

- **Input:** SVG with arbitrary dimensions
- **Processing:** Calculate bounds, normalize to [0.0, 1.0]
- **Output:** Position-independent pen commands

**Benefits:**
- Component reusability
- Easy scaling/positioning
- Anchor point integration

### Absolute Coordinates (Pixels)

- **Screen:** 1404 × 1872 pixels (reMarkable 2)
- **Conversion:** `abs_x = rel_x * scale + offset_x`
- **Clamping:** Ensures coordinates stay within screen bounds

## Integration with Component Library

Phase 3 tools integrate with the component definition system:

```python
# Component with anchor points (0.0-1.0 relative)
{
  "name": "Resistor",
  "width": 120,      # Reference width
  "height": 48,      # Reference height
  "anchors": [
    {"name": "left", "x": 0.0, "y": 0.5},
    {"name": "right", "x": 1.0, "y": 0.5}
  ]
}

# Render at absolute position
./draw_component.sh R.svg --width 120 --x 500 --y 800 --rm2 10.11.99.1
```

## Test Results

```
✓ SVG Parser Test: 16/16 components passed
✓ Relative Coords Test: 4/4 tests passed
✓ Component Render Test: 7/7 tests passed
```

### Test Coverage

1. **SVG Parsing:** All 16 components parse correctly
2. **Coordinate Range:** All coordinates in [0.0, 1.0]
3. **Scaling:** Verified with multiple scale factors
4. **Positioning:** Offset calculations correct
5. **Bounds Clamping:** No overflow beyond screen limits
6. **Show Pins:** Pin visualization works
7. **Complex Components:** OPAMP, transistors, MOSFETs render correctly

## Workflow Examples

### Draw Single Component

```bash
# 1. Convert SVG to relative coordinates
python3 src/svg_to_lamp_relative.py assets/components/R.svg > R_relative.lamp

# 2. Scale and position (manual)
cat R_relative.lamp | python3 -c "
import sys
scale, x, y = 100, 500, 800
for line in sys.stdin:
    parts = line.strip().split()
    if len(parts) == 4 and parts[1] in ('down', 'move'):
        rx, ry = float(parts[2]), float(parts[3])
        print(f'pen {parts[1]} {int(rx*scale+x)} {int(ry*scale+y)}')
    else:
        print(line.strip())
" | ssh root@10.11.99.1 /opt/bin/lamp

# OR use draw_component.sh (recommended)
./src/draw_component.sh assets/components/R.svg --scale 100 --x 500 --y 800 --rm2 10.11.99.1
```

### Render Component Grid

```bash
# Render all components in 4-column grid
./src/test_component_render.sh --rm2 10.11.99.1 --gallery
```

### Debug Component Anchors

```bash
# Show pin circles to verify anchor point placement
./src/draw_component.sh assets/components/OPAMP.svg --show-pins --scale 150 --x 600 --y 400 --rm2 10.11.99.1
```

## Troubleshooting

### No pen commands generated

```bash
# Check SVG file structure
python3 src/svg_to_lamp_relative.py assets/components/R.svg --show-pins

# Verify SVG has drawable elements
xmllint --format assets/components/R.svg | grep -E "(path|line|circle|rect)"
```

### Coordinates out of range

```bash
# Test with verbose output
./src/test_svg_parser.sh --component R --verbose

# Check if SVG needs normalization
python3 src/svg_normalizer_v2.py assets/components/old/R.svg
```

### RM2 connection failed

```bash
# Test SSH connection
ssh root@10.11.99.1 "test -x /opt/bin/lamp && echo OK"

# Check lamp binary
ssh root@10.11.99.1 "ls -la /opt/bin/lamp"

# Try manual deployment
cat test.lamp | ssh root@10.11.99.1 /opt/bin/lamp
```

## Performance

- **R.svg:** 5 commands (simple resistor)
- **OPAMP.svg:** 29 commands (complex component)
- **Average:** ~20 commands per component
- **Rendering time:** <100ms per component on RM2

## Next Steps

Phase 3 provides the foundation for:
- **Circuit builder integration:** Use relative coords with anchor points
- **Component library expansion:** Add more symbols
- **Netlist rendering:** Automatic circuit layout
- **Interactive editing:** Real-time component placement

## License

MIT License - See LICENSE file

## References

- [NORMALIZED_SVG_COMPONENTS.md](NORMALIZED_SVG_COMPONENTS.md) - Component specifications
- [COMPONENT_SYSTEM_ARCHITECTURE.md](COMPONENT_SYSTEM_ARCHITECTURE.md) - Design patterns
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
