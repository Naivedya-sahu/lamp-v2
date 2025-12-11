#!/usr/bin/env python3
"""
Improved text to lamp stroke renderer with proper coordinate handling
"""

import sys


class StrokeFontRenderer:
    def __init__(self):
        # 7-segment style stroke-based font
        # Each character defined as list of line segments: [(x1,y1,x2,y2), ...]
        # Coordinates in 10x14 grid
        self.font = {
            'A': [(0,14,0,7), (0,7,5,0), (5,0,10,7), (10,7,10,14), (0,7,10,7)],
            'B': [(0,0,0,14), (0,0,7,0), (7,0,10,3), (10,3,7,7), (0,7,7,7), (7,7,10,11), (10,11,7,14), (7,14,0,14)],
            'C': [(10,0,0,0), (0,0,0,14), (0,14,10,14)],
            'D': [(0,0,0,14), (0,0,7,0), (7,0,10,3), (10,3,10,11), (10,11,7,14), (7,14,0,14)],
            'E': [(10,0,0,0), (0,0,0,14), (0,14,10,14), (0,7,7,7)],
            'F': [(0,0,0,14), (0,0,10,0), (0,7,7,7)],
            'G': [(10,0,0,0), (0,0,0,14), (0,14,10,14), (10,14,10,7), (10,7,5,7)],
            'H': [(0,0,0,14), (10,0,10,14), (0,7,10,7)],
            'I': [(3,0,7,0), (5,0,5,14), (3,14,7,14)],
            'J': [(0,14,5,14), (5,14,5,0), (5,0,10,0)],
            'K': [(0,0,0,14), (10,0,0,7), (0,7,10,14)],
            'L': [(0,0,0,14), (0,14,10,14)],
            'M': [(0,14,0,0), (0,0,5,7), (5,7,10,0), (10,0,10,14)],
            'N': [(0,14,0,0), (0,0,10,14), (10,14,10,0)],
            'O': [(0,0,10,0), (10,0,10,14), (10,14,0,14), (0,14,0,0)],
            'P': [(0,14,0,0), (0,0,10,0), (10,0,10,7), (10,7,0,7)],
            'Q': [(0,0,10,0), (10,0,10,14), (10,14,0,14), (0,14,0,0), (7,10,10,14)],
            'R': [(0,14,0,0), (0,0,10,0), (10,0,10,7), (10,7,0,7), (5,7,10,14)],
            'S': [(10,0,0,0), (0,0,0,7), (0,7,10,7), (10,7,10,14), (10,14,0,14)],
            'T': [(0,0,10,0), (5,0,5,14)],
            'U': [(0,0,0,14), (0,14,10,14), (10,14,10,0)],
            'V': [(0,0,5,14), (5,14,10,0)],
            'W': [(0,0,0,14), (0,14,5,7), (5,7,10,14), (10,14,10,0)],
            'X': [(0,0,10,14), (0,14,10,0)],
            'Y': [(0,0,5,7), (10,0,5,7), (5,7,5,14)],
            'Z': [(0,0,10,0), (10,0,0,14), (0,14,10,14)],

            # Numbers
            '0': [(0,0,10,0), (10,0,10,14), (10,14,0,14), (0,14,0,0)],
            '1': [(5,0,5,14), (5,0,3,2)],
            '2': [(0,0,10,0), (10,0,10,7), (10,7,0,7), (0,7,0,14), (0,14,10,14)],
            '3': [(0,0,10,0), (10,0,10,14), (10,14,0,14), (10,7,5,7)],
            '4': [(0,0,0,7), (0,7,10,7), (10,0,10,14)],
            '5': [(10,0,0,0), (0,0,0,7), (0,7,10,7), (10,7,10,14), (10,14,0,14)],
            '6': [(10,0,0,0), (0,0,0,14), (0,14,10,14), (10,14,10,7), (10,7,0,7)],
            '7': [(0,0,10,0), (10,0,10,14)],
            '8': [(0,0,10,0), (10,0,10,14), (10,14,0,14), (0,14,0,0), (0,7,10,7)],
            '9': [(10,7,0,7), (0,7,0,0), (0,0,10,0), (10,0,10,14), (10,14,0,14)],

            # Special symbols
            '+': [(5,3,5,11), (1,7,9,7)],
            '-': [(1,7,9,7)],
            'Ω': [(0,14,0,7), (0,7,3,0), (3,0,7,0), (7,0,10,7), (10,7,10,14), (0,14,3,14), (7,14,10,14)],
            'μ': [(0,0,0,14), (0,14,5,14), (5,14,5,7), (5,7,10,7), (10,0,10,14)],
            'K': [(0,0,0,14), (10,0,0,7), (0,7,10,14)],
            ' ': [],
        }

        self.char_width = 10
        self.char_height = 14
        self.char_spacing = 3

    def render_text(self, text, x, y, scale=1.0):
        """Render text as lamp pen commands."""
        commands = []
        current_x = x

        for char in text.upper():
            if char in self.font:
                strokes = self.font[char]
                for stroke in strokes:
                    x1, y1, x2, y2 = stroke

                    # Scale and position
                    lamp_x1 = int(current_x + x1 * scale)
                    lamp_y1 = int(y + y1 * scale)
                    lamp_x2 = int(current_x + x2 * scale)
                    lamp_y2 = int(y + y2 * scale)

                    commands.append(f"pen down {lamp_x1} {lamp_y1}")
                    commands.append(f"pen move {lamp_x2} {lamp_y2}")
                    commands.append("pen up")

                current_x += int((self.char_width + self.char_spacing) * scale)
            else:
                # Unknown character - skip with spacing
                current_x += int((self.char_width + self.char_spacing) * scale)

        return '\n'.join(commands)

    def get_text_width(self, text, scale=1.0):
        """Calculate rendered text width."""
        return int(len(text) * (self.char_width + self.char_spacing) * scale)


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 text_to_lamp.py <text> <x> <y> [scale]")
        print("Example: python3 text_to_lamp.py '10K' 720 1680 0.5")
        print("Supports: A-Z, 0-9, +, -, Ω, μ")
        sys.exit(1)

    text = sys.argv[1]
    x = int(sys.argv[2])
    y = int(sys.argv[3])
    scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0

    renderer = StrokeFontRenderer()
    commands = renderer.render_text(text, x, y, scale)
    print(commands)


if __name__ == '__main__':
    main()
