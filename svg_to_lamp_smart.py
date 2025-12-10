#!/usr/bin/env python3
"""
svg_to_lamp_smart.py
Intelligent SVG parser that distinguishes between straight lines and curves
- Lines: outputs only endpoints (2 commands)
- Curves: samples appropriately based on curvature
- Result: Minimal pen commands for clean rendering
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from svgpathtools import parse_path, Line, Arc, CubicBezier, QuadraticBezier
import re
import math

SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

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
    sp = parse_path(d)
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

def transform_point(x, y, scale, offset_x, offset_y, shift_x=0, shift_y=0):
    tx = int((x + shift_x) * scale + offset_x)
    ty = int((y + shift_y) * scale + offset_y)
    tx = max(0, min(tx, SCREEN_WIDTH - 1))
    ty = max(0, min(ty, SCREEN_HEIGHT - 1))
    return tx, ty

def collect_bounds(root):
    """Quick bounds calculation"""
    minx = float('inf'); miny = float('inf')
    maxx = float('-inf'); maxy = float('-inf')
    
    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        
        if tag == 'path':
            d = elem.get('d', '')
            if not d:
                continue
            try:
                pts = smart_parse_path(d, tolerance=0.5)
                for x, y in pts:
                    minx = min(minx, x); maxx = max(maxx, x)
                    miny = min(miny, y); maxy = max(maxy, y)
            except:
                continue
        
        elif tag == 'rect':
            x = float(elem.get('x', 0)); y = float(elem.get('y', 0))
            w = float(elem.get('width', 0)); h = float(elem.get('height', 0))
            minx = min(minx, x); maxx = max(maxx, x + w)
            miny = min(miny, y); maxy = max(maxy, y + h)
        
        elif tag == 'circle':
            cx = float(elem.get('cx', 0)); cy = float(elem.get('cy', 0))
            r = float(elem.get('r', 0))
            minx = min(minx, cx - r); maxx = max(maxx, cx + r)
            miny = min(miny, cy - r); maxy = max(maxy, cy + r)
        
        elif tag == 'line':
            x1 = float(elem.get('x1', 0)); y1 = float(elem.get('y1', 0))
            x2 = float(elem.get('x2', 0)); y2 = float(elem.get('y2', 0))
            minx = min(minx, x1, x2); maxx = max(maxx, x1, x2)
            miny = min(miny, y1, y2); maxy = max(maxy, y1, y2)
        
        elif tag in ('polyline', 'polygon'):
            pts = [float(n) for n in re.findall(r'-?\d*\.?\d+', elem.get('points', ''))]
            for i in range(0, len(pts), 2):
                if i < len(pts):
                    minx = min(minx, pts[i]); maxx = max(maxx, pts[i])
            for i in range(1, len(pts), 2):
                if i < len(pts):
                    miny = min(miny, pts[i]); maxy = max(maxy, pts[i])
    
    return (minx, miny, maxx, maxy)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 svg_to_lamp_smart.py file.svg [scale] [offsetX] [offsetY] [tolerance]")
        print("\nArguments:")
        print("  scale      - Scale factor (default: auto)")
        print("  offsetX    - X offset (default: auto-center)")
        print("  offsetY    - Y offset (default: auto-center)")
        print("  tolerance  - Simplification tolerance in SVG units (default: 1.0)")
        print("               Lower = more detail, Higher = fewer commands")
        print("\nExamples:")
        print("  python3 svg_to_lamp_smart.py R.svg")
        print("  python3 svg_to_lamp_smart.py R.svg 10")
        print("  python3 svg_to_lamp_smart.py R.svg 10 500 800")
        print("  python3 svg_to_lamp_smart.py R.svg 10 500 800 2.0  # More aggressive simplification")
        sys.exit(1)
    
    svg_file = sys.argv[1]
    scale = 1.0; offset_x = 0; offset_y = 0; tolerance = 1.0
    
    if len(sys.argv) > 2: scale = float(sys.argv[2])
    if len(sys.argv) > 3: offset_x = int(sys.argv[3])
    if len(sys.argv) > 4: offset_y = int(sys.argv[4])
    if len(sys.argv) > 5: tolerance = float(sys.argv[5])
    
    if not Path(svg_file).exists():
        print(f"Error: File not found: {svg_file}", file=sys.stderr)
        sys.exit(1)
    
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    # Calculate bounds
    minx, miny, maxx, maxy = collect_bounds(root)
    if minx == float('inf'):
        print("# No drawable content found", file=sys.stderr)
        sys.exit(0)
    
    svg_width = maxx - minx
    svg_height = maxy - miny
    
    # Auto-scale if not specified
    if scale == 1.0 and svg_width > 0 and svg_height > 0:
        MARGIN = 50
        scale_x = (SCREEN_WIDTH - 2 * MARGIN) / svg_width
        scale_y = (SCREEN_HEIGHT - 2 * MARGIN) / svg_height
        scale = int(max(1, min(30, min(scale_x, scale_y))))
    
    # Auto-center if not specified
    if offset_x == 0 and offset_y == 0:
        offset_x = max(50, int((SCREEN_WIDTH - svg_width * scale) / 2))
        offset_y = max(50, int((SCREEN_HEIGHT - svg_height * scale) / 2))
    
    shift_x = -minx
    shift_y = -miny
    
    # Generate pen commands
    commands = []
    path_stats = []
    
    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        elem_id = elem.get('id', '')
        
        # Skip pin circles
        if 'pin' in elem_id.lower():
            continue
        
        if tag == 'path':
            d = elem.get('d', '')
            if not d:
                continue
            
            try:
                pts = smart_parse_path(d, tolerance)
                if not pts:
                    continue
                
                path_stats.append(len(pts))
                
                # Emit pen commands
                x0, y0 = pts[0]
                tx, ty = transform_point(x0, y0, scale, offset_x, offset_y, shift_x, shift_y)
                commands.append(f"pen down {tx} {ty}")
                
                for x, y in pts[1:]:
                    tx, ty = transform_point(x, y, scale, offset_x, offset_y, shift_x, shift_y)
                    commands.append(f"pen move {tx} {ty}")
                
                commands.append("pen up")
            
            except Exception as e:
                print(f"Warning: Failed to parse path: {e}", file=sys.stderr)
                continue
        
        elif tag == 'rect':
            x = float(elem.get('x', 0)); y = float(elem.get('y', 0))
            w = float(elem.get('width', 0)); h = float(elem.get('height', 0))
            x1, y1 = transform_point(x, y, scale, offset_x, offset_y, shift_x, shift_y)
            x2, y2 = transform_point(x + w, y + h, scale, offset_x, offset_y, shift_x, shift_y)
            commands.append(f"pen rectangle {x1} {y1} {x2} {y2}")
        
        elif tag == 'circle':
            cx = float(elem.get('cx', 0)); cy = float(elem.get('cy', 0))
            r = float(elem.get('r', 0))
            cx_t, cy_t = transform_point(cx, cy, scale, offset_x, offset_y, shift_x, shift_y)
            commands.append(f"pen circle {cx_t} {cy_t} {int(r * scale)}")
        
        elif tag == 'line':
            x1 = float(elem.get('x1', 0)); y1 = float(elem.get('y1', 0))
            x2 = float(elem.get('x2', 0)); y2 = float(elem.get('y2', 0))
            tx1, ty1 = transform_point(x1, y1, scale, offset_x, offset_y, shift_x, shift_y)
            tx2, ty2 = transform_point(x2, y2, scale, offset_x, offset_y, shift_x, shift_y)
            commands.append(f"pen line {tx1} {ty1} {tx2} {ty2}")
        
        elif tag in ('polyline', 'polygon'):
            pts = [float(n) for n in re.findall(r'-?\d*\.?\d+', elem.get('points', ''))]
            if len(pts) >= 4:
                x0, y0 = pts[0], pts[1]
                tx, ty = transform_point(x0, y0, scale, offset_x, offset_y, shift_x, shift_y)
                commands.append(f"pen down {tx} {ty}")
                
                for i in range(2, len(pts), 2):
                    tx, ty = transform_point(pts[i], pts[i + 1], scale, offset_x, offset_y, shift_x, shift_y)
                    commands.append(f"pen move {tx} {ty}")
                
                if tag == 'polygon':
                    tx, ty = transform_point(pts[0], pts[1], scale, offset_x, offset_y, shift_x, shift_y)
                    commands.append(f"pen move {tx} {ty}")
                
                commands.append("pen up")
    
    # Output statistics
    if path_stats:
        avg_points = sum(path_stats) / len(path_stats)
        print(f"# Processed {len(path_stats)} paths", file=sys.stderr)
        print(f"# Average points per path: {avg_points:.1f}", file=sys.stderr)
        print(f"# Total commands: {len(commands)}", file=sys.stderr)
        print(f"# Tolerance: {tolerance}", file=sys.stderr)
    
    # Output pen commands
    print("\n".join(commands))

if __name__ == '__main__':
    main()
