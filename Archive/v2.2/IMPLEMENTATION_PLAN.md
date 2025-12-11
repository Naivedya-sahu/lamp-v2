# lamp-v2 Implementation Plan

**Date:** 2025-12-10
**Goal:** Complete circuit drawing system with netlist-based rendering
**Status:** Implementation Roadmap

---

## Executive Summary

Transform lamp-v2 from a mixed development state into a production-ready circuit drawing system with:

1. **Netlist-to-Circuit Rendering** - Parse SPICE netlists and draw complete circuits
2. **Component Rendering System** - Draw individual, properly-sized components
3. **Block-Based Coordinate System** - Relative positioning with anchor points
4. **Optimal Workspace Layout** - Auto-arrange circuits for any complexity/size
5. **Template-Driven Architecture** - JSON-based component definitions

**Future (Not in this plan):** Dynamic component library with eraser/gestures

---

## Current State Assessment

### ✅ What Works
- **Eraser support** - BTN_TOOL_RUBBER events functional
- **SVG to lamp conversion** - Multiple converters exist
- **Component library** - 214 electrical symbols available
- **Basic circuit builder** - Proof of concept with anchor points
- **Netlist support** - Early implementation exists

### 🔴 Critical Gaps
1. **SVG inconsistencies** - Sizes, scales, and paths not standardized
2. **No unified coordinate system** - Absolute vs relative positioning unclear
3. **No template system** - Component definitions scattered/hardcoded
4. **No workspace optimization** - Manual placement only
5. **Incomplete netlist parser** - Not production-ready
6. **Poor integration** - Systems don't work together seamlessly

### 📊 Code Analysis
```
Existing Assets:
├── circuit_builder.py (437 lines)      - Has anchor points, needs workspace optimizer
├── component_definitions.py (355 lines) - Has fixed sizes, needs templates
├── netlist_parser.py (in claude/)      - Early prototype, needs completion
├── svg_to_lamp_improved.py (709 lines) - Comprehensive but needs standardization
└── Electrical_symbols_library.svg      - 214 components, needs fixing
```

---

## Architecture Overview

### System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INPUT                                   │
│  ┌──────────────────┐           ┌──────────────────┐            │
│  │  Netlist File    │           │  Component Name  │            │
│  │  (.net/.cir)     │           │  + Position      │            │
│  └────────┬─────────┘           └────────┬─────────┘            │
└───────────┼──────────────────────────────┼──────────────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────┐      ┌───────────────────────┐
│  Netlist Parser       │      │  Component Renderer   │
│  ├─ Parse components  │      │  ├─ Load from JSON    │
│  ├─ Parse connections │      │  ├─ Apply transforms  │
│  └─ Build circuit obj │      │  └─ Generate commands │
└───────────┬───────────┘      └───────────┬───────────┘
            │                              │
            └──────────┬───────────────────┘
                       ▼
            ┌─────────────────────┐
            │  Circuit Builder    │
            │  ├─ Workspace calc   │
            │  ├─ Layout optimizer │
            │  ├─ Place components │
            │  ├─ Route wires      │
            │  └─ Generate output  │
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │  Block System       │
            │  ├─ Grid coords      │
            │  ├─ Anchor points    │
            │  └─ Relative offsets │
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │  Template Engine    │
            │  ├─ Load JSON def    │
            │  ├─ Apply scale      │
            │  └─ Generate paths   │
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │  SVG Processor      │
            │  ├─ Normalize paths  │
            │  ├─ Apply transforms │
            │  └─ Extract strokes  │
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │  Lamp Command Gen   │
            │  ├─ pen down/move/up │
            │  ├─ Coordinate trans │
            │  └─ Output .lamp     │
            └──────────┬──────────┘
                       ▼
                ┌──────────┐
                │   LAMP   │ → reMarkable Tablet
                └──────────┘
```

---

## Implementation Phases

## PHASE 0: Repository Reorganization (Foundation)
**Duration:** 1-2 hours
**Priority:** CRITICAL - Must complete first

### Tasks
1. Execute `./reorganize_repo.sh` to establish clean structure
2. Move all files to proper locations
3. Update all import paths
4. Test that existing code still runs

### Deliverables
- ✅ Clean `src/` directory with production code
- ✅ Consolidated `docs/` directory
- ✅ Archived development history
- ✅ Single source of truth for all files

### Validation
```bash
# Test build system
src/build/build_lamp_enhanced.sh

# Test Python imports
python3 -c "from src.core.circuit_builder import Circuit"
python3 -c "from src.core.component_definitions import ComponentLibrary"

