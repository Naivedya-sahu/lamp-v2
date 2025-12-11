# lamp-v2

Circuit drawing system for reMarkable tablets with eraser support and netlist-based rendering.

## Features

- **Circuit Builder** - Draw circuits from SPICE netlists with auto-layout
- **Component Library** - 214 electrical symbols with anchor points
- **Eraser Support** - Programmatic erasing via BTN_TOOL_RUBBER events
- **SVG Rendering** - Convert SVG components to lamp drawing commands

## Quick Start

```bash
# Draw a circuit from netlist
python3 circuit_builder.py

# Draw single component
python3 svg_to_lamp_improved.py components/R.svg 500 800 1.0 | ssh root@10.11.99.1 lamp

# Build lamp with eraser support
./build_lamp_enhanced.sh
scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/
```

## Core Files

```
circuit_builder.py          # Circuit renderer with anchor points
component_definitions.py    # Component library (214 symbols)
svg_to_lamp_improved.py     # SVG to lamp converter
component_library.json      # Component configuration
component_definitions.json  # Component templates
```

## Directory Structure

```
lamp-v2/
├── circuit_builder.py              # Main circuit builder
├── component_definitions.py        # Component library
├── svg_to_lamp_improved.py         # SVG converter
├── build_lamp_enhanced.sh          # Build script
│
├── components/                     # Individual component SVGs
│   ├── R.svg, C.svg, L.svg        # Passive components
│   ├── VDC.svg, VAC.svg           # Sources
│   └── GND.svg, OPAMP.svg         # Other components
│
├── examples/                       # Examples and library
│   └── Electrical_symbols_library.svg  # 214 symbols
│
├── claude/                         # Development experiments (v2)
│   ├── netlist_parser.py          # SPICE netlist parser
│   ├── circuit_placer.py          # Layout optimizer
│   └── *.net                      # Example netlists
│
├── old/                            # Legacy code (v1)
└── resources/                      # rmkit source and docs
```

## Usage

### Draw Circuit from Netlist

```python
# Example netlist: rc_filter.net
V1 1 0 DC 5V
R1 1 2 10k
C1 2 0 100nF
.end
```

```bash
# Generate and draw
python3 circuit_builder.py  # Creates rc_vdc_circuit.lamp
ssh root@10.11.99.1 "cat > /tmp/circuit.lamp" < rc_vdc_circuit.lamp
ssh root@10.11.99.1 "lamp < /tmp/circuit.lamp"
```

### Draw Individual Components

```bash
# Resistor at (500, 800), scale 1.5
python3 svg_to_lamp_improved.py components/R.svg 500 800 1.5 | ssh root@10.11.99.1 lamp

# Capacitor
python3 svg_to_lamp_improved.py components/C.svg 700 800 1.5 | ssh root@10.11.99.1 lamp
```

### Eraser Commands

```bash
# Erase line
echo "eraser line 100 100 500 500" | ssh root@10.11.99.1 lamp

# Erase rectangle outline
echo "eraser rectangle 100 100 500 500" | ssh root@10.11.99.1 lamp

# Fill area with eraser (default 8px spacing)
echo "eraser fill 100 100 500 500" | ssh root@10.11.99.1 lamp

# Fill area with custom spacing
echo "eraser fill 100 100 500 500 10" | ssh root@10.11.99.1 lamp

# Dense clear (5px spacing for complete coverage)
echo "eraser clear 100 100 500 500" | ssh root@10.11.99.1 lamp

# Low-level eraser control
echo "eraser down 100 100" | ssh root@10.11.99.1 lamp
echo "eraser move 500 500" | ssh root@10.11.99.1 lamp
echo "eraser up" | ssh root@10.11.99.1 lamp
```

## Component Library

**Available Components:**
- **Passive:** R (Resistor), C (Capacitor), L (Inductor)
- **Sources:** VDC, VAC
- **Semiconductors:** D (Diode), ZD (Zener), OPAMP
- **Other:** GND (Ground), P_CAP (Polarized Capacitor)

**Component Format:**
```json
{
  "name": "Resistor",
  "width": 120,
  "height": 48,
  "anchors": [
    {"name": "left", "x": 0.0, "y": 0.5},
    {"name": "right", "x": 1.0, "y": 0.5}
  ],
  "svg_group_ids": ["g1087"]
}
```

## Development Versions

### v3 (Current) - Root Directory
Production code with circuit builder and anchor point system.
- `circuit_builder.py` - Circuit rendering with netlist support
- `component_definitions.py` - Component library
- `svg_to_lamp_improved.py` - SVG converter

### v2 - claude/ Directory
Experimental features developed with Claude Code.
- Netlist parser prototypes
- Layout optimization experiments
- Component placement algorithms

### v1 - old/ Directory
Legacy implementation.
- Original component library
- Early SVG converters
- Documentation archive

## Build Requirements

- **ARM Cross-compiler:** `gcc-arm-linux-gnueabihf`, `g++-arm-linux-gnueabihf`
- **okp Transpiler:** For .cpy file compilation
- **Python 3.9+:** Standard library only
- **reMarkable Tablet:** Firmware 3.15+

## Configuration

**component_library.json** - Component visibility settings
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

**component_definitions.json** - Component templates with dimensions and anchor points

## License

MIT License - Based on [rmkit](https://github.com/rmkit-dev/rmkit)

Electrical symbols: CC0 Public Domain (Wikimedia Commons)

## Links

- [rmkit](https://github.com/rmkit-dev/rmkit) - Original lamp tool
- [reMarkable 2](https://remarkable.com/) - Target device
