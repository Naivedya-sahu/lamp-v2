#!/usr/bin/env python3
"""
SVG Normalizer v2 - Remove transforms, center coordinates, clean output

Processes SVG files to create standalone, normalized versions that:
1. Apply all transforms to absolute coordinates
2. Center the component at viewBox origin
3. Remove all transform attributes
4. Output clean, copy-paste ready SVG code
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
import math


def parse_transform(transform_str):
    """Parse SVG transform string and return 2x3 matrix [a,b,c,d,e,f]"""
    if not transform_str:
        return [1, 0, 0, 1, 0, 0]  # Identity matrix

    # Parse matrix(a, b, c, d, e, f)
    matrix_match = re.search(r'matrix\(([-\d.e]+)[,\s]+([-\d.e]+)[,\s]+([-\d.e]+)[,\s]+([-\d.e]+)[,\s]+([-\d.e]+)[,\s]+([-\d.e]+)\)', transform_str)
    if matrix_match:
        return [float(x) for x in matrix_match.groups()]

    # Parse translate(x, y) or translate(x)
    translate_match = re.search(r'translate\(([-\d.e]+)(?:[,\s]+([-\d.e]+))?\)', transform_str)
    if translate_match:
        tx = float(translate_match.group(1))
        ty = float(translate_match.group(2)) if translate_match.group(2) else 0
        return [1, 0, 0, 1, tx, ty]

    # Parse scale(x, y) or scale(x)
    scale_match = re.search(r'scale\(([-\d.e]+)(?:[,\s]+([-\d.e]+))?\)', transform_str)
    if scale_match:
        sx = float(scale_match.group(1))
        sy = float(scale_match.group(2)) if scale_match.group(2) else sx
        return [sx, 0, 0, sy, 0, 0]

    return [1, 0, 0, 1, 0, 0]


def multiply_matrices(m1, m2):
    """Multiply two 2x3 transformation matrices"""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2

    return [
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1
    ]


def apply_matrix(x, y, matrix):
    """Apply transformation matrix to point"""
    a, b, c, d, e, f = matrix
    new_x = a * x + c * y + e
    new_y = b * x + d * y + f
    return new_x, new_y


def parse_path_data(path_d):
    """Parse SVG path data and extract all coordinate points"""
    if not path_d:
        return []

    # Split into tokens
    tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-\d.e]+', path_d)

    points = []
    i = 0
    current_x, current_y = 0, 0

    while i < len(tokens):
        cmd = tokens[i]
        i += 1

        if cmd in 'Zz':
            continue

        # Extract coordinates based on command
        if cmd in 'Mm':
            if i + 1 < len(tokens):
                x, y = float(tokens[i]), float(tokens[i+1])
                if cmd == 'm':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y
                points.append((current_x, current_y))
                i += 2

        elif cmd in 'Ll':
            if i + 1 < len(tokens):
                x, y = float(tokens[i]), float(tokens[i+1])
                if cmd == 'l':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y
                points.append((current_x, current_y))
                i += 2

        elif cmd in 'Hh':
            if i < len(tokens):
                x = float(tokens[i])
                current_x = current_x + x if cmd == 'h' else x
                points.append((current_x, current_y))
                i += 1

        elif cmd in 'Vv':
            if i < len(tokens):
                y = float(tokens[i])
                current_y = current_y + y if cmd == 'v' else y
                points.append((current_x, current_y))
                i += 1

        elif cmd in 'Cc':
            if i + 5 < len(tokens):
                coords = [float(tokens[i+j]) for j in range(6)]
                if cmd == 'c':
                    points.extend([
                        (current_x + coords[0], current_y + coords[1]),
                        (current_x + coords[2], current_y + coords[3]),
                        (current_x + coords[4], current_y + coords[5])
                    ])
                    current_x += coords[4]
                    current_y += coords[5]
                else:
                    points.extend([
                        (coords[0], coords[1]),
                        (coords[2], coords[3]),
                        (coords[4], coords[5])
                    ])
                    current_x, current_y = coords[4], coords[5]
                i += 6

    return points


def extract_all_points(elem, parent_matrix=None):
    """Recursively extract all coordinate points from an element tree"""
    if parent_matrix is None:
        parent_matrix = [1, 0, 0, 1, 0, 0]

    # Get element's transform
    transform_str = elem.get('transform', '')
    elem_matrix = parse_transform(transform_str)

    # Combine with parent matrix
    combined_matrix = multiply_matrices(parent_matrix, elem_matrix)

    all_points = []
    tag = elem.tag.split('}')[-1]  # Remove namespace

    # Extract points based on element type
    if tag == 'path':
        path_d = elem.get('d', '')
        path_points = parse_path_data(path_d)
        for x, y in path_points:
            tx, ty = apply_matrix(x, y, combined_matrix)
            all_points.append((tx, ty))

    elif tag == 'circle':
        cx = float(elem.get('cx', 0))
        cy = float(elem.get('cy', 0))
        r = float(elem.get('r', 0))
        tx, ty = apply_matrix(cx, cy, combined_matrix)
        # Add circle bounding box points
        all_points.extend([(tx-r, ty-r), (tx+r, ty+r)])

    elif tag == 'rect':
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        w = float(elem.get('width', 0))
        h = float(elem.get('height', 0))
        # Add all corners
        for px, py in [(x, y), (x+w, y), (x, y+h), (x+w, y+h)]:
            tx, ty = apply_matrix(px, py, combined_matrix)
            all_points.append((tx, ty))

    # Recurse into children
    for child in elem:
        all_points.extend(extract_all_points(child, combined_matrix))

    return all_points


def transform_element(elem, matrix, offset_x, offset_y):
    """Apply transformation and offset to element, removing transform attribute"""
    tag = elem.tag.split('}')[-1]

    if tag == 'path':
        path_d = elem.get('d', '')
        if path_d:
            # Transform and offset path
            transformed_path = transform_path_data(path_d, matrix, offset_x, offset_y)
            elem.set('d', transformed_path)

    elif tag == 'circle':
        cx = float(elem.get('cx', 0))
        cy = float(elem.get('cy', 0))
        tx, ty = apply_matrix(cx, cy, matrix)
        elem.set('cx', f"{tx + offset_x:.3f}")
        elem.set('cy', f"{ty + offset_y:.3f}")

    elif tag == 'rect':
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        tx, ty = apply_matrix(x, y, matrix)
        elem.set('x', f"{tx + offset_x:.3f}")
        elem.set('y', f"{ty + offset_y:.3f}")

    # Remove transform attribute
    if 'transform' in elem.attrib:
        del elem.attrib['transform']

    # Recurse into children
    for child in elem:
        transform_element(child, matrix, offset_x, offset_y)


def transform_path_data(path_d, matrix, offset_x, offset_y):
    """Transform path data and convert to simple format"""
    if not path_d:
        return ""

    tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-\d.e]+', path_d)

    result = []
    i = 0
    current_x, current_y = 0, 0

    while i < len(tokens):
        cmd = tokens[i]
        i += 1

        if cmd in 'Zz':
            continue

        if cmd in 'Mm':
            if i + 1 < len(tokens):
                x, y = float(tokens[i]), float(tokens[i+1])
                if cmd == 'm':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y

                tx, ty = apply_matrix(current_x, current_y, matrix)
                result.append(f"M {tx + offset_x:.3f},{ty + offset_y:.3f}")
                i += 2

        elif cmd in 'Ll':
            if i + 1 < len(tokens):
                x, y = float(tokens[i]), float(tokens[i+1])
                if cmd == 'l':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y

                tx, ty = apply_matrix(current_x, current_y, matrix)
                result.append(f"L {tx + offset_x:.3f},{ty + offset_y:.3f}")
                i += 2

        elif cmd in 'Hh':
            if i < len(tokens):
                x = float(tokens[i])
                current_x = current_x + x if cmd == 'h' else x
                tx, ty = apply_matrix(current_x, current_y, matrix)
                result.append(f"L {tx + offset_x:.3f},{ty + offset_y:.3f}")
                i += 1

        elif cmd in 'Vv':
            if i < len(tokens):
                y = float(tokens[i])
                current_y = current_y + y if cmd == 'v' else y
                tx, ty = apply_matrix(current_x, current_y, matrix)
                result.append(f"L {tx + offset_x:.3f},{ty + offset_y:.3f}")
                i += 1

    return " ".join(result)


def normalize_svg_file(svg_path):
    """Normalize SVG: remove transforms, center component"""
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Extract all points to calculate bounding box
    all_points = extract_all_points(root)

    if not all_points:
        return None, "No drawable elements found"

    # Calculate bounding box
    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)

    width = max_x - min_x
    height = max_y - min_y

    # Calculate offset to move to origin
    offset_x = -min_x
    offset_y = -min_y

    # Process all elements
    def process_tree(elem, parent_matrix=None):
        if parent_matrix is None:
            parent_matrix = [1, 0, 0, 1, 0, 0]

        transform_str = elem.get('transform', '')
        elem_matrix = parse_transform(transform_str)
        combined_matrix = multiply_matrices(parent_matrix, elem_matrix)

        # Transform this element
        transform_element(elem, combined_matrix, offset_x, offset_y)

        # Process children
        for child in elem:
            process_tree(child, combined_matrix)

    for child in root:
        process_tree(child)

    # Update root viewBox
    root.set('viewBox', f"0 0 {width:.3f} {height:.3f}")
    root.set('width', f"{width:.3f}")
    root.set('height', f"{height:.3f}")

    return tree, None


def create_clean_svg(tree, component_id):
    """Create a minimal, clean SVG string"""
    root = tree.getroot()

    # Create new minimal SVG
    svg_elem = ET.Element('svg')
    svg_elem.set('xmlns', 'http://www.w3.org/2000/svg')
    svg_elem.set('viewBox', root.get('viewBox', ''))
    svg_elem.set('width', root.get('width', ''))
    svg_elem.set('height', root.get('height', ''))

    # Find all drawable elements (paths, circles, etc.)
    def collect_drawable_elements(elem):
        drawables = []
        tag = elem.tag.split('}')[-1]

        if tag in ['path', 'circle', 'rect', 'line', 'polyline', 'polygon']:
            drawables.append(elem)

        for child in elem:
            drawables.extend(collect_drawable_elements(child))

        return drawables

    # Collect all drawable elements
    drawable_elements = collect_drawable_elements(root)

    # Add to clean SVG
    g_elem = ET.SubElement(svg_elem, 'g')
    g_elem.set('id', component_id)

    for elem in drawable_elements:
        g_elem.append(elem)

    return svg_elem


def main():
    """Process all SVG component files"""
    assets_dir = Path('assets')
    component_dirs = [
        assets_dir / 'components',
        assets_dir / 'components' / 'e'
    ]

    output_md = "# Normalized SVG Components\n\n"
    output_md += "All transforms removed, coordinates absolute, ready to copy-paste.\n\n"
    output_md += "---\n\n"

    processed_count = 0

    for comp_dir in component_dirs:
        if not comp_dir.exists():
            continue

        for svg_file in sorted(comp_dir.glob('*.svg')):
            print(f"Processing {svg_file.name}...")

            try:
                tree, error = normalize_svg_file(svg_file)

                if error:
                    print(f"  ✗ Error: {error}")
                    continue

                # Create clean SVG
                clean_svg = create_clean_svg(tree, svg_file.stem)

                # Convert to string
                svg_string = ET.tostring(clean_svg, encoding='unicode')

                # Pretty print (basic)
                svg_string = svg_string.replace('><', '>\n  <')
                svg_string = svg_string.replace('</g>', '\n  </g>')

                # Add to markdown
                component_name = svg_file.stem
                relative_path = svg_file.relative_to(assets_dir)

                output_md += f"## {component_name}\n\n"
                output_md += f"**Path:** `{relative_path}`\n\n"
                output_md += f"```xml\n{svg_string}\n```\n\n"
                output_md += "---\n\n"

                processed_count += 1
                print(f"  ✓ {component_name}")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                continue

    # Write output
    output_file = Path('NORMALIZED_SVG_COMPONENTS.md')
    output_file.write_text(output_md)

    print(f"\n✓ Created {output_file}")
    print(f"  Processed {processed_count} components")


if __name__ == '__main__':
    main()