# Verify structure
ls -la src/ docs/ config/ assets/
```

---

## PHASE 1: SVG Standardization & Template System
**Duration:** 2-3 days
**Priority:** HIGH - Foundation for everything else

### Problem Statement
Current SVGs have:
- Inconsistent bounding boxes
- Arbitrary scales
- Mixed coordinate systems
- Complex/nested paths
- No standardized anchor points

### Goals
1. **Normalize all 214 SVG components**
   - Fixed, predictable sizes (e.g., R/L/C = 120×48px)
   - Centered at origin (0,0)
   - Simplified paths (no transforms, relative coords only)
   - Standardized anchor points

2. **Create JSON template system**
   - Define components as templates
   - Store normalized SVG paths
   - Include metadata (size, category, anchors)
   - Enable easy modifications

### Architecture

#### Component Template JSON Format
```json
{
  "component_templates": {
    "resistor": {
      "id": "R",
      "name": "Resistor",
      "category": "passive",
      "size": {
        "width": 120,
        "height": 48,
        "unit": "px"
      },
      "anchors": [
        {"name": "left", "x": 0, "y": 24, "direction": "W"},
        {"name": "right", "x": 120, "y": 24, "direction": "E"}
      ],
      "svg_paths": [
        {
          "type": "path",
          "d": "M 0,24 L 20,24 L 25,12 L 35,36 L 45,12 L 55,36 L 65,12 L 75,36 L 85,12 L 95,36 L 100,24 L 120,24",
          "stroke": "black",
          "stroke_width": 2,
          "fill": "none"
        }
      ],
      "svg_source": "g1087",
      "variants": ["resistor_us", "resistor_iec"],
      "value_label": {
        "position": {"x": 60, "y": 60},
        "anchor": "middle"
      }
    },
    "capacitor": {
      "id": "C",
      "name": "Capacitor",
      "category": "passive",
      "size": {"width": 120, "height": 48},
      "anchors": [
        {"name": "left", "x": 0, "y": 24},
        {"name": "right", "x": 120, "y": 24}
      ],
      "svg_paths": [
        {"type": "path", "d": "M 0,24 L 50,24"},
        {"type": "path", "d": "M 50,8 L 50,40"},
        {"type": "path", "d": "M 70,8 L 70,40"},
        {"type": "path", "d": "M 70,24 L 120,24"}
      ]
    },
    "vdc": {
      "id": "V",
      "name": "DC Voltage Source",
      "category": "source",
      "size": {"width": 80, "height": 80},
      "anchors": [
        {"name": "positive", "x": 40, "y": 0, "direction": "N"},
        {"name": "negative", "x": 40, "y": 80, "direction": "S"}
      ],
      "svg_paths": [
        {"type": "circle", "cx": 40, "cy": 40, "r": 35},
        {"type": "path", "d": "M 30,40 L 50,40"},
        {"type": "path", "d": "M 40,48 L 40,52"}
      ]
    }
  }
}
```

#### SVG Normalization Process

**Input:** `examples/Electrical_symbols_library.svg` (214 components)
**Output:** `config/component_templates.json`

```python
# Tool: src/tools/svg_normalizer.py

class SVGNormalizer:
    """Normalize SVG components to standard format"""

    def extract_component(self, svg_group_id: str) -> dict:
        """Extract and normalize a single component"""
        # 1. Extract SVG group by ID
        # 2. Calculate tight bounding box
        # 3. Translate to origin (0,0)
        # 4. Scale to target size (maintain aspect ratio)
        # 5. Simplify paths (convert to relative coords)
        # 6. Remove transforms
        # 7. Flatten nested groups
        # 8. Return normalized template

    def calculate_anchors(self, component_type: str, bbox: BBox) -> list:
        """Auto-calculate anchor points based on component type"""
        # Resistor/Cap/Inductor: left/right at vertical center
        # VDC/VAC: positive/negative at top/bottom center
        # Transistor: base/emitter/collector at standard positions
        # Ground: single anchor at top center

    def simplify_paths(self, svg_path: str) -> str:
        """Convert absolute coords to relative, remove transforms"""
        # Parse path commands
        # Convert M/L/H/V/C to relative (m/l/h/v/c)
        # Merge consecutive commands
        # Round to 2 decimal places
```

### Tasks

#### 1.1 Build SVG Normalization Tool
**File:** `src/tools/svg_normalizer.py`

```bash
python3 src/tools/svg_normalizer.py \
  --input assets/symbols/Electrical_symbols_library.svg \
  --output config/component_templates.json \
  --validate
```

**Features:**
- Extract all 214 components by group ID
- Calculate tight bounding boxes
- Normalize to standard sizes (configurable)
- Auto-detect anchor points
- Simplify path commands
- Validate output

#### 1.2 Define Standard Component Sizes
**File:** `config/component_sizes.yaml`

```yaml
standard_sizes:
  passive_2pin:     # R, L, C
    width: 120
    height: 48
    anchors: [left, right]

  source_2pin:      # V, I
    width: 80
    height: 80
    anchors: [positive, negative]

  semiconductor_3pin:  # BJT, MOSFET
    width: 100
    height: 100
    anchors: [base, collector, emitter]  # or gate, drain, source

  opamp:
    width: 120
    height: 100
    anchors: [v+, v-, in+, in-, out]

  ground:
    width: 60
    height: 40
    anchors: [terminal]

  wire:
    flexible: true
    anchors: [start, end]
```

#### 1.3 Create Template Engine
**File:** `src/core/template_engine.py`

```python
class TemplateEngine:
    """Load and render components from JSON templates"""

    def __init__(self, template_file: str):
        self.templates = self.load_templates(template_file)

    def get_component(self, component_id: str) -> ComponentTemplate:
        """Retrieve component template by ID"""

    def render_to_lamp(self,
                       component_id: str,
                       position: tuple[float, float],
                       scale: float = 1.0,
                       rotation: int = 0) -> list[str]:
        """Render component to lamp commands at position"""
        # 1. Load template
        # 2. Apply scale
        # 3. Apply rotation (0/90/180/270)
        # 4. Translate to position
        # 5. Generate lamp commands

    def get_anchor_position(self,
                           component_id: str,
                           anchor_name: str,
                           position: tuple[float, float]) -> tuple[float, float]:
        """Calculate absolute anchor position given component placement"""
