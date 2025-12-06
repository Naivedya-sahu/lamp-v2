#!/usr/bin/env python3
"""
Custom Electrical Component Library System
Extracts and manages individual symbols from the electrical symbols library SVG file.
"""

import xml.etree.ElementTree as ET
import json
import os
import sys
from typing import Dict, List, Optional, Set
from pathlib import Path


class SymbolExtractor:
    """Extracts individual symbols from the electrical component library SVG."""

    def __init__(self, library_path: str):
        self.library_path = library_path
        self.tree = None
        self.root = None
        self.symbols = {}
        self.categories = {}
        self._parse_library()

    def _parse_library(self):
        """Parse the SVG library file and extract all symbols."""
        try:
            self.tree = ET.parse(self.library_path)
            self.root = self.tree.getroot()
            self._extract_symbols()
        except Exception as e:
            print(f"Error parsing SVG library: {e}", file=sys.stderr)
            raise

    def _extract_symbols(self):
        """Extract all group elements that represent symbols."""
        # Define SVG namespace
        ns = {
            'svg': 'http://www.w3.org/2000/svg',
            'inkscape': 'http://www.inkscape.org/namespaces/inkscape'
        }

        # Find all groups in the SVG
        for elem in self.root.iter():
            if elem.tag.endswith('}g') or elem.tag == 'g':
                group_id = elem.get('id')
                if group_id and group_id.startswith('g'):
                    # Extract the group and its bounding box
                    bbox = self._calculate_bbox(elem)
                    self.symbols[group_id] = {
                        'id': group_id,
                        'element': elem,
                        'bbox': bbox,
                        'category': self._infer_category(group_id, elem)
                    }

        print(f"Extracted {len(self.symbols)} symbols from library")

    def _calculate_bbox(self, element) -> Dict[str, float]:
        """Calculate bounding box for an element."""
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        for elem in element.iter():
            # Extract coordinates from various SVG elements
            if 'path' in elem.tag:
                d = elem.get('d', '')
                coords = self._extract_coords_from_path(d)
                for x, y in coords:
                    min_x, max_x = min(min_x, x), max(max_x, x)
                    min_y, max_y = min(min_y, y), max(max_y, y)

            elif 'rect' in elem.tag:
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                w = float(elem.get('width', 0))
                h = float(elem.get('height', 0))
                min_x, max_x = min(min_x, x), max(max_x, x + w)
                min_y, max_y = min(min_y, y), max(max_y, y + h)

            elif 'circle' in elem.tag:
                cx = float(elem.get('cx', 0))
                cy = float(elem.get('cy', 0))
                r = float(elem.get('r', 0))
                min_x, max_x = min(min_x, cx - r), max(max_x, cx + r)
                min_y, max_y = min(min_y, cy - r), max(max_y, cy + r)

        return {
            'x': min_x if min_x != float('inf') else 0,
            'y': min_y if min_y != float('inf') else 0,
            'width': max_x - min_x if max_x != float('-inf') else 0,
            'height': max_y - min_y if max_y != float('-inf') else 0
        }

    def _extract_coords_from_path(self, d: str) -> List[tuple]:
        """Extract coordinate pairs from SVG path data."""
        coords = []
        import re
        # Simple extraction of numeric coordinates
        numbers = re.findall(r'-?\d+\.?\d*', d)
        for i in range(0, len(numbers) - 1, 2):
            try:
                coords.append((float(numbers[i]), float(numbers[i + 1])))
            except (ValueError, IndexError):
                continue
        return coords

    def _infer_category(self, group_id: str, element) -> str:
        """Infer category based on position or context."""
        # You can enhance this based on the SVG structure
        return "general"

    def get_symbol_ids(self) -> List[str]:
        """Get list of all symbol IDs."""
        return list(self.symbols.keys())

    def get_symbol(self, symbol_id: str) -> Optional[Dict]:
        """Get symbol data by ID."""
        return self.symbols.get(symbol_id)

    def export_symbol(self, symbol_id: str, output_path: str):
        """Export a single symbol to a standalone SVG file."""
        symbol = self.symbols.get(symbol_id)
        if not symbol:
            print(f"Symbol '{symbol_id}' not found", file=sys.stderr)
            return

        # Create a new SVG with just this symbol
        bbox = symbol['bbox']
        width = bbox['width'] + 20  # Add padding
        height = bbox['height'] + 20

        svg_header = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   width="{width}"
   height="{height}"
   viewBox="{bbox['x']-10} {bbox['y']-10} {width} {height}"
   version="1.1"
   xmlns="http://www.w3.org/2000/svg">
