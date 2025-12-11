#!/usr/bin/env python3
"""
svg_to_pen_commands.py (updated)

Usage examples:
  python3 svg_to_pen_commands.py D.svg -o D.cmds --target-width 1404 --target-height 1872 --margin 20
  python3 svg_to_pen_commands.py D.svg -o D.cmds --scale 2.0 --rdp-epsilon 0.2

Key additions vs prior:
 - --scale: uniform multiplier after fitting (multiplicative)
 - --margin: pixels (applied inside the target area)
 - --margin-percent: percentage of smaller device dimension (overrides --margin if >0)
 - Produces # BOUNDS in final command coordinate space (after scale+margin)
"""

from xml.etree import ElementTree as ET
from svgpathtools import parse_path, svg2paths2
import math, argparse, re, sys

# ---------- helpers ----------
def matrix_multiply(a, b):
    a1,b1,c1,d1,e1,f1 = a
    a2,b2,c2,d2,e2,f2 = b
    return (
        a1*a2 + c1*b2,
        b1*a2 + d1*b2,
        a1*c2 + c1*d2,
        b1*c2 + d1*d2,
        a1*e2 + c1*f2 + e1,
        b1*e2 + d1*f2 + f1
    )

def parse_transform(transform_str):
    if not transform_str: return (1,0,0,1,0,0)
    tokens = re.finditer(r'(?P<name>\w+)\s*\(\s*(?P<args>[^)]+)\)', transform_str)
    mat = (1,0,0,1,0,0)
    for m in tokens:
        name = m.group('name')
        args = [float(x) for x in re.split(r'[,\s]+', m.group('args').strip()) if x!='']
        if name == 'matrix' and len(args) >= 6:
            mat2 = tuple(args[:6])
        elif name == 'translate':
            tx = args[0] if len(args)>0 else 0.0
            ty = args[1] if len(args)>1 else 0.0
            mat2 = (1,0,0,1,tx,ty)
        elif name == 'scale':
            sx = args[0] if len(args)>0 else 1.0
            sy = args[1] if len(args)>1 else sx
            mat2 = (sx,0,0,sy,0,0)
        elif name == 'rotate':
            a = math.radians(args[0])
            cosA = math.cos(a); sinA = math.sin(a)
            if len(args) > 2:
                cx, cy = args[1], args[2]
                mat2 = (cosA, sinA, -sinA, cosA, cx - cosA*cx + sinA*cy, cy - sinA*cx - cosA*cy)
            else:
                mat2 = (cosA, sinA, -sinA, cosA, 0, 0)
        else:
            mat2 = (1,0,0,1,0,0)
        mat = matrix_multiply(mat, mat2)
    return mat

def apply_matrix_to_point(x, y, m):
    a,b,c,d,e,f = m
    return a*x + c*y + e, b*x + d*y + f

# RDP
def point_line_dist(px, py, x1, y1, x2, y2):
    dx = x2 - x1; dy = y2 - y1
    if dx==0 and dy==0:
        return math.hypot(px-x1, py-y1)
    t = ((px-x1)*dx + (py-y1)*dy) / (dx*dx + dy*dy)
    t = max(0.0, min(1.0, t))
    projx = x1 + t*dx; projy = y1 + t*dy
    return math.hypot(px-projx, py-projy)

def rdp(points, eps):
    if eps <= 0 or len(points) < 3: return points[:]
    def _rdp(pts):
        if len(pts) < 3:
            return pts
        x1,y1 = pts[0]; x2,y2 = pts[-1]
        maxd = -1; idx = -1
        for i in range(1,len(pts)-1):
            d = point_line_dist(pts[i][0], pts[i][1], x1,y1, x2,y2)
            if d > maxd:
                maxd = d; idx = i
        if maxd > eps:
            left = _rdp(pts[:idx+1]); right = _rdp(pts[idx:])
            return left[:-1] + right
        else:
            return [pts[0], pts[-1]]
    return _rdp(points)

# Collect paths with cumulative transforms
def collect_paths(svg_root):
    stack = [(svg_root, (1,0,0,1,0,0))]
    collected = []
    while stack:
        elem, cmat = stack.pop()
        tr = elem.get('transform')
        if tr:
            this = parse_transform(tr)
            cmat = matrix_multiply(cmat, this)
        tag = elem.tag.split('}')[-1]
        if tag == 'path':
            d = elem.get('d')
            if d:
                collected.append((d, cmat, elem))
        for child in list(elem):
            stack.append((child, cmat))
    return collected

def sample_path_d(d, transform_matrix, samples_per_unit):
    path_obj = parse_path(d)
    pts = []
    for seg in path_obj:
        try:
            length = seg.length(error=1e-4)
        except Exception:
            length = 1.0
        n = max(2, int(math.ceil(length * samples_per_unit)))
        for i in range(n):
            t = i / (n-1)
            z = seg.point(t)
            x,y = z.real, z.imag
            X,Y = apply_matrix_to_point(x,y,transform_matrix)
            pts.append((X,Y))
    return pts

