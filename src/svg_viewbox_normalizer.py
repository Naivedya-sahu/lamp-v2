#!/usr/bin/env python3
"""
SVG ViewBox Normalizer - Remove transforms, adjust viewBox to match path coordinates
Keeps original path data intact, only changes viewBox to show the correct area
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_path_coords(path_d):
    """Extract all coordinates from path data"""
    if not path_d:
        return []

    coords = []
    tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-\d.]+', path_d)

    i = 0
    current_x, current_y = 0, 0

    while i < len(tokens):
        cmd = tokens[i]
        i += 1

        if cmd in 'Zz':
            continue
        elif cmd in 'Mm':
            if i + 1 < len(tokens):
                x, y = float(tokens[i]), float(tokens[i+1])
                if cmd == 'm':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y
                coords.append((current_x, current_y))
                i += 2
        elif cmd in 'Ll':
            if i + 1 < len(tokens):
                x, y = float(tokens[i]), float(tokens[i+1])
                if cmd == 'l':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y
                coords.append((current_x, current_y))
                i += 2
        elif cmd in 'Hh':
            if i < len(tokens):
                x = float(tokens[i])
                current_x = current_x + x if cmd == 'h' else x
                coords.append((current_x, current_y))
                i += 1
        elif cmd in 'Vv':
            if i < len(tokens):
                y = float(tokens[i])
                current_y = current_y + y if cmd == 'v' else y
                coords.append((current_x, current_y))
                i += 1
        elif cmd in 'Cc':
            if i + 5 < len(tokens):
                vals = [float(tokens[i+j]) for j in range(6)]
                if cmd == 'c':
                    coords.extend([
                        (current_x + vals[0], current_y + vals[1]),
                        (current_x + vals[2], current_y + vals[3]),
                        (current_x + vals[4], current_y + vals[5])
                    ])
                    current_x += vals[4]
                    current_y += vals[5]
                else:
                    coords.extend([
                        (vals[0], vals[1]),
                        (vals[2], vals[3]),
                        (vals[4], vals[5])
                    ])
                    current_x, current_y = vals[4], vals[5]
                i += 6

    return coords

def get_element_coords(elem):
    """Get all coordinates from an element (paths, circles, etc)"""
    coords = []
    tag = elem.tag.split('}')[-1]

    if tag == 'path':
        d = elem.get('d', '')
        coords.extend(parse_path_coords(d))
    elif tag == 'circle':
        cx = float(elem.get('cx', 0))
        cy = float(elem.get('cy', 0))
        r = float(elem.get('r', 0))
        coords.extend([(cx - r, cy - r), (cx + r, cy + r)])
    elif tag == 'rect':
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        w = float(elem.get('width', 0))
        h = float(elem.get('height', 0))
        coords.extend([(x, y), (x + w, y + h)])

    # Recurse into children
    for child in elem:
        coords.extend(get_element_coords(child))

    return coords

def remove_transforms_adjust_viewbox(svg_path):
    """Remove transforms and adjust viewBox to match path coordinates"""
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Get all coordinates from the document
    all_coords = get_element_coords(root)

    if not all_coords:
        return None

    # Calculate bounding box
    min_x = min(c[0] for c in all_coords)
    max_x = max(c[0] for c in all_coords)
    min_y = min(c[1] for c in all_coords)
    max_y = max(c[1] for c in all_coords)

    width = max_x - min_x
    height = max_y - min_y

    # Add small padding
    padding = 2
    min_x -= padding
    min_y -= padding
    width += 2 * padding
    height += 2 * padding

    # Set viewBox to show the area where coordinates actually are
    root.set('viewBox', f"{min_x:.3f} {min_y:.3f} {width:.3f} {height:.3f}")
    root.set('width', f"{width:.3f}")
    root.set('height', f"{height:.3f}")

    # Remove all transform attributes
    def remove_transforms(elem):
        if 'transform' in elem.attrib:
            del elem.attrib['transform']
        for child in elem:
            remove_transforms(child)

    remove_transforms(root)

    return tree

def create_clean_svg_string(tree):
    """Convert tree to clean SVG string"""
    root = tree.getroot()

    # Create minimal SVG
    svg_str = f'<svg xmlns="http://www.w3.org/2000/svg" '
    svg_str += f'viewBox="{root.get("viewBox", "")}" '
    svg_str += f'width="{root.get("width", "")}" '
    svg_str += f'height="{root.get("height", "")}">\n'

    # Process children
    def element_to_string(elem, indent=1):
        s = ''
        tag = elem.tag.split('}')[-1]

        # Skip metadata elements
        if tag in ['namedview', 'defs', 'metadata']:
            return s

        ind = '  ' * indent

        # Start tag
        s += f'{ind}<{tag}'

        # Add attributes (skip namespace attributes)
        for key, val in elem.attrib.items():
            if ':' not in key or key.startswith('xlink:'):
                s += f' {key}="{val}"'

        # Check if has children
        has_drawable_children = any(
            child.tag.split('}')[-1] in ['g', 'path', 'circle', 'rect', 'line']
            for child in elem
        )

        if has_drawable_children or len(list(elem)) > 0:
            s += '>\n'
            for child in elem:
                child_tag = child.tag.split('}')[-1]
                if child_tag not in ['namedview', 'defs', 'metadata']:
                    s += element_to_string(child, indent + 1)
            s += f'{ind}</{tag}>\n'
        else:
            s += ' />\n'

        return s

    for child in root:
        svg_str += element_to_string(child, 1)

    svg_str += '</svg>'

    return svg_str

def main():
    """Process all component SVGs"""
    assets_dir = Path('assets/components')

    output_md = "# Normalized SVG Components\n\n"
    output_md += "Transforms removed, viewBox adjusted to show path coordinates.\n"
    output_md += "Original path data preserved intact.\n\n"
    output_md += "---\n\n"

    svg_files = sorted(list(assets_dir.glob('*.svg')) + list((assets_dir/'e').glob('*.svg')))

    for svg_file in svg_files:
        print(f"Processing {svg_file.name}...")

        try:
            tree = remove_transforms_adjust_viewbox(svg_file)

            if tree:
                svg_str = create_clean_svg_string(tree)

                output_md += f"## {svg_file.stem}\n\n"
                output_md += f"**Path:** `{svg_file.relative_to(Path('assets'))}`\n\n"
                output_md += f"```xml\n{svg_str}\n```\n\n"
                output_md += "---\n\n"

                print(f"  ✓ {svg_file.stem}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

    output_file = Path('NORMALIZED_SVG_COMPONENTS.md')
    output_file.write_text(output_md)

    print(f"\n✓ Created {output_file}")
    print(f"  Processed {len(svg_files)} components")

if __name__ == '__main__':
    main()
