#!/usr/bin/env python3
"""
svg_to_lamp_svgpathtools.py
Optimized converter using svgpathtools to parse paths and sample curves.
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from svgpathtools import parse_path, Path as SPath
import re

SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

def transform_point(x, y, scale, offset_x, offset_y, shift_x=0, shift_y=0):
    tx = int((x + shift_x) * scale + offset_x)
    ty = int((y + shift_y) * scale + offset_y)
    tx = max(0, min(tx, SCREEN_WIDTH - 1))
    ty = max(0, min(ty, SCREEN_HEIGHT - 1))
    return tx, ty

def sample_svg_path(d, samples_per_unit=0.5, max_samples=40):
    """
    Parse d using svgpathtools.parse_path and return a list of points sampled along the path.
    samples_per_unit scales sampling density relative to segment length; clamp to max_samples per segment.
    """
    sp = parse_path(d)
    pts = []
    for seg in sp:
        seg_len = seg.length(error=1e-5)
        n = max(1, min(max_samples, int(max(1, seg_len * samples_per_unit * 10))))
        for i in range(n+1):
            t = i / n
            p = seg.point(t)
            pts.append((p.real, p.imag))
    # Remove near-duplicate consecutive points
    out = []
    last = (None, None)
    for x,y in pts:
        if last[0] is None or abs(x-last[0])>1e-6 or abs(y-last[1])>1e-6:
            out.append((x,y)); last = (x,y)
    return out

def collect_bounds(root):
    minx = float('inf'); miny = float('inf'); maxx = float('-inf'); maxy = float('-inf')
    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        if tag == 'path':
            d = elem.get('d','')
            if not d: continue
            pts = sample_svg_path(d, samples_per_unit=0.3)
            for x,y in pts:
                minx = min(minx, x); maxx = max(maxx, x)
                miny = min(miny, y); maxy = max(maxy, y)
        elif tag in ('rect','circle','line','polyline','polygon'):
            # simple handling similar to previous script
            if tag == 'rect':
                x = float(elem.get('x',0)); y = float(elem.get('y',0))
                w = float(elem.get('width',0)); h = float(elem.get('height',0))
                minx = min(minx, x); maxx = max(maxx, x+w)
                miny = min(miny, y); maxy = max(maxy, y+h)
            elif tag == 'circle':
                cx = float(elem.get('cx',0)); cy = float(elem.get('cy',0)); r = float(elem.get('r',0))
                minx = min(minx, cx-r); maxx = max(maxx, cx+r)
                miny = min(miny, cy-r); maxy = max(maxy, cy+r)
            elif tag == 'line':
                x1=float(elem.get('x1',0)); y1=float(elem.get('y1',0))
                x2=float(elem.get('x2',0)); y2=float(elem.get('y2',0))
                minx=min(minx,x1,x2); maxx=max(maxx,x1,x2)
                miny=min(miny,y1,y2); maxy=max(maxy,y1,y2)
            else: # polyline/polygon
                pts = [float(n) for n in re.findall(r'-?\d*\.?\d+', elem.get('points',''))]
                for i in range(0,len(pts),2):
                    minx = min(minx, pts[i]); maxx = max(maxx, pts[i])
                for i in range(1,len(pts),2):
                    miny = min(miny, pts[i]); maxy = max(maxy, pts[i])
    return (minx, miny, maxx, maxy)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 svg_to_lamp_svgpathtools.py file.svg [scale] [offsetX] [offsetY]")
        sys.exit(1)
    svg_file = sys.argv[1]
    scale = 1.0; offset_x = 0; offset_y = 0
    if len(sys.argv)>2: scale = float(sys.argv[2])
    if len(sys.argv)>3: offset_x = int(sys.argv[3])
    if len(sys.argv)>4: offset_y = int(sys.argv[4])

    if not Path(svg_file).exists():
        print(f"File not found: {svg_file}"); sys.exit(1)

    tree = ET.parse(svg_file); root = tree.getroot()
    minx, miny, maxx, maxy = collect_bounds(root)
    if minx==float('inf'):
        print("# No drawable content found"); sys.exit(0)

    svg_width = maxx - minx; svg_height = maxy - miny
    if scale == 1.0 and svg_width>0 and svg_height>0:
        MARGIN=50
        scale_x=(SCREEN_WIDTH-2*MARGIN)/svg_width
        scale_y=(SCREEN_HEIGHT-2*MARGIN)/svg_height
        scale=int(max(1,min(30,int(min(scale_x,scale_y)))))
    if offset_x==0 and offset_y==0:
        offset_x = max(50, int((SCREEN_WIDTH - svg_width*scale)/2))
        offset_y = max(50, int((SCREEN_HEIGHT - svg_height*scale)/2))
    shift_x = -minx; shift_y = -miny

    commands = []
    drawn_min_x = float('inf'); drawn_min_y = float('inf'); drawn_max_x = float('-inf'); drawn_max_y = float('-inf')

    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        if tag == 'path':
            d = elem.get('d','')
            if not d: continue
            pts = sample_svg_path(d, samples_per_unit=0.35)
            if not pts: continue
            # Emit commands: pen down at first point then pen move...
            x0,y0 = pts[0]
            tx,ty = transform_point(x0, y0, scale, offset_x, offset_y, shift_x, shift_y)
            drawn_min_x=min(drawn_min_x,tx); drawn_min_y=min(drawn_min_y,ty)
            drawn_max_x=max(drawn_max_x,tx); drawn_max_y=max(drawn_max_y,ty)
            commands.append(f"pen down {tx} {ty}")
            for x,y in pts[1:]:
                tx,ty = transform_point(x,y, scale, offset_x, offset_y, shift_x, shift_y)
                drawn_min_x=min(drawn_min_x,tx); drawn_min_y=min(drawn_min_y,ty)
                drawn_max_x=max(drawn_max_x,tx); drawn_max_y=max(drawn_max_y,ty)
                commands.append(f"pen move {tx} {ty}")
            commands.append("pen up")
        elif tag == 'rect':
            x=float(elem.get('x',0)); y=float(elem.get('y',0)); w=float(elem.get('width',0)); h=float(elem.get('height',0))
            x1,y1 = transform_point(x,y,scale,offset_x,offset_y,shift_x,shift_y)
            x2,y2 = transform_point(x+w,y+h,scale,offset_x,offset_y,shift_x,shift_y)
            commands.append(f"pen rectangle {x1} {y1} {x2} {y2}")
        elif tag == 'circle':
            cx=float(elem.get('cx',0)); cy=float(elem.get('cy',0)); r=float(elem.get('r',0))
            cx_t, cy_t = transform_point(cx, cy, scale, offset_x, offset_y, shift_x, shift_y)
            commands.append(f"pen circle {cx_t} {cy_t} {int(r*scale)}")
        elif tag == 'line':
            x1=float(elem.get('x1',0)); y1=float(elem.get('y1',0))
            x2=float(elem.get('x2',0)); y2=float(elem.get('y2',0))
            tx1,ty1 = transform_point(x1,y1,scale,offset_x,offset_y,shift_x,shift_y)
            tx2,ty2 = transform_point(x2,y2,scale,offset_x,offset_y,shift_x,shift_y)
            commands.append(f"pen line {tx1} {ty1} {tx2} {ty2}")
        elif tag in ('polyline','polygon'):
            pts = [float(n) for n in re.findall(r'-?\d*\.?\d+', elem.get('points',''))]
            if len(pts)>=4:
                x0,y0 = pts[0], pts[1]
                tx,ty = transform_point(x0,y0,scale,offset_x,offset_y,shift_x,shift_y)
                commands.append(f"pen down {tx} {ty}")
                for i in range(2,len(pts),2):
                    tx,ty = transform_point(pts[i], pts[i+1], scale, offset_x, offset_y, shift_x, shift_y)
                    commands.append(f"pen move {tx} {ty}")
                if tag=='polygon':
                    tx,ty = transform_point(pts[0], pts[1], scale, offset_x, offset_y, shift_x, shift_y)
                    commands.append(f"pen move {tx} {ty}")
                commands.append("pen up")

    if drawn_min_x!=float('inf'):
        margin=10
        #commands.insert(0, f"# BOUNDS {int(drawn_min_x-margin)} {int(drawn_min_y-margin)} {int(drawn_max_x+margin)} {int(drawn_max_y+margin)}")

    print("\n".join(commands))


if __name__=='__main__':
    main()
