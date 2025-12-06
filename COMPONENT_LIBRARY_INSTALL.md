# Component Library - Install/Use/Uninstall Guide

## Prerequisites

- Python 3.x
- lamp-v2 repository
- `svg_to_lamp.py` (included in repo)

## Installation

### Step 1: Verify Files

```bash
cd /path/to/lamp-v2

# Check required files exist
ls component_library.py component_selector.py
ls examples/svg_symbols/Electrical_symbols_library.svg
```

### Step 2: Initialize Configuration

```bash
# Generate component_library_config.json with 214 symbols
python3 component_library.py init
```

### Step 3: Make Scripts Executable (Optional)

```bash
chmod +x component_library.py component_selector.py
chmod +x examples/component_library_demo.sh
```

### Step 4: Test Installation

```bash
# Run demo
./examples/component_library_demo.sh

# Should output:
# - Extracted 214 symbols from library
# - Configuration initialized successfully
# - Exported symbols to exported_symbols/
```

## Usage

### Basic Operations

**List all symbols:**
```bash
python3 component_library.py list
```

**Configure symbol visibility:**
```bash
# Set to cycled (for button navigation)
python3 component_library.py set g1087 cycled

# Set to viewed (always available)
python3 component_library.py set g1263 viewed

# Set to hidden (exclude from menus)
python3 component_library.py set g6082 hidden
```

**Export symbols:**
```bash
# Export all cycled symbols
python3 component_library.py export --visibility cycled --output symbols/

# Export specific symbol
python3 component_library.py export --symbol g1087 --output symbols/
```

### Interactive Mode

```bash
python3 component_selector.py
```

**Commands:**
- `n` - Next symbol in cycle
- `p` - Previous symbol in cycle
- `c` - Show current symbol
- `e <id>` - Export symbol
- `m` - Show menu
- `q` - Quit

### Drawing Workflow

**1. Configure favorites:**
```bash
python3 component_library.py set g1087 cycled  # resistor
python3 component_library.py set g1092 cycled  # capacitor
python3 component_library.py set g1058 cycled  # inductor
```

**2. Export symbols:**
```bash
python3 component_library.py export --visibility cycled --output my_symbols/
```

**3. Draw on tablet:**
```bash
# Draw resistor at (x=500, y=800), scale=2.0
python3 svg_to_lamp.py my_symbols/g1087.svg 500 800 2.0 | lamp
```

### Configuration File

Edit `component_library_config.json` directly:

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
      "category": "passive",
      "description": "Basic resistor symbol"
    }
  }
}
```

**Fields:**
- `visibility`: `"viewed"` | `"cycled"` | `"hidden"`
- `name`: Human-readable name (optional)
- `category`: Group name (optional)
- `description`: Details (optional)

## Common Workflows

### Workflow 1: Create Component Palette

```bash
# Configure
python3 component_library.py set g1087 cycled  # resistor
python3 component_library.py set g1092 cycled  # capacitor
python3 component_library.py set g1058 cycled  # inductor

# Export
python3 component_library.py export --visibility cycled --output palette/

# Use
for svg in palette/*.svg; do
  python3 svg_to_lamp.py "$svg" 500 800 1.5 | lamp
done
```

### Workflow 2: Hide Unused Symbols

```bash
# Hide category backgrounds
python3 component_library.py set g6082 hidden
python3 component_library.py set g4365 hidden

# Verify
python3 component_library.py list --visibility hidden
```

### Workflow 3: Reset Configuration

```bash
# Delete and reinitialize
rm component_library_config.json
python3 component_library.py init
```

## Troubleshooting

**"Symbol not found"**
```bash
# List all available IDs
python3 component_library.py list | grep g1087
```

**"Nothing exported"**
```bash
# Check visibility is set
python3 component_library.py list --visibility cycled
```

**"Drawing looks wrong"**
```bash
# Adjust scale parameter (try 0.5 to 3.0)
python3 svg_to_lamp.py symbols/g1087.svg 500 800 0.8 | lamp
```

**"Config file corrupt"**
```bash
# Use example as template
cp component_library_config.example.json component_library_config.json
python3 component_library.py init
```

## Uninstallation

### Step 1: Remove Configuration

```bash
rm component_library_config.json
```

### Step 2: Remove Exported Files

```bash
rm -rf exported_symbols/
rm -rf my_symbols/  # or whatever you named it
```

### Step 3: Remove Scripts (Optional)

```bash
git checkout main  # switch to main branch
# Or manually remove:
rm component_library.py
rm component_selector.py
rm examples/component_library_demo.sh
rm component_library_config.example.json
```

### Step 4: Clean Git (If on Feature Branch)

```bash
# Switch to main and delete feature branch
git checkout main
git branch -D claude/custom-component-library-01MpXSzHcG2jmF4tpS793ZER
```

## File Locations

```
lamp-v2/
├── component_library.py              # Core manager
├── component_selector.py             # Interactive selector
├── component_library_config.json     # Your config (generated)
├── component_library_config.example.json  # Example
├── exported_symbols/                 # Generated (gitignored)
└── examples/
    ├── component_library_demo.sh     # Demo script
    └── svg_symbols/
        └── Electrical_symbols_library.svg  # Source (214 symbols)
```

## Help

```bash
# Command help
python3 component_library.py --help
python3 component_selector.py --help

# List commands
python3 component_library.py list --help
python3 component_library.py export --help
```
