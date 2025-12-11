# Component Library Scripts

Three scripts for working with the JSON component library on reMarkable 2.

## Prerequisites

1. **Component Library**: Run `component_library_builder.py` first to generate `component_library.json`
   ```bash
   python3 component_library_builder.py ../components
   ```

2. **reMarkable 2 Connection**: Device must be accessible via SSH with lamp binary installed at `/opt/bin/lamp`

---

## Scripts

### 1. send_component.sh
Send individual components from the library to reMarkable 2.

**Usage:**
```bash
./send_component.sh <component_name> [scale] [x] [y] [RM2_IP]
```

**Arguments:**
- `component_name` - Component from library (required)
- `scale` - Scale factor (default: 1.0)
- `x` - X position in pixels (default: from library anchor)
- `y` - Y position in pixels (default: from library anchor)
- `RM2_IP` - reMarkable 2 IP address (default: 10.11.99.1)

**Examples:**
```bash
# Draw resistor at library default position
./send_component.sh R

# Draw BJT scaled 2x
./send_component.sh NPN_BJT 2

# Draw OpAmp scaled 1.5x at position (500, 800)
./send_component.sh OPAMP 1.5 500 800

# Draw VDC at (0,0) on device at 192.168.1.100
./send_component.sh VDC 1 0 0 192.168.1.100
```

**Features:**
- Automatically extracts pen commands from JSON
- Transforms coordinates based on scale and position
- Shows preview before sending
- Reports success/failure

---

### 2. list_components.sh
Display all components in the library with metadata.

**Usage:**
```bash
./list_components.sh
```

**Output:**
```
Component Library Contents
==========================================

Total components: 16

Component       |  Width | Height | Commands | Anchor (x,y)    | Pins
-----------------------------------------------------------------------------------
C               |    100 |     85 |       10 | (50, 42)        | 2
D               |    140 |     70 |        8 | (70, 35)        | 2
GND             |    100 |     85 |       15 | (50, 0)         | 1
...
```

Shows:
- Component dimensions (width, height)
- Number of pen commands
- Anchor point coordinates
- Pin count

---

### 3. test_library.sh
Draw all components in a grid layout for visual verification.

**Usage:**
```bash
./test_library.sh [RM2_IP]
```

**Arguments:**
- `RM2_IP` - reMarkable 2 IP address (default: 10.11.99.1)

**Example:**
```bash
# Draw grid on default device
./test_library.sh

# Draw grid on specific device
./test_library.sh 192.168.1.100
```

**Features:**
- Draws all components in 4-column grid layout
- Components scaled to 0.8x for dense packing
- Small circle at each anchor point for reference
- Useful for verifying library integrity

---

## Component Library Structure

The `component_library.json` file format:
```json
{
  "R": {
    "width": 140,
    "height": 32,
    "anchor": [70, 16],
    "pins": [
      {"id": "pin1", "x": 0, "y": 16},
      {"id": "pin2", "x": 140, "y": 16}
    ],
    "commands": [
      {"type": "pen_down", "x": 0, "y": 16},
      {"type": "pen_move", "x": 15, "y": 16},
      ...
    ]
  }
}
```

**Fields:**
- `width`, `height` - Component bounding box
- `anchor` - Reference point (usually center or first pin)
- `pins` - Pin locations with IDs
- `commands` - Pen commands (pen_down, pen_move, pen_up, pen_line, pen_rectangle, pen_circle)

---

## Coordinate Transformation

When sending components, coordinates are transformed as:
```
transformed_x = (original_x - anchor_x) * scale + offset_x
transformed_y = (original_y - anchor_y) * scale + offset_y
```

This allows:
- **Scaling**: Multiply relative coordinates by scale factor
- **Positioning**: Add offset to place component anywhere
- **Anchor-relative**: All coordinates relative to component anchor point

---

## Available Components

Standard library includes:
- **2-terminal**: R, C, L, D, ZD
- **Voltage sources**: VDC, VAC, GND
- **3-terminal**: NPN_BJT, PNP_BJT, N_MOSFET, P_MOSFET
- **Op-Amp**: OPAMP
- **Polarized**: P_CAP
- **Switches**: SW_CL (closed), SW_OP (open)

---

## Workflow

1. **Build library** (once):
   ```bash
   python3 component_library_builder.py ../components
   ```

2. **List components**:
   ```bash
   ./list_components.sh
   ```

3. **Test visual appearance**:
   ```bash
   ./test_library.sh
   ```

4. **Send individual components**:
   ```bash
   ./send_component.sh R 2 500 800
   ./send_component.sh OPAMP 1.5 300 400
   ```

---

## Troubleshooting

**Library not found:**
```
Error: Component library 'component_library.json' not found
```
→ Run `component_library_builder.py` first

**Component not found:**
```
Error: Component 'RESISTOR' not found in library
Available components: R, C, L, ...
```
→ Use exact component name (case-sensitive)

**Connection failed:**
```
Error: Cannot connect to 10.11.99.1 or lamp not found
```
→ Check reMarkable 2 connection and lamp installation

**Commands not visible:**
- Verify scale factor (too large may go off-screen)
- Check position coordinates (negative or > 1404x1872)
- Use `test_library.sh` to verify library integrity

---

## Integration with Circuit System

These scripts complement the full circuit assembly pipeline:
1. `component_library_builder.py` → Creates JSON library
2. `send_component.sh` → Tests individual components
3. `netlist_parser.py` → Parses LTSpice netlists
4. `circuit_placer.py` → Places components for circuits
5. `circuit_to_rm2.sh` → Complete circuit rendering

Use `send_component.sh` for:
- Testing new components before adding to library
- Manual component placement
- Debugging pen command generation
- Quick visualization of component designs
