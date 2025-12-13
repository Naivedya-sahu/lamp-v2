#!/usr/bin/env python3
"""
SVG to Relative Lamp Coordinates - High Fidelity Version

Converts SVG components to relative coordinate pen commands (0.0-1.0 normalized).
Based on svg_to_lamp_smartv2.py but outputs relative coordinates for component library.

Features:
- Full SVG path parsing with svgpathtools (preserves all strokes)
- Intelligent line vs curve detection
- Outputs relative coordinates [0.0-1.0] instead of absolute pixels
- Pin visualization with --show-pins flag
- Douglas-Peucker path simplification

Usage:
    python3 svg_to_lamp_relative.py component.svg
    python3 svg_to_lamp_relative.py component.svg --show-pins
    python3 svg_to_lamp_relative.py component.svg --tolerance 2.0
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from svgpathtools import parse_path, Line, Arc, CubicBezier, QuadraticBezier
import re
import math

def is_collinear(p1, p2, p3, tolerance=1e-3):
    """Check if three points are collinear (on same straight line)"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    # Cross product should be zero for collinear points
    cross = abs((y2 - y1) * (x3 - x2) - (y3 - y2) * (x2 - x1))
    return cross < tolerance

def simplify_points(points, tolerance=1.0):
    """Remove redundant collinear points using Douglas-Peucker-like algorithm"""
    if len(points) <= 2:
        return points

    simplified = [points[0]]

    for i in range(1, len(points) - 1):
        # Check if current point can be skipped (is collinear with neighbors)
        if not is_collinear(simplified[-1], points[i], points[i + 1], tolerance):
            simplified.append(points[i])

    simplified.append(points[-1])
    return simplified

def smart_sample_segment(seg, tolerance=1.0):
    """
    Intelligently sample a path segment:
    - Line: return only endpoints
    - Curve: sample based on curvature, then simplify
    """
    if isinstance(seg, Line):
        # Straight line: only need start and end
        return [(seg.start.real, seg.start.imag), (seg.end.real, seg.end.imag)]

    else:
        # Curve: sample and simplify
        seg_len = seg.length(error=1e-5)

        # Adaptive sampling based on segment length
        if seg_len < 10:
            n = 3
        elif seg_len < 50:
            n = 5
        elif seg_len < 100:
            n = 8
        else:
            n = max(8, min(20, int(seg_len * 0.1)))

        points = []
        for i in range(n + 1):
            t = i / n
            p = seg.point(t)
            points.append((p.real, p.imag))

        # Simplify to remove collinear points
        return simplify_points(points, tolerance)

def smart_parse_path(d, tolerance=1.0):
    """
    Parse SVG path with intelligent sampling:
    - Detects lines vs curves
    - Minimizes commands for straight segments
    - Preserves curve quality
    """
    try:
        sp = parse_path(d)
    except:
        return []

    all_points = []

    for seg in sp:
        seg_points = smart_sample_segment(seg, tolerance)

        # Avoid duplicate points between segments
        if all_points and seg_points:
            # Check if last point of previous segment equals first point of current
            last = all_points[-1]
            first = seg_points[0]
            if abs(last[0] - first[0]) < 1e-6 and abs(last[1] - first[1]) < 1e-6:
                all_points.extend(seg_points[1:])
            else:
                all_points.extend(seg_points)
        else:
            all_points.extend(seg_points)

    # Final simplification pass
    return simplify_points(all_points, tolerance)

def extract_pins(root):
    """Extract pin information from SVG"""
    pins = []

    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        elem_id = elem.get('id', '')

        if 'pin' in elem_id.lower():
            if tag == 'circle':
                cx = float(elem.get('cx', 0))
                cy = float(elem.get('cy', 0))
                r = float(elem.get('r', 0))
                pins.append({
                    'id': elem_id,
                    'x': cx,
                    'y': cy,
                    'r': r
                })
            elif tag == 'path':
                # Pin as path (some SVGs use this)
                d = elem.get('d', '')
                match = re.search(r'[Mm]\s*([\d.-]+)[,\s]+([\d.-]+)', d)
                if match:
                    cx = float(match.group(1))
                    cy = float(match.group(2))
                    pins.append({
                        'id': elem_id,
                        'x': cx,
                        'y': cy,
                        'r': 1.0
                    })

    return pins

