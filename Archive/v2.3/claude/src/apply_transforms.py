#!/usr/bin/env python3
"""
Remove transforms from SVG files by baking them into coordinates
"""
import xml.etree.ElementTree as ET
import re
import sys

def parse_matrix(transform_str):
    """Parse matrix(a,b,c,d,e,f)"""
    match = re.search(r'matrix\(([-\d.eE]+),([-\d.eE]+),([-\d.eE]+),([-\d.eE]+),([-\d.eE]+),([-\d.eE]+)\)', transform_str)
    if match:
        return [float(x) for x in match.groups()]
    return None

def apply_matrix(x, y, matrix):
    """Apply affine transform"""
    a, b, c, d, e, f = matrix
    return a*x + c*y + e, b*x + d*y + f

def transform_path(d, matrix):
    """Apply matrix to path data"""
    # Simple number extraction and transformation
    def transform_coords(match):
        x, y = float(match.group(1)), float(match.group(2))
        nx, ny = apply_matrix(x, y, matrix)
        return f"{nx:.3f},{ny:.3f}"
    
    # Transform coordinate pairs
    d = re.sub(r'([-\d.]+)[,\s]+([-\d.]+)', transform_coords, d)
    return d

def remove_transforms(svg_file, output_file):
    """Remove all transforms by baking into coordinates"""
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    for elem in root.iter():
        transform = elem.get('transform')
        if not transform:
            continue
        
        matrix = parse_matrix(transform)
        if not matrix:
            continue
        
        tag = elem.tag.split('}')[-1]
        
        if tag == 'path':
            d = elem.get('d', '')
            if d:
                elem.set('d', transform_path(d, matrix))
        
        elif tag == 'circle':
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            r = float(elem.get('r', 0))
            nx, ny = apply_matrix(cx, cy, matrix)
            # Scale radius by average of x/y scale factors
            nr = r * ((abs(matrix[0]) + abs(matrix[3])) / 2)
            elem.set('cx', str(nx))
            elem.set('cy', str(ny))
            elem.set('r', str(nr))
        
        elif tag == 'line':
            x1, y1 = float(elem.get('x1', 0)), float(elem.get('y1', 0))
            x2, y2 = float(elem.get('x2', 0)), float(elem.get('y2', 0))
            nx1, ny1 = apply_matrix(x1, y1, matrix)
            nx2, ny2 = apply_matrix(x2, y2, matrix)
            elem.set('x1', str(nx1))
            elem.set('y1', str(ny1))
            elem.set('x2', str(nx2))
            elem.set('y2', str(ny2))
        
        # Remove the transform
        elem.attrib.pop('transform')
    
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    print(f"Removed transforms from {svg_file} -> {output_file}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 apply_transforms.py input.svg output.svg")
        sys.exit(1)
    remove_transforms(sys.argv[1], sys.argv[2])
