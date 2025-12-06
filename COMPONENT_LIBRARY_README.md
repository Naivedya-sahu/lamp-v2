# Custom Electrical Component Library

A flexible system for managing and using electrical component symbols from the comprehensive SVG library.

## Overview

This system provides:

1. **Symbol Extraction** - Extract individual symbols from the large `Electrical_symbols_library.svg` file
2. **Configuration Management** - Control which symbols are visible, cycled, or hidden
3. **Interactive Selection** - Browse and select components through a menu interface
4. **Integration with lamp** - Export symbols for drawing on reMarkable tablet

## Files

- **`component_library.py`** - Core library manager and symbol extractor
- **`component_selector.py`** - Interactive component selector interface
- **`component_library_config.json`** - Configuration file (auto-generated)
- **`component_library_config.example.json`** - Example configuration with explanations
- **`examples/component_library_demo.sh`** - Demo script showing all features

## Quick Start

### 1. Initialize the Library

```bash
python3 component_library.py \
    --library examples/svg_symbols/Electrical_symbols_library.svg \
    --config component_library_config.json \
    init
```

This creates `component_library_config.json` with all 214 symbols set to "viewed" by default.

### 2. Configure Symbol Visibility

Set symbols to different visibility modes:

```bash
# Set a symbol to 'cycled' (rotates through in cycle mode)
python3 component_library.py set g1087 cycled

# Set a symbol to 'hidden' (not shown in menus)
python3 component_library.py set g6082 hidden

# Keep as 'viewed' (always available)
python3 component_library.py set g1263 viewed
```

### 3. List Symbols

```bash
# List all symbols
python3 component_library.py list

# List only cycled symbols
python3 component_library.py list --visibility cycled

# List only viewed symbols
python3 component_library.py list --visibility viewed
```

### 4. Export Symbols

Export symbols to individual SVG files:

```bash
# Export all cycled symbols
python3 component_library.py export --visibility cycled --output exported_symbols/

# Export a specific symbol
python3 component_library.py export --symbol g1087 --output exported_symbols/

# Export all viewed symbols
python3 component_library.py export --visibility viewed --output exported_symbols/
```

### 5. Interactive Mode

Run the interactive selector:

```bash
python3 component_selector.py
```

Commands in interactive mode:
- `n` - Cycle to next symbol
- `p` - Cycle to previous symbol
- `c` - Show current cycled symbol
- `e <symbol_id>` - Export specific symbol
- `d <symbol_id> <x> <y> [scale]` - Generate drawing commands
- `m` - Show menu
- `q` - Quit

## Visibility Modes

### Viewed
- Always visible in menus
- Available for direct selection
- Use for frequently used components

### Cycled
- Available in cycle mode
- Symbols rotate when user presses next/previous
- Use for related components (e.g., different resistor types)
- Perfect for tablet button interface

### Hidden
- Not shown in menus or cycle
- Excluded from exports (unless specifically requested)
- Use for deprecated or rarely used symbols

## Configuration File Format

The configuration file (`component_library_config.json`) uses this structure:

```json
{
  "metadata": {
    "version": "1.0",
    "description": "Component library configuration"
  },
  "symbols": {
    "g1087": {
      "visibility": "cycled",
      "name": "resistor",
      "category": "passive_components",
      "description": "Basic resistor symbol"
    },
    "g1263": {
      "visibility": "viewed",
      "name": "npn_transistor",
      "category": "semiconductors"
    }
  }
}
```

### Fields:
- **visibility** (required): `"viewed"`, `"cycled"`, or `"hidden"`
- **name** (optional): Human-readable name for the symbol
- **category** (optional): Group symbols by category
- **description** (optional): Detailed description

## Integration with lamp Drawing System

### Basic Drawing

1. Export a symbol:
```bash
python3 component_library.py export --symbol g1087 --output symbols/
```

2. Convert to lamp commands:
```bash
python3 svg_to_lamp.py symbols/g1087.svg 500 800 2.0 | lamp
```

### Advanced: Dynamic UI

