# Quick Start Guide

Get up and running with lamp-v2 in 5 minutes.

## Prerequisites

```bash
# Install ARM cross-compiler
sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf

# Install okp transpiler
# See: https://github.com/raisjn/okp

# Python 3.9+ (usually pre-installed)
python3 --version
```

## 1. Build lamp with Eraser Support

```bash
./build_lamp_enhanced.sh
```

## 2. Deploy to reMarkable

```bash
# Find your tablet's IP (Settings → Help → Copyrights and licenses)
export RM_IP="10.11.99.1"

# Copy lamp binary
scp resources/rmkit/src/build/lamp root@$RM_IP:/opt/bin/

# Test connection
ssh root@$RM_IP "lamp --version"
```

## 3. Draw Your First Component

```bash
# Draw a resistor at position (500, 800)
python3 svg_to_lamp_improved.py components/R.svg 500 800 1.5 | ssh root@$RM_IP lamp
```

You should see a resistor appear on your reMarkable screen!

## 4. Draw a Complete Circuit

```bash
# Use the built-in example
python3 circuit_builder.py

# This creates rc_vdc_circuit.lamp
cat rc_vdc_circuit.lamp | ssh root@$RM_IP lamp
```

You should see a complete RC circuit with voltage source and ground!

## 5. Try Eraser Commands

```bash
# Test eraser line
echo "eraser line 100 100 500 500" | ssh root@$RM_IP lamp

# Test eraser rectangle
echo "eraser rectangle 600 100 1000 500" | ssh root@$RM_IP lamp

# Test fill area
echo "eraser fill 100 600 500 1000 8" | ssh root@$RM_IP lamp

# Clear everything with dense erasure
echo "eraser clear 0 0 1404 1872" | ssh root@$RM_IP lamp

# Draw circuit again
cat rc_vdc_circuit.lamp | ssh root@$RM_IP lamp
```

## Next Steps

### Draw Different Components

```bash
# Capacitor
python3 svg_to_lamp_improved.py components/C.svg 700 800 1.5 | ssh root@$RM_IP lamp

# Inductor
python3 svg_to_lamp_improved.py components/L.svg 900 800 1.5 | ssh root@$RM_IP lamp

# Op-amp
python3 svg_to_lamp_improved.py components/OPAMP.svg 500 1000 1.0 | ssh root@$RM_IP lamp
```

### Explore Available Components

```bash
ls components/
# Output: C.svg D.svg GND.svg L.svg OPAMP.svg P_CAP.svg R.svg VAC.svg VDC.svg ZD.svg
```

### Create Your Own Netlist

See `claude/*.net` for netlist examples:

```bash
cat claude/rc_filter.net
cat claude/voltage_divider.net
cat claude/inverting_amp.net
```

## Common Issues

### "Permission denied" when SSHing
Enable SSH on reMarkable and set root password.

### "lamp: command not found"
Make sure you deployed to `/opt/bin/` which is in PATH.

### Components not rendering correctly
Check SVG file exists and path is correct. Scale parameter affects size.

### Eraser not working
Requires firmware 3.15+. Rebuild lamp if you updated firmware.

## Keyboard Shortcuts

When connected via SSH, you can pipe commands directly:

```bash
# Alias for quick commands
alias lamp="ssh root@$RM_IP lamp"

# Now you can do:
echo "pen circle 500 800 100" | lamp
echo "eraser circle 500 800 50" | lamp
```

## Configuration

Edit `component_library.json` to show/hide components:

```json
{
  "symbols": {
    "g1087": {
      "visibility": "cycled",  // cycled, viewed, hidden
      "name": "resistor"
    }
  }
}
```

## Help

For more details, see [README.md](README.md)

For development history, check `claude/` and `old/` directories.