'''

        # Convert element to string
        element_str = ET.tostring(symbol['element'], encoding='unicode')

        svg_footer = '\n</svg>'

        with open(output_path, 'w') as f:
            f.write(svg_header)
            f.write(element_str)
            f.write(svg_footer)

        print(f"Exported symbol '{symbol_id}' to {output_path}")


class ComponentLibraryManager:
    """Manages component library with configuration for visibility and cycling."""

    def __init__(self, library_path: str, config_path: str):
        self.extractor = SymbolExtractor(library_path)
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from JSON file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            # Create default configuration
            default_config = self._create_default_config()
            self.save_config(default_config)
            return default_config

    def _create_default_config(self) -> Dict:
        """Create default configuration with all symbols as 'viewed'."""
        config = {
            "metadata": {
                "version": "1.0",
                "description": "Component library configuration"
            },
            "symbols": {}
        }

        # Default all symbols to 'viewed'
        for symbol_id in self.extractor.get_symbol_ids():
            config["symbols"][symbol_id] = {
                "visibility": "viewed",
                "name": symbol_id,
                "category": self.extractor.get_symbol(symbol_id).get('category', 'general')
            }

        return config

    def save_config(self, config: Optional[Dict] = None):
        """Save configuration to JSON file."""
        if config is None:
            config = self.config

        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"Configuration saved to {self.config_path}")

    def get_symbols_by_visibility(self, visibility: str) -> List[str]:
        """
        Get list of symbol IDs by visibility status.

        Args:
            visibility: 'viewed', 'cycled', or 'hidden'

        Returns:
            List of symbol IDs matching the visibility status
        """
        return [
            symbol_id
            for symbol_id, data in self.config['symbols'].items()
            if data.get('visibility') == visibility
        ]

    def set_symbol_visibility(self, symbol_id: str, visibility: str):
        """
        Set visibility for a symbol.

        Args:
            symbol_id: Symbol identifier
            visibility: 'viewed', 'cycled', or 'hidden'
        """
        if symbol_id not in self.config['symbols']:
            print(f"Symbol '{symbol_id}' not found in configuration", file=sys.stderr)
            return

        if visibility not in ['viewed', 'cycled', 'hidden']:
            print(f"Invalid visibility: {visibility}. Must be 'viewed', 'cycled', or 'hidden'",
                  file=sys.stderr)
            return

        self.config['symbols'][symbol_id]['visibility'] = visibility
        print(f"Set '{symbol_id}' visibility to '{visibility}'")

    def export_symbols_by_visibility(self, visibility: str, output_dir: str):
        """Export all symbols with specific visibility to individual SVG files."""
        os.makedirs(output_dir, exist_ok=True)

        symbol_ids = self.get_symbols_by_visibility(visibility)
        print(f"Exporting {len(symbol_ids)} symbols with visibility '{visibility}'...")

        for symbol_id in symbol_ids:
            output_path = os.path.join(output_dir, f"{symbol_id}.svg")
            self.extractor.export_symbol(symbol_id, output_path)

    def list_symbols(self, visibility: Optional[str] = None):
        """List symbols, optionally filtered by visibility."""
        if visibility:
            symbols = self.get_symbols_by_visibility(visibility)
            print(f"\nSymbols with visibility '{visibility}' ({len(symbols)}):")
        else:
            symbols = list(self.config['symbols'].keys())
            print(f"\nAll symbols ({len(symbols)}):")

        for symbol_id in sorted(symbols):
            data = self.config['symbols'][symbol_id]
            vis = data.get('visibility', 'unknown')
            cat = data.get('category', 'general')
            print(f"  {symbol_id:20} [{vis:8}] ({cat})")

    def export_cycled_symbols(self, output_dir: str):
        """Export symbols marked for cycling to individual files."""
        self.export_symbols_by_visibility('cycled', output_dir)

    def get_cycle_order(self) -> List[str]:
        """Get ordered list of symbols to cycle through."""
        cycled = self.get_symbols_by_visibility('cycled')
        return sorted(cycled)  # You can customize the ordering


def main():
    """Command-line interface for the component library manager."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Manage electrical component library'
    )
    parser.add_argument(
        '--library',
        default='examples/svg_symbols/Electrical_symbols_library.svg',
        help='Path to SVG library file'
    )
    parser.add_argument(
        '--config',
        default='component_library_config.json',
        help='Path to configuration file'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List symbols')
    list_parser.add_argument(
        '--visibility',
        choices=['viewed', 'cycled', 'hidden'],
        help='Filter by visibility'
    )

    # Set visibility command
    set_parser = subparsers.add_parser('set', help='Set symbol visibility')
    set_parser.add_argument('symbol_id', help='Symbol ID')
    set_parser.add_argument(
        'visibility',
        choices=['viewed', 'cycled', 'hidden'],
        help='Visibility status'
    )

    # Export command
    export_parser = subparsers.add_parser('export', help='Export symbols')
    export_parser.add_argument(
        '--visibility',
        choices=['viewed', 'cycled', 'hidden'],
        help='Export symbols with this visibility'
    )
    export_parser.add_argument(
        '--output',
        default='exported_symbols',
        help='Output directory'
    )
    export_parser.add_argument(
        '--symbol',
        help='Export specific symbol ID'
    )

    # Initialize command
    init_parser = subparsers.add_parser('init', help='Initialize configuration')

    args = parser.parse_args()

    if args.command == 'init':
        manager = ComponentLibraryManager(args.library, args.config)
        print("Configuration initialized successfully")
        return

    if args.command is None:
        parser.print_help()
        return

    # Create manager
    manager = ComponentLibraryManager(args.library, args.config)

    if args.command == 'list':
        manager.list_symbols(args.visibility)

    elif args.command == 'set':
        manager.set_symbol_visibility(args.symbol_id, args.visibility)
        manager.save_config()

    elif args.command == 'export':
        if args.symbol:
            # Export specific symbol
            output_path = os.path.join(args.output, f"{args.symbol}.svg")
            os.makedirs(args.output, exist_ok=True)
            manager.extractor.export_symbol(args.symbol, output_path)
        elif args.visibility:
            # Export by visibility
            manager.export_symbols_by_visibility(args.visibility, args.output)
        else:
            print("Specify either --symbol or --visibility", file=sys.stderr)


if __name__ == '__main__':
    main()
