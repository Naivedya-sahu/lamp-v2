# Redesigned Circuit Assembly System - Anchor-Relative Coordinates

## System Architecture

Complete redesign using **bounding-box-centered anchors** with **relative coordinate system**.

### Key Changes

1. **Component Library (JSON)**
   - All coordinates relative to anchor at bounding box center
   - Anchor always at (0, 0) in component space
   - Pin positions as offsets (dx, dy) from anchor
   - Pen commands as list format: `["pen", "down", dx, dy]`

2. **Netlist Format**
   - Simplified: `COMP_TYPE REF NODE1 NODE2 [VALUE]`
   - Example: `R R1 N1 N2 10k`
   - Only 2-pin components supported
   - Ground can be: `0`, `GND`, or `gnd`

3. **Circuit Placer**
   - Places components by anchor position
   - Rotates around anchor
   - Transforms from component space → circuit space → screen space

4. **Coordinate Transforms**
   ```
   Component Space (anchor-relative)
         ↓ (rotation + translation to anchor position)
   Circuit Space (absolute positions before scaling)
         ↓ (scaling + screen centering)
   Screen Space (reMarkable 2 pixels)
   ```

## File Structure

```
src_redesign/
├── component_library_builder.py  # SVG → JSON converter
├── netlist_parser.py              # Parse netlists
├── circuit_placer.py              # Placement + rendering
├── svg_to_lamp_svgpathtools.py   # SVG parser (dependency)
├── rc_filter.net                  # Example netlist
└── README.md                      # This file
```

## Usage

### 1. Build Component Library

```bash
# Convert SVG components to anchor-relative JSON
python3 component_library_builder.py ../../assets/components component_library.json
```

**Output Format:**
```json
{
  "R": {
    "width": 140.0,
    "height": 32.77,
    "anchor": {"x": 0.0, "y": 0.0},
    "pins": [
      {"id": "pin1", "dx": -70.0, "dy": 0.0},
      {"id": "pin2", "dx": 70.0, "dy": 0.0}
    ],
    "pen_commands": [
      ["pen", "down", -70.0, 0.0],
      ["pen", "move", -35.0, 16.5],
      ["pen", "move", 0.0, -16.5],
      ...
      ["pen", "up"]
    ]
  }
}
```

### 2. Write Netlist

Create `circuit.net`:
```
* RC Filter
VDC V1 VIN GND 5V
R R1 VIN VOUT 10k
C C1 VOUT GND 100nF
```

### 3. Generate Circuit

```bash
# Parse netlist and generate pen commands
python3 circuit_placer.py rc_filter.net component_library.json > output.txt

# With custom scale
python3 circuit_placer.py rc_filter.net component_library.json 2.0 > output.txt
```

### 4. Send to reMarkable 2

```bash
cat output.txt | ssh root@10.11.99.1 /opt/bin/lamp
```

## Component Library Structure

### Anchor Point
- **Always at bounding box center**: `anchor = (min_x + max_x) / 2, (min_y + max_y) / 2`
- All coordinates relative to this point

### Pin Definitions

**2-pin horizontal (R, C, L, D, ZD):**
```json
"pins": [
  {"id": "pin1", "dx": -width/2, "dy": 0.0},
  {"id": "pin2", "dx": width/2, "dy": 0.0}
]
```

**2-pin vertical (VDC, VAC, P_CAP):**
```json
"pins": [
  {"id": "pin1", "dx": 0.0, "dy": -height/2},
  {"id": "pin2", "dx": 0.0, "dy": height/2}
]
```

**Single pin (GND):**
```json
"pins": [
  {"id": "pin1", "dx": 0.0, "dy": -height/2}
]
```

### Pen Command Format

List-based structure for easy transformation:
```json
["pen", "down", dx, dy]      // Pen down at relative position
["pen", "move", dx, dy]      // Move to relative position
["pen", "up"]                // Lift pen
["pen", "circle", dx, dy, r] // Circle at relative position
["pen", "line", dx1, dy1, dx2, dy2]      // Line between relative positions
["pen", "rectangle", dx1, dy1, dx2, dy2] // Rectangle at relative positions
```

## Coordinate Transformation

### Component Rendering Algorithm

```python
def render_component(placed, scale, offset_x, offset_y):
    for cmd in pen_commands:
        dx, dy = cmd[2], cmd[3]  # Relative to anchor
        
        # 1. Rotate around anchor
        dx_rot, dy_rot = rotate(dx, dy, placed.rotation)
        
        # 2. Translate to anchor position (circuit space)
        x = placed.anchor_x + dx_rot
        y = placed.anchor_y + dy_rot
        
        # 3. Scale to screen space
        sx = x * scale + offset_x
        sy = y * scale + offset_y
        
        # 4. Output
        print(f"pen move {int(sx)} {int(sy)}")
```