def collect_bounds(root, show_pins=False):
    """Calculate bounding box of drawable elements"""
    minx = float('inf')
    miny = float('inf')
    maxx = float('-inf')
    maxy = float('-inf')

    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        elem_id = elem.get('id', '')
        is_pin = 'pin' in elem_id.lower()

        # Skip pins from bounds unless showing them
        if is_pin and not show_pins:
            continue

        if tag == 'path':
            d = elem.get('d', '')
            if not d:
                continue
            try:
                pts = smart_parse_path(d, tolerance=0.5)
                for x, y in pts:
                    minx = min(minx, x)
                    maxx = max(maxx, x)
                    miny = min(miny, y)
                    maxy = max(maxy, y)
            except:
                continue

        elif tag == 'rect':
            x = float(elem.get('x', 0))
            y = float(elem.get('y', 0))
            w = float(elem.get('width', 0))
            h = float(elem.get('height', 0))
            minx = min(minx, x)
            maxx = max(maxx, x + w)
            miny = min(miny, y)
            maxy = max(maxy, y + h)

        elif tag == 'circle':
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            r = float(elem.get('r', 0))
            minx = min(minx, cx - r)
            maxx = max(maxx, cx + r)
            miny = min(miny, cy - r)
            maxy = max(maxy, cy + r)

        elif tag == 'line':
            x1 = float(elem.get('x1', 0))
            y1 = float(elem.get('y1', 0))
            x2 = float(elem.get('x2', 0))
            y2 = float(elem.get('y2', 0))
            minx = min(minx, x1, x2)
            maxx = max(maxx, x1, x2)
            miny = min(miny, y1, y2)
            maxy = max(maxy, y1, y2)

        elif tag in ('polyline', 'polygon'):
            pts = [float(n) for n in re.findall(r'-?\d*\.?\d+', elem.get('points', ''))]
            for i in range(0, len(pts), 2):
                if i < len(pts):
                    minx = min(minx, pts[i])
                    maxx = max(maxx, pts[i])
            for i in range(1, len(pts), 2):
                if i < len(pts):
                    miny = min(miny, pts[i])
                    maxy = max(maxy, pts[i])

    return (minx, miny, maxx, maxy)

def to_relative(x, y, bounds):
    """Convert absolute SVG coordinates to relative [0.0, 1.0]"""
    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    height = maxy - miny

    if width == 0 or height == 0:
        return 0.5, 0.5

    rel_x = (x - minx) / width
    rel_y = (y - miny) / height

    # Clamp to [0, 1]
    rel_x = max(0.0, min(1.0, rel_x))
    rel_y = max(0.0, min(1.0, rel_y))

    return rel_x, rel_y

