# Component System Architecture
## Anchor-Based Relative Coordinate System

### Overview
Transform Library.svg components into anchor-based relative coordinate system for dynamic circuit placement. Each component will have:
- **Central anchor** (0,0 in component space)
- **Pin anchors** (connection points)
- **Bounding box** (for collision detection)
- **Relative paths** (all coordinates relative to center)

---

## 1. Component Definition Format (JSON)

```json
{
  "component_name": "R",
  "type": "resistor",
  "bbox": {
    "width": 132.63,
    "height": 29.47
  },
  "center_anchor": {
    "x": 0,
    "y": 0
  },
  "pin_anchors": [
    {
      "name": "pin1",
      "x": -66.32,
      "y": 0,
      "direction": "left"
    },
    {
      "name": "pin2",
      "x": 66.32,
      "y": 0,
      "direction": "right"
    }
  ],
  "paths": [
    {
      "type": "polyline",
      "points": [
        {"x": -66.32, "y": 0},
        {"x": -44.21, "y": 0},
        {"x": -36.84, "y": 14.74},
        ...
      ],
      "style": {
        "stroke": "#000000",
        "stroke_width": 7.368,
        "fill": "none"
      }
    }
  ],
  "symbols": []
}
```

---

## 2. Coordinate System

### Local Component Space
- **Origin**: Component geometric center
- **Units**: reMarkable pixels (1404x1872)
- **Coordinates**: All relative to center (0,0)

### Pin Anchor System
```
Pin directions: "left", "right", "top", "bottom", "center"

Example: Resistor (R)
    pin1 ←──────[ RESISTOR ]──────→ pin2
  (-66,0)      center:(0,0)       (66,0)
```

### Placement Algorithm
```python
# When placing component at absolute position (cx, cy):
for path_point in component.paths:
    abs_x = cx + path_point.x  # Add center offset
    abs_y = cy + path_point.y
    lamp_command(abs_x, abs_y)

# When connecting pins:
pin_abs_x = cx + pin.x
pin_abs_y = cy + pin.y
```

---

## 3. Processing Pipeline

### Step 1: Extract Component Groups
**Input**: Library.svg
**Output**: Individual `<g>` elements with IDs
**Tool**: `svg_component_extractor.py`

```python
# Extract all <g> elements with id attribute
components = {
    "R": <g id="R">...</g>,
    "C": <g id="NP_CAP">...</g>,
    ...
}
```

### Step 2: Apply Matrix Transforms
**Challenge**: Components have transforms like:
```xml
<g transform="matrix(2.10526,0,0,2.10526,-779.75,128.69)">
```

**Solution**: Apply transform matrix to ALL coordinates
```python
def apply_transform(x, y, matrix):
    # matrix = [a, b, c, d, e, f]
    # x' = a*x + c*y + e
    # y' = b*x + d*y + f
    a, b, c, d, e, f = matrix
    new_x = a * x + c * y + e
    new_y = b * x + d * y + f
    return new_x, new_y
```

### Step 3: Convert Paths to Absolute Coordinates
**Challenge**: SVG paths use relative commands (lowercase)
```
d="m 322,899.41665 v 14"  # relative: move, then vertical +14
```

**Solution**: Parse and convert all to absolute
```python
# Relative commands: m, l, h, v, c, s, q, t, a, z
# Absolute commands: M, L, H, V, C, S, Q, T, A, Z

path_data = parse_svg_path("m 322,899 v 14 h 28")
absolute_path = convert_to_absolute(path_data)
# Result: "M 322,899 L 322,913 L 350,913"
```

### Step 4: Calculate Bounding Box
**Method**: Find min/max of all coordinates
```python
all_points = extract_all_coordinates(component)
min_x = min(p.x for p in all_points)
max_x = max(p.x for p in all_points)
min_y = min(p.y for p in all_points)
max_y = max(p.y for p in all_points)

bbox_width = max_x - min_x
bbox_height = max_y - min_y
```

### Step 5: Calculate Center Anchor
**Method**: Geometric center of bounding box
```python
center_x = (min_x + max_x) / 2
center_y = (min_y + max_y) / 2
```

### Step 6: Detect Pin Anchors
**Heuristic**: Pins are typically:
1. Line endpoints at component boundary
2. Connection points extending beyond main body
3. Points at bbox edges