def emit_points_to_cmds(points, rdp_eps, roundfn):
    if not points: return []
    if rdp_eps and rdp_eps > 0:
        pts = rdp(points, rdp_eps)
    else:
        pts = points
    cmds = []
    prev = None; started = False
    for (x,y) in pts:
        ix = int(roundfn(x)); iy = int(roundfn(y))
        if prev == (ix,iy): continue
        if not started:
            cmds.append(f"pen down {ix} {iy}")
            started = True
        else:
            cmds.append(f"pen move {ix} {iy}")
        prev = (ix,iy)
    if started: cmds.append("pen up")
    return cmds

# Main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--samples-per-unit", type=float, default=0.6)
    ap.add_argument("--rdp-epsilon", type=float, default=0.5)
    ap.add_argument("--out", "-o")
    ap.add_argument("--target-width", type=float, default=None)
    ap.add_argument("--target-height", type=float, default=None)
    ap.add_argument("--no-preserve-aspect", dest='preserve_aspect', action='store_false')
    ap.add_argument("--scale", type=float, default=1.0, help="uniform multiplier applied after fitting")
    ap.add_argument("--margin", type=float, default=0.0, help="margin in pixels inside the target area")
    ap.add_argument("--margin-percent", type=float, default=0.0, help="margin as percentage of smaller device dimension (overrides --margin if >0)")
    ap.add_argument("--round", choices=['round','floor','ceil'], default='round')
    args = ap.parse_args()

    roundfn = round
    if args.round == 'floor': roundfn = math.floor
    if args.round == 'ceil': roundfn = math.ceil

    tree = ET.parse(args.svg)
    root = tree.getroot()

    collected = collect_paths(root)
    if not collected:
        print("# No path elements found", file=sys.stderr); return

    all_points = []
    for d, mat, elem in collected:
        pts = sample_path_d(d, mat, args.samples_per_unit)
        if pts: all_points.extend(pts)
    if not all_points:
        print("# No sample points produced", file=sys.stderr); return

    xs = [p[0] for p in all_points]; ys = [p[1] for p in all_points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    width = max(1.0, maxx - minx); height = max(1.0, maxy - miny)

    # Determine target area
    target_w = args.target_width if args.target_width else width
    target_h = args.target_height if args.target_height else height

    # compute margin final
    margin_px = args.margin
    if args.margin_percent and args.margin_percent > 0:
        margin_px = min(target_w, target_h) * (args.margin_percent / 100.0)

    # compute scale to fit into (target_w - 2*margin) x (target_h - 2*margin)
    eff_w = max(1.0, target_w - 2*margin_px); eff_h = max(1.0, target_h - 2*margin_px)
    if args.preserve_aspect:
        s_fit = min(eff_w / width, eff_h / height)
        scale_x = scale_y = s_fit
    else:
        scale_x = eff_w / width
        scale_y = eff_h / height

    # apply user multiplier scale
    scale_x *= args.scale
    scale_y *= args.scale

    # translation: center inside target area by default (use center)
    scaled_w = width * scale_x
    scaled_h = height * scale_y
    offset_x = margin_px + (eff_w - scaled_w) / 2.0
    offset_y = margin_px + (eff_h - scaled_h) / 2.0

    # global transform: translate (-minx,-miny) then scale then offset
    def global_transform(x,y):
        X = (x - minx) * scale_x + offset_x
        Y = (y - miny) * scale_y + offset_y
        return X, Y

    # process each collected path to final commands
    out_cmds = []
    for d, mat, elem in collected:
        pts = sample_path_d(d, mat, args.samples_per_unit)
        if not pts: continue
        pts_trans = [global_transform(x,y) for (x,y) in pts]
        cmds = emit_points_to_cmds(pts_trans, args.rdp_epsilon, roundfn)
        # if path contains close 'z', attempt to close
        if 'z' in d.lower():
            if cmds and cmds[0].startswith('pen down') and len(cmds) >= 3:
                try:
                    first = cmds[0].split()[2:4]; last = None
                    if cmds[-1] == 'pen up' and len(cmds) >= 2:
                        last = cmds[-2].split()[2:4]
                    elif cmds[-1].startswith('pen move'):
                        last = cmds[-1].split()[2:4]
                    if last and first != last:
                        close_cmd = f"pen move {first[0]} {first[1]}"
                        if cmds[-1] == 'pen up':
                            cmds.insert(-1, close_cmd)
                        else:
                            cmds.append(close_cmd)
                except Exception:
                    pass
        if cmds:
            out_cmds.extend(cmds)

    # compute output bounds (after transform + scale)
    out_minx, out_miny = global_transform(minx, miny)
    out_maxx, out_maxy = global_transform(maxx, maxy)

    # produce output with BOUNDS header
    header = f"# BOUNDS {int(round(out_minx))} {int(round(out_miny))} {int(round(out_maxx))} {int(round(out_maxy))}"
    output_lines = [header] + out_cmds
    if args.out:
        with open(args.out,'w') as f: f.write('\n'.join(output_lines))
    else:
        print('\n'.join(output_lines))

if __name__ == '__main__':
    main()