```

#### 1.4 Manual Review & Fixes
- Review auto-normalized components
- Fix any malformed paths
- Adjust anchor points if needed
- Add missing components manually

### Deliverables
- ✅ `src/tools/svg_normalizer.py` - Normalization tool
- ✅ `config/component_templates.json` - All 214 normalized templates
- ✅ `config/component_sizes.yaml` - Standard size definitions
- ✅ `src/core/template_engine.py` - Template rendering engine
- ✅ `tests/test_templates.py` - Template validation tests

### Success Criteria
```python
# Every component has:
assert component.size.width > 0
assert component.size.height > 0
assert len(component.anchors) >= 1
assert all(path.is_normalized() for path in component.svg_paths)

# Can render any component:
lamp_cmds = template_engine.render_to_lamp("R", position=(100, 100))
assert lamp_cmds[0].startswith("pen down")
```

---

## PHASE 2: Block-Based Coordinate System
**Duration:** 1-2 days
**Priority:** HIGH - Required for layout optimization

### Problem Statement
Current system uses absolute pixel coordinates, making:
- Layout optimization difficult
- Component repositioning tedious
- Circuit scaling problematic
- Wire routing complex

### Goals
1. **Grid-based placement** - Components snap to grid blocks
2. **Relative positioning** - Blocks reference each other
3. **Flexible scaling** - Scale entire circuit by changing block size
4. **Anchor-based wiring** - Wires connect via anchor points

### Architecture

#### Block Coordinate System

```
Coordinate Hierarchy:
┌─────────────────────────────────────┐
│  Workspace (reMarkable screen)      │
│  ├─ Origin: (0, 0)                  │
│  ├─ Size: 1404 × 1872 px            │
│  └─ Margin: 50px                    │
│                                      │
│  ┌─────────────────────────────┐   │
│  │  Circuit Canvas              │   │
│  │  ├─ Grid size: 40px          │   │
│  │  ├─ Blocks: (cols × rows)    │   │
│  │  └─ Auto-sized to content    │   │
│  │                               │   │
│  │  Block (0,0)  Block (1,0)    │   │
│  │  ┌─────────┐  ┌─────────┐   │   │
│  │  │ [  R1  ]│──│ [  C1  ]│   │   │
│  │  └─────────┘  └─────────┘   │   │
│  │       │            │         │   │
│  │  Block (0,1)       │         │   │
│  │  ┌─────────┐       │         │   │
│  │  │ [ GND  ]│───────┘         │   │
│  │  └─────────┘                 │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

#### Component in Block

```
Block Coordinate: (bx, by) = (2, 3)
Grid Size: 40px
Block Size: depends on component

Component R1 (120×48px occupies 3×2 blocks):
┌────────┬────────┬────────┐
│        │        │        │  Block row 3
│   R1 Component  │        │
│        │        │        │
├────────┼────────┼────────┤
│        │        │        │  Block row 4
│        │        │        │
└────────┴────────┴────────┘
 Block   Block    Block
 col 2   col 3    col 4

Anchor "left" at block-relative (0, 0.5):
  Absolute pixel pos = (2*40, 3*40 + 48*0.5) = (80, 144)

Anchor "right" at block-relative (3, 0.5):
  Absolute pixel pos = (2*40 + 120, 3*40 + 48*0.5) = (200, 144)
```

#### Implementation

**File:** `src/core/block_system.py`

```python
@dataclass
class BlockCoord:
    """Block-based coordinate"""
    x: int  # Block column
    y: int  # Block row

@dataclass
class BlockSize:
    """Size in blocks"""
    width: int   # Blocks wide
    height: int  # Blocks tall

class BlockSystem:
    """Block-based coordinate system"""

    def __init__(self, grid_size: int = 40):
        self.grid_size = grid_size  # pixels per block

    def block_to_pixel(self, block: BlockCoord) -> tuple[int, int]:
        """Convert block coord to pixel coord"""
        return (block.x * self.grid_size, block.y * self.grid_size)

    def pixel_to_block(self, x: int, y: int) -> BlockCoord:
        """Convert pixel coord to block coord (snap to grid)"""
        return BlockCoord(
            x=round(x / self.grid_size),
            y=round(y / self.grid_size)
        )

    def component_blocks(self, component: ComponentTemplate) -> BlockSize:
        """Calculate how many blocks a component occupies"""
        return BlockSize(
            width=ceil(component.size.width / self.grid_size),
            height=ceil(component.size.height / self.grid_size)
        )

    def anchor_position(self,
                       block: BlockCoord,
                       component: ComponentTemplate,
                       anchor_name: str) -> tuple[int, int]:
        """Calculate absolute pixel position of anchor point"""
        px, py = self.block_to_pixel(block)
        anchor = component.get_anchor(anchor_name)
        return (px + anchor.x, py + anchor.y)

class PlacedComponent:
    """Component placed at a block coordinate"""
    block: BlockCoord
    component: ComponentTemplate
    reference: str  # R1, C1, etc.
    value: str      # 10k, 100nF, etc.
    rotation: int   # 0, 90, 180, 270

    def get_anchor_pixel(self, anchor_name: str, block_system: BlockSystem) -> tuple[int, int]:
        """Get absolute pixel position of this component's anchor"""
        return block_system.anchor_position(self.block, self.component, anchor_name)
```

