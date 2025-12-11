# Circuit Builder System

A comprehensive system for building electronic circuits with component anchor points and automatic netlist-based wiring.

## Overview

This system provides:
- **Fixed block-size components** (e.g., R/L/C = 120x48px)
- **Anchor points** for component connections (leads)
- **Netlist support** for circuit connectivity
- **Automatic SVG-to-lamp conversion** with coordinate transformation
- **Library of 214 electrical symbols** from Electrical_symbols_library.svg

## Files

### Core System
- `component_definitions.py` - Component library with anchor points and fixed sizes
- `circuit_builder.py` - Circuit renderer that generates lamp commands
- `component_definitions.json` - JSON database of component definitions
- `Library.txt` - Index of all 214 component groups from SVG library

### Legacy Tools
- `component_library.py` - Original component extractor
- `svg_to_lamp_improved.py` - Standalone SVG converter
- `component_selector.py` - Interactive component browser

## Component Definitions

### Standard Components

| Symbol | Name      | Size (px) | Anchors | Description |
|--------|-----------|-----------|---------|-------------|
| R      | Resistor  | 120×48    | left, right | 2-terminal passive |
| C      | Capacitor | 120×48    | left, right | 2-terminal passive |
| L      | Inductor  | 120×48    | left, right | 2-terminal passive |
| V      | VDC       | 80×80     | positive, negative | DC voltage source |
| V~     | VAC       | 80×80     | positive, negative | AC voltage source |
| D      | Diode     | 80×60     | anode, cathode | Diode |
| GND    | Ground    | 60×40     | gnd | Ground reference |
| -      | Wire      | flexible  | endpoints | Connection wire |

### Anchor Points

Anchor points are normalized (0.0 to 1.0) positions within component boundaries:
- `0.0, 0.5` = Left side, vertical center
- `1.0, 0.5` = Right side, vertical center
- `0.5, 0.0` = Top side, horizontal center
- `0.5, 1.0` = Bottom side, horizontal center

Example:
```python
AnchorPoint("left", 0.0, 0.5)   # Left terminal
AnchorPoint("right", 1.0, 0.5)  # Right terminal
```

## Usage

### 1. Test Circuit Structure

```bash
python3 circuit_builder.py test
```

Output:
```
Circuit: RC Series Circuit with DC Source
Components: 4
  V1: VDC @ (100, 100)
  R1: R @ (200, 160)
  C1: C @ (340, 160)
  GND1: GND @ (100, 200)

Netlist:
  VCC: V1.positive, R1.left
  N1: R1.right, C1.left
  GND: C1.right, GND1.gnd, V1.negative, GND1.gnd
```

### 2. Generate Lamp Commands

```bash
python3 circuit_builder.py
```

Creates: `rc_vdc_circuit.lamp`

### 3. Draw on reMarkable 2

```bash
cat rc_vdc_circuit.lamp | ssh root@10.11.99.1 lamp
```

## Creating Custom Circuits

### Python API

```python
from component_definitions import ComponentLibrary, PlacedComponent, Circuit
from circuit_builder import SVGComponentRenderer, CircuitRenderer

# Initialize library
library = ComponentLibrary()

# Create circuit
circuit = Circuit("My Circuit")

# Place components
r1 = PlacedComponent(ref="R1", component_type="R", x=100, y=100, value="10k")
c1 = PlacedComponent(ref="C1", component_type="C", x=240, y=100, value="100nF")
gnd = PlacedComponent(ref="GND1", component_type="GND", x=300, y=150)

circuit.add_component(r1)
circuit.add_component(c1)
circuit.add_component(gnd)

# Define netlist connections
circuit.connect("R1", "right", "C1", "left", "N1")
circuit.connect("C1", "right", "GND1", "gnd", "GND")

# Render
svg_renderer = SVGComponentRenderer("examples/svg_symbols/Electrical_symbols_library.svg")
renderer = CircuitRenderer(library, svg_renderer)
lamp_commands = renderer.render_circuit(circuit, draw_wires=True)

print(lamp_commands)
```

### Circuit Topology