**Algorithm**:
```python
def detect_pins(component, bbox, center):
    pins = []

    # Find all line/path endpoints
    for path in component.paths:
        start = path.points[0]
        end = path.points[-1]

        # Check if point is at boundary
        tolerance = 2  # pixels

        # Left edge
        if abs(start.x - bbox.min_x) < tolerance:
            pins.append({
                "name": f"pin{len(pins)+1}",
                "x": start.x - center.x,
                "y": start.y - center.y,
                "direction": "left"
            })

        # Right edge
        if abs(end.x - bbox.max_x) < tolerance:
            pins.append({
                "name": f"pin{len(pins)+1}",
                "x": end.x - center.x,
                "y": end.y - center.y,
                "direction": "right"
            })

    return pins
```

### Step 7: Convert to Relative Coordinates
**Transform**: Subtract center from all coordinates
```python
def to_relative(point, center):
    return {
        "x": point.x - center.x,
        "y": point.y - center.y
    }

# Apply to all paths, circles, pins
for path in component.paths:
    for point in path.points:
        point.x -= center.x
        point.y -= center.y
```

---

## 4. Tool Chain

### Tool 1: `svg_component_extractor.py`
**Purpose**: Extract individual components from Library.svg
**Output**: Dictionary of component elements

### Tool 2: `svg_transform_applier.py`
**Purpose**: Apply matrix transforms to coordinates
**Uses**: Matrix multiplication for coordinate transformation

### Tool 3: `svg_path_parser.py`
**Purpose**: Parse SVG path data
**Converts**: Relative commands → Absolute coordinates
**Handles**: M, L, H, V, C, S, Q, T, A, Z and lowercase variants

### Tool 4: `component_analyzer.py`
**Purpose**: Calculate bbox, center, detect pins
**Algorithm**: Geometric analysis of all coordinates

### Tool 5: `component_library_builder.py`
**Purpose**: Main orchestrator
**Input**: Library.svg
**Output**: component_library.json
**Process**:
1. Extract components
2. Apply transforms
3. Convert to absolute
4. Calculate anchors
5. Convert to relative
6. Generate JSON

### Tool 6: `netlist_to_lamp.py`
**Purpose**: Convert netlist + component library → lamp commands
**Input**:
- circuit.net (netlist)
- component_library.json
- placement.json (optional layout hints)
**Output**: circuit.lamp (lamp pen commands)

---

## 5. Inkscape Normalization Guide

### Before Processing: Manual Symbol Preparation

#### Step 1: Remove Transforms
```
1. Select component in Inkscape
2. Path → Object to Path
3. Edit → Select All in Group
4. Object → Ungroup (if nested)
5. Path → Object to Path (again)
6. Extensions → Modify Path → Apply Transform
```

#### Step 2: Center Symbol
```
1. Select all paths in component
2. Object → Align and Distribute
3. Align: Center on vertical axis
4. Align: Center on horizontal axis
5. Move to origin area (near 0,0)
```

#### Step 3: Verify No Transforms
```
1. XML Editor (Ctrl+Shift+X)
2. Check no "transform" attributes on paths
3. All coordinates should be absolute
```

#### Step 4: Normalize Stroke Widths
```
1. Select paths
2. Object → Fill and Stroke → Stroke Style
3. Set consistent width (3.5px recommended)
4. Scale stroke width with object: UNCHECKED
```

---

## 6. Example: Processing Resistor (R)

### Original SVG
```xml
<path id="R"
      style="stroke-width:7.36842"
      d="m 176.27512,629.86698 h 22.10526 l 7.36842,14.7368
         14.73684,-29.47362 14.73684,29.47362 14.73685,-29.47362
         14.73684,29.47362 14.73684,-29.47362 7.36842,14.73682
         h 22.10526"/>
```

### After Processing

#### Bounding Box Calculation
```
Points extracted: (176.27, 629.87), (198.38, 629.87), (205.75, 644.60), ...
Min: (176.27, 615.13)
Max: (308.90, 644.60)
Width: 132.63
Height: 29.47
Center: (242.59, 629.87)
```

#### Pin Detection
```
Pin 1: (176.27, 629.87) - leftmost point
Pin 2: (308.90, 629.87) - rightmost point
```