### Tasks

#### 2.1 Implement Block System
**File:** `src/core/block_system.py`
- Block ↔ pixel conversion
- Component block size calculation
- Anchor position calculation
- Grid snapping

#### 2.2 Update Circuit Builder
**File:** `src/core/circuit_builder.py`
- Replace absolute coordinates with block coordinates
- Update `PlacedComponent` to use blocks
- Update wire routing to use anchor points
- Add block-based collision detection

#### 2.3 Create Block Layout Optimizer
**File:** `src/core/layout_optimizer.py`

```python
class LayoutOptimizer:
    """Optimize component placement to minimize wire length and canvas size"""

    def optimize_layout(self, circuit: Circuit) -> Circuit:
        """
        Given circuit with components and netlist,
        return optimized block placements.

        Algorithm:
        1. Parse netlist to build connectivity graph
        2. Use force-directed layout algorithm
        3. Snap to grid blocks
        4. Minimize canvas size
        5. Ensure no overlaps
        """

    def calculate_canvas_size(self, components: list[PlacedComponent]) -> BlockSize:
        """Calculate minimum canvas size to fit all components"""

    def detect_collisions(self, components: list[PlacedComponent]) -> list[tuple]:
        """Detect overlapping components"""
```

### Deliverables
- ✅ `src/core/block_system.py` - Block coordinate system
- ✅ `src/core/layout_optimizer.py` - Layout optimization
- ✅ Updated `circuit_builder.py` - Block-based placement
- ✅ `tests/test_blocks.py` - Block system tests

---

## PHASE 3: Netlist Parser
**Duration:** 2-3 days
**Priority:** HIGH - Primary user interface

### Problem Statement
Users want to draw circuits from SPICE netlists, not manually place components.

### Goals
1. **Parse standard SPICE netlists** (.net, .cir, .sp)
2. **Extract components and connections**
3. **Build circuit object** ready for layout
4. **Support common formats** (LTspice, ngspice, KiCAD)

### Netlist Format Support

#### Example: RC Filter
```spice
* RC Low-Pass Filter
* Input file: rc_filter.net

V1 1 0 DC 5V
R1 1 2 10k
C1 2 0 100nF
.end
```

#### Parsed Structure
```python
Circuit(
    name="RC Low-Pass Filter",
    components=[
        Component(ref="V1", type="V", nodes=["1", "0"], value="5V", params={"DC": True}),
        Component(ref="R1", type="R", nodes=["1", "2"], value="10k"),
        Component(ref="C1", type="C", nodes=["2", "0"], value="100nF")
    ],
    nets=[
        Net(name="VCC", nodes=["1"], connections=["V1.positive", "R1.left"]),
        Net(name="N1", nodes=["2"], connections=["R1.right", "C1.left"]),
        Net(name="GND", nodes=["0"], connections=["C1.right", "V1.negative"])
    ]
)
```

### Architecture

**File:** `src/core/netlist_parser.py`

```python
class NetlistParser:
    """Parse SPICE netlist files"""

    def __init__(self, template_library: TemplateEngine):
        self.templates = template_library

    def parse_file(self, filepath: str) -> Circuit:
        """Parse netlist file and return Circuit object"""
        with open(filepath) as f:
            return self.parse(f.read())

    def parse(self, netlist_text: str) -> Circuit:
        """Parse netlist text"""
        circuit = Circuit()

        for line in netlist_text.split('\n'):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('*') or line.startswith('.'):
                continue

            # Parse component line
            component = self.parse_component_line(line)
            if component:
                circuit.add_component(component)

        # Build netlist from component connections
        circuit.build_netlist()

        return circuit

    def parse_component_line(self, line: str) -> Component:
        """
        Parse component line:
        R1 1 2 10k         → Resistor
        C1 2 0 100nF       → Capacitor
        V1 1 0 DC 5V       → Voltage source
        Q1 2 1 0 2N2222    → BJT transistor
        """
        parts = line.split()
        ref = parts[0]

        # Determine component type from reference prefix
        comp_type = self.ref_to_type(ref)

        # Extract nodes
        nodes = self.extract_nodes(parts[1:], comp_type)

        # Extract value
        value = self.extract_value(parts, comp_type)

        # Create component
        return Component(
            reference=ref,
            component_type=comp_type,
            nodes=nodes,
            value=value
        )

    def ref_to_type(self, ref: str) -> str:
        """Convert reference prefix to component type"""
        prefix = ref[0].upper()
        mapping = {
            'R': 'R',      # Resistor
            'C': 'C',      # Capacitor
            'L': 'L',      # Inductor
            'V': 'V',      # Voltage source
            'I': 'I',      # Current source
            'D': 'D',      # Diode
            'Q': 'BJT',    # BJT transistor
            'M': 'MOSFET', # MOSFET
            'U': 'OPAMP',  # Op-amp (if integrated)
        }
        return mapping.get(prefix, 'UNKNOWN')

    def build_netlist(self, circuit: Circuit):
        """Build net connections from component node lists"""
        # Group components by shared nodes
        # Create Net objects with connection lists
        # Map node numbers to net names (0=GND, others auto-name)

@dataclass
class Component:
    reference: str       # R1, C1, Q1
    component_type: str  # R, C, BJT
    nodes: list[str]     # Node connections
    value: str           # 10k, 100nF, 2N2222
    params: dict = None  # Additional parameters

@dataclass
class Net:
    name: str                    # VCC, GND, N1
    nodes: list[str]             # SPICE node numbers
    connections: list[str]       # ["R1.left", "V1.positive"]

class Circuit:
    name: str
    components: list[Component]
    nets: list[Net]

    def add_component(self, component: Component):
        """Add component to circuit"""

    def build_netlist(self):
        """Build net connections from component nodes"""
        # Node 0 is always GND
        # Other nodes get auto-named (N1, N2, ...)
        # Special nodes can be named (VCC, VDD, etc.)

    def map_component_to_template(self, component: Component) -> ComponentTemplate:
        """Map parsed component to template for rendering"""
```

