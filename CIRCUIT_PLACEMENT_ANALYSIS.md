# Circuit Placement & Routing Analysis

## Current State Assessment

### ✅ Completed Phases

**Phase 1: Eraser Function**
- Enhanced lamp with BTN_TOOL_RUBBER support
- Commands: `eraser line`, `eraser fill`, `eraser clear`
- Status: Production ready

**Phase 2: Normalized SVG Components**
- 16 components with standardized format
- Coordinates normalized to (0,0) origin
- Pin circles marked for anchor points
- Status: Complete

**Phase 3: Relative Coordinate System** (Just Completed)
- `svg_to_lamp_relative.py`: SVG → relative (0.0-1.0) coords
- `draw_component.sh`: Deployment with scaling/positioning
- Comprehensive test suite (all passing)
- Status: Production ready

---

## Critical Issues Identified

### 1. **Circuit Placer Limitations** (`Archive/v2.3/claude/src/circuit_placer.py`)

#### Placement Algorithm (Lines 84-130)
```python
def _place_components_blocked(self, components):
    """Place components in organized blocked structure"""
    # Current: Simple grid layout
    if num_components <= 3:
        cols = num_components
        rows = 1
    elif num_components <= 6:
        cols = 3
        rows = 2
    else:
        cols = math.ceil(math.sqrt(num_components * 1.5))
        rows = math.ceil(num_components / cols)
```

**Problems:**
- ❌ No connectivity awareness (just grid-based)
- ❌ Doesn't minimize wire length
- ❌ No consideration for signal flow
- ❌ Fixed spacing (200 units) regardless of component size
- ❌ No collision detection

#### Wire Routing (Lines 204-234)
```python
def _route_orthogonal(self, net_name, pins):
    """Route wire using orthogonal (Manhattan) routing"""
    # Simple L-shaped paths between pairs
    for i in range(len(pins) - 1):
        x1, y1 = pins[i]
        x2, y2 = pins[i + 1]

        # L-shaped routing (horizontal then vertical)
        if dx > dy:
            points.append((x2, y1))
            points.append((x2, y2))
        else:
            points.append((x1, y2))
            points.append((x2, y2))
```