#### Relative Conversion
```
Center at: (242.59, 629.87)
Pin 1 relative: (-66.32, 0)
Pin 2 relative: (66.32, 0)
Path points: [(-66.32,0), (-44.21,0), (-36.84,14.73), ...]
```

#### Final JSON
```json
{
  "component_name": "R",
  "bbox": {"width": 132.63, "height": 29.47},
  "center_anchor": {"x": 0, "y": 0},
  "pin_anchors": [
    {"name": "pin1", "x": -66.32, "y": 0, "direction": "left"},
    {"name": "pin2", "x": 66.32, "y": 0, "direction": "right"}
  ],
  "paths": [...]
}
```

---

## 7. Usage: Netlist to Lamp Commands

### Input Netlist (`rc_circuit.net`)
```
R1 node1 node2 10k
C1 node2 gnd 100u
```

### Placement Algorithm (Grid-Based)
```python
# Place components on grid
positions = {
    "R1": {"x": 500, "y": 500},
    "C1": {"x": 700, "y": 500}
}

# Generate lamp commands
for component_id, pos in positions.items():
    comp_def = library[component_type]

    # Draw component at position
    for path in comp_def.paths:
        for point in path.points:
            abs_x = pos.x + point.x
            abs_y = pos.y + point.y
            lamp_draw(abs_x, abs_y)

    # Get pin absolute positions for wiring
    pins[f"{component_id}.pin1"] = {
        "x": pos.x + comp_def.pin_anchors[0].x,
        "y": pos.y + comp_def.pin_anchors[0].y
    }
```

### Wire Routing
```python
# Connect R1.pin2 to C1.pin1
start = pins["R1.pin2"]
end = pins["C1.pin1"]

# Draw wire
lamp_command(f"pen down {start.x} {start.y}")
lamp_command(f"pen line {start.x} {start.y} {end.x} {end.y}")
lamp_command(f"pen up")
```

---

## 8. Implementation Priority

### Phase 1: Core Tools (Week 1)
1. ✅ svg_path_parser.py - Parse SVG path data
2. ✅ svg_transform_applier.py - Apply matrix transforms
3. ✅ component_analyzer.py - Bbox, center, pins

### Phase 2: Library Builder (Week 1-2)
4. ✅ svg_component_extractor.py - Extract from Library.svg
5. ✅ component_library_builder.py - Orchestrate pipeline
6. ✅ Manual Inkscape normalization (if needed)

### Phase 3: Circuit Generator (Week 2-3)
7. ⬜ netlist_parser.py - Parse SPICE netlist
8. ⬜ circuit_placer.py - Auto-place components
9. ⬜ wire_router.py - Route wires between pins
10. ⬜ netlist_to_lamp.py - Generate final lamp commands

---

## 9. Testing Strategy

### Unit Tests
- Test each SVG path command conversion
- Test matrix transform application
- Test bounding box calculation
- Test pin detection heuristics

### Integration Tests
- Process entire Library.svg
- Verify all 25+ components extracted
- Check relative coordinates correct
- Validate JSON schema

### End-to-End Test
```
Input: rc_circuit.net
Expected Output: circuit.lamp with:
- R at (500, 500)
- C at (700, 500)
- Wire connecting pins
- All coordinates absolute
- Visual verification on reMarkable
```

---

## 10. File Structure

```
lamp-v2/
├── assets/
│   └── Library.svg (source)
├── src/
│   ├── svg_path_parser.py
│   ├── svg_transform_applier.py
│   ├── svg_component_extractor.py
│   ├── component_analyzer.py
│   └── component_library_builder.py
├── lib/
│   └── component_library.json (generated)
├── examples/
│   ├── rc_circuit.net
│   └── rc_circuit.lamp (generated)
└── COMPONENT_SYSTEM_ARCHITECTURE.md (this file)
```

---

## Summary

This architecture provides:
✅ **Anchor-based positioning** - All coordinates relative to center
✅ **Pin detection** - Automatic connection point identification
✅ **Transform handling** - Proper matrix math for Inkscape transforms
✅ **Absolute → Relative** - Two-stage coordinate conversion
✅ **Netlist integration** - Connect to circuit definition
✅ **Extensible** - Easy to add new components

**Next Step**: Implement Phase 1 core tools and test with simple components (R, C, L).