### Netlist Formats

#### LTspice Format
```spice
* LTspice RC Filter
V1 N001 0 5
R1 N001 N002 10k
C1 N002 0 100n
.tran 1m
.end
```

#### ngspice Format
```spice
.title RC Filter
V1 1 0 DC 5V
R1 1 2 10k
C1 2 0 100nF
.control
tran 1us 10ms
plot v(2)
.endc
.end
```

#### KiCAD Export Format
```spice
.title KiCad schematic
R1 Net-1 Net-2 10k
C1 Net-2 GND 100nF
V1 Net-1 GND DC 5
.end
```

### Tasks

#### 3.1 Build Netlist Parser Core
- Parse component lines (R, C, L, V, I, D, Q, M)
- Extract nodes, values, parameters
- Handle comments and directives
- Support multiple formats

#### 3.2 Build Netlist Analyzer
- Group components by nets
- Detect ground node (0, GND)
- Auto-name nets (VCC, N1, N2, ...)
- Build connectivity graph

#### 3.3 Component-to-Template Mapper
- Map SPICE component types to templates
- Handle component variants (resistor types, etc.)
- Apply default values if missing

#### 3.4 Netlist Validation
- Check for floating nodes
- Detect shorts
- Verify all components have templates
- Warn about unsupported components

### Deliverables
- ✅ `src/core/netlist_parser.py` - Parser implementation
- ✅ `tests/test_netlist_parser.py` - Parser tests
- ✅ `assets/examples/test_netlists/` - Test netlists
- ✅ `docs/user-guide/netlist-format.md` - Format documentation

---

## PHASE 4: Workspace Optimizer
**Duration:** 2-3 days
**Priority:** MEDIUM - Nice-to-have for complex circuits

### Problem Statement
Circuits need to be automatically laid out to:
- Minimize wire lengths
- Fit within reMarkable screen (1404×1872)
- Look visually clean
- Handle any complexity/size

### Goals
1. **Auto-arrange components** from netlist
2. **Minimize wire crossings** and lengths
3. **Scale to fit workspace** (zoom in/out)
4. **Handle complex circuits** (50+ components)

### Algorithm: Force-Directed Layout

```python
class ForceDirectedLayout:
    """
    Physics-based layout algorithm:
    - Connected components attract each other
    - All components repel each other
    - Iterate until stable
    """

    def layout(self, circuit: Circuit) -> dict[str, BlockCoord]:
        """
        Return optimal block positions for all components

        Algorithm:
        1. Initialize: random or heuristic positions
        2. Calculate forces:
           - Attraction: connected components pull together
           - Repulsion: all components push apart
           - Gravity: slight pull toward center
        3. Update positions based on net force
        4. Snap to grid blocks
        5. Resolve collisions
        6. Repeat until convergence or max iterations
        """

        positions = self.initialize_positions(circuit)

        for iteration in range(max_iterations):
            forces = self.calculate_forces(circuit, positions)
            positions = self.apply_forces(positions, forces)
            positions = self.snap_to_grid(positions)
            positions = self.resolve_collisions(positions, circuit)

            if self.is_converged(positions):
                break

        return positions
```

### Alternative: Hierarchical Layout

For complex circuits, use hierarchical approach:
1. Identify subcircuits (clusters)
2. Layout each subcircuit independently
3. Layout subcircuits relative to each other
4. Flatten to final layout

### Tasks

#### 4.1 Implement Force-Directed Layout
- Attraction/repulsion forces
- Grid snapping
- Collision resolution
- Convergence detection

#### 4.2 Implement Workspace Scaling
- Calculate bounding box of circuit
- Scale to fit reMarkable screen
- Maintain aspect ratio
- Apply zoom factor

#### 4.3 Add Layout Heuristics
- Power rails at top/bottom
- Ground at bottom
- Signal flow left-to-right
- Symmetrical layouts

#### 4.4 Wire Routing
- Orthogonal (Manhattan) routing
- Avoid component overlaps
- Minimize crossings
- Use anchor points

