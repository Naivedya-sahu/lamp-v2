# Component Library - Quick Start Guide

## What is This?

This custom component library system lets you:
- ✅ Extract individual symbols from the large electrical library SVG
- ✅ Configure which symbols appear in menus (viewed/cycled/hidden)
- ✅ Export symbols for drawing on your reMarkable tablet
- ✅ Cycle through selected components using buttons

## 5-Minute Setup

### 1. Run the Demo (See It In Action)

```bash
./examples/component_library_demo.sh
```

This will:
- Initialize the library with 214 symbols
- Configure 3 symbols for cycling (resistor, capacitor, inductor)
- Export them to individual SVG files
- Show you how to draw them

### 2. List Available Symbols

```bash
python3 component_library.py list
```

You'll see all 214 symbols like: g1087, g1092, g1058, etc.

### 3. Configure Your Favorites

Pick symbols you want to cycle through:

```bash
# Add to cycle mode
python3 component_library.py set g1087 cycled   # resistor
python3 component_library.py set g1263 cycled   # transistor
python3 component_library.py set g1136 cycled   # diode

# Hide unused symbols
python3 component_library.py set g6082 hidden
```

### 4. Export for Drawing

```bash
# Export all cycled symbols
python3 component_library.py export --visibility cycled --output my_symbols/
```

### 5. Draw a Component

```bash
# Draw exported symbol at position (x=500, y=800) with scale 2.0
python3 svg_to_lamp.py my_symbols/g1087.svg 500 800 2.0 | lamp
```

## Three Visibility Modes

| Mode | When to Use | Button Behavior |
|------|------------|----------------|
| **cycled** | Components you switch between frequently | Press button → cycle through these |
| **viewed** | Always available in menu | Always visible, no cycling |
| **hidden** | Deprecated or unused symbols | Never shown |

## Common Workflows

### Workflow 1: Circuit Design Palette

Create a set of passive components:

```bash
python3 component_library.py set g1087 cycled  # resistor
python3 component_library.py set g1092 cycled  # capacitor
python3 component_library.py set g1058 cycled  # inductor
python3 component_library.py set g1136 cycled  # diode

python3 component_library.py export --visibility cycled --output passive/
```

### Workflow 2: Semiconductor Library

```bash
python3 component_library.py set g1263 viewed  # NPN transistor
python3 component_library.py set g1100 viewed  # PNP transistor
python3 component_library.py set g1162 viewed  # NMOS
python3 component_library.py set g1253 viewed  # PMOS

python3 component_library.py export --visibility viewed --output semiconductors/
```

### Workflow 3: Interactive Selection

```bash
python3 component_selector.py
```

Then use:
- `n` = next component
- `p` = previous component
- `c` = show current
- `e g1087` = export specific symbol
- `m` = show menu

## Configuration File

Edit `component_library_config.json` directly for bulk changes:

```json
{
  "symbols": {
    "g1087": {
      "visibility": "cycled",
      "name": "resistor",
      "category": "passive"
    },
    "g1263": {
      "visibility": "viewed",
      "name": "npn_transistor",
      "category": "semiconductors"
    }
  }
}
```

## Tips

1. **Start small**: Configure 5-10 symbols first
2. **Name them**: Add human-readable names in config
3. **Use categories**: Organize by type (passive, active, logic, etc.)
4. **Preview SVGs**: Open exported files to see what they look like
5. **Adjust scale**: If symbol is too big/small, change the scale parameter

## File Structure

```
lamp-v2/
├── component_library.py              # Core library manager
├── component_selector.py             # Interactive selector
├── component_library_config.json     # Your configuration
├── exported_symbols/                 # Exported SVG files
├── COMPONENT_LIBRARY_README.md       # Full documentation
└── examples/
    ├── component_library_demo.sh     # Demo script
    └── svg_symbols/
        └── Electrical_symbols_library.svg  # Source library (214 symbols)
```

## Troubleshooting

**"Symbol not found"**
→ Run `python3 component_library.py list` to see all IDs

**"Nothing exported"**
→ Check you set visibility: `python3 component_library.py set g1087 cycled`

**"Drawing looks wrong"**
→ Adjust scale: try values between 0.5 and 3.0

**"Want to reset everything"**
→ Delete `component_library_config.json` and run `init` again

## Next Steps

1. Read the full documentation: `COMPONENT_LIBRARY_README.md`
2. Check out the dynamic UI guide: `DYNAMIC_UI_WITH_ERASER.md`
3. Customize `component_library_config.json` with your preferences
4. Integrate with your tablet button mappings

## Help

- List commands: `python3 component_library.py --help`
- Interactive help: `python3 component_selector.py` then type `m`
- Full docs: See `COMPONENT_LIBRARY_README.md`
