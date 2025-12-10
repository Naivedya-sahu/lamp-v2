#!/usr/bin/env python3
"""
Interactive Component Selector
Provides a simple interface for selecting and drawing electrical components.
"""

import sys
import os
from component_library import ComponentLibraryManager
from svg_to_lamp import SVGToLamp


class ComponentSelector:
    """Interactive selector for electrical components."""

    def __init__(self, library_path: str, config_path: str):
        self.manager = ComponentLibraryManager(library_path, config_path)
        self.current_cycle_index = 0
        self.cycled_symbols = self.manager.get_cycle_order()

    def show_menu(self):
        """Display main menu with available symbols."""
        print("\n" + "="*60)
        print("ELECTRICAL COMPONENT LIBRARY")
        print("="*60)

        # Show symbols by category
        print("\nVIEWED SYMBOLS (Always Available):")
        viewed = self.manager.get_symbols_by_visibility('viewed')
        if viewed:
            for i, symbol_id in enumerate(sorted(viewed), 1):
                data = self.manager.config['symbols'][symbol_id]
                name = data.get('name', symbol_id)
                cat = data.get('category', 'general')
                print(f"  {i:2}. {name:25} ({cat})")
        else:
            print("  (none)")

        print("\nCYCLED SYMBOLS (Available in Cycle Mode):")
        if self.cycled_symbols:
            for i, symbol_id in enumerate(self.cycled_symbols, 1):
                data = self.manager.config['symbols'][symbol_id]
                name = data.get('name', symbol_id)
                cat = data.get('category', 'general')
                marker = "◄ CURRENT" if i - 1 == self.current_cycle_index else ""
                print(f"  {i:2}. {name:25} ({cat}) {marker}")
        else:
            print("  (none)")

        hidden_count = len(self.manager.get_symbols_by_visibility('hidden'))
        print(f"\nHIDDEN SYMBOLS: {hidden_count} (not shown)")

    def cycle_next(self):
        """Move to next symbol in cycle."""
        if not self.cycled_symbols:
            print("No symbols in cycle mode")
            return None

        self.current_cycle_index = (self.current_cycle_index + 1) % len(self.cycled_symbols)
        current_symbol = self.cycled_symbols[self.current_cycle_index]
        data = self.manager.config['symbols'][current_symbol]
        name = data.get('name', current_symbol)
        print(f"Cycled to: {name} ({current_symbol})")
        return current_symbol

    def cycle_previous(self):
        """Move to previous symbol in cycle."""
        if not self.cycled_symbols:
            print("No symbols in cycle mode")
            return None

        self.current_cycle_index = (self.current_cycle_index - 1) % len(self.cycled_symbols)
        current_symbol = self.cycled_symbols[self.current_cycle_index]
        data = self.manager.config['symbols'][current_symbol]
        name = data.get('name', current_symbol)
        print(f"Cycled to: {name} ({current_symbol})")
        return current_symbol

    def get_current_cycled_symbol(self):
        """Get the currently selected cycled symbol."""
        if not self.cycled_symbols:
            return None
        return self.cycled_symbols[self.current_cycle_index]

    def export_symbol_for_drawing(self, symbol_id: str, output_path: str):
        """Export symbol to SVG file for use with svg_to_lamp.py."""
        self.manager.extractor.export_symbol(symbol_id, output_path)

    def draw_symbol(self, symbol_id: str, x: int, y: int, scale: float = 1.0):
        """
        Export symbol and generate lamp commands for drawing.

        Args:
            symbol_id: Symbol to draw
            x, y: Position on tablet (in pixels)
            scale: Scale factor
        """
        # Export to temporary file
        temp_svg = f"/tmp/{symbol_id}.svg"
        self.export_symbol_for_drawing(symbol_id, temp_svg)

        # Convert to lamp commands
        converter = SVGToLamp()
        commands = converter.parse_svg_file(temp_svg, scale, x, y)

        return commands


def main():
    """Interactive command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Interactive component selector and viewer'
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
    parser.add_argument(
        '--export-all',
        action='store_true',
        help='Export all visible symbols to individual SVG files'
    )
    parser.add_argument(
        '--export-cycled',
        action='store_true',
        help='Export only cycled symbols'
    )
    parser.add_argument(
        '--output-dir',
        default='exported_symbols',
        help='Output directory for exported symbols'
    )

    args = parser.parse_args()

    selector = ComponentSelector(args.library, args.config)

    if args.export_all:
        print("Exporting all viewed symbols...")
        selector.manager.export_symbols_by_visibility('viewed', args.output_dir)
        print("Exporting all cycled symbols...")
        selector.manager.export_symbols_by_visibility('cycled', args.output_dir)
        print(f"Symbols exported to {args.output_dir}/")
        return

    if args.export_cycled:
        print("Exporting cycled symbols...")
        selector.manager.export_cycled_symbols(args.output_dir)
        print(f"Cycled symbols exported to {args.output_dir}/")
        return

    # Interactive mode
    print("\nWelcome to the Component Selector!")
    selector.show_menu()

    print("\n" + "="*60)
    print("COMMANDS:")
    print("  n - Cycle to next symbol")
    print("  p - Cycle to previous symbol")
    print("  c - Show current cycled symbol")
    print("  e <symbol_id> - Export specific symbol")
    print("  d <symbol_id> <x> <y> [scale] - Generate drawing commands")
    print("  m - Show menu again")
    print("  q - Quit")
    print("="*60)

    while True:
        try:
            cmd = input("\n> ").strip().split()
            if not cmd:
                continue

            if cmd[0] == 'q':
                print("Goodbye!")
                break

            elif cmd[0] == 'm':
                selector.show_menu()

            elif cmd[0] == 'n':
                selector.cycle_next()

            elif cmd[0] == 'p':
                selector.cycle_previous()

            elif cmd[0] == 'c':
                current = selector.get_current_cycled_symbol()
                if current:
                    data = selector.manager.config['symbols'][current]
                    name = data.get('name', current)
                    print(f"Current cycled symbol: {name} ({current})")
                else:
                    print("No symbols in cycle mode")

            elif cmd[0] == 'e' and len(cmd) >= 2:
                symbol_id = cmd[1]
                output_path = f"{symbol_id}.svg"
                selector.export_symbol_for_drawing(symbol_id, output_path)
                print(f"Exported to {output_path}")

            elif cmd[0] == 'd' and len(cmd) >= 4:
                symbol_id = cmd[1]
                x = int(cmd[2])
                y = int(cmd[3])
                scale = float(cmd[4]) if len(cmd) >= 5 else 1.0

                print(f"Generating drawing commands for {symbol_id}...")
                commands = selector.draw_symbol(symbol_id, x, y, scale)
                print(f"\nTo draw this symbol, run:")
                print(f"  python3 svg_to_lamp.py /tmp/{symbol_id}.svg {x} {y} {scale} | lamp")

            else:
                print("Unknown command. Type 'm' for menu or 'q' to quit.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == '__main__':
    main()