### Deliverables
- ✅ `src/core/layout_optimizer.py` - Layout algorithms
- ✅ `src/core/wire_router.py` - Wire routing
- ✅ `tests/test_layout.py` - Layout tests

---

## PHASE 5: Integration & End-to-End System
**Duration:** 2-3 days
**Priority:** CRITICAL - Ties everything together

### Goals
1. **Complete pipeline**: Netlist → Circuit → Layout → Lamp commands
2. **Two usage modes**: Full circuit or individual component
3. **Command-line interface** for easy use
4. **Validation and testing** at each stage

### System Integration

**File:** `src/circuit_to_lamp.py` (Main entry point)

```python
#!/usr/bin/env python3
"""
circuit_to_lamp.py - Convert SPICE netlist to lamp drawing commands

Usage:
  # Draw complete circuit from netlist
  python3 circuit_to_lamp.py input.net -o output.lamp

  # Draw single component at position
  python3 circuit_to_lamp.py --component R --position 100,200 -o r1.lamp

  # Draw with custom scale
  python3 circuit_to_lamp.py input.net --scale 1.5 -o output.lamp

  # Optimize layout
  python3 circuit_to_lamp.py input.net --optimize -o output.lamp
"""

from src.core.netlist_parser import NetlistParser
from src.core.template_engine import TemplateEngine
from src.core.block_system import BlockSystem
from src.core.layout_optimizer import LayoutOptimizer
from src.core.circuit_builder import CircuitBuilder

class CircuitToLamp:
    """Main orchestrator"""

    def __init__(self):
        self.templates = TemplateEngine("config/component_templates.json")
        self.parser = NetlistParser(self.templates)
        self.blocks = BlockSystem(grid_size=40)
        self.optimizer = LayoutOptimizer()
        self.builder = CircuitBuilder(self.templates, self.blocks)

    def netlist_to_lamp(self, netlist_file: str, optimize: bool = True) -> str:
        """
        Complete pipeline: netlist → circuit → layout → lamp commands
        """
        # 1. Parse netlist
        circuit = self.parser.parse_file(netlist_file)

        # 2. Optimize layout (optional)
        if optimize:
            circuit = self.optimizer.optimize_layout(circuit)

        # 3. Build circuit (place components, route wires)
        self.builder.set_circuit(circuit)

        # 4. Generate lamp commands
        lamp_commands = self.builder.render()

        return lamp_commands

    def component_to_lamp(self,
                         component_id: str,
                         position: tuple[int, int],
                         scale: float = 1.0) -> str:
        """
        Draw single component at position
        """
        return self.templates.render_to_lamp(component_id, position, scale)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert circuit netlist to lamp commands")

    # Mutually exclusive: netlist OR component
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("netlist", nargs='?', help="Input netlist file (.net, .cir)")
    group.add_argument("--component", help="Component ID (R, C, L, V, etc.)")

    # Common options
    parser.add_argument("-o", "--output", required=True, help="Output .lamp file")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale factor")
    parser.add_argument("--optimize", action="store_true", help="Optimize layout")
    parser.add_argument("--position", help="Position for component (x,y)")

    args = parser.parse_args()

    converter = CircuitToLamp()

    if args.netlist:
        # Full circuit mode
        lamp_commands = converter.netlist_to_lamp(args.netlist, args.optimize)
    else:
        # Single component mode
        if not args.position:
            print("Error: --position required for component mode")
            return 1
        x, y = map(int, args.position.split(','))
        lamp_commands = converter.component_to_lamp(args.component, (x, y), args.scale)

    # Write output
    with open(args.output, 'w') as f:
        f.write(lamp_commands)

    print(f"Generated {len(lamp_commands.splitlines())} lamp commands")
    print(f"Output: {args.output}")

if __name__ == "__main__":
    main()
```

### Usage Examples

#### Example 1: Draw RC Filter Circuit
```bash
# Input: assets/examples/rc_filter.net
python3 src/circuit_to_lamp.py \
  assets/examples/rc_filter.net \
  --optimize \
  -o rc_filter.lamp

# Deploy to tablet
cat rc_filter.lamp | ssh root@10.11.99.1 lamp
```

#### Example 2: Draw Single Resistor
```bash
python3 src/circuit_to_lamp.py \
  --component R \
  --position 500,800 \
  --scale 1.5 \
  -o resistor.lamp

cat resistor.lamp | ssh root@10.11.99.1 lamp
```

#### Example 3: Draw Complex Circuit
```bash
# Input: 50+ component circuit
python3 src/circuit_to_lamp.py \
  assets/examples/audio_amplifier.net \
  --optimize \
  --scale 0.8 \
  -o amp.lamp
```

### Tasks

#### 5.1 Create Main Entry Point
- `src/circuit_to_lamp.py` with CLI
- Integrate all systems
- Add error handling
- Add progress output

#### 5.2 End-to-End Testing
- Test with simple circuits (RC, RL, RLC)
- Test with medium circuits (amplifiers, filters)
- Test with complex circuits (50+ components)
- Validate output visually on tablet

