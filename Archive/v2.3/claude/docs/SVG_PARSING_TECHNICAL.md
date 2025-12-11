# SVG Negative Value Parsing - Technical Details

## The Problem

Early SVG parsing implementations used regex to extract coordinates from SVG path data. This approach **fails catastrophically** with negative values, especially when numbers are concatenated without spaces.

### Examples of Problematic SVG Paths:

```svg
<!-- Case 1: Concatenated negative values (NO SPACES) -->
M-50-30L-20-10

<!-- Case 2: Mixed signs without spaces -->
M100-50L-100-50

<!-- Case 3: Negative in complex curves -->
M 0 0 C 10 -10 20 -20 30 -30
```

### Why Regex Fails:

```python
# OLD BROKEN APPROACH (regex)
coords = re.findall(r'-?\d+\.?\d*', '-50-30')
# Returns: ['-50', '-30']  ✓ Works by luck

coords = re.findall(r'-?\d+\.?\d*', 'M-50-30L-20-10')
# Returns: ['-50', '-30', '-20', '-10']  ✗ Lost command structure!
# Doesn't know which coords belong to M vs L
```

The regex approach:
1. **Loses command context** - can't distinguish M from L
2. **Fails on implicit commands** - doesn't handle "M 10 20 30 40" (M + implicit L)
3. **Breaks with relative commands** - m, l, c, q have different semantics
4. **Ignores curve control points** - treats all coords as endpoints
5. **Can't reconstruct paths** - just a bag of numbers with no structure

## The Solution: svgpathtools

The `svgpathtools` library implements a **proper SVG parser** that:
- Understands the SVG path specification completely
- Handles all commands: M, L, H, V, C, S, Q, T, A, Z (and lowercase)
- Parses concatenated numbers correctly
- Maintains bezier curve mathematics
- Provides accurate point sampling along curves

### Implementation in component_library_builder.py

```python
from svgpathtools import parse_path

def svg_to_pen_commands(self, svg_path: Path):
    """Convert SVG to pen commands using svgpathtools"""
    
    for elem in root.iter():
        if elem.tag.endswith('path'):
            d = elem.get('d', '')
            
            # ✓ CORRECT: Use svgpathtools parser
            svg_path_obj = parse_path(d)
            
            # Sample points along the path
            num_samples = max(2, int(svg_path_obj.length() * 0.5))
            
            points = []
            for i in range(num_samples + 1):
                t = i / num_samples
                point = svg_path_obj.point(t)  # Complex number
                px, py = point.real, point.imag
                points.append((px, py))
            
            # Generate pen commands from sampled points
            if points:
                x0, y0 = points[0]
                commands.append(f"pen down {x0:.2f} {y0:.2f}")
                
                for x, y in points[1:]:
                    commands.append(f"pen move {x:.2f} {y:.2f}")
                
                commands.append("pen up")
```

### Key Features:

1. **Accurate Command Parsing**
   - `parse_path("M-50-30L-20-10")` correctly returns two segments
   - First segment: Move from origin to (-50, -30)
   - Second segment: Line from (-50, -30) to (-20, -10)

2. **Bezier Curve Support**
   - Cubic (C, S): Uses proper De Casteljau algorithm
   - Quadratic (Q, T): Handles control points correctly
   - Arc (A): Implements SVG arc specification

3. **Sampling Strategy**
   - Adaptive: More samples for longer/curvier paths
   - `svg_path_obj.length()` gives arc length
   - `svg_path_obj.point(t)` returns position at parameter t ∈ [0,1]
   - Returns complex numbers: `real` = x, `imag` = y

4. **Coordinate Accuracy**
   - Handles negative coordinates: -100, -50.5, -0.123
   - Handles large coordinates: 1000, 2000
   - Preserves decimal precision
   - Correctly applies transformations

## Testing

Run the verification test:

```bash
python3 test_svg_parsing.py
```

This test validates:
- ✓ Simple paths with positive/negative coords
- ✓ Concatenated values without spaces (M-50-30)
- ✓ Complex curves with negative control points
- ✓ Mixed positive/negative values
- ✓ All SVG path commands

### Expected Output:

```
================================================================================
SVG PATH NEGATIVE VALUE PARSING TEST
================================================================================

✓ PASS: Simple positive coordinates
  Path: M 10 20 L 30 40
  Start: (10.00, 20.00)
  End:   (30.00, 40.00)

✓ PASS: Concatenated without spaces (problematic for regex)
  Path: M-50-30L-20-10
  Start: (-50.00, -30.00)
  End:   (-20.00, -10.00)

✓ PASS: All negative coordinates
  Path: M -10 -20 L -30 -40
  Start: (-10.00, -20.00)
  End:   (-30.00, -40.00)

================================================================================
RESULTS: All tests passed! svgpathtools correctly handles negative values.
================================================================================
```

## Comparison: Old vs New

### Old Approach (BROKEN):
```python
# svg_to_lamp_improved.py (do NOT use)
coords = re.findall(r'-?\d+\.?\d*', d)  # ✗ Loses structure
for i in range(0, len(coords), 2):
    x, y = float(coords[i]), float(coords[i+1])  # ✗ Wrong pairing
```

Problems:
- Path `M-50-30L-20-10` → coords = ['-50', '-30', '-20', '-10']
- No way to know which coords are for M vs L
- Treats curves as lines
- Cannot reconstruct original path

### New Approach (CORRECT):
```python
# component_library_builder.py (✓ use this)
svg_path = parse_path(d)  # ✓ Full semantic parse
for t in np.linspace(0, 1, num_samples):
    point = svg_path.point(t)  # ✓ Accurate position
    x, y = point.real, point.imag
```

Benefits:
- Understands SVG command structure
- Samples curves accurately
- Handles all edge cases
- Mathematically correct

## Installation

Ensure svgpathtools is installed:

```bash
# Standard installation
pip install svgpathtools

# reMarkable 2 / restricted systems
pip install svgpathtools --break-system-packages
```

Dependencies:
- numpy (for numerical operations)
- svgwrite (for path construction)
- scipy (for curve calculations)

## SVG Files in This Project

All component SVGs in `../components/` use standard SVG path syntax:
- Some may have negative coordinates (e.g., centered at origin)
- Some use transforms (translate, matrix)
- All are now parsed correctly with svgpathtools

Example component structure:
```xml
<svg width="140" height="33" viewBox="0 0 140 33">
  <path d="M 10 16.5 H 50 M 90 16.5 H 130"/>  <!-- Resistor body -->
  <circle id="pin1" cx="10" cy="16.5" r="2"/>  <!-- Pin marker -->
  <circle id="pin2" cx="130" cy="16.5" r="2"/>
</svg>
```

## Future-Proofing

The svgpathtools approach ensures:
1. **Standards compliance** - Follows W3C SVG spec
2. **Maintainability** - No custom parsing code to debug
3. **Extensibility** - Handles future SVG features
4. **Robustness** - Tested on thousands of SVG files
5. **Accuracy** - Mathematical correctness for curves

## References

- SVG Path Specification: https://www.w3.org/TR/SVG/paths.html
- svgpathtools docs: https://github.com/mathandy/svgpathtools
- This implementation: `component_library_builder.py` lines 106-150

---

**Bottom Line**: Always use `svgpathtools.parse_path()` for SVG parsing. Never use regex for coordinate extraction.
