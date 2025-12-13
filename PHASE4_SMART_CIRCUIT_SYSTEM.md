
# Phase 4-6: Smart Circuit Placement & Routing System

Complete intelligent circuit layout system for ECE bachelor's degree circuits.

## Overview

Building on Phase 3's component rendering, this system adds:
- **Phase 4**: Unified component library with pin metadata
- **Phase 5**: Template-based intelligent placement
- **Phase 6**: Manhattan routing with A* pathfinding

Designed for progressive complexity: from basic filters to advanced amplifiers and oscillators.

## Architecture

```
SPICE Netlist (.net)
      ↓
  Netlist Parser → JSON
      ↓
  Topology Detector (series, parallel, filters, amplifiers, etc.)
      ↓
  Template Placer → Placed Components (x, y positions)
      ↓
  Manhattan Router (A* pathfinding) → Wire Paths
      ↓
  Component Renderer (Phase 3) → RM2
```

## Components

### 1. Component Library (`src/component_library.json`)

**Generated from Phase 3 SVGs with extracted pin metadata:**

```json
{
  "components": {
    "R": {
      "name": "Resistor",
      "category": "passive",
      "bbox": {"width": 58.95, "height": 29.47},
      "pins": [
        {"id": "1", "x": 0.0, "y": 0.5, "angle": 180},
        {"id": "2", "x": 1.0, "y": 0.5, "angle": 0}
      ],
      "default_orientation": "horizontal"
    }
  }
}
```

**16 components**: R, C, L, D, ZD, VDC, VAC, GND, OPAMP, NPN_BJT, PNP_BJT, N_MOSFET, P_MOSFET, P_CAP, SW_OP, SW_CL

### 2. Tools

**`src/build_component_library.py`**
- Extracts pin positions from SVG pin circles
- Calculates bounding boxes
- Determines pin angles (wire direction)
- Generates unified library JSON

**`src/netlist_to_json.py`**
- Parses SPICE netlist format
- Supports standard ECE components (R, C, L, V, Q, M, U, etc.)
- Builds net connectivity graph
- Outputs JSON for pipeline

**`src/template_placer.py`**
- Detects circuit topology patterns
- Applies optimal layouts per topology:
  - **Series**: Horizontal chain (filters, resonant circuits)
  - **Voltage Divider**: Vertical stack
  - **Parallel**: Stacked branches
  - **Op-amp**: Centered with peripherals
  - **Amplifier**: Transistor-based layouts
- Calculates absolute pin positions

**`src/manhattan_router.py`**
- A* pathfinding on grid
- Orthogonal (90°) routing only
- Obstacle avoidance (component boundaries)
- Multi-pin net routing via MST approximation
- Path simplification (removes collinear points)

**`src/circuit_to_rm2.py`**
- End-to-end pipeline orchestrator
- Auto-scaling to fit RM2 screen
- Integrates with Phase 3 rendering
- Dry-run and live RM2 modes

## Usage

### Quick Start

```bash
# 1. Build component library (one-time)
python3 src/build_component_library.py assets/components/ > src/component_library.json

# 2. Create circuit netlist
cat > my_circuit.net << 'EOF'
* RC Low-Pass Filter
V1 IN 0 5V
R1 IN OUT 10k
C1 OUT 0 100nF
EOF

# 3. Render to RM2
python3 src/circuit_to_rm2.py my_circuit.net --rm2 10.11.99.1

# Or test without RM2
python3 src/circuit_to_rm2.py my_circuit.net --dry-run
```

### Individual Tools

```bash
# Parse netlist to JSON
python3 src/netlist_to_json.py examples/ece_circuits/rc_lowpass.net > circuit.json

# Place components (topology-aware)
python3 src/template_placer.py circuit.json src/component_library.json > placed.json

# Route wires
python3 src/manhattan_router.py placed.json > routed.json
```

## Supported Circuit Topologies

### 1. Series Circuits
```
VDC → R → L → C → GND
```
**Layout**: Horizontal chain, left-to-right signal flow