**Problems:**
- ❌ Only pairwise connections (doesn't create proper multi-point nets)
- ❌ No obstacle avoidance
- ❌ No wire crossing minimization
- ❌ Can't handle complex topologies (loops, feedback)
- ❌ No support for buses or ground planes
- ❌ Routing doesn't respect component orientations

### 2. **Component Library Integration Gap**

Current system has THREE incompatible formats:

1. **Archive/v2.1/component_library_config.json**: SVG group visibility
2. **Archive/v2.2 component_definitions.py**: Anchor point system (Python dataclasses)
3. **Phase 3 assets/components/**: Individual normalized SVGs

**Missing:**
- Unified JSON library with:
  - Component dimensions
  - Pin positions (relative 0.0-1.0)
  - Pen command templates
  - Rotation variants

### 3. **Netlist to Layout Pipeline Broken**

```
Netlist (.net) → Parser → Circuit Graph
                              ↓
                         [BROKEN LINK]
                              ↓
                    Component Placement
                              ↓
                         Wire Routing
                              ↓
                    Phase 3 Rendering
```

**Issues:**
- Netlist parser outputs `NetlistComponent` with nodes
- Circuit placer expects component library with pins/bounds
- No bridge between the two
- Component rotation not propagated to rendering

---

## Textbook Circuit Requirements

Based on your screenshots (RC circuit, RLC loop):

### Common Circuit Patterns Needed

1. **Series Connections**
   ```
   VDC → R → L → C → GND
   (Simple loop, components in line)
   ```

2. **Parallel Connections**
   ```
        ┌──R──┐
   VDC──┤     ├── GND
        └──C──┘
   ```

3. **Voltage Dividers**
   ```
        R1
   VIN──┴──VOUT
        R2
        ┴
       GND
   ```

4. **Filter Circuits**
   - Low-pass: R-C
   - High-pass: C-R
   - Band-pass: RLC

5. **Amplifier Circuits**
   - Inverting op-amp
   - Non-inverting op-amp
   - Common emitter

### Layout Requirements

1. **Left-to-right signal flow**
   - Sources on left
   - Outputs on right
   - Ground at bottom

2. **Minimal wire crossings**
   - Prefer orthogonal (90°) routing
   - Avoid diagonal wires
   - Maintain grid alignment

3. **Visual clarity**
   - Adequate component spacing
   - Clear node labels
   - Readable component values

4. **Standard orientations**
   - Resistors/capacitors: horizontal
   - Voltage sources: vertical (+ up)
   - Ground: pointing down
   - Op-amps: left inputs, right output

---

## Proposed Solution Architecture

### Phase 4: Unified Component Library

**Goal:** Single source of truth for all component data

**File:** `src/component_library.json`

```json
{
  "metadata": {
    "version": "2.0",
    "coordinate_system": "relative_0_1"
  },
  "components": {
    "R": {
      "name": "Resistor",
      "svg_file": "assets/components/R.svg",
      "bbox": {"width": 58.95, "height": 29.47},
      "pins": [
        {"id": "1", "name": "left", "x": 0.0, "y": 0.5, "angle": 180},
        {"id": "2", "name": "right", "x": 1.0, "y": 0.5, "angle": 0}
      ],
      "default_orientation": "horizontal",
      "rotations": [0, 90, 180, 270]
    },
    "VDC": {
      "name": "DC Voltage Source",
      "svg_file": "assets/components/VDC.svg",
      "bbox": {"width": 94.11, "height": 147.06},
      "pins": [
        {"id": "1", "name": "positive", "x": 0.5, "y": 0.0, "angle": 90},
        {"id": "2", "name": "negative", "x": 0.5, "y": 1.0, "angle": 270}
      ],
      "default_orientation": "vertical",
      "polarity": true
    },
    "GND": {
      "name": "Ground",
      "svg_file": "assets/components/GND.svg",
      "bbox": {"width": 100.0, "height": 75.54},
      "pins": [
        {"id": "1", "name": "connection", "x": 0.5, "y": 0.0, "angle": 90}
      ],
      "default_orientation": "down"
    }
  }
}
```

### Phase 5: Intelligent Circuit Placer

**File:** `src/smart_circuit_placer.py`

#### 5.1 Topology-Aware Placement

```python
class SmartCircuitPlacer:
    def analyze_topology(self, circuit):
        """Detect circuit pattern (series, parallel, feedback, etc.)"""
        - Count nodes and degrees
        - Identify loops and branches
        - Classify as: linear, tree, mesh, mixed

    def place_by_pattern(self, circuit, topology):
        """Use template-based placement for common patterns"""
        if topology == "series":
            return self._place_series(circuit)
        elif topology == "parallel":
            return self._place_parallel(circuit)
        elif topology == "voltage_divider":
            return self._place_divider(circuit)
        else:
            return self._place_force_directed(circuit)
```

#### 5.2 Force-Directed Placement

```python
def _place_force_directed(self, circuit):
    """
    Physics-based placement:
    - Connected components attract
    - All components repel
    - Iterate until stable
    """
    # Initialize random positions
    # Apply forces iteratively:
    #   F_spring = k * (distance - ideal_length)
    #   F_repulsion = k / distance^2
    # Update positions
    # Align to grid
```

#### 5.3 Template-Based Layouts

```python
CIRCUIT_TEMPLATES = {
    "rc_lowpass": {
        "pattern": "V-R-C",
        "layout": "horizontal_series",
        "positions": {
            "V": (0, 0),
            "R": (200, 0),
            "C": (400, 0)
        }
    },
    "voltage_divider": {
        "pattern": "V-R1-R2-GND",
        "layout": "vertical_stack",
        "positions": {
            "V": (0, 0),
            "R1": (0, 150),
            "R2": (0, 300),
            "GND": (0, 450)
        }
    }
}
```

### Phase 6: Manhattan Router with Obstacle Avoidance

**File:** `src/manhattan_router.py`

```python
class ManhattanRouter:
    def route_net(self, pins, obstacles):
        """
        A* pathfinding for Manhattan routing

        Steps:
        1. Build grid with obstacles
        2. Find minimal spanning tree of pins
        3. Route each segment with A*
        4. Merge overlapping segments
        5. Straighten unnecessary bends
        """

    def cost_function(self, path):
        """
        Minimize:
        - Total wire length
        - Number of bends
        - Crossings with other wires
        - Proximity to components
        """
```

---

## Implementation Roadmap

### Immediate Priorities (This Week)

1. **Create Unified Component Library**
   - Generate JSON from Phase 3 SVGs
   - Add pin definitions (extract from SVG pin circles)
   - Calculate bounding boxes
   - Tool: `src/build_component_library.py`

2. **Simple Template-Based Placer**
   - Detect series circuits (most common in textbooks)
   - Horizontal layout for series
   - Vertical layout for parallel
   - Tool: `src/template_placer.py`

3. **Basic Manhattan Router**
   - Two-pin routing with A*
   - Grid-based obstacles
   - Multi-pin nets via Steiner tree approximation
   - Tool: `src/basic_router.py`

### Medium Term (Next 2 Weeks)

4. **Topology Detector**
   - Analyze netlist graph structure
   - Classify common patterns
   - Suggest optimal layouts

5. **Force-Directed Placement**
   - For complex circuits without templates
   - Physics simulation
   - Grid alignment post-processing

6. **Enhanced Router**
   - Wire crossing minimization
   - Via support (layer changes)
   - Bus routing
   - Ground plane handling

### Long Term

7. **Interactive Placement**
   - Manual component dragging
   - Constraint-based layout
   - Real-time re-routing

8. **Schematic Beautification**
   - Wire straightening
   - Component alignment
   - Node label placement
   - Value annotation

---

## Example: RC Circuit Pipeline

### Input Netlist (`rc_lowpass.net`)
```
* RC Low-Pass Filter
V1 IN 0 5V
R1 IN OUT 10k
C1 OUT 0 100nF
```

### Phase 4: Load Component Library
```python
library = ComponentLibrary("src/component_library.json")
# Library loaded: R, C, VDC, GND with pin definitions
```

### Phase 5: Intelligent Placement
```python
placer = SmartCircuitPlacer(library)
topology = placer.analyze_topology(circuit)
# Detected: series topology (V → R → C → GND)

placed = placer.place_by_pattern(circuit, "series")
# V1: (100, 400)   - vertical, + at top
# R1: (300, 400)   - horizontal
# C1: (500, 400)   - vertical
# GND: (500, 600)  - pointing down
```

### Phase 6: Manhattan Routing
```python
router = ManhattanRouter(placed, grid_size=10)

# Net "IN": V1.pin1 → R1.pin1
wire_in = router.route_net(["V1.1", "R1.1"])
# Path: (100,350) → (100,400) → (250,400)

# Net "OUT": R1.pin2 → C1.pin1
wire_out = router.route_net(["R1.2", "C1.1"])
# Path: (350,400) → (500,400)

# Net "GND": V1.pin2, C1.pin2 → GND
wire_gnd = router.route_net(["V1.2", "C1.2", "GND.1"])
# Path: (100,450) → (100,600) → (500,600) → (500,550)
#       (500,450) → (500,550)
```

### Phase 3: Render to RM2
```python
# For each component:
draw_component.sh assets/components/VDC.svg --x 100 --y 400 --height 100
draw_component.sh assets/components/R.svg --x 300 --y 400 --width 100
draw_component.sh assets/components/C.svg --x 500 --y 400 --height 100
draw_component.sh assets/components/GND.svg --x 500 --y 600 --width 50

# For each wire:
echo "pen down 100 350" | ssh root@10.11.99.1 /opt/bin/lamp
echo "pen move 100 400" | ssh root@10.11.99.1 /opt/bin/lamp
# ... etc
```

---

## Recommended Next Steps

### Step 1: Build Component Library (Today)
```bash
# Create tool to extract pin positions from SVGs
python3 src/build_component_library.py assets/components/ > src/component_library.json
```

### Step 2: Template Placer (Tomorrow)
```bash
# Implement series/parallel templates
python3 src/template_placer.py rc_lowpass.net component_library.json
```

### Step 3: Basic Router (Day 3)
```bash
# A* Manhattan routing
python3 src/manhattan_router.py placed_circuit.json
```

### Step 4: End-to-End Test (Day 4)
```bash
# Complete pipeline
python3 src/circuit_to_rm2.py examples/rc_lowpass.net --rm2 10.11.99.1
```

---

## Questions for You

1. **Priorities:** Should we focus on:
   - [ ] Template-based layouts (fast, textbook-perfect)
   - [ ] Force-directed (flexible, handles any circuit)
   - [ ] Manual placement UI (full control)

2. **Textbook Circuits:** Which circuits are most important?
   - [ ] Basic filters (RC, RL, RLC)
   - [ ] Voltage dividers
   - [ ] Op-amp circuits
   - [ ] Transistor amplifiers
   - [ ] Digital logic gates

3. **Wire Routing:** Preferences?
   - [ ] Minimize crossings (cleaner, may be longer)
   - [ ] Minimize length (shorter, may cross)
   - [ ] Grid-aligned only (strict Manhattan)
   - [ ] Allow 45° angles (more natural)

4. **Component Values:** Display on schematic?
   - [ ] Show values (10kΩ, 100nF)
   - [ ] Show reference only (R1, C1)
   - [ ] Both

---

## Files to Create

```
src/
├── component_library.json          # Unified component database
├── build_component_library.py      # Generate library from SVGs
├── template_placer.py              # Pattern-based placement
├── manhattan_router.py             # Wire routing engine
├── topology_detector.py            # Circuit pattern recognition
├── circuit_to_rm2.py              # End-to-end pipeline
└── examples/
    ├── textbook_circuits/
    │   ├── rc_lowpass.net
    │   ├── voltage_divider.net
    │   ├── rlc_series.net
    │   ├── inverting_amp.net
    │   └── common_emitter.net
    └── expected_outputs/
        └── (reference images)
```

Let me know your priorities and I'll start building!