### Rotation Matrix

```python
def rotate(dx, dy, angle):
    if angle == 0:   return dx, dy
    if angle == 90:  return -dy, dx
    if angle == 180: return -dx, -dy
    if angle == 270: return dy, -dx
```

## Netlist Parser

### Supported Components

| Type | Reference | Nodes | Example |
|------|-----------|-------|---------|
| Resistor | R | 2 | `R R1 N1 N2 10k` |
| Capacitor | C | 2 | `C C1 N2 GND 100nF` |
| Inductor | L | 2 | `L L1 N1 N2 10mH` |
| Diode | D | 2 | `D D1 N1 N2` |
| Zener | ZD | 2 | `ZD ZD1 N1 N2 5V1` |
| Voltage DC | VDC | 2 | `VDC V1 VIN GND 5V` |
| Voltage AC | VAC | 2 | `VAC V1 VIN GND 10Vrms` |
| Polarized Cap | P_CAP | 2 | `P_CAP C1 VIN GND 100uF` |
| Ground | GND | 1 | Automatically added |

### Netlist Rules

1. **Format**: `COMP_TYPE REF NODE1 NODE2 [VALUE]`
2. **Comments**: Lines starting with `*` or `.`
3. **Ground nodes**: Use `0`, `GND`, or `gnd` (normalized to `GND`)
4. **Node names**: Any alphanumeric string
5. **Values**: Optional, any string (10k, 100nF, 5V, etc.)

## Circuit Placement

### Grid Layout

Components placed in grid based on count:
- 1-3 components: 1 row
- 4-6 components: 2 rows × 3 cols
- 7+ components: Calculated as ceil(sqrt(n * 1.5))

**Grid spacing:**
- Horizontal: 300 units
- Vertical: 250 units

### Component Ordering

1. **Voltage sources** (VDC, VAC) - leftmost
2. **Passive components** (R, C, L, D, ZD)
3. **Ground** (GND) - rightmost

### Wire Routing

**Manhattan (orthogonal) routing:**
- Only horizontal and vertical segments
- L-shaped paths between pins
- Prioritizes horizontal-first or vertical-first based on distance

**Algorithm:**
```python
for each pair of pins (x1, y1) → (x2, y2):
    if |x2 - x1| > |y2 - y1|:
        # Horizontal-first
        waypoints = [(x1, y1), (x2, y1), (x2, y2)]
    else:
        # Vertical-first
        waypoints = [(x1, y1), (x1, y2), (x2, y2)]
```

## Scaling and Centering

### Auto-scaling

If no scale provided:
```python
MARGIN = 100  # pixels
scale_x = (SCREEN_WIDTH - 2*MARGIN) / circuit_width
scale_y = (SCREEN_HEIGHT - 2*MARGIN) / circuit_height
scale = min(scale_x, scale_y, 5.0)  # Cap at 5x
```

### Centering

```python
scaled_width = circuit_width * scale
scaled_height = circuit_height * scale
offset_x = (SCREEN_WIDTH - scaled_width) / 2
offset_y = (SCREEN_HEIGHT - scaled_height) / 2
```

## Dependencies

```bash
pip install svgpathtools --break-system-packages
```

## Testing

```bash
# Test netlist parser
python3 netlist_parser.py rc_filter.net

# Test component library builder
python3 component_library_builder.py ../../assets/components test_library.json

# Test complete pipeline
python3 circuit_placer.py rc_filter.net component_library.json
```

## Differences from Old System

| Aspect | Old System | New System |
|--------|-----------|------------|
| Coordinates | Absolute SVG coords | Anchor-relative |
| Anchor | Arbitrary/pin-based | Bounding box center |
| JSON format | String commands | List-based commands |
| Pin positions | Absolute | Relative offsets |
| Rotation | Complex | Simple around anchor |
| Netlist | Multi-format | Single format |
| Components | 2-pin + multi-pin | 2-pin only |

## Example Output

```
# Circuit: 3 components, 2 wires
# Scale: 2.50x
# V1 (VDC)
pen down 565 623
pen circle 565 623 555
pen down 565 68
pen move 565 243
pen up
# ... (more commands)
```

## Future Enhancements

1. Add rotation support in netlists
2. Support multi-pin components (transistors, opamps)
3. Grid snapping for cleaner routing
4. Component overlap detection
5. Wire crossing minimization
6. Component value labels
7. Net name labels
