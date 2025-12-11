#!/usr/bin/env python3
"""
SVG Normalizer - Remove transforms and convert to absolute coordinates

This script processes SVG files to:
1. Apply all matrix transforms to coordinates
2. Convert relative path commands to absolute
3. Output clean SVG with same visual appearance but no transforms
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
import math

# SVG namespace
SVG_NS = {'svg': 'http://www.w3.org/2000/svg',
          'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
          'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'}

# Register namespaces
for prefix, uri in SVG_NS.items():
    ET.register_namespace(prefix, uri)


def parse_transform(transform_str):
    """Parse SVG transform string and return transformation function"""
    if not transform_str:
        return lambda x, y: (x, y)

    # Parse matrix(a, b, c, d, e, f)
    matrix_match = re.search(r'matrix\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)', transform_str)
    if matrix_match:
        a, b, c, d, e, f = map(float, matrix_match.groups())
        return lambda x, y: (a * x + c * y + e, b * x + d * y + f)

    # Parse translate(x, y) or translate(x)
    translate_match = re.search(r'translate\(([-\d.]+)(?:,\s*([-\d.]+))?\)', transform_str)
    if translate_match:
        tx = float(translate_match.group(1))
        ty = float(translate_match.group(2)) if translate_match.group(2) else 0
        return lambda x, y: (x + tx, y + ty)

    # Parse scale(x, y) or scale(x)
    scale_match = re.search(r'scale\(([-\d.]+)(?:,\s*([-\d.]+))?\)', transform_str)
    if scale_match:
        sx = float(scale_match.group(1))
        sy = float(scale_match.group(2)) if scale_match.group(2) else sx
        return lambda x, y: (x * sx, y * sy)

    # Parse rotate(angle, cx, cy) or rotate(angle)
    rotate_match = re.search(r'rotate\(([-\d.]+)(?:,\s*([-\d.]+),\s*([-\d.]+))?\)', transform_str)
    if rotate_match:
        angle = float(rotate_match.group(1)) * math.pi / 180
        cx = float(rotate_match.group(2)) if rotate_match.group(2) else 0
        cy = float(rotate_match.group(3)) if rotate_match.group(3) else 0
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return lambda x, y: (
            cos_a * (x - cx) - sin_a * (y - cy) + cx,
            sin_a * (x - cx) + cos_a * (y - cy) + cy
        )

    return lambda x, y: (x, y)


def combine_transforms(*transforms):
    """Combine multiple transformation functions"""
    def combined(x, y):
        for transform in transforms:
            x, y = transform(x, y)
        return x, y
    return combined


def parse_path_data(path_d):
    """Parse SVG path data and convert to absolute coordinates"""
    if not path_d:
        return []

    # Split path data into commands and coordinates
    tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-\d.]+', path_d)

    commands = []
    i = 0
    current_x, current_y = 0, 0
    start_x, start_y = 0, 0

    while i < len(tokens):
        cmd = tokens[i]
        i += 1

        # Get coordinates for this command
        if cmd in 'Zz':
            commands.append(('L', start_x, start_y))
            current_x, current_y = start_x, start_y
            continue

        # Determine number of parameters
        param_counts = {
            'M': 2, 'm': 2, 'L': 2, 'l': 2,
            'H': 1, 'h': 1, 'V': 1, 'v': 1,
            'C': 6, 'c': 6, 'S': 4, 's': 4,
            'Q': 4, 'q': 4, 'T': 2, 't': 2,
            'A': 7, 'a': 7
        }

        param_count = param_counts.get(cmd, 0)
        params = []
        for _ in range(param_count):
            if i < len(tokens) and tokens[i] not in 'MmLlHhVvCcSsQqTtAaZz':
                params.append(float(tokens[i]))
                i += 1

        # Convert to absolute coordinates
        if cmd == 'M':
            current_x, current_y = params[0], params[1]
            start_x, start_y = current_x, current_y
            commands.append(('M', current_x, current_y))
        elif cmd == 'm':
            current_x += params[0]
            current_y += params[1]
            start_x, start_y = current_x, current_y
            commands.append(('M', current_x, current_y))
        elif cmd == 'L':
            current_x, current_y = params[0], params[1]
            commands.append(('L', current_x, current_y))
        elif cmd == 'l':
            current_x += params[0]
            current_y += params[1]
            commands.append(('L', current_x, current_y))
        elif cmd == 'H':
            current_x = params[0]
            commands.append(('L', current_x, current_y))
        elif cmd == 'h':
            current_x += params[0]
            commands.append(('L', current_x, current_y))
        elif cmd == 'V':
            current_y = params[0]
            commands.append(('L', current_x, current_y))
        elif cmd == 'v':
            current_y += params[0]
            commands.append(('L', current_x, current_y))
        elif cmd in 'Cc':
            if cmd == 'C':
                x1, y1, x2, y2, x, y = params
            else:  # 'c'
                x1 = current_x + params[0]
                y1 = current_y + params[1]
                x2 = current_x + params[2]
                y2 = current_y + params[3]
                x = current_x + params[4]
                y = current_y + params[5]
            current_x, current_y = x, y
            commands.append(('C', x1, y1, x2, y2, x, y))

    return commands


def commands_to_path_string(commands):
    """Convert command list back to path string"""
    if not commands:
        return ""

    parts = []
    for cmd in commands:
        if cmd[0] == 'M':
            parts.append(f"M {cmd[1]:.3f},{cmd[2]:.3f}")
        elif cmd[0] == 'L':
            parts.append(f"L {cmd[1]:.3f},{cmd[2]:.3f}")
        elif cmd[0] == 'C':
            parts.append(f"C {cmd[1]:.3f},{cmd[2]:.3f} {cmd[3]:.3f},{cmd[4]:.3f} {cmd[5]:.3f},{cmd[6]:.3f}")

    return " ".join(parts)


def apply_transform_to_path(path_d, transform_func):
    """Apply transformation to SVG path data"""
    commands = parse_path_data(path_d)

    transformed_commands = []
    for cmd in commands:
        if cmd[0] == 'M' or cmd[0] == 'L':
            x, y = transform_func(cmd[1], cmd[2])
            transformed_commands.append((cmd[0], x, y))
        elif cmd[0] == 'C':
            x1, y1 = transform_func(cmd[1], cmd[2])
            x2, y2 = transform_func(cmd[3], cmd[4])
            x, y = transform_func(cmd[5], cmd[6])
            transformed_commands.append((cmd[0], x1, y1, x2, y2, x, y))

    return commands_to_path_string(transformed_commands)


def normalize_svg(svg_path):
    """Normalize an SVG file by removing transforms and converting to absolute coordinates"""
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Track accumulated transforms
    def process_element(elem, parent_transform=None):
        """Recursively process elements and apply transforms"""
        # Get element's own transform
        transform_str = elem.get('transform', '')
        elem_transform = parse_transform(transform_str)

        # Combine with parent transform
        if parent_transform:
            combined_transform = combine_transforms(parent_transform, elem_transform)
        else:
            combined_transform = elem_transform

        # Apply transform to paths
        if elem.tag.endswith('path'):
            path_d = elem.get('d', '')
            if path_d and combined_transform:
                new_d = apply_transform_to_path(path_d, combined_transform)
                elem.set('d', new_d)
            # Remove transform attribute
            if 'transform' in elem.attrib:
                del elem.attrib['transform']

        # Apply transform to circles
        elif elem.tag.endswith('circle'):
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            if combined_transform:
                new_cx, new_cy = combined_transform(cx, cy)
                elem.set('cx', f"{new_cx:.3f}")
                elem.set('cy', f"{new_cy:.3f}")
            # Remove transform attribute
            if 'transform' in elem.attrib:
                del elem.attrib['transform']

        # Apply transform to rectangles
        elif elem.tag.endswith('rect'):
            x = float(elem.get('x', 0))
            y = float(elem.get('y', 0))
            if combined_transform:
                new_x, new_y = combined_transform(x, y)
                elem.set('x', f"{new_x:.3f}")
                elem.set('y', f"{new_y:.3f}")
            # Remove transform attribute
            if 'transform' in elem.attrib:
                del elem.attrib['transform']

        # Process children with accumulated transform
        for child in elem:
            process_element(child, combined_transform)

        # If this is a group with only transform, remove it after processing
        if elem.tag.endswith('g') and 'transform' in elem.attrib:
            del elem.attrib['transform']

    # Start processing from root
    for child in root:
        process_element(child)

    return tree


def main():
    """Process all SVG files in assets directory"""
    assets_dir = Path('assets')
    svg_files = list(assets_dir.glob('**/*.svg'))

    output_md = "# Normalized SVG Components\n\n"
    output_md += "All components with transforms removed and converted to absolute coordinates.\n\n"
    output_md += "---\n\n"

    for svg_file in sorted(svg_files):
        print(f"Processing {svg_file}...")

        # Skip Library.svg files (source files)
        if 'Library.svg' in svg_file.name or 'Electrical_symbols' in svg_file.name:
            print(f"  Skipping library file: {svg_file.name}")
            continue

        try:
            # Normalize the SVG
            tree = normalize_svg(svg_file)

            # Convert to string
            ET.register_namespace('', 'http://www.w3.org/2000/svg')
            svg_string = ET.tostring(tree.getroot(), encoding='unicode')

            # Pretty format
            svg_string = svg_string.replace('><', '>\n  <')

            # Add to markdown
            component_name = svg_file.stem
            relative_path = svg_file.relative_to(assets_dir)

            output_md += f"## {component_name}\n\n"
            output_md += f"**Path:** `{relative_path}`\n\n"
            output_md += f"```xml\n{svg_string}\n```\n\n"
            output_md += "---\n\n"

            print(f"  ✓ Processed: {component_name}")

        except Exception as e:
            print(f"  ✗ Error processing {svg_file}: {e}")
            continue

    # Write output
    output_file = Path('NORMALIZED_SVG_COMPONENTS.md')
    output_file.write_text(output_md)
    print(f"\n✓ Created {output_file}")
    print(f"  Processed {len([f for f in svg_files if 'Library' not in f.name])} components")


if __name__ == '__main__':
    main()