#### 5.3 Create Example Netlists
```
assets/examples/netlists/
├── rc_lowpass.net        # Simple 3-component filter
├── voltage_divider.net   # 2 resistors
├── bjt_amplifier.net     # 10-component amp
├── opamp_inverting.net   # Op-amp circuit
└── full_audio_amp.net    # 50+ components
```

#### 5.4 Documentation
- User guide: How to use circuit_to_lamp.py
- Netlist format reference
- Examples and tutorials
- Troubleshooting guide

### Deliverables
- ✅ `src/circuit_to_lamp.py` - Main CLI tool
- ✅ `assets/examples/netlists/` - Example circuits
- ✅ `tests/test_integration.py` - End-to-end tests
- ✅ `docs/user-guide/getting-started.md` - User guide

---

## PHASE 6: Testing & Validation
**Duration:** 1-2 days
**Priority:** HIGH - Ensure quality

### Test Strategy

#### Unit Tests
```
tests/
├── test_template_engine.py      # Template loading/rendering
├── test_block_system.py         # Block coordinates
├── test_netlist_parser.py       # Netlist parsing
├── test_layout_optimizer.py     # Layout algorithms
├── test_circuit_builder.py      # Circuit building
└── test_integration.py          # End-to-end
```

#### Integration Tests
```python
def test_rc_filter_netlist_to_lamp():
    """Test complete pipeline with RC filter"""
    converter = CircuitToLamp()
    lamp_cmds = converter.netlist_to_lamp("tests/data/rc_filter.net")

    # Validate output
    assert "pen down" in lamp_cmds
    assert "pen up" in lamp_cmds
    assert lamp_cmds.count("pen down") >= 3  # At least 3 components

def test_component_rendering():
    """Test individual component rendering"""
    converter = CircuitToLamp()
    lamp_cmds = converter.component_to_lamp("R", (100, 100))

    assert lamp_cmds.startswith("pen down")
    assert lamp_cmds.endswith("pen up\n")
```

#### Visual Tests
- Draw circuits on reMarkable tablet
- Verify component sizes
- Check wire connections
- Validate layout quality

### Test Data
```
tests/data/
├── simple_rc.net          # 3 components
├── voltage_divider.net    # 2 resistors
├── complex_amp.net        # 20+ components
├── malformed.net          # Invalid netlist (should error)
└── expected/
    ├── simple_rc.lamp     # Expected output
    └── voltage_divider.lamp
```

### Validation Criteria
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Visual tests look correct on tablet
- ✅ Performance: <5s for 50-component circuit
- ✅ No crashes on malformed input
- ✅ Error messages are clear and helpful

---

## Project Timeline

### Week 1: Foundation
- ✅ **Day 1**: Phase 0 - Repository reorganization
- 🔨 **Day 2-3**: Phase 1 - SVG normalization tool
- 🔨 **Day 4-5**: Phase 1 - Template system

### Week 2: Core Systems
- 🔨 **Day 1-2**: Phase 2 - Block system
- 🔨 **Day 3-4**: Phase 3 - Netlist parser
- 🔨 **Day 5**: Phase 3 - Testing

### Week 3: Integration
- 🔨 **Day 1-2**: Phase 4 - Layout optimizer
- 🔨 **Day 3-4**: Phase 5 - Integration
- 🔨 **Day 5**: Phase 6 - Testing

### Week 4: Polish
- 🔨 **Day 1-2**: Documentation
- 🔨 **Day 3**: Bug fixes
- 🔨 **Day 4-5**: Final validation & release

**Total: ~20 working days (4 weeks)**

---

## Success Metrics

### Feature 1: Draw Circuit from Netlist ✅
```bash
# Create netlist
cat > my_circuit.net <<EOF
* My RC Filter
V1 1 0 DC 5V
R1 1 2 10k
C1 2 0 100nF
.end
EOF

# Generate lamp commands
python3 src/circuit_to_lamp.py my_circuit.net -o output.lamp

# Draw on tablet
cat output.lamp | ssh root@10.11.99.1 lamp

# Expected: Complete circuit drawn correctly on tablet
```

### Feature 2: Draw Individual Component ✅
```bash
# Draw resistor at position
python3 src/circuit_to_lamp.py \
  --component R \
  --position 500,800 \
  -o resistor.lamp

cat resistor.lamp | ssh root@10.11.99.1 lamp

# Expected: Single resistor drawn at correct position and size
```

### Quality Metrics
- ✅ Components are correctly sized and proportioned
- ✅ Wire connections match netlist
- ✅ Layout fits within reMarkable screen
- ✅ No overlapping components (unless unavoidable)
- ✅ Circuits are visually clear and readable
- ✅ Performance: <5s for typical circuits

---

## Risk Mitigation

### Risk 1: SVG Complexity
**Risk:** Some SVGs too complex to normalize automatically
**Mitigation:** Manual review and fixes, create simplified versions

### Risk 2: Layout Quality
**Risk:** Auto-layout produces poor results for some circuits
**Mitigation:** Add manual placement override, improve heuristics

### Risk 3: Netlist Format Variations
**Risk:** Many SPICE dialects, hard to support all
**Mitigation:** Focus on common formats (LTspice, ngspice), document limitations

### Risk 4: Performance
**Risk:** Large circuits (100+ components) too slow
**Mitigation:** Optimize algorithms, add caching, consider simplification

---

## Future Enhancements (Not in This Plan)