def main():
    # Parse command line arguments
    show_pins = False
    args = []

    for arg in sys.argv[1:]:
        if arg == '--show-pins':
            show_pins = True
        else:
            args.append(arg)

    if len(args) < 1:
        print("Usage: python3 svg_to_lamp_relative.py file.svg [tolerance] [--show-pins]")
        print("\nArguments:")
        print("  tolerance   - Simplification tolerance in SVG units (default: 1.0)")
        print("                Lower = more detail, Higher = fewer commands")
        print("  --show-pins - Include pin circles in output")
        print("\nExamples:")
        print("  python3 svg_to_lamp_relative.py R.svg")
        print("  python3 svg_to_lamp_relative.py R.svg --show-pins")
        print("  python3 svg_to_lamp_relative.py R.svg 2.0")
        print("  python3 svg_to_lamp_relative.py OPAMP.svg 0.5 --show-pins")
        print("\nOutput: Pen commands with relative coordinates [0.0, 1.0]")
        sys.exit(1)

    svg_file = args[0]
    tolerance = 1.0

    if len(args) > 1:
        tolerance = float(args[1])

    if not Path(svg_file).exists():
        print(f"Error: File not found: {svg_file}", file=sys.stderr)
        sys.exit(1)

    tree = ET.parse(svg_file)
    root = tree.getroot()

    # Extract pins first
    pins = extract_pins(root)
    if pins:
        print(f"# Found {len(pins)} pins:", file=sys.stderr)
        for pin in pins:
            print(f"#   {pin['id']}: ({pin['x']:.2f}, {pin['y']:.2f})", file=sys.stderr)
    else:
        print("# Warning: No pins found in SVG", file=sys.stderr)

    # Calculate bounds
    bounds = collect_bounds(root, show_pins)
    minx, miny, maxx, maxy = bounds

    if minx == float('inf'):
        print("# No drawable content found", file=sys.stderr)
        sys.exit(0)

    svg_width = maxx - minx
    svg_height = maxy - miny

    print(f"# SVG: {Path(svg_file).name}", file=sys.stderr)
    print(f"# Bounds: ({minx:.2f}, {miny:.2f}) to ({maxx:.2f}, {maxy:.2f})", file=sys.stderr)
    print(f"# Size: {svg_width:.2f} x {svg_height:.2f}", file=sys.stderr)
    print(f"# Tolerance: {tolerance}", file=sys.stderr)
    print(f"# Pin visualization: {'ENABLED' if show_pins else 'DISABLED'}", file=sys.stderr)

    # Generate pen commands with relative coordinates
    commands = []
    path_count = 0
    pin_count = 0

    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        elem_id = elem.get('id', '')
        is_pin = 'pin' in elem_id.lower()

        if tag == 'path':
            # Skip pins unless showing them
            if is_pin and not show_pins:
                continue

            d = elem.get('d', '')
            if not d:
                continue

            try:
                pts = smart_parse_path(d, tolerance)
                if not pts:
                    continue

                path_count += 1

                # Convert to relative and emit pen commands
                x0, y0 = pts[0]
                rel_x, rel_y = to_relative(x0, y0, bounds)
                commands.append(f"pen down {rel_x:.6f} {rel_y:.6f}")

                for x, y in pts[1:]:
                    rel_x, rel_y = to_relative(x, y, bounds)
                    commands.append(f"pen move {rel_x:.6f} {rel_y:.6f}")

                commands.append("pen up")

            except Exception as e:
                print(f"Warning: Failed to parse path: {e}", file=sys.stderr)
                continue

        elif tag == 'rect':
            if is_pin and not show_pins:
                continue

            x = float(elem.get('x', 0))
            y = float(elem.get('y', 0))
            w = float(elem.get('width', 0))
            h = float(elem.get('height', 0))

            # Rectangle as path
            rx1, ry1 = to_relative(x, y, bounds)
            rx2, ry2 = to_relative(x + w, y, bounds)
            rx3, ry3 = to_relative(x + w, y + h, bounds)
            rx4, ry4 = to_relative(x, y + h, bounds)

            commands.append(f"pen down {rx1:.6f} {ry1:.6f}")
            commands.append(f"pen move {rx2:.6f} {ry2:.6f}")
            commands.append(f"pen move {rx3:.6f} {ry3:.6f}")
            commands.append(f"pen move {rx4:.6f} {ry4:.6f}")
            commands.append(f"pen move {rx1:.6f} {ry1:.6f}")
            commands.append("pen up")

        elif tag == 'circle':
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            r = float(elem.get('r', 0))

            # Handle pin circles
            if is_pin:
                pin_count += 1
                if not show_pins:
                    continue
                # Draw pin as small circle (will scale with component)
                # Use fixed relative size (0.02 of component size)
                r_rel = 0.02
            else:
                # Convert radius to relative
                r_rel = r / max(svg_width, svg_height)

            # Approximate circle with 16-point polygon
            circle_pts = []
            for i in range(17):  # 17 points to close circle
                angle = 2 * math.pi * i / 16
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                circle_pts.append((x, y))

            # Convert to relative and draw
            if circle_pts:
                rel_x, rel_y = to_relative(circle_pts[0][0], circle_pts[0][1], bounds)
                commands.append(f"pen down {rel_x:.6f} {rel_y:.6f}")

                for x, y in circle_pts[1:]:
                    rel_x, rel_y = to_relative(x, y, bounds)
                    commands.append(f"pen move {rel_x:.6f} {rel_y:.6f}")

                commands.append("pen up")

        elif tag == 'line':
            if is_pin and not show_pins:
                continue

            x1 = float(elem.get('x1', 0))
            y1 = float(elem.get('y1', 0))
            x2 = float(elem.get('x2', 0))
            y2 = float(elem.get('y2', 0))

            rx1, ry1 = to_relative(x1, y1, bounds)
            rx2, ry2 = to_relative(x2, y2, bounds)

            commands.append(f"pen down {rx1:.6f} {ry1:.6f}")
            commands.append(f"pen move {rx2:.6f} {ry2:.6f}")
            commands.append("pen up")

        elif tag in ('polyline', 'polygon'):
            if is_pin and not show_pins:
                continue

            pts = [float(n) for n in re.findall(r'-?\d*\.?\d+', elem.get('points', ''))]
            if len(pts) >= 4:
                x0, y0 = pts[0], pts[1]
                rel_x, rel_y = to_relative(x0, y0, bounds)
                commands.append(f"pen down {rel_x:.6f} {rel_y:.6f}")

                for i in range(2, len(pts), 2):
                    rel_x, rel_y = to_relative(pts[i], pts[i + 1], bounds)
                    commands.append(f"pen move {rel_x:.6f} {rel_y:.6f}")

                if tag == 'polygon':
                    rel_x, rel_y = to_relative(pts[0], pts[1], bounds)
                    commands.append(f"pen move {rel_x:.6f} {rel_y:.6f}")

                commands.append("pen up")

    # Output statistics
    print(f"# Processed {path_count} drawable elements", file=sys.stderr)
    print(f"# Total commands: {len(commands)}", file=sys.stderr)
    print(f"# Pins: {len(pins)} ({'drawn' if show_pins else 'skipped'})", file=sys.stderr)
    print("", file=sys.stderr)

    # Output pen commands
    print("\n".join(commands))

if __name__ == '__main__':
    main()
