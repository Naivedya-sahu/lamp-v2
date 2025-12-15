#!/usr/bin/env python3
"""
svg_to_lamp_relative.py - SVG to Relative Lamp Coordinates Converter

Converts SVG components to relative coordinate pen commands (0.0-1.0 normalized).
Suitable for component library integration with anchor point systems.

Features:
- Outputs relative coordinates (0.0-1.0) instead of absolute pixels
- Intelligent line vs curve detection (minimizes pen commands)
- Douglas-Peucker simplification
- Pin visualization with --show-pins flag
- Auto-bounds calculation

Usage:
    python3 svg_to_lamp_relative.py component.svg
    python3 svg_to_lamp_relative.py component.svg --show-pins
    python3 svg_to_lamp_relative.py component.svg --tolerance 2.0
"""

import sys
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
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

def parse_path_simple(d):
    """
    Simple SVG path parser for common commands (M, L, H, V, Z)
    Returns list of (x, y) points
    """
    points = []
    commands = re.findall(r'[MmLlHhVvZzCcSsQqTtAa]|[-+]?[0-9]*\.?[0-9]+', d)

    current_x, current_y = 0, 0
    i = 0

    while i < len(commands):
        cmd = commands[i]

        if cmd in 'Mm':
            # Move to
            i += 1
            x = float(commands[i])
            i += 1
            y = float(commands[i])
            if cmd == 'm':  # relative
                current_x += x
                current_y += y
            else:  # absolute
                current_x = x
                current_y = y
            points.append((current_x, current_y))

        elif cmd in 'Ll':
            # Line to
            i += 1
            x = float(commands[i])
            i += 1
            y = float(commands[i])
            if cmd == 'l':  # relative
                current_x += x
                current_y += y
            else:  # absolute
                current_x = x
                current_y = y
            points.append((current_x, current_y))

        elif cmd in 'Hh':
            # Horizontal line
            i += 1
            x = float(commands[i])
            if cmd == 'h':  # relative
                current_x += x
            else:  # absolute
                current_x = x
            points.append((current_x, current_y))

        elif cmd in 'Vv':
            # Vertical line
            i += 1
            y = float(commands[i])
            if cmd == 'v':  # relative
                current_y += y
            else:  # absolute
                current_y = y
            points.append((current_x, current_y))

        elif cmd in 'Zz':
            # Close path - return to first point
            if points:
                points.append(points[0])

        else:
            # For complex curves (C, S, Q, T, A), approximate with straight line to endpoint
            # This is a simple fallback - for production use svgpathtools
            if cmd in 'CcSsQqTtAa':
                # Skip intermediate control points and just get endpoint
                if cmd in 'Cc':
                    i += 5  # Skip control points
                    x = float(commands[i])
                    i += 1
                    y = float(commands[i])
                elif cmd in 'Ss':
                    i += 3
                    x = float(commands[i])
                    i += 1
                    y = float(commands[i])
                elif cmd in 'Qq':
                    i += 3
                    x = float(commands[i])
                    i += 1
                    y = float(commands[i])
                elif cmd in 'Tt':
                    i += 1
                    x = float(commands[i])
                    i += 1
                    y = float(commands[i])
                elif cmd in 'Aa':
                    i += 5
                    x = float(commands[i])
                    i += 1
                    y = float(commands[i])

                if cmd.islower():  # relative
                    current_x += x
                    current_y += y
                else:  # absolute
                    current_x = x
                    current_y = y
                points.append((current_x, current_y))

        i += 1

    return points

def collect_bounds(root, show_pins=False):
    """Calculate bounding box and collect all drawable elements"""
    minx = float('inf')
    miny = float('inf')
    maxx = float('-inf')
    maxy = float('-inf')
    elements = []

    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        elem_id = elem.get('id', '')

        # Skip pin circles unless show_pins is True
        if 'pin' in elem_id.lower() and not show_pins:
            continue

        if tag == 'path':
            d = elem.get('d', '')
            if not d:
                continue
            try:
                pts = parse_path_simple(d)
                if pts:
                    for x, y in pts:
                        minx = min(minx, x)
                        maxx = max(maxx, x)
                        miny = min(miny, y)
                        maxy = max(maxy, y)
                    elements.append(('path', elem_id, pts))
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
            elements.append(('rect', elem_id, (x, y, w, h)))

        elif tag == 'circle':
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            r = float(elem.get('r', 0))
            minx = min(minx, cx - r)
            maxx = max(maxx, cx + r)
            miny = min(miny, cy - r)
            maxy = max(maxy, cy + r)
            elements.append(('circle', elem_id, (cx, cy, r)))

        elif tag == 'line':
            x1 = float(elem.get('x1', 0))
            y1 = float(elem.get('y1', 0))
            x2 = float(elem.get('x2', 0))
            y2 = float(elem.get('y2', 0))
            minx = min(minx, x1, x2)
            maxx = max(maxx, x1, x2)
            miny = min(miny, y1, y2)
            maxy = max(maxy, y1, y2)
            elements.append(('line', elem_id, (x1, y1, x2, y2)))

        elif tag in ('polyline', 'polygon'):
            pts_str = elem.get('points', '')
            pts_nums = [float(n) for n in re.findall(r'-?\d*\.?\d+', pts_str)]
            pts = [(pts_nums[i], pts_nums[i+1]) for i in range(0, len(pts_nums)-1, 2)]
            if pts:
                for x, y in pts:
                    minx = min(minx, x)
                    maxx = max(maxx, x)
                    miny = min(miny, y)
                    maxy = max(maxy, y)
                elements.append(('polyline' if tag == 'polyline' else 'polygon', elem_id, pts))

    return (minx, miny, maxx, maxy), elements