These are explicitly excluded per your requirements:

### ❌ Dynamic Component Library (Future)
- Gesture-based component selection
- Eraser function integration
- Real-time component swapping
- **Status:** Deferred to future release

### Other Future Ideas
- Rotation support (90/180/270°)
- Component value labels (text rendering)
- SPICE simulation integration
- Export to KiCAD/EagleCAD formats
- Interactive editing on tablet
- Multi-page schematics

---

## Development Guidelines

### Code Style
- Python 3.9+
- Type hints for all functions
- Docstrings for all public methods
- PEP 8 compliance

### Git Workflow
```bash
# Feature branches
git checkout -b feature/svg-normalizer
git checkout -b feature/netlist-parser

# Commit messages
git commit -m "Add SVG normalization tool

- Extracts components from library SVG
- Normalizes to standard sizes
- Auto-calculates anchor points
- Generates component_templates.json

Closes #123"
```

### Testing
- Write tests before or alongside implementation
- Aim for 80%+ code coverage
- Run tests before committing: `pytest tests/`

### Documentation
- Update docs/ as features are added
- Include code examples in docstrings
- Keep README.md up to date

---

## Appendix A: File Structure (After Reorganization)

```
lamp-v2/
├── src/
│   ├── core/
│   │   ├── template_engine.py        # [NEW] Load/render templates
│   │   ├── block_system.py           # [NEW] Block coordinates
│   │   ├── netlist_parser.py         # [NEW] Parse SPICE netlists
│   │   ├── layout_optimizer.py       # [NEW] Auto-layout
│   │   ├── wire_router.py            # [NEW] Wire routing
│   │   ├── circuit_builder.py        # [UPDATED] Use blocks
│   │   └── component_definitions.py  # [UPDATED] Use templates
│   ├── tools/
│   │   ├── svg_normalizer.py         # [NEW] Normalize SVGs
│   │   └── component_selector.py     # [EXISTING] Interactive selector
│   └── circuit_to_lamp.py            # [NEW] Main CLI tool
│
├── config/
│   ├── component_templates.json      # [NEW] Normalized templates
│   ├── component_sizes.yaml          # [NEW] Standard sizes
│   └── examples/
│       └── custom_config.json
│
├── assets/
│   ├── symbols/
│   │   ├── Electrical_symbols_library.svg   # [EXISTING]
│   │   └── individual/               # [NEW] Extracted SVGs
│   └── examples/
│       └── netlists/                 # [NEW] Example circuits
│           ├── rc_filter.net
│           ├── voltage_divider.net
│           └── amplifier.net
│
├── tests/
│   ├── test_template_engine.py       # [NEW]
│   ├── test_block_system.py          # [NEW]
│   ├── test_netlist_parser.py        # [NEW]
│   ├── test_layout_optimizer.py      # [NEW]
│   └── test_integration.py           # [NEW]
│
└── docs/
    └── user-guide/
        ├── netlist-format.md         # [NEW]
        └── getting-started.md        # [NEW]
```

---

## Appendix B: Example Workflows

### Workflow 1: Create New Circuit
```bash
# 1. Write netlist in text editor
cat > my_filter.net <<EOF
* Band-Pass Filter
V1 1 0 AC 1V
R1 1 2 1k
C1 2 3 100nF
L1 3 0 10mH
.end
EOF

# 2. Generate lamp commands
python3 src/circuit_to_lamp.py my_filter.net --optimize -o filter.lamp

# 3. Preview (optional - check line count)
wc -l filter.lamp

# 4. Deploy to tablet
cat filter.lamp | ssh root@10.11.99.1 lamp

# 5. View on reMarkable screen
```

### Workflow 2: Add Custom Component
```bash
# 1. Extract from library
python3 src/tools/svg_normalizer.py \
  --extract g1234 \
  --output config/my_component.json

# 2. Edit JSON template
nano config/my_component.json
# Add to component_templates.json

# 3. Test rendering
python3 src/circuit_to_lamp.py \
  --component MY_COMP \
  --position 500,800 \
  -o test.lamp
```

### Workflow 3: Debug Layout
```bash
# 1. Generate with debug info
python3 src/circuit_to_lamp.py my_circuit.net --debug -o output.lamp

# 2. Check component placements
grep "# Component" output.lamp

# 3. Check wire routes
grep "# Wire" output.lamp

# 4. Manual adjustment if needed
nano my_circuit.net  # Adjust component order
```

---

## Next Immediate Action

**START HERE:**

1. **Review and approve this plan** ✋
   - Read through each phase
   - Ask questions if anything is unclear
   - Suggest modifications

2. **Execute Phase 0: Reorganization** 🚀
   ```bash
   ./reorganize_repo.sh --dry-run  # Preview first
   ./reorganize_repo.sh            # Execute
   git commit -m "Reorganize repository structure"
   git push
   ```

3. **Begin Phase 1: SVG Normalization** 🔨
   - Start building `src/tools/svg_normalizer.py`
   - Process first 10 components as proof-of-concept
   - Validate output

**Questions?** Let me know if you want to:
- Modify any phase
- Change priorities
- Add/remove features
- Adjust timeline

**Ready to proceed?** Say "Let's start Phase 0" and I'll begin the reorganization! 🎯