**Examples**:
- RC low-pass filter
- RL circuit
- RLC resonant circuit

### 2. Voltage Dividers
```
    VDC
     |
    R1
     |-- VOUT
    R2
     |
    GND
```
**Layout**: Vertical stack

**Use**: Voltage scaling, biasing

### 3. Parallel Circuits
```
        ┌── R ──┐
   VDC──┤       ├── GND
        └── C ──┘
```
**Layout**: Stacked branches

**Use**: RC parallel, current dividers

### 4. Amplifier Circuits *(future extension)*
- Common emitter (CE)
- Common collector (CC)
- Op-amp inverting/non-inverting

### 5. Oscillators *(future extension)*
- Wien bridge
- Colpitts
- Hartley

## Example Circuits

Located in `examples/ece_circuits/`:

**`rc_lowpass.net`** - Basic RC low-pass filter
```
V1 IN 0 5V
R1 IN OUT 10k
C1 OUT 0 100nF
```

**`voltage_divider.net`** - Resistive divider
```
V1 VIN 0 12V
R1 VIN VOUT 10k
R2 VOUT 0 10k
```

**`rlc_series.net`** - RLC resonant circuit
```
V1 IN 0 5V
R1 IN N1 100
L1 N1 N2 10mH
C1 N2 0 100nF
```

**`rl_circuit.net`** - RL transient response
```
V1 IN 0 12V
R1 IN OUT 1k
L1 OUT 0 100mH
```

**`rc_highpass.net`** - High-pass filter
```
V1 IN 0 5V
C1 IN OUT 100nF
R1 OUT 0 10k
```

## Circuit Pipeline Details

### Step 1: Topology Detection

**Algorithm**:
```python
- Count sources, passives, active components
- Analyze net connectivity (node degrees)
- Classify as: series, parallel, divider, amplifier, oscillator
```

**Heuristics**:
- Most nodes degree-2 → Series
- Some nodes degree >2 → Parallel
- One active component + feedback → Amplifier/Oscillator
- Two resistors in series → Voltage divider

### Step 2: Template Placement

**Series Layout**:
- Sources vertical (+ at top)
- Passives horizontal
- GND pointing down
- Spacing: 250px between components

**Parallel Layout**:
- Source on left
- Branches vertically stacked (200px apart)
- GND on right

**Extensible**: Add templates for new topologies

### Step 3: Manhattan Routing

**A* Cost Function**:
```python
cost = wire_length
     + 0.5 * direction_changes  # Prefer straight lines
     + 100 * obstacles_crossed  # Avoid components
```

**Multi-pin nets**:
1. Build MST of pins
2. Route each MST edge with A*
3. Merge overlapping segments

**Grid**: 10px spacing for fine control

### Step 4: Rendering

**Auto-scaling**:
- Calculate circuit bounding box
- Scale to fit 1404×1872 screen with 100px margins
- Cap at 2.0× max scale

**Component rendering**: Uses Phase 3 `draw_component.sh`

**Wire rendering**: Direct pen commands

## Netlist Format

Supports standard SPICE format:

```
* Comments start with asterisk
* Component format: REF N1 N2 [N3 ...] [VALUE]

V1 1 0 5V           # Voltage source: 5V between nodes 1 and 0
R1 1 2 10k          # Resistor: 10kΩ between nodes 1 and 2
C1 2 0 100nF        # Capacitor: 100nF between nodes 2 and 0
Q1 C B E NPN        # BJT: Collector Base Emitter, NPN model
M1 D G S NMOS       # MOSFET: Drain Gate Source, NMOS model
U1 IN+ IN- VCC VEE OUT  # Op-amp: 5 terminals

.end                # Optional end marker (ignored)
```

**Node naming**:
- `0` or `GND` → Ground
- Any alphanumeric → Named net
- Case-insensitive

**Component prefixes**:
- `R` → Resistor
- `C` → Capacitor
- `L` → Inductor
- `D` → Diode
- `ZD` → Zener diode
- `V` → DC voltage source
- `I` → DC current source
- `Q` → NPN transistor
- `M` → N-channel MOSFET
- `U` → Op-amp