Integrate with the dynamic UI system (see `DYNAMIC_UI_WITH_ERASER.md`):

```bash
#!/bin/bash
# Component menu with cycling

COMPONENT_REGION="700 1400 1350 1850"

# Clear component area
echo "eraser fill $COMPONENT_REGION 15" | lamp

# Draw current component
CURRENT_SYMBOL="g1087"
python3 svg_to_lamp.py exported_symbols/$CURRENT_SYMBOL.svg 900 1600 1.5 | lamp

# Add label
python3 text_to_lamp.py "RESISTOR" 850 1750 0.5 | lamp
```

## Use Cases

### 1. Circuit Design Palette

Create a palette of commonly used components:

```bash
# Configure favorites
python3 component_library.py set g1087 cycled  # resistor
python3 component_library.py set g1092 cycled  # capacitor
python3 component_library.py set g1058 cycled  # inductor
python3 component_library.py set g1136 cycled  # diode

# Export to palette directory
python3 component_library.py export --visibility cycled --output palette/
```

### 2. Category-Based Organization

Organize by component type in the config file:

```json
{
  "symbols": {
    "g1087": {"visibility": "cycled", "category": "passive"},
    "g1092": {"visibility": "cycled", "category": "passive"},
    "g1263": {"visibility": "viewed", "category": "transistors"},
    "g1100": {"visibility": "viewed", "category": "transistors"}
  }
}
```

### 3. Tablet Button Mapping

Map physical buttons to cycle through components:

```bash
# Button 1: Next component
python3 -c "from component_selector import ComponentSelector; \
    s = ComponentSelector('...', '...'); \
    symbol = s.cycle_next(); \
    print(symbol)"

# Button 2: Previous component
python3 -c "from component_selector import ComponentSelector; \
    s = ComponentSelector('...', '...'); \
    symbol = s.cycle_previous(); \
    print(symbol)"
```

## Symbol IDs

The library contains 214 symbols with IDs like:
- `g1087` - `g1263` - Various components
- Category backgrounds: `g6082`, `g4365`, `g3794`, `g3955`, `g2999`, `g1474`, `g6275`

To identify specific symbols, export them individually and view the SVG files.

## Tips

1. **Start Small**: Begin with 5-10 most-used symbols in "cycled" mode
2. **Use Categories**: Organize symbols by category for easier management
3. **Name Your Symbols**: Add descriptive names in the config for clarity
4. **Test Exports**: Always preview exported SVGs before using with lamp
5. **Version Control**: Keep your config file in git to track changes

## Troubleshooting

### Symbol not found
- Check symbol ID with: `python3 component_library.py list`
- Ensure config file is up to date

### Export failed
- Verify SVG library path is correct
- Check write permissions on output directory

### Drawing looks wrong
- Adjust scale parameter in svg_to_lamp.py
- Check symbol bounding box: some symbols may have extra whitespace

## Advanced: Custom Scripts

### Batch Export by Category

```python
from component_library import ComponentLibraryManager

manager = ComponentLibraryManager('library.svg', 'config.json')

# Get all symbols in a category
for symbol_id, data in manager.config['symbols'].items():
    if data.get('category') == 'semiconductors':
        manager.extractor.export_symbol(symbol_id, f'semiconductors/{symbol_id}.svg')
```

### Auto-Generate Menu

```python
from component_library import ComponentLibraryManager

manager = ComponentLibraryManager('library.svg', 'config.json')
cycled = manager.get_cycle_order()

for i, symbol_id in enumerate(cycled):
    # Generate menu entry
    x = 100
    y = 100 + (i * 50)
    print(f"# Menu item {i}: {symbol_id}")
    print(f"python3 svg_to_lamp.py symbols/{symbol_id}.svg {x} {y} 1.0 | lamp")
```

## License

This component library system is part of the lamp-v2 project. The electrical symbols in `Electrical_symbols_library.svg` are CC0 (Public Domain) from Wikimedia Commons.

## Credits

- SVG Library: Filip Dominec and contributors (Wikimedia Commons)
- Component Library System: Created for lamp-v2 reMarkable tablet drawing tool
