# Circuit Assembly System for reMarkable 2

Complete 4-layer pipeline for drawing circuits from LTSpice netlists on reMarkable 2.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Circuit to RM2 Pipeline                  │
└─────────────────────────────────────────────────────────────┘

Layer 1: Component Library Builder
  ├─ Input: SVG symbol files (./components/*.svg)
  ├─ Process: Extract anchor points + convert to pen commands
  └─ Output: component_library.json (header file)

Layer 2: Netlist Parser
  ├─ Input: LTSpice netlist file (*.net)
  ├─ Process: Parse components and connectivity
  └─ Output: Circuit graph with nets

Layer 3: Circuit Placer & Renderer
  ├─ Input: Circuit graph + component library
  ├─ Process: Auto-placement + wire routing + scaling
  └─ Output: Pen commands for entire circuit

Layer 4: Transmission
  ├─ Input: Pen commands (optimized or raw)
  ├─ Process: SSH transmission to reMarkable 2
  └─ Output: Circuit drawn on screen
```

## Quick Start

### 1. Build Component Library (One-time)

```bash
python3 component_library_builder.py ./components ./component_library.json
```

This scans all SVG files in `./components/`, extracts pin locations, converts to pen commands, and generates the component library header.

### 2. Create a Netlist

Create a file `my_circuit.net` with LTSpice format:

```
* RC Low-Pass Filter
V1 IN 0 5V
R1 IN OUT 10k
C1 OUT 0 100nF
```

### 3. Draw Circuit on reMarkable 2

```bash
./circuit_to_rm2.sh my_circuit.net
```

## Netlist Format

### Standard LTSpice Syntax

```
* Comment lines start with asterisk
ComponentRef Node1 Node2 [Node3...] Value

Examples:
  V1 N1 0 5V          # Voltage source: 5V between N1 and ground
  R1 N1 N2 10k        # Resistor: 10kΩ between N1 and N2
  C1 N2 0 100nF       # Capacitor: 100nF between N2 and ground
```

### Supported Components

| Prefix | Component Type | Netlist Format | Pins |
|--------|---------------|----------------|------|
| `V` | DC Voltage Source | `V1 + - value` | 2 |
| `VAC` | AC Voltage Source | `VAC1 + - value` | 2 |
| `I` | DC Current Source | `I1 + - value` | 2 |
| `R` | Resistor | `R1 n1 n2 value` | 2 |
| `C` | Capacitor | `C1 n1 n2 value` | 2 |
| `L` | Inductor | `L1 n1 n2 value` | 2 |
| `D` | Diode | `D1 anode cathode` | 2 |
| `ZD` | Zener Diode | `ZD1 anode cathode` | 2 |
| `Q` | NPN BJT | `Q1 C B E model` | 3 |
| `QP` | PNP BJT | `QP1 C B E model` | 3 |
| `M` | N-Channel MOSFET | `M1 D G S model` | 3 |
| `MP` | P-Channel MOSFET | `MP1 D G S model` | 3 |
| `U` | Op-Amp | `U1 + - Vcc Vee Out` | 5 |
| `0`, `GND` | Ground | `0` or `GND` | 1 |

### Node Naming

- Node `0` or `GND` is ground (reference node)
- All other nodes can be named arbitrarily: `N1`, `VIN`, `VOUT`, etc.
- Nodes with same name are electrically connected

## Example Circuits

### RC Low-Pass Filter

**Netlist:** `examples/rc_filter.net`
```
* Simple RC Low-Pass Filter
V1 IN 0 5V
R1 IN OUT 10k
C1 OUT 0 100nF
```

**Draw:**
```bash
./circuit_to_rm2.sh examples/rc_filter.net
```

### Voltage Divider

**Netlist:** `examples/voltage_divider.net`
```
* Voltage Divider
V1 VIN 0 12V
R1 VIN VOUT 10k
R2 VOUT 0 10k
```

### Inverting Op-Amp

**Netlist:** `examples/inverting_amp.net`
```
* Inverting Amplifier
V1 VIN 0 1V
R1 VIN NINV 1k
R2 NINV VOUT 10k
U1 GND NINV VCC VEE VOUT
VCC VCC 0 15V
VEE VEE 0 -15V
```

## Advanced Usage

### Custom Scaling

```bash
# Auto-scale (default)
./circuit_to_rm2.sh circuit.net

# 2x scale
./circuit_to_rm2.sh circuit.net 2.0

# 0.5x scale (fit large circuits)
./circuit_to_rm2.sh circuit.net 0.5
```

### Optimized Mode

```bash
# Raw commands (default, fastest)
./circuit_to_rm2.sh circuit.net auto 10.11.99.1 raw

# Optimized commands (reduces redundant pen movements)
./circuit_to_rm2.sh circuit.net auto 10.11.99.1 optimize
```

### WiFi Connection

```bash
# USB connection (default)
./circuit_to_rm2.sh circuit.net auto 10.11.99.1

# WiFi connection (find IP in Settings > Storage)
./circuit_to_rm2.sh circuit.net auto 192.168.1.123
```

## Component Library

### Adding New Components

1. Create SVG file in `./components/` directory
2. Add anchor point circles with IDs `pin1`, `pin2`, etc.
3. Rebuild library: `python3 component_library_builder.py ./components`

**Example SVG structure:**
```xml
<svg width="140" height="32.768864">
  <path id="R" d="M 176,629 h 22 ..." />
  <circle id="pin1" cx="176.09" cy="629.98" r="1" />
  <circle id="pin2" cx="308.59" cy="629.78" r="1" />
</svg>
```

### Pin Conventions

- **2-terminal components** (R, C, L, D): `pin1` (left), `pin2` (right)
- **3-terminal transistors** (BJT, MOSFET): `pin1` (collector/drain), `pin2` (base/gate), `pin3` (emitter/source)
- **Op-Amps**: `pin1` (non-inv), `pin2` (inv), `pin3` (Vcc), `pin4` (Vee), `pin5` (output)

## Placement Algorithm

The circuit placer uses a **blocked structure** algorithm:

1. **Topological Sort**: Orders components for left-to-right signal flow
   - Voltage sources → Components → Ground
   
2. **Grid Placement**: Places components in organized grid
   - Simple circuits (≤3): Single row
   - Medium circuits (4-6): 3×2 grid
   - Complex circuits (7+): Adaptive grid

3. **Wire Routing**: Orthogonal (Manhattan) routing between pins
   - L-shaped paths minimize wire crossings
   - Prioritizes horizontal or vertical based on distance

## Pipeline Internals

### Layer 1: Component Library Builder

**Script:** `component_library_builder.py`

**Functions:**
- `extract_pins_from_svg()`: Parses SVG `<circle id="pinN">` elements
- `svg_to_pen_commands()`: Calls `svg_to_lamp_svgpathtools.py`
- `export_to_header()`: Generates JSON library file

**Output format:**
```json
{
  "R": {
    "width": 140,
    "height": 32.77,
    "bounds": [176, 625, 308, 634],
    "pins": [
      {"id": "pin1", "x": 176.09, "y": 629.98},
      {"id": "pin2", "x": 308.59, "y": 629.78}
    ],
    "pen_commands": [
      "pen down 176 629",
      "pen move 198 629",
      ...
    ]
  }
}
```

### Layer 2: Netlist Parser

**Script:** `netlist_parser.py`

**Classes:**
- `NetlistComponent`: Component instance (ref, type, nodes, value)
- `NetlistNet`: Electrical net (name, connected pins)
- `Circuit`: Complete circuit graph

**Parser:**
- Reads LTSpice format line-by-line
- Maps component prefixes to symbol types
- Builds net connectivity graph

### Layer 3: Circuit Placer & Renderer

**Script:** `circuit_placer.py`

**Classes:**
- `CircuitPlacer`: Auto-placement algorithm
  - `place_circuit()`: Main entry point
  - `_topological_sort()`: Orders components
  - `_place_components_blocked()`: Grid placement
  - `_route_wires()`: Wire routing
  
- `CircuitRenderer`: Converts to pen commands
  - `render()`: Generates final pen commands
  - Auto-scaling and centering
  - Screen bounds checking (1404×1872)

### Layer 4: Transmission

**Script:** `circuit_to_rm2.sh`

**Process:**
1. Check component library freshness
2. Rebuild if components directory updated
3. Parse netlist and place circuit
4. Optionally optimize pen commands
5. SSH transmission to `lamp` on reMarkable 2

## Troubleshooting

### Component Library Issues

**Problem:** "Pin not found in SVG"

**Solution:** Check SVG has `<circle id="pinN">` elements:
```bash
grep 'id="pin' components/R.svg
```

**Problem:** "No pen commands generated"

**Solution:** Verify SVG converter works:
```bash
python3 svg_to_lamp_svgpathtools.py components/R.svg
```

### Netlist Parsing Issues

**Problem:** "Unknown component type"

**Solution:** Check component prefix matches `COMPONENT_MAP` in `netlist_parser.py`. Add custom mappings if needed.

**Problem:** "Net has no connections"

**Solution:** Verify node names match exactly (case-sensitive). Node `0` and `GND` are treated as ground.

### Placement Issues

**Problem:** "Circuit too large for screen"

**Solution:** Use smaller scale:
```bash
./circuit_to_rm2.sh circuit.net 0.5
```

**Problem:** "Components overlapping"

**Solution:** Increase spacing in `circuit_placer.py`:
```python
COMPONENT_SPACING_X = 300  # Increase from 200
COMPONENT_SPACING_Y = 300  # Increase from 200
```

### Connection Issues

**Problem:** "Cannot connect to reMarkable 2"

**Solution:** 
- USB: Check cable, verify IP is `10.11.99.1`
- WiFi: Find IP in Settings > Storage > Scroll down
- Test: `ssh root@10.11.99.1` (password shown on screen)

**Problem:** "lamp binary not found"

**Solution:** Deploy lamp to `/opt/bin/lamp`:
```bash
cd resources/repos/rmkit/src
make lamp
scp build/lamp root@10.11.99.1:/opt/bin/
```

## Performance

### Typical Performance

- **Component Library Build**: ~5-10 seconds (16 symbols)
- **Netlist Parsing**: <1 second
- **Circuit Placement**: 1-2 seconds
- **Transmission**: 2-5 seconds (depends on complexity)

**Total Pipeline**: 5-15 seconds

### Optimization Tips

1. **Use cached library**: Library rebuilds only when components change
2. **Raw mode**: Skip optimization for faster drawing
3. **Simplify netlists**: Fewer components = faster placement
4. **USB connection**: Faster than WiFi

## File Structure

```
.
├── component_library_builder.py   # Layer 1: Build component library
├── netlist_parser.py              # Layer 2: Parse netlists
├── circuit_placer.py              # Layer 3: Place and render
├── circuit_to_rm2.sh              # Layer 4: Orchestration
├── component_library.json         # Component library header (generated)
├── components/                    # SVG symbol files
│   ├── R.svg
│   ├── C.svg
│   ├── L.svg
│   ├── D.svg
│   ├── VDC.svg
│   ├── OPAMP.svg
│   └── ...
├── examples/                      # Example netlists
│   ├── rc_filter.net
│   ├── voltage_divider.net
│   └── inverting_amp.net
└── README.md                      # This file
```

## Future Enhancements

### Planned Features

- [ ] **Command optimization**: Merge redundant pen movements
- [ ] **Component rotation**: Optimize orientation based on connectivity
- [ ] **Multi-layer routing**: Handle wire crossings with jumpers
- [ ] **Subcircuits**: Support hierarchical designs
- [ ] **Component values**: Render text labels for values
- [ ] **Annotation**: Add net names and component references
- [ ] **Interactive placement**: Manual component positioning
- [ ] **Export formats**: Save as SVG, PDF, or PNG

### Advanced Algorithms

- **Force-directed placement**: Physics-based layout optimization
- **A\* routing**: Smarter wire paths avoiding obstacles
- **Hierarchical placement**: Handle large circuits with blocks
- **Symmetry detection**: Optimize symmetric circuit layouts

## Contributing

To add new features or components:

1. Fork the repository
2. Create feature branch
3. Test with multiple example circuits
4. Submit pull request

## License

MIT License - See LICENSE file for details

## Credits

Built on top of:
- **rmkit**: reMarkable UI framework
- **lamp**: Direct pen input tool
- **svg_to_lamp_svgpathtools**: SVG to pen command converter

---

**Version:** 1.0.0  
**Last Updated:** 2025-12-10  
**Author:** Navy (lamp-v2 project)