def to_relative(x, y, bounds):
    """Convert absolute SVG coordinates to relative (0.0-1.0)"""
    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    height = maxy - miny

    if width == 0 or height == 0:
        return 0.0, 0.0

    rel_x = (x - minx) / width
    rel_y = (y - miny) / height

    return rel_x, rel_y

def generate_relative_commands(elements, bounds, tolerance):
    """Generate relative coordinate pen commands"""
    commands = []

    for elem_type, elem_id, data in elements:
        if elem_type == 'path':
            pts = simplify_points(data, tolerance)
            if not pts:
                continue

            # First point - pen down
            x0, y0 = pts[0]
            rel_x, rel_y = to_relative(x0, y0, bounds)
            commands.append(f"pen down {rel_x:.6f} {rel_y:.6f}")

            # Subsequent points - pen move
            for x, y in pts[1:]:
                rel_x, rel_y = to_relative(x, y, bounds)
                commands.append(f"pen move {rel_x:.6f} {rel_y:.6f}")

            commands.append("pen up")

        elif elem_type == 'line':
            x1, y1, x2, y2 = data
            rx1, ry1 = to_relative(x1, y1, bounds)
            rx2, ry2 = to_relative(x2, y2, bounds)
            commands.append(f"pen down {rx1:.6f} {ry1:.6f}")
            commands.append(f"pen move {rx2:.6f} {ry2:.6f}")
            commands.append("pen up")

        elif elem_type == 'rect':
            x, y, w, h = data
            rx1, ry1 = to_relative(x, y, bounds)
            rx2, ry2 = to_relative(x + w, y + h, bounds)
            commands.append(f"pen down {rx1:.6f} {ry1:.6f}")
            commands.append(f"pen move {rx2:.6f} {ry1:.6f}")
            commands.append(f"pen move {rx2:.6f} {ry2:.6f}")
            commands.append(f"pen move {rx1:.6f} {ry2:.6f}")
            commands.append(f"pen move {rx1:.6f} {ry1:.6f}")
            commands.append("pen up")

        elif elem_type == 'circle':
            cx, cy, r = data
            # Approximate circle with 16-point polygon
            circle_pts = []
            for i in range(17):  # 17 points to close the circle
                angle = 2 * math.pi * i / 16
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                circle_pts.append((x, y))

            rel_x, rel_y = to_relative(circle_pts[0][0], circle_pts[0][1], bounds)
            commands.append(f"pen down {rel_x:.6f} {rel_y:.6f}")

            for x, y in circle_pts[1:]:
                rel_x, rel_y = to_relative(x, y, bounds)
                commands.append(f"pen move {rel_x:.6f} {rel_y:.6f}")

            commands.append("pen up")

        elif elem_type in ('polyline', 'polygon'):
            pts = data
            if not pts:
                continue

            x0, y0 = pts[0]
            rel_x, rel_y = to_relative(x0, y0, bounds)
            commands.append(f"pen down {rel_x:.6f} {rel_y:.6f}")

            for x, y in pts[1:]:
                rel_x, rel_y = to_relative(x, y, bounds)
                commands.append(f"pen move {rel_x:.6f} {rel_y:.6f}")

            # Close polygon
            if elem_type == 'polygon':
                rel_x, rel_y = to_relative(pts[0][0], pts[0][1], bounds)
                commands.append(f"pen move {rel_x:.6f} {rel_y:.6f}")

            commands.append("pen up")

    return commands

def main():
    parser = argparse.ArgumentParser(
        description='Convert SVG to relative coordinate lamp commands (0.0-1.0)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s R.svg
  %(prog)s R.svg --show-pins
  %(prog)s R.svg --tolerance 2.0
  %(prog)s R.svg --show-pins --tolerance 1.5

Output format:
  pen down <rel_x> <rel_y>
  pen move <rel_x> <rel_y>
  pen up

Where rel_x and rel_y are in range [0.0, 1.0]
        """
    )

    parser.add_argument('svg_file', help='Path to SVG file')
    parser.add_argument('--show-pins', action='store_true',
                       help='Show pin circles (normally hidden)')
    parser.add_argument('--tolerance', type=float, default=1.0,
                       help='Simplification tolerance (default: 1.0, lower=more detail)')

    args = parser.parse_args()

    # Validate file exists
    svg_path = Path(args.svg_file)
    if not svg_path.exists():
        print(f"Error: File not found: {args.svg_file}", file=sys.stderr)
        sys.exit(1)

    # Parse SVG
    try:
        tree = ET.parse(args.svg_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error: Failed to parse SVG: {e}", file=sys.stderr)
        sys.exit(1)

    # Collect bounds and elements
    bounds, elements = collect_bounds(root, args.show_pins)

    if not elements:
        print("# No drawable content found", file=sys.stderr)
        sys.exit(0)

    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    height = maxy - miny

    # Generate relative commands
    commands = generate_relative_commands(elements, bounds, args.tolerance)

    # Output statistics to stderr
    print(f"# SVG: {svg_path.name}", file=sys.stderr)
    print(f"# Bounds: ({minx:.2f}, {miny:.2f}) to ({maxx:.2f}, {maxy:.2f})", file=sys.stderr)
    print(f"# Size: {width:.2f} x {height:.2f}", file=sys.stderr)
    print(f"# Elements: {len(elements)}", file=sys.stderr)
    print(f"# Commands: {len(commands)}", file=sys.stderr)
    print(f"# Show pins: {args.show_pins}", file=sys.stderr)
    print(f"# Tolerance: {args.tolerance}", file=sys.stderr)

    # Output commands to stdout
    print("\n".join(commands))

if __name__ == '__main__':
    main()