The netlist system connects components through anchor points:

```
VDC(+)---[R1]---[C1]---GND
  |                     |
  +---------------------+

Netlist:
  VCC: V1.positive -> R1.left
  N1:  R1.right -> C1.left
  GND: C1.right -> GND1.gnd
       V1.negative -> GND1.gnd
```

## Coordinate System

### SVG to Lamp Transformation

1. **Extract original component bounding box** from SVG
2. **Calculate scale factor** to fit target size (maintain aspect ratio)
3. **Apply transformation**:
   ```
   lamp_x = svg_x × scale + offset_x
   lamp_y = svg_y × scale + offset_y
   ```

### Negative Coordinate Handling

The system correctly parses negative coordinates using regex: `-?\d+\.?\d*`

Example from SVG:
```svg
<path d="m 84,766.41665 -21,-28 H 49 v 14"/>
```

Parsed values: `[-21, -28]` are correctly interpreted as relative movements.

## Library.txt Format

Lists all 214 component groups:
```
# Electrical Component Library
# Total Components: 214

Group: g1058
  Paths: 4
  Sample: M 42,752.41665 H 56...

Group: g1087
  Paths: 2
  Sample: M 7,836.41665 H 21...
```

## Component SVG Group Mapping

| Component | SVG Groups |
|-----------|------------|
| Resistor  | g1087, g1092, g1263, g1253 |
| Capacitor | g1058, g1100, g1136, g1162 |
| Inductor  | g1046, g1063, g1081, g1091 |
| VDC       | g184, g188 |
| VAC       | g1032 |
| Ground    | g1080, g1080-3 |
| Diode     | g2999, g3007 |

## Future Enhancements

### Planned Features
1. **Rotation support** - Rotate components (0°, 90°, 180°, 270°)
2. **Auto-routing** - Automatic wire path finding
3. **SPICE netlist export** - Full netlist generation
4. **Component value labels** - Text rendering for values
5. **Multi-terminal components** - Transistors, ICs
6. **Schematic validation** - Check for unconnected nets

### Adding New Components

1. **Identify SVG group** in Library.txt
2. **Measure dimensions** and determine appropriate fixed size
3. **Define anchor points** based on terminals/leads
4. **Add to ComponentLibrary**:

```python
self.add_component(ComponentDefinition(
    name="MyComponent",
    category="custom",
    width=100,
    height=60,
    anchors=[
        AnchorPoint("in", 0.0, 0.5),
        AnchorPoint("out", 1.0, 0.5)
    ],
    svg_group_ids=["g1234"],
    symbol="MC"
))
```

## Troubleshooting

### Components not rendering
- Check SVG group ID exists in `examples/svg_symbols/Electrical_symbols_library.svg`
- Verify component definition in `component_definitions.json`

### Wires not connecting
- Verify netlist connections reference correct anchor names
- Check anchor point definitions in ComponentDefinition

### Coordinates incorrect
- SVG uses different coordinate system than lamp
- Check scale and offset calculations in `_transform_point()`

### Negative coordinates missing
- Regex pattern `-?\d+\.?\d*` should capture negatives
- Check path parsing in `_parse_path_to_lamp()`

## Example: RC Series Circuit

Generated topology:
```
V1 (VDC 5V)
 ├─ positive (140, 100) ──> R1.left (200, 184) [Net: VCC]
 └─ negative (140, 180) ──> GND1.gnd (130, 200) [Net: GND]

R1 (10k)
 ├─ left (200, 184)     <── V1.positive [Net: VCC]
 └─ right (320, 184)    ──> C1.left (340, 184) [Net: N1]

C1 (100nF)
 ├─ left (340, 184)     <── R1.right [Net: N1]
 └─ right (460, 184)    ──> GND1.gnd (130, 200) [Net: GND]

GND1
 └─ gnd (130, 200)      <── C1.right, V1.negative [Net: GND]
```

## License

Same as lamp-v2 repository.

## Credits

- Electrical symbols from Filip Dominec's library (CC0)
- lamp tool from rmkit
- reMarkable 2 tablet platform
