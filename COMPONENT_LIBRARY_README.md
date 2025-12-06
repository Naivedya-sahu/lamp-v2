# Custom Electrical Component Library

Extract and manage individual symbols from the electrical symbols SVG library (214 symbols).

## Features

- **Symbol Extraction**: Extract individual symbols from `Electrical_symbols_library.svg`
- **Visibility Control**: Configure symbols as `viewed`, `cycled`, or `hidden`
- **Export**: Generate individual SVG files for drawing
- **Interactive Mode**: Cycle through components with button controls
- **Integration**: Works with existing `svg_to_lamp.py` for reMarkable tablet

## Components

| File | Purpose |
|------|---------|
| `component_library.py` | Core library manager and symbol extractor |
| `component_selector.py` | Interactive selector with cycling support |
| `component_library_config.json` | Configuration (214 symbols, customizable) |
| `component_library_config.example.json` | Example configuration |
| `examples/component_library_demo.sh` | Demo script |

## Visibility Modes

- **`viewed`**: Always available in menu
- **`cycled`**: Rotate through with next/previous buttons
- **`hidden`**: Excluded from menus and exports

## Quick Commands

```bash
# Initialize
python3 component_library.py init

# List symbols
python3 component_library.py list
python3 component_library.py list --visibility cycled

# Set visibility
python3 component_library.py set g1087 cycled
python3 component_library.py set g1263 viewed
python3 component_library.py set g6082 hidden

# Export symbols
python3 component_library.py export --visibility cycled --output symbols/
python3 component_library.py export --symbol g1087 --output symbols/

# Interactive mode
python3 component_selector.py
```

## Drawing Integration

```bash
# Export symbol
python3 component_library.py export --symbol g1087 --output symbols/

# Draw on tablet
python3 svg_to_lamp.py symbols/g1087.svg 500 800 2.0 | lamp
```

## Configuration

Edit `component_library_config.json`:

```json
{
  "symbols": {
    "g1087": {
      "visibility": "cycled",
      "name": "resistor",
      "category": "passive"
    }
  }
}
```

## License

CC0 Public Domain (SVG symbols from Wikimedia Commons)
