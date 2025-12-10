# Installation and Usage Guide

Complete guide for installing, using, and uninstalling lamp-v2 with eraser support and component library.

## Prerequisites

### Required
- ARM cross-compiler: `gcc-arm-linux-gnueabihf`, `g++-arm-linux-gnueabihf`
- [okp](https://github.com/raisjn/okp) transpiler
- Python 3.x
- reMarkable tablet (firmware 3.24+)
- SSH access to reMarkable (USB or WiFi)

### Installing Prerequisites

**Ubuntu/Debian**:
```bash
sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf python3
```

**okp transpiler**:
```bash
git clone https://github.com/raisjn/okp.git
cd okp
# Follow okp installation instructions
```

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/lamp-v2.git
cd lamp-v2
```

### Step 2: Initialize Submodules

```bash
git submodule update --init --recursive
```

### Step 3: Build Enhanced Lamp

```bash
./build_lamp_enhanced.sh
```

**Expected output**:
```
Applying eraser patch...
Building lamp with okp...
Build complete: resources/repos/rmkit/src/build/lamp
```

### Step 4: Deploy to reMarkable

```bash
# Via USB (10.11.99.1) or WiFi
scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/

# Make executable
ssh root@10.11.99.1 'chmod +x /opt/bin/lamp'
```

### Step 5: Verify Installation

```bash
ssh root@10.11.99.1
echo "pen rectangle 100 100 500 500" | /opt/bin/lamp
echo "eraser fill 100 100 500 500 15" | /opt/bin/lamp
```

You should see a rectangle appear and then get erased.

### Step 6: Initialize Component Library

```bash
# On your computer
python3 component_library.py init
```

**Expected output**:
```
Extracted 214 symbols from library
Configuration saved to component_library_config.json
Configuration initialized successfully
```

---

## Usage

### Eraser Commands

#### Basic Operations

```bash
# Erase a line
echo "eraser line x1 y1 x2 y2" | lamp

# Erase rectangle outline
echo "eraser rectangle x1 y1 x2 y2" | lamp

# Fill area with eraser strokes
echo "eraser fill x1 y1 x2 y2 [spacing]" | lamp
# spacing: gap between strokes (default: 20px)

# Dense clearing (10px spacing)
echo "eraser clear x1 y1 x2 y2" | lamp
```

#### Low-Level Control

```bash
echo "eraser down x y" | lamp    # Start erasing at position
echo "eraser move x y" | lamp    # Continue erasing to position
echo "eraser up" | lamp          # Stop erasing
```

#### Pen Commands (Original)

```bash
echo "pen line x1 y1 x2 y2" | lamp
echo "pen rectangle x1 y1 x2 y2" | lamp
echo "pen circle cx cy radius" | lamp
echo "pen down x y" | lamp
echo "pen move x y" | lamp
echo "pen up" | lamp
```

### Component Library

#### List Symbols

```bash
# List all symbols
python3 component_library.py list

# List by visibility
python3 component_library.py list --visibility cycled
python3 component_library.py list --visibility viewed
python3 component_library.py list --visibility hidden
```

#### Configure Symbol Visibility

```bash
# Set to cycled (for button navigation)
python3 component_library.py set g1087 cycled

# Set to viewed (always available)
python3 component_library.py set g1263 viewed

# Set to hidden (exclude from menus)
python3 component_library.py set g6082 hidden
```

#### Export Symbols

```bash
# Export all cycled symbols
python3 component_library.py export --visibility cycled --output symbols/

# Export specific symbol
python3 component_library.py export --symbol g1087 --output symbols/

# Export all viewed symbols
python3 component_library.py export --visibility viewed --output my_symbols/
```

#### Interactive Mode

```bash
python3 component_selector.py
```

**Commands**:
- `n` - Cycle to next symbol
- `p` - Cycle to previous symbol
- `c` - Show current cycled symbol
- `e <symbol_id>` - Export specific symbol
- `d <symbol_id> <x> <y> [scale]` - Generate drawing commands
- `m` - Show menu again
- `q` - Quit

### SVG to Lamp Conversion

```bash
# Convert SVG to lamp commands
python3 svg_to_lamp.py symbol.svg x y scale | lamp

# Examples
python3 svg_to_lamp.py examples/svg_symbols/resistor.svg 500 800 2.0 | lamp
python3 svg_to_lamp.py examples/svg_symbols/capacitor.svg 500 800 2.0 | lamp
```

**Parameters**:
- `symbol.svg` - Path to SVG file
- `x y` - Position on tablet (pixels)
- `scale` - Scale factor (0.5 to 3.0 recommended)

### Text Rendering

```bash
# Render text as vector strokes
python3 text_to_lamp.py "Hello" x y size | lamp

# Examples
python3 text_to_lamp.py "10kΩ" 720 1680 0.5 | lamp
python3 text_to_lamp.py "RESISTOR" 850 1750 0.5 | lamp
```

**Supported characters**: A-Z, 0-9, +, -, Ω, μ

---

## Common Workflows

### Workflow 1: Create Component Palette

```bash
# Step 1: Configure favorites
python3 component_library.py set g1087 cycled  # resistor
python3 component_library.py set g1092 cycled  # capacitor
python3 component_library.py set g1058 cycled  # inductor
python3 component_library.py set g1136 cycled  # diode

# Step 2: Export to palette directory
python3 component_library.py export --visibility cycled --output palette/

# Step 3: Verify exports
ls -lh palette/

# Step 4: Draw components on tablet
python3 svg_to_lamp.py palette/g1087.svg 500 800 1.5 | lamp
```

### Workflow 2: Dynamic Menu System

```bash
# Draw main menu
echo "pen rectangle 50 1400 350 1850" | lamp

# User makes selection...

# Transition: erase old menu, draw new
echo "eraser fill 50 1400 350 1850 15" | lamp
sleep 0.5
echo "pen rectangle 370 1400 670 1850" | lamp
```

### Workflow 3: Component Preview System

```bash
# Define region
COMPONENT_REGION="700 1400 1350 1850"

# Show component
python3 svg_to_lamp.py symbols/g1087.svg 900 1600 1.5 | lamp
python3 text_to_lamp.py "RESISTOR" 850 1750 0.5 | lamp

# User interaction...

# Clear preview
echo "eraser fill $COMPONENT_REGION 15" | lamp

# Show next component
python3 svg_to_lamp.py symbols/g1092.svg 900 1600 1.5 | lamp
python3 text_to_lamp.py "CAPACITOR" 850 1750 0.5 | lamp
```

### Workflow 4: Batch Component Export

```bash
# Export all passive components
python3 component_library.py set g1087 cycled  # resistor
python3 component_library.py set g1092 cycled  # capacitor
python3 component_library.py set g1058 cycled  # inductor

python3 component_library.py export --visibility cycled --output passive/

# Export all semiconductors
python3 component_library.py set g1263 viewed  # NPN
python3 component_library.py set g1100 viewed  # PNP
python3 component_library.py set g1162 viewed  # NMOS
python3 component_library.py set g1253 viewed  # PMOS

python3 component_library.py export --visibility viewed --output semiconductors/
```

---

## Testing

### Run Demo Scripts

```bash
# Component library demo
./examples/component_library_demo.sh

# Dynamic UI demo
./examples/dynamic_ui_demo.sh

# Eraser tests
./test_eraser.sh
```

### Manual Testing

#### Test 1: Basic Eraser

```bash
ssh root@10.11.99.1

# Draw a rectangle
echo "pen rectangle 200 200 600 600" | lamp

# Erase it
echo "eraser fill 200 200 600 600 15" | lamp
```

#### Test 2: Component Drawing

```bash
# On your computer
python3 component_library.py export --symbol g1087 --output test/

# Deploy to tablet
scp test/g1087.svg root@10.11.99.1:/tmp/

# On tablet
python3 svg_to_lamp.py /tmp/g1087.svg 500 800 2.0 | lamp
```

#### Test 3: Interactive Selector

```bash
python3 component_selector.py

# Try commands:
n   # Next symbol
p   # Previous symbol
c   # Show current
e g1087   # Export resistor
```

---

## Configuration

### Component Library Config

Edit `component_library_config.json`:

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

**Fields**:
- `visibility`: `"viewed"` | `"cycled"` | `"hidden"`
- `name`: Human-readable name (optional)
- `category`: Group name (optional)
- `description`: Details (optional)

### Reset Configuration

```bash
# Delete and regenerate
rm component_library_config.json
python3 component_library.py init
```

---

## Troubleshooting

### Build Issues

**"okp not found"**
```bash
# Install okp transpiler
git clone https://github.com/raisjn/okp.git
# Follow installation instructions
```

**"arm compiler not found"**
```bash
sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf
```

**"Patch failed"**
```bash
# Clean and retry
cd resources/repos/rmkit
git reset --hard
cd ../../..
./build_lamp_enhanced.sh
```

### Deployment Issues

**"Connection refused"**
```bash
# Check USB connection
ping 10.11.99.1

# Or use WiFi IP
ssh root@192.168.1.XXX
```

**"Permission denied"**
```bash
ssh root@10.11.99.1 'chmod +x /opt/bin/lamp'
```

### Component Library Issues

**"Symbol not found"**
```bash
# List all available symbols
python3 component_library.py list | grep g1087
```

**"Nothing exported"**
```bash
# Check visibility is set
python3 component_library.py list --visibility cycled

# Set visibility
python3 component_library.py set g1087 cycled
```

**"Drawing looks wrong"**
```bash
# Adjust scale parameter (try 0.5 to 3.0)
python3 svg_to_lamp.py symbol.svg 500 800 0.8 | lamp
```

**"Config file corrupt"**
```bash
# Use example as template
cp component_library_config.example.json component_library_config.json
# Or regenerate
rm component_library_config.json
python3 component_library.py init
```

### Runtime Issues

**"Eraser not working"**
```bash
# Verify lamp version
ssh root@10.11.99.1 '/opt/bin/lamp --version'

# Check deployment
ssh root@10.11.99.1 'ls -l /opt/bin/lamp'

# Rebuild and redeploy
./build_lamp_enhanced.sh
scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/
```

**"Coordinates wrong"**
```
reMarkable display: 1404x1872 pixels
Touch input: 767x1023 (scaled)
Wacom input: 15725x20967 (professional stylus)

Use display coordinates for lamp commands.
```

---

## Uninstallation

### Step 1: Remove from reMarkable

```bash
ssh root@10.11.99.1
rm /opt/bin/lamp
```

### Step 2: Remove Configuration

```bash
rm component_library_config.json
```

### Step 3: Remove Exported Files

```bash
rm -rf exported_symbols/
rm -rf symbols/
rm -rf palette/
# Or whatever directories you created
```

### Step 4: Remove Local Build

```bash
# Clean rmkit build
cd resources/repos/rmkit
make clean
cd ../../..

# Or remove entire build
rm -rf resources/repos/rmkit/src/build/
```

### Step 5: Remove Repository (Optional)

```bash
cd ..
rm -rf lamp-v2/
```

### Step 6: Clean Git Branch (If Applicable)

```bash
# Switch to main branch
git checkout main

# Delete feature branch
git branch -D claude/custom-component-library-01MpXSzHcG2jmF4tpS793ZER
```

---

## File Locations

### On Your Computer

```
lamp-v2/
├── README.md                           # Overview
├── DEV_HISTORY.md                      # Development history
├── INSTALL.md                          # This file
├── component_library.py                # Library manager
├── component_selector.py               # Interactive selector
├── component_library_config.json       # Configuration (generated)
├── exported_symbols/                   # Exported SVGs (generated, gitignored)
├── svg_to_lamp.py                      # SVG converter
├── text_to_lamp.py                     # Text renderer
├── build_lamp_enhanced.sh              # Build script
├── test_eraser.sh                      # Tests
└── examples/
    ├── component_library_demo.sh       # Demo
    ├── dynamic_ui_demo.sh              # Demo
    └── svg_symbols/
        └── Electrical_symbols_library.svg  # 214 symbols
```

### On reMarkable

```
/opt/bin/lamp                           # Enhanced lamp binary
/home/root/                             # Optional test scripts
```

---

## Help

```bash
# Component library help
python3 component_library.py --help
python3 component_library.py list --help
python3 component_library.py export --help

# Component selector help
python3 component_selector.py --help

# SVG converter help
python3 svg_to_lamp.py --help

# Text renderer help
python3 text_to_lamp.py --help
```

---

## Additional Resources

- **README.md** - Project overview and quick start
- **DEV_HISTORY.md** - Development timeline and technical details
- Demo scripts in `examples/` directory
- Example SVG symbols in `examples/svg_symbols/`
- Example configuration in `component_library_config.example.json`