## Extending the System

### Adding New Component

1. **Create normalized SVG** (Phase 2)
   - Pin circles with `id="pin1"`, `id="pin2"`, etc.
   - Coordinates start at (0,0)

2. **Add to component type map**
   ```python
   # In build_component_library.py
   COMPONENT_TYPES = {
       'NEW_COMP': {
           'name': 'New Component',
           'category': 'passive',
           'default_orientation': 'horizontal'
       }
   }
   ```

3. **Rebuild library**
   ```bash
   python3 src/build_component_library.py assets/components/ > src/component_library.json
   ```

### Adding New Topology Template

```python
# In template_placer.py
def _place_my_topology(self, circuit):
    placed = []
    # Custom placement logic
    return placed

# In place() method:
elif topology == 'my_topology':
    return self._place_my_topology(circuit)
```

### Improving Router

**Future enhancements**:
- Multi-layer routing (vias)
- Wire crossing cost minimization
- Bus routing (parallel wires)
- Ground plane handling
- Dynamic obstacle updates

## Test Results

**RC Low-Pass Filter**:
```
Detected topology: rc_filter
Placed: 3 components
Routed 3 nets: IN (5 points), GND (5 points), OUT (2 points)
Scale: 1.43×
Status: ✓ Renders correctly
```

**Voltage Divider**:
```
Detected topology: voltage_divider
Placed: 3 components (vertical stack)
Routed 3 nets
Status: ✓ Renders correctly
```

**RLC Series**:
```
Detected topology: rlc_filter
Placed: 4 components
Routed 4 nets
Status: ✓ Renders correctly
```

## Performance

- **Netlist parsing**: <10ms
- **Topology detection**: <5ms
- **Component placement**: <20ms
- **Wire routing (A*)**: 50-200ms per net
- **Total pipeline**: <1s for basic circuits

## Limitations & Future Work

**Current limitations**:
1. No component rotation in rendering (always 0°)
2. Simplified topology detection (heuristic-based)
3. No manual placement override
4. Wire crossings not tracked

**Planned improvements**:
1. **Force-directed placement** for complex circuits
2. **Advanced topology patterns** (feedback loops, differential pairs)
3. **Component rotation** in final rendering
4. **Interactive placement editor**
5. **Schematic beautification** (auto-align, straighten)
6. **Component value labels** (optional display)
7. **Multi-sheet circuits**

## Integration with Previous Phases

**Phase 1**: Eraser commands (separate feature)

**Phase 2**: Normalized SVG components
- Input for component library

**Phase 3**: Relative coordinate rendering
- `draw_component.sh` used for component rendering
- `svg_to_lamp_relative.py` generates pen commands

**Phase 4-6**: Smart circuit system
- Uses Phase 3 tools for final rendering
- Adds intelligence layer: placement + routing

## Files Created

```
src/
├── component_library.json          # Unified component database (567 lines)
├── build_component_library.py      # Library generator (250 lines)
├── netlist_to_json.py             # SPICE parser (150 lines)
├── template_placer.py             # Intelligent placement (450 lines)
├── manhattan_router.py            # A* routing engine (400 lines)
└── circuit_to_rm2.py              # End-to-end pipeline (250 lines)

examples/ece_circuits/
├── rc_lowpass.net                 # RC low-pass filter
├── rc_highpass.net                # RC high-pass filter
├── voltage_divider.net            # Resistive divider
├── rlc_series.net                 # RLC resonant circuit
└── rl_circuit.net                 # RL transient

Total: ~1500 lines of production Python code
```

## License

MIT License - See main LICENSE file

## References

- **Phase 3**: [PHASE3_README.md](PHASE3_README.md)
- **Component Architecture**: [COMPONENT_SYSTEM_ARCHITECTURE.md](COMPONENT_SYSTEM_ARCHITECTURE.md)
- **Analysis**: [CIRCUIT_PLACEMENT_ANALYSIS.md](CIRCUIT_PLACEMENT_ANALYSIS.md)
