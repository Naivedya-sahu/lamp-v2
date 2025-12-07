#!/usr/bin/env python3
"""
Improved SVG to lamp converter with proper coordinate handling
"""

import xml.etree.ElementTree as ET
import sys
import re
from pathlib import Path


class SVGToLamp:
    def __init__(self):
        self.commands = []

    def parse_svg_file(self, svg_path, scale=1.0, offset_x=0, offset_y=0):
        """Parse SVG and convert to lamp commands."""
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # Extract viewBox or use width/height
        viewbox = root.get('viewBox')
        if viewbox:
            _, _, vb_width, vb_height = map(float, viewbox.split())
        else:
            vb_width = float(root.get('width', 100))
            vb_height = float(root.get('height', 100))

        # Process all drawing elements
        for elem in root.iter():
            tag = elem.tag.split('}')[-1]  # Remove namespace

            if tag == 'path':
                self.parse_path(elem, scale, offset_x, offset_y)
            elif tag == 'rect':
                self.parse_rect(elem, scale, offset_x, offset_y)
            elif tag == 'circle':
                self.parse_circle(elem, scale, offset_x, offset_y)
            elif tag == 'line':
                self.parse_line(elem, scale, offset_x, offset_y)
            elif tag == 'polyline' or tag == 'polygon':
                self.parse_polyline(elem, scale, offset_x, offset_y, tag == 'polygon')

        return '\n'.join(self.commands)

    def transform_point(self, x, y, scale, offset_x, offset_y):
        """Transform SVG coordinates to lamp coordinates."""
        return (
            int(x * scale + offset_x),
            int(y * scale + offset_y)
        )

    def parse_path(self, elem, scale, offset_x, offset_y):
        """Parse SVG path element."""
        d = elem.get('d', '')
        if not d:
            return

        # Simple path parser for M, L, H, V, Z commands
        commands = re.findall(r'([MLHVZmlhvz])([^MLHVZmlhvz]*)', d)

        current_x, current_y = 0, 0
        start_x, start_y = 0, 0
        pen_down = False

        for cmd, coords in commands:
            coords = coords.strip()
            if not coords and cmd.upper() not in ['Z']:
                continue

            nums = [float(n) for n in re.findall(r'-?\d+\.?\d*', coords)]

            if cmd == 'M':  # Move to (absolute)
                if pen_down:
                    self.commands.append("pen up")
                    pen_down = False
                current_x, current_y = nums[0], nums[1]
                start_x, start_y = current_x, current_y

            elif cmd == 'm':  # Move to (relative)
                if pen_down:
                    self.commands.append("pen up")
                    pen_down = False
                current_x += nums[0]
                current_y += nums[1]
                start_x, start_y = current_x, current_y

            elif cmd in ['L', 'l']:  # Line to
                for i in range(0, len(nums), 2):
                    if cmd == 'L':
                        next_x, next_y = nums[i], nums[i+1]
                    else:
                        next_x = current_x + nums[i]
                        next_y = current_y + nums[i+1]

                    if not pen_down:
                        x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y)
                        self.commands.append(f"pen down {x1} {y1}")
                        pen_down = True

                    x2, y2 = self.transform_point(next_x, next_y, scale, offset_x, offset_y)
                    self.commands.append(f"pen move {x2} {y2}")
                    current_x, current_y = next_x, next_y

            elif cmd in ['H', 'h']:  # Horizontal line
                for num in nums:
                    next_x = num if cmd == 'H' else current_x + num
                    next_y = current_y

                    if not pen_down:
                        x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y)
                        self.commands.append(f"pen down {x1} {y1}")
                        pen_down = True

                    x2, y2 = self.transform_point(next_x, next_y, scale, offset_x, offset_y)
                    self.commands.append(f"pen move {x2} {y2}")
                    current_x = next_x

            elif cmd in ['V', 'v']:  # Vertical line
                for num in nums:
                    next_x = current_x
                    next_y = num if cmd == 'V' else current_y + num

                    if not pen_down:
                        x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y)
                        self.commands.append(f"pen down {x1} {y1}")
                        pen_down = True

                    x2, y2 = self.transform_point(next_x, next_y, scale, offset_x, offset_y)
                    self.commands.append(f"pen move {x2} {y2}")
                    current_y = next_y

            elif cmd in ['Z', 'z']:  # Close path
                if pen_down:
                    x2, y2 = self.transform_point(start_x, start_y, scale, offset_x, offset_y)
                    self.commands.append(f"pen move {x2} {y2}")
                    self.commands.append("pen up")
                    pen_down = False

        if pen_down:
            self.commands.append("pen up")

    def parse_rect(self, elem, scale, offset_x, offset_y):
        """Parse SVG rectangle."""
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        w = float(elem.get('width', 0))
        h = float(elem.get('height', 0))

        x1, y1 = self.transform_point(x, y, scale, offset_x, offset_y)
        x2, y2 = self.transform_point(x + w, y + h, scale, offset_x, offset_y)

        self.commands.append(f"pen rectangle {x1} {y1} {x2} {y2}")

    def parse_circle(self, elem, scale, offset_x, offset_y):
        """Parse SVG circle."""
        cx = float(elem.get('cx', 0))
        cy = float(elem.get('cy', 0))
        r = float(elem.get('r', 0))

        cx_t, cy_t = self.transform_point(cx, cy, scale, offset_x, offset_y)
        r_t = int(r * scale)

        self.commands.append(f"pen circle {cx_t} {cy_t} {r_t}")

    def parse_line(self, elem, scale, offset_x, offset_y):
        """Parse SVG line."""
        x1 = float(elem.get('x1', 0))
        y1 = float(elem.get('y1', 0))
        x2 = float(elem.get('x2', 0))
        y2 = float(elem.get('y2', 0))

        x1_t, y1_t = self.transform_point(x1, y1, scale, offset_x, offset_y)
        x2_t, y2_t = self.transform_point(x2, y2, scale, offset_x, offset_y)

        self.commands.append(f"pen line {x1_t} {y1_t} {x2_t} {y2_t}")

    def parse_polyline(self, elem, scale, offset_x, offset_y, close=False):
        """Parse SVG polyline or polygon."""
        points = elem.get('points', '')
        if not points:
            return

        coords = [float(n) for n in re.findall(r'-?\d+\.?\d*', points)]
        if len(coords) < 4:
            return

        # Start at first point
        x1, y1 = self.transform_point(coords[0], coords[1], scale, offset_x, offset_y)
        self.commands.append(f"pen down {x1} {y1}")

        # Draw to each subsequent point
        for i in range(2, len(coords), 2):
            x2, y2 = self.transform_point(coords[i], coords[i+1], scale, offset_x, offset_y)
            self.commands.append(f"pen move {x2} {y2}")

        # Close polygon if needed
        if close:
            x2, y2 = self.transform_point(coords[0], coords[1], scale, offset_x, offset_y)
            self.commands.append(f"pen move {x2} {y2}")

        self.commands.append("pen up")


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 svg_to_lamp.py <svg_file> <x> <y> [scale]")
        print("Example: python3 svg_to_lamp.py symbol.svg 500 800 2.0")
        sys.exit(1)

    svg_file = sys.argv[1]
    offset_x = int(sys.argv[2])
    offset_y = int(sys.argv[3])
    scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0

    if not Path(svg_file).exists():
        print(f"Error: File '{svg_file}' not found", file=sys.stderr)
        sys.exit(1)

    converter = SVGToLamp()
    commands = converter.parse_svg_file(svg_file, scale, offset_x, offset_y)
    print(commands)


if __name__ == '__main__':
    main()
