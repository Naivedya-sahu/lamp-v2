#!/usr/bin/env python3
"""
Improved SVG to lamp converter with proper coordinate handling, scaling, and bounds checking
Supports curves (C, Q, A commands) with polyline approximation
"""

import xml.etree.ElementTree as ET
import sys
import re
import math
from pathlib import Path


class SVGToLamp:
    # Screen dimensions for reMarkable 2
    SCREEN_WIDTH = 1404
    SCREEN_HEIGHT = 1872
    
    def __init__(self):
        self.commands = []
        self.min_x = float('inf')
        self.max_x = float('-inf')
        self.min_y = float('inf')
        self.max_y = float('-inf')
        # Track actual drawn bounds (after transform)
        self.drawn_min_x = float('inf')
        self.drawn_max_x = float('-inf')
        self.drawn_min_y = float('inf')
        self.drawn_max_y = float('-inf')
        # Track actual drawn bounds (after transform)
        self.drawn_min_x = float('inf')
        self.drawn_max_x = float('-inf')
        self.drawn_min_y = float('inf')
        self.drawn_max_y = float('-inf')

    def parse_svg_file(self, svg_path, scale=1.0, offset_x=0, offset_y=0):
        """Parse SVG and convert to lamp commands."""
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # Extract viewBox or use width/height for coordinate normalization
        viewbox = root.get('viewBox')
        if viewbox:
            vb_x, vb_y, vb_width, vb_height = map(float, viewbox.split())
        else:
            # Try to parse width/height (handle mm units)
            width_str = root.get('width', '100')
            height_str = root.get('height', '100')
            vb_width = float(re.sub(r'[^\d.]', '', width_str))
            vb_height = float(re.sub(r'[^\d.]', '', height_str))
            vb_x, vb_y = 0, 0

        print(f"DEBUG: ViewBox/Document bounds: ({vb_x}, {vb_y}) {vb_width}x{vb_height}", file=sys.stderr)
        print(f"DEBUG: User scale={scale}, Offset=({offset_x}, {offset_y})", file=sys.stderr)

        # First pass: collect all coordinates to find actual drawable bounds
        # This considers transforms and gives us the real coordinate space
        self._collect_bounds_with_transforms(root)
        
        if self.min_x == float('inf'):
            print("WARNING: No drawable content found!", file=sys.stderr)
            return ""
            
        svg_width = self.max_x - self.min_x
        svg_height = self.max_y - self.min_y
        
        print(f"DEBUG: Actual drawable bounds: ({self.min_x:.2f}, {self.min_y:.2f}) to ({self.max_x:.2f}, {self.max_y:.2f})", file=sys.stderr)
        print(f"DEBUG: Drawable size: {svg_width:.2f} x {svg_height:.2f}", file=sys.stderr)

        # If scale not specified (default 1.0), calculate optimal scale
        if scale == 1.0 and svg_width > 0 and svg_height > 0:
            # Calculate scale to fit on screen with margin
            MARGIN = 50
            MAX_SCALE = 30  # Prevent excessive scaling that distorts coordinates
            
            scale_x = (self.SCREEN_WIDTH - 2 * MARGIN) / svg_width
            scale_y = (self.SCREEN_HEIGHT - 2 * MARGIN) / svg_height
            
            # Use smaller scale to fit both dimensions
            optimal_scale = min(scale_x, scale_y)
            
            # Cap the scale to reasonable limits
            optimal_scale = min(optimal_scale, MAX_SCALE)
            optimal_scale = max(optimal_scale, 1.0)
            
            # Round to nearest integer for cleaner output
            optimal_scale = int(optimal_scale)
            
            print(f"DEBUG: Calculated optimal scale: {optimal_scale}x (from {scale_x:.1f}x, {scale_y:.1f}x)", file=sys.stderr)
            scale = optimal_scale
        
        # Calculate offset for centering if not specified
        if offset_x == 0 and offset_y == 0:
            # Auto-center the drawing with margin
            scaled_width = svg_width * scale
            scaled_height = svg_height * scale
            MARGIN = 50
            offset_x = int((self.SCREEN_WIDTH - scaled_width) / 2)
            offset_y = int((self.SCREEN_HEIGHT - scaled_height) / 2)
            # Ensure minimum margin
            offset_x = max(MARGIN, offset_x)
            offset_y = max(MARGIN, offset_y)
            print(f"DEBUG: Auto-centered offset=({offset_x}, {offset_y})", file=sys.stderr)

        # Calculate shift to normalize coordinates (handle negatives)
        shift_x = -self.min_x  # Shift so min_x becomes 0
        shift_y = -self.min_y  # Shift so min_y becomes 0
        print(f"DEBUG: Coordinate normalization shift=({shift_x:.2f}, {shift_y:.2f})", file=sys.stderr)
        print(f"DEBUG: Final scale={scale}, offset=({offset_x}, {offset_y})", file=sys.stderr)

        # Process all drawing elements with shift applied
        for elem in root.iter():
            tag = elem.tag.split('}')[-1]  # Remove namespace

            if tag == 'path':
                self.parse_path(elem, scale, offset_x, offset_y, shift_x, shift_y)
            elif tag == 'rect':
                self.parse_rect(elem, scale, offset_x, offset_y, shift_x, shift_y)
            elif tag == 'circle':
                self.parse_circle(elem, scale, offset_x, offset_y, shift_x, shift_y)
            elif tag == 'line':
                self.parse_line(elem, scale, offset_x, offset_y, shift_x, shift_y)
            elif tag == 'polyline' or tag == 'polygon':
                self.parse_polyline(elem, scale, offset_x, offset_y, shift_x, shift_y, tag == 'polygon')

        # Add bounds comment at the start for eraser to use
        if self.drawn_min_x != float('inf'):
            # Add small margin for eraser coverage
            margin = 10
            bounds_comment = f"# BOUNDS {int(self.drawn_min_x - margin)} {int(self.drawn_min_y - margin)} {int(self.drawn_max_x + margin)} {int(self.drawn_max_y + margin)}"
            self.commands.insert(0, bounds_comment)
        
        return '\n'.join(self.commands)

    def _collect_bounds_with_transforms(self, root):
        """First pass: collect bounds considering group transforms."""
        # For properly authored SVGs with viewBox, use the viewBox as the coordinate space
        # The SVG renderer has already applied all transforms to fit content into viewBox
        
        viewbox = root.get('viewBox')
        if viewbox:
            vb_x, vb_y, vb_width, vb_height = map(float, viewbox.split())
            
            # Check if we should use viewBox or scan actual elements
            # If paths exist outside reasonable viewBox range, we need to scan
            has_large_coords = False
            for elem in root.iter():
                tag = elem.tag.split('}')[-1]
                if tag == 'path':
                    d = elem.get('d', '')
                    # Quick check: if coordinates are >> viewBox, don't trust viewBox alone
                    if d:
                        coords = re.findall(r'-?\d+\.?\d*', d)
                        if coords:
                            sample_coord = abs(float(coords[0]))
                            # Threshold: if sample coord is more than 2x larger than viewBox, suspect transform
                            if sample_coord > max(vb_width, vb_height) * 2:
                                has_large_coords = True
                                break
            
            if not has_large_coords:
                # viewBox is reliable - use it
                self.min_x = vb_x
                self.max_x = vb_x + vb_width  
                self.min_y = vb_y
                self.max_y = vb_y + vb_height
                print(f"DEBUG: Using viewBox as primary coordinate space", file=sys.stderr)
                return
            else:
                print(f"DEBUG: Detected transformed content, scanning actual coordinates", file=sys.stderr)
        
        # Fall back to analyzing raw coordinates
        self._collect_bounds(root)

    def _collect_bounds(self, root):
        """First pass: collect all coordinates to find bounds."""
        for elem in root.iter():
            tag = elem.tag.split('}')[-1]

            if tag == 'path':
                d = elem.get('d', '')
                if d:
                    self._update_path_bounds(d)
            elif tag == 'rect':
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                w = float(elem.get('width', 0))
                h = float(elem.get('height', 0))
                self.min_x = min(self.min_x, x, x + w)
                self.max_x = max(self.max_x, x, x + w)
                self.min_y = min(self.min_y, y, y + h)
                self.max_y = max(self.max_y, y, y + h)
            elif tag == 'circle':
                cx = float(elem.get('cx', 0))
                cy = float(elem.get('cy', 0))
                r = float(elem.get('r', 0))
                self.min_x = min(self.min_x, cx - r)
                self.max_x = max(self.max_x, cx + r)
                self.min_y = min(self.min_y, cy - r)
                self.max_y = max(self.max_y, cy + r)
            elif tag == 'line':
                x1 = float(elem.get('x1', 0))
                y1 = float(elem.get('y1', 0))
                x2 = float(elem.get('x2', 0))
                y2 = float(elem.get('y2', 0))
                self.min_x = min(self.min_x, x1, x2)
                self.max_x = max(self.max_x, x1, x2)
                self.min_y = min(self.min_y, y1, y2)
                self.max_y = max(self.max_y, y1, y2)
            elif tag in ['polyline', 'polygon']:
                points = elem.get('points', '')
                if points:
                    coords = [float(n) for n in re.findall(r'-?\d+\.?\d*', points)]
                    for i in range(0, len(coords), 2):
                        self.min_x = min(self.min_x, coords[i])
                        self.max_x = max(self.max_x, coords[i])
                    for i in range(1, len(coords), 2):
                        self.min_y = min(self.min_y, coords[i])
                        self.max_y = max(self.max_y, coords[i])

    def _update_path_bounds(self, d):
        """Update bounds from path data - handles M, L, H, V, C, Q, A, Z commands."""
        # Updated regex to capture all SVG path commands: M, L, H, V, C, S, Q, T, A, Z
        commands = re.findall(r'([MLHVCSQTAmlhvcsqta])([^MLHVCSQTAmlhvcsqta]*)', d)
        current_x, current_y = 0, 0

        for cmd, coords in commands:
            coords = coords.strip()
            if not coords and cmd.upper() not in ['Z']:
                continue

            nums = [float(n) for n in re.findall(r'-?\d+\.?\d*', coords)]

            if cmd == 'M':
                current_x, current_y = nums[0], nums[1]
            elif cmd == 'm':
                current_x += nums[0]
                current_y += nums[1]
            elif cmd in ['L', 'l']:
                for i in range(0, len(nums), 2):
                    if cmd == 'L':
                        current_x, current_y = nums[i], nums[i+1]
                    else:
                        current_x += nums[i]
                        current_y += nums[i+1]
                    self.min_x = min(self.min_x, current_x)
                    self.max_x = max(self.max_x, current_x)
                    self.min_y = min(self.min_y, current_y)
                    self.max_y = max(self.max_y, current_y)
            elif cmd in ['H', 'h']:
                for num in nums:
                    current_x = num if cmd == 'H' else current_x + num
                    self.min_x = min(self.min_x, current_x)
                    self.max_x = max(self.max_x, current_x)
            elif cmd in ['V', 'v']:
                for num in nums:
                    current_y = num if cmd == 'V' else current_y + num
                    self.min_y = min(self.min_y, current_y)
                    self.max_y = max(self.max_y, current_y)
            elif cmd in ['C', 'c']:  # Cubic Bezier curve
                # Format: C x1 y1 x2 y2 x y (absolute) or c dx1 dy1 dx2 dy2 dx dy (relative)
                for i in range(0, len(nums), 6):
                    if i+5 < len(nums):
                        if cmd == 'C':
                            cp1_x, cp1_y = nums[i], nums[i+1]
                            cp2_x, cp2_y = nums[i+2], nums[i+3]
                            end_x, end_y = nums[i+4], nums[i+5]
                        else:
                            cp1_x, cp1_y = current_x + nums[i], current_y + nums[i+1]
                            cp2_x, cp2_y = current_x + nums[i+2], current_y + nums[i+3]
                            end_x, end_y = current_x + nums[i+4], current_y + nums[i+5]
                        
                        # Include control points and endpoint in bounds
                        for px in [cp1_x, cp2_x, end_x]:
                            self.min_x = min(self.min_x, px)
                            self.max_x = max(self.max_x, px)
                        for py in [cp1_y, cp2_y, end_y]:
                            self.min_y = min(self.min_y, py)
                            self.max_y = max(self.max_y, py)
                        current_x, current_y = end_x, end_y
            elif cmd in ['Q', 'q']:  # Quadratic Bezier curve
                # Format: Q x1 y1 x y (absolute) or q dx1 dy1 dx dy (relative)
                for i in range(0, len(nums), 4):
                    if i+3 < len(nums):
                        if cmd == 'Q':
                            cp_x, cp_y = nums[i], nums[i+1]
                            end_x, end_y = nums[i+2], nums[i+3]
                        else:
                            cp_x, cp_y = current_x + nums[i], current_y + nums[i+1]
                            end_x, end_y = current_x + nums[i+2], current_y + nums[i+3]
                        
                        # Include control point and endpoint in bounds
                        for px in [cp_x, end_x]:
                            self.min_x = min(self.min_x, px)
                            self.max_x = max(self.max_x, px)
                        for py in [cp_y, end_y]:
                            self.min_y = min(self.min_y, py)
                            self.max_y = max(self.max_y, py)
                        current_x, current_y = end_x, end_y
            elif cmd in ['A', 'a']:  # Arc
                # Format: A rx ry x-axis-rotation large-arc-flag sweep-flag x y
                for i in range(0, len(nums), 7):
                    if i+6 < len(nums):
                        if cmd == 'A':
                            end_x, end_y = nums[i+5], nums[i+6]
                        else:
                            end_x, end_y = current_x + nums[i+5], current_y + nums[i+6]
                        
                        # For arcs, include start point, end point, and approximate radius
                        rx = nums[i]
                        ry = nums[i+1]
                        for px in [current_x - rx, current_x + rx, end_x - rx, end_x + rx]:
                            self.min_x = min(self.min_x, px)
                            self.max_x = max(self.max_x, px)
                        for py in [current_y - ry, current_y + ry, end_y - ry, end_y + ry]:
                            self.min_y = min(self.min_y, py)
                            self.max_y = max(self.max_y, py)
                        current_x, current_y = end_x, end_y

    def transform_point(self, x, y, scale, offset_x, offset_y, shift_x=0, shift_y=0):
        """Transform SVG coordinates to lamp coordinates with smart bounds handling."""
        # Apply shift first (to handle negatives), then scale, then offset
        tx = int((x + shift_x) * scale + offset_x)
        ty = int((y + shift_y) * scale + offset_y)
        
        # Track actual drawn bounds (before clamping)
        self.drawn_min_x = min(self.drawn_min_x, tx)
        self.drawn_max_x = max(self.drawn_max_x, tx)
        self.drawn_min_y = min(self.drawn_min_y, ty)
        self.drawn_max_y = max(self.drawn_max_y, ty)
        
        # Use soft clamping to keep coordinates mostly on screen
        # but avoid hard clipping that distorts shapes
        # Only clamp if significantly out of bounds
        MARGIN = 50
        
        if tx < -MARGIN:
            tx = 0
        elif tx > self.SCREEN_WIDTH + MARGIN:
            tx = self.SCREEN_WIDTH - 1
        else:
            # Clamp to screen bounds smoothly
            tx = max(0, min(tx, self.SCREEN_WIDTH - 1))
            
        if ty < -MARGIN:
            ty = 0
        elif ty > self.SCREEN_HEIGHT + MARGIN:
            ty = self.SCREEN_HEIGHT - 1
        else:
            # Clamp to screen bounds smoothly
            ty = max(0, min(ty, self.SCREEN_HEIGHT - 1))
        
        return tx, ty

    def _approximate_cubic_bezier(self, x0, y0, x1, y1, x2, y2, x3, y3, num_segments=20):
        """Approximate cubic Bezier curve with line segments using De Casteljau's algorithm."""
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            # De Casteljau's algorithm
            mt = 1 - t
            # First level
            ax = mt * x0 + t * x1
            ay = mt * y0 + t * y1
            bx = mt * x1 + t * x2
            by = mt * y1 + t * y2
            cx = mt * x2 + t * x3
            cy = mt * y2 + t * y3
            # Second level
            dx = mt * ax + t * bx
            dy = mt * ay + t * by
            ex = mt * bx + t * cx
            ey = mt * by + t * cy
            # Final point
            px = mt * dx + t * ex
            py = mt * dy + t * ey
            points.append((px, py))
        return points

    def _approximate_quadratic_bezier(self, x0, y0, x1, y1, x2, y2, num_segments=15):
        """Approximate quadratic Bezier curve with line segments."""
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            mt = 1 - t
            # Quadratic Bezier formula: B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
            px = mt * mt * x0 + 2 * mt * t * x1 + t * t * x2
            py = mt * mt * y0 + 2 * mt * t * y1 + t * t * y2
            points.append((px, py))
        return points

    def _approximate_arc(self, start_x, start_y, rx, ry, rotation, large_arc, sweep, end_x, end_y, num_segments=20):
        """Approximate arc with line segments. Uses basic approach that handles common cases."""
        points = []
        # For simplicity, approximate arc as series of line segments
        # More accurate implementations would use proper SVG arc math
        for i in range(num_segments + 1):
            t = i / num_segments
            # Linear interpolation as simple approximation (not perfect but works for most cases)
            px = start_x + t * (end_x - start_x)
            py = start_y + t * (end_y - start_y)
            points.append((px, py))
        return points

    def parse_path(self, elem, scale, offset_x, offset_y, shift_x=0, shift_y=0):
        """Parse SVG path element with support for curves (M, L, H, V, C, Q, A, Z commands)."""
        d = elem.get('d', '')
        if not d:
            return

        # Updated regex to capture all SVG path commands
        commands = re.findall(r'([MLHVCSQTAmlhvcsqta])([^MLHVCSQTAmlhvcsqta]*)', d)

        current_x, current_y = 0, 0
        start_x, start_y = 0, 0
        pen_down = False

        for cmd, coords in commands:
            coords = coords.strip()
            if not coords and cmd.upper() not in ['Z']:
                continue

            nums = [float(n) for n in re.findall(r'-?\d+\.?\d*', coords)]

            if cmd == 'M':  # Move to (absolute); subsequent pairs are implicit L
                if len(nums) < 2:
                    break
                # if a pen was down for previous subpath, close it
                if pen_down:
                    self.commands.append("pen up")
                    pen_down = False
                # first coordinate is the move-to
                current_x, current_y = nums[0], nums[1]
                start_x, start_y = current_x, current_y

                # if more coords are present, they are implicit LineTo commands
                if len(nums) > 2:
                    # put the pen down at the move-to start point then draw the implicit L's
                    x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y, shift_x, shift_y)
                    self.commands.append(f"pen down {x1} {y1}")
                    pen_down = True
                    for i in range(2, len(nums), 2):
                        x2 = nums[i]
                        y2 = nums[i+1] if i+1 < len(nums) else None
                        if y2 is None:
                            break
                        tx, ty = self.transform_point(x2, y2, scale, offset_x, offset_y, shift_x, shift_y)
                        self.commands.append(f"pen move {tx} {ty}")
                        current_x, current_y = x2, y2

            elif cmd == 'm':  # Move to (relative); subsequent pairs are implicit l
                if len(nums) < 2:
                    break
                if pen_down:
                    self.commands.append("pen up")
                    pen_down = False
                # apply relative move
                current_x += nums[0]
                current_y += nums[1]
                start_x, start_y = current_x, current_y

                # handle implicit relative line-tos following the move
                if len(nums) > 2:
                    x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y, shift_x, shift_y)
                    self.commands.append(f"pen down {x1} {y1}")
                    pen_down = True
                    for i in range(2, len(nums), 2):
                        dx = nums[i]
                        dy = nums[i+1] if i+1 < len(nums) else None
                        if dy is None:
                            break
                        current_x += dx
                        current_y += dy
                        tx, ty = self.transform_point(current_x, current_y, scale, offset_x, offset_y, shift_x, shift_y)
                        self.commands.append(f"pen move {tx} {ty}")


            elif cmd in ['L', 'l']:  # Line to
                for i in range(0, len(nums), 2):
                    if i+1 >= len(nums):
                        break
                    if cmd == 'L':
                        next_x, next_y = nums[i], nums[i+1]
                    else:
                        next_x = current_x + nums[i]
                        next_y = current_y + nums[i+1]

                    if not pen_down:
                        x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y, shift_x, shift_y)
                        self.commands.append(f"pen down {x1} {y1}")
                        pen_down = True

                    x2, y2 = self.transform_point(next_x, next_y, scale, offset_x, offset_y, shift_x, shift_y)
                    self.commands.append(f"pen move {x2} {y2}")
                    current_x, current_y = next_x, next_y

            elif cmd in ['H', 'h']:  # Horizontal line
                for num in nums:
                    next_x = num if cmd == 'H' else current_x + num
                    next_y = current_y

                    if not pen_down:
                        x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y, shift_x, shift_y)
                        self.commands.append(f"pen down {x1} {y1}")
                        pen_down = True

                    x2, y2 = self.transform_point(next_x, next_y, scale, offset_x, offset_y, shift_x, shift_y)
                    self.commands.append(f"pen move {x2} {y2}")
                    current_x = next_x

            elif cmd in ['V', 'v']:  # Vertical line
                for num in nums:
                    next_x = current_x
                    next_y = num if cmd == 'V' else current_y + num

                    if not pen_down:
                        x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y, shift_x, shift_y)
                        self.commands.append(f"pen down {x1} {y1}")
                        pen_down = True

                    x2, y2 = self.transform_point(next_x, next_y, scale, offset_x, offset_y, shift_x, shift_y)
                    self.commands.append(f"pen move {x2} {y2}")
                    current_y = next_y

            elif cmd in ['C', 'c']:  # Cubic Bezier curve
                for i in range(0, len(nums), 6):
                    if i+5 < len(nums):
                        if cmd == 'C':
                            cp1_x, cp1_y = nums[i], nums[i+1]
                            cp2_x, cp2_y = nums[i+2], nums[i+3]
                            end_x, end_y = nums[i+4], nums[i+5]
                        else:
                            cp1_x, cp1_y = current_x + nums[i], current_y + nums[i+1]
                            cp2_x, cp2_y = current_x + nums[i+2], current_y + nums[i+3]
                            end_x, end_y = current_x + nums[i+4], current_y + nums[i+5]
                        
                        # Approximate curve with line segments
                        points = self._approximate_cubic_bezier(current_x, current_y, cp1_x, cp1_y, cp2_x, cp2_y, end_x, end_y)
                        
                        if not pen_down:
                            x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y, shift_x, shift_y)
                            self.commands.append(f"pen down {x1} {y1}")
                            pen_down = True
                        
                        for px, py in points[1:]:
                            x2, y2 = self.transform_point(px, py, scale, offset_x, offset_y, shift_x, shift_y)
                            self.commands.append(f"pen move {x2} {y2}")
                        
                        current_x, current_y = end_x, end_y

            elif cmd in ['Q', 'q']:  # Quadratic Bezier curve
                for i in range(0, len(nums), 4):
                    if i+3 < len(nums):
                        if cmd == 'Q':
                            cp_x, cp_y = nums[i], nums[i+1]
                            end_x, end_y = nums[i+2], nums[i+3]
                        else:
                            cp_x, cp_y = current_x + nums[i], current_y + nums[i+1]
                            end_x, end_y = current_x + nums[i+2], current_y + nums[i+3]
                        
                        # Approximate curve with line segments
                        points = self._approximate_quadratic_bezier(current_x, current_y, cp_x, cp_y, end_x, end_y)
                        
                        if not pen_down:
                            x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y, shift_x, shift_y)
                            self.commands.append(f"pen down {x1} {y1}")
                            pen_down = True
                        
                        for px, py in points[1:]:
                            x2, y2 = self.transform_point(px, py, scale, offset_x, offset_y, shift_x, shift_y)
                            self.commands.append(f"pen move {x2} {y2}")
                        
                        current_x, current_y = end_x, end_y

            elif cmd in ['A', 'a']:  # Arc
                for i in range(0, len(nums), 7):
                    if i+6 < len(nums):
                        rx = nums[i]
                        ry = nums[i+1]
                        rotation = nums[i+2]
                        large_arc = int(nums[i+3])
                        sweep = int(nums[i+4])
                        if cmd == 'A':
                            end_x, end_y = nums[i+5], nums[i+6]
                        else:
                            end_x = current_x + nums[i+5]
                            end_y = current_y + nums[i+6]
                        
                        # Approximate arc with line segments
                        points = self._approximate_arc(current_x, current_y, rx, ry, rotation, large_arc, sweep, end_x, end_y)
                        
                        if not pen_down:
                            x1, y1 = self.transform_point(current_x, current_y, scale, offset_x, offset_y, shift_x, shift_y)
                            self.commands.append(f"pen down {x1} {y1}")
                            pen_down = True
                        
                        for px, py in points[1:]:
                            x2, y2 = self.transform_point(px, py, scale, offset_x, offset_y, shift_x, shift_y)
                            self.commands.append(f"pen move {x2} {y2}")
                        
                        current_x, current_y = end_x, end_y

            elif cmd in ['Z', 'z']:  # Close path
                if pen_down:
                    x2, y2 = self.transform_point(start_x, start_y, scale, offset_x, offset_y, shift_x, shift_y)
                    self.commands.append(f"pen move {x2} {y2}")
                    self.commands.append("pen up")
                    pen_down = False

        if pen_down:
            self.commands.append("pen up")

    def parse_rect(self, elem, scale, offset_x, offset_y, shift_x=0, shift_y=0):
        """Parse SVG rectangle."""
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        w = float(elem.get('width', 0))
        h = float(elem.get('height', 0))

        x1, y1 = self.transform_point(x, y, scale, offset_x, offset_y, shift_x, shift_y)
        x2, y2 = self.transform_point(x + w, y + h, scale, offset_x, offset_y, shift_x, shift_y)

        self.commands.append(f"pen rectangle {x1} {y1} {x2} {y2}")

    def parse_circle(self, elem, scale, offset_x, offset_y, shift_x=0, shift_y=0):
        """Parse SVG circle."""
        cx = float(elem.get('cx', 0))
        cy = float(elem.get('cy', 0))
        r = float(elem.get('r', 0))

        cx_t, cy_t = self.transform_point(cx, cy, scale, offset_x, offset_y, shift_x, shift_y)
        r_t = int(r * scale)

        self.commands.append(f"pen circle {cx_t} {cy_t} {r_t}")

    def parse_line(self, elem, scale, offset_x, offset_y, shift_x=0, shift_y=0):
        """Parse SVG line."""
        x1 = float(elem.get('x1', 0))
        y1 = float(elem.get('y1', 0))
        x2 = float(elem.get('x2', 0))
        y2 = float(elem.get('y2', 0))

        x1_t, y1_t = self.transform_point(x1, y1, scale, offset_x, offset_y, shift_x, shift_y)
        x2_t, y2_t = self.transform_point(x2, y2, scale, offset_x, offset_y, shift_x, shift_y)

        self.commands.append(f"pen line {x1_t} {y1_t} {x2_t} {y2_t}")

    def parse_polyline(self, elem, scale, offset_x, offset_y, shift_x=0, shift_y=0, close=False):
        """Parse SVG polyline or polygon."""
        points = elem.get('points', '')
        if not points:
            return

        coords = [float(n) for n in re.findall(r'-?\d+\.?\d*', points)]
        if len(coords) < 4:
            return

        # Start at first point
        x1, y1 = self.transform_point(coords[0], coords[1], scale, offset_x, offset_y, shift_x, shift_y)
        self.commands.append(f"pen down {x1} {y1}")

        # Draw to each subsequent point
        for i in range(2, len(coords), 2):
            x2, y2 = self.transform_point(coords[i], coords[i+1], scale, offset_x, offset_y, shift_x, shift_y)
            self.commands.append(f"pen move {x2} {y2}")

        # Close polygon if needed
        if close:
            x2, y2 = self.transform_point(coords[0], coords[1], scale, offset_x, offset_y, shift_x, shift_y)
            self.commands.append(f"pen move {x2} {y2}")

        self.commands.append("pen up")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 svg_to_lamp_improved.py <svg_file> [scale] [x] [y]")
        print("Examples:")
        print("  python3 svg_to_lamp_improved.py symbol.svg           # Auto-scale to center")
        print("  python3 svg_to_lamp_improved.py symbol.svg 4         # Scale by 4x, auto-center")
        print("  python3 svg_to_lamp_improved.py symbol.svg 4 100 200 # Scale by 4x at position (100,200)")
        sys.exit(1)

    svg_file = sys.argv[1]
    
    # Parse arguments
    scale = 1.0
    offset_x = 0
    offset_y = 0
    
    if len(sys.argv) > 2:
        scale = float(sys.argv[2])
    if len(sys.argv) > 3:
        offset_x = int(sys.argv[3])
    if len(sys.argv) > 4:
        offset_y = int(sys.argv[4])

    if not Path(svg_file).exists():
        print(f"Error: File '{svg_file}' not found", file=sys.stderr)
        sys.exit(1)

    converter = SVGToLamp()
    commands = converter.parse_svg_file(svg_file, scale, offset_x, offset_y)
    print(commands)


if __name__ == '__main__':
    main()

