# Smart Routing System - Textbook-Style Circuits

## New Routing Algorithm Features

The circuit placer now intelligently detects circuit topology and applies appropriate routing:

### 1. **Topology Detection**

**Series Circuit:**
- Components form a chain: `V → R → C → GND`
- Each component connects to different nodes

**Parallel Circuit:**
- Multiple components share the same two nodes
- Example: R and C both connect between VIN and GND

### 2. **Series Routing**

For series circuits, the router creates clean rectangular paths with:

**Features:**
- **Series spacing**: `SERIES_SPACING = 80` units between components
- **Corner waypoints**: Clean 90-degree turns at midpoints
- **Rectangular flow**: Components arranged around perimeter

**Example - RC Filter (Series):**
```
         R (horizontal)
      ┌──────────────┐
      │              │
   V  │              │  C
  (v) │              │ (v)
      │              │
      └──────────────┘
       (direct wire)
```

### 3. **Parallel Routing**

For parallel circuits, the router creates bus-style wiring with:

**Features:**
- **Bus rail**: Common vertical line for all parallel branches
- **Uniform padding**: `PARALLEL_WIRE_PADDING = 50` units
- **Equal branch lengths**: All branches extend same distance to bus
- **Separate wire segments**: Main bus + individual branches

**Example - Parallel RC:**
```
      ┌─────────────────┐
   V ─┤                 │
  (v) │   ┌──── R ──────┤
      │   │             │
      │   ├──── C ──────┤
      │   │             │
      └───┴─────────────┘
       (bus)  (branches)
```

### 4. **Wire Padding Logic**

**Series Circuits:**
```python
# Add intermediate waypoints for clean corners
if horizontal_dominant:
    mid_x = (x1 + x2) / 2
    waypoints = [(x1, y1), (mid_x, y1), (mid_x, y2), (x2, y2)]
else:
    mid_y = (y1 + y2) / 2
    waypoints = [(x1, y1), (x1, mid_y), (x2, mid_y), (x2, y2)]
```

**Parallel Circuits:**
```python
# Create common bus rail
bus_x = min(branch_x) - PARALLEL_WIRE_PADDING

# Route main bus through all branch points
bus_waypoints = [(source), (bus_x, source_y), (bus_x, branch1_y), ...]

# Route each branch with equal length
for branch in branches:
    branch_waypoints = [(bus_x, branch_y), (component_x, branch_y)]
```

## Configuration Parameters

```python
# Rectangle dimensions for layout
RECT_WIDTH = 700
RECT_HEIGHT = 500

# Wire padding for parallel components
PARALLEL_WIRE_PADDING = 50

# Series component spacing
SERIES_SPACING = 80
```

## Testing Examples

### Series RC Filter
```bash
# rc_filter.net (series topology)
VDC V1 VIN GND 5V
R R1 VIN VOUT 10k
C C1 VOUT GND 100nF

# Test:
python3 circuit_placer.py rc_filter.net component_library.json
```

**Output:**
```
Circuit topology: SERIES
Placing in SERIES layout
  V1: LEFT (0, 250), rot=0°
  R1: (350, 0), rot=0°
  C1: (700, 250), rot=90°
```

### Parallel RC
```bash
# parallel_rc.net (parallel topology)
VDC V1 VIN GND 5V
R R1 VIN GND 10k
C C1 VIN GND 100nF

# Test:
python3 circuit_placer.py parallel_rc.net component_library.json
```

**Output:**
```
Circuit topology: PARALLEL
  Detected parallel: ['R1', 'C1'] on nodes ('GND', 'VIN')
Placing in PARALLEL layout
  V1: LEFT (0, 250), rot=0°
  R1: CENTER (350, 166), rot=0°
  C1: CENTER (350, 333), rot=0°
  
  Bus nodes: ['VIN', 'GND']
```

### Three-Component Series
```bash
# series_rcl.net
VDC V1 VIN GND 5V
R R1 VIN N1 10k
C C1 N1 N2 100nF
L L1 N2 GND 10mH

# Test:
python3 circuit_placer.py series_rcl.net component_library.json
```

## Routing Algorithm Details

### Series Routing (`_route_series`)

1. Analyze pin-to-pin distances (dx, dy)
2. Determine routing direction (horizontal vs vertical dominant)
3. Add midpoint waypoints for clean corners
4. Apply series spacing between segments
5. Create rectangular path flow

### Parallel Routing (`_route_parallel`)

1. Identify bus nodes (nodes with 3+ connections)
2. Calculate bus rail position (leftmost component - padding)
3. Route main bus vertically through all branch points
4. Create individual branches from bus to each component
5. Ensure uniform branch extension lengths

## Wire Structure

Each wire is a `Wire` dataclass:
```python
@dataclass
class Wire:
    net_name: str
    points: List[Tuple[float, float]]  # Waypoints
```

**Series wire example:**
```python
Wire(
    net_name="VIN",
    points=[(0, 250), (175, 250), (175, 0), (350, 0)]
)
```

**Parallel bus example:**
```python
# Main bus
Wire(
    net_name="VIN_bus",
    points=[(0, 250), (300, 250), (300, 166), (300, 333)]
)

# Branch to R1
Wire(
    net_name="VIN_br1",
    points=[(300, 166), (400, 166)]
)

# Branch to C1
Wire(
    net_name="VIN_br2",
    points=[(300, 333), (400, 333)]
)
```

## Visual Comparison

### Before (Simple L-routing)
```
V ──┐
    │
    └──> R ──┐
             │
             └──> C
```
Problems:
- Uneven wire lengths
- No padding
- Looks unprofessional

### After (Smart Routing)

**Series:**
```
      ┌─── R ───┐
      │         │
   V ─┤         ├─ C
      │         │
      └─────────┘
```

**Parallel:**
```
   V ──┬─── R ───┐
       │         │
       ├─── C ───┤
       │         │
       └─────────┘
    (bus) (uniform)
```

Benefits:
- Professional textbook appearance
- Uniform wire lengths for parallel
- Clean corners for series
- Easy to understand topology

## Troubleshooting

**Q: Components overlap?**
A: Increase `RECT_WIDTH` and `RECT_HEIGHT`

**Q: Wires too short/long?**
A: Adjust `PARALLEL_WIRE_PADDING` for parallel, `SERIES_SPACING` for series

**Q: Wrong topology detected?**
A: Check netlist - parallel components must share exact same two nodes

**Q: Wires don't look rectangular?**
A: Series routing adds midpoint waypoints - check pin positions are aligned

## Future Enhancements

- [ ] Auto-adjust rectangle size based on component count
- [ ] Support mixed series/parallel topologies
- [ ] Add component value labels on wires
- [ ] Net name annotations
- [ ] Optimize bus rail positioning for minimum wire length
- [ ] Support for 3-terminal components (transistors)
