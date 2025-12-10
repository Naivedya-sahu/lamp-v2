#!/bin/bash
# SVG Gallery - Quick Usage Guide

## Overview
The `svg_gallery.sh` script provides an interactive viewer for SVG files on your reMarkable 2 device.
It cycles through SVG files, displays them, and waits for user commands to erase and navigate.

## Basic Usage

### View all symbols in default folder
```bash
./svg_gallery.sh
```

### View symbols from a specific folder
```bash
./svg_gallery.sh ./examples/svg_symbols/Digital
```

### View with custom scale (auto-detection if not specified)
```bash
./svg_gallery.sh ./examples/svg_symbols 5
```

### Specify custom RM2 IP address
```bash
./svg_gallery.sh ./examples/svg_symbols 10 192.168.1.100
```

## Interactive Commands

While viewing a symbol, press:

| Command | Action |
|---------|--------|
| **ENTER** | Erase current symbol and show next |
| **p** | Go back to previous symbol |
| **r** | Redraw current symbol (re-send to RM2) |
| **s N** | Skip to symbol number N (e.g., `s 3` for 3rd symbol) |
| **q** | Quit gallery and exit |

## Examples

```bash
# Start digital logic gates gallery
./svg_gallery.sh ./examples/svg_symbols/Digital

# Output:
# ==========================================
# SVG Gallery - reMarkable 2 Viewer
# ==========================================
# Directory: ./examples/svg_symbols/Digital
# Found SVGs: 7 files
# Scale: auto
# Target: 10.11.99.1
#
# Testing SSH connection...
# ✓ Connected
#
# [1/7] AND.svg
# ✓ Sent (30 commands)
#
# Options:
#   [ENTER] - Erase and next
#   [p]     - Previous
#   [r]     - Redraw current
#   [s N]   - Skip to symbol N
#   [q]     - Quit
#
# Command: 
```

After pressing ENTER at the command prompt, AND.svg is erased and EXNOR.svg is displayed.

## Features

- **Auto-detection**: Automatically discovers all .svg files in directory
- **Recursive search**: Finds SVGs in subdirectories too
- **Progress display**: Shows [current/total] for each symbol
- **Scaling**: Supports custom scale factor or auto-scaling
- **Error handling**: Gracefully skips symbols that fail to render
- **SSH validation**: Tests connection to RM2 before starting gallery
- **Color output**: Color-coded messages for easy reading

## Screen Navigation Pattern

The gallery displays symbols in sorted order (alphabetically):

```
Folder: ./examples/svg_symbols/Digital/
1. AND.svg        → [1/7] AND.svg       (displayed, press ENTER for next)
2. EXNOR.svg      → [2/7] EXNOR.svg     (can jump with 's 2')
3. EXOR.svg       → [3/7] EXOR.svg
4. INV.svg        → [4/7] INV.svg
5. NAND.svg       → [5/7] NAND.svg
6. NOR.svg        → [6/7] NOR.svg
7. OR.svg         → [7/7] OR.svg
```

You can:
- Go forward: Press ENTER
- Go backward: Press 'p' 
- Jump to specific: Press 's 3' to jump to symbol 3
- Redraw: Press 'r' to see current symbol again
- Exit: Press 'q' to quit at any time

## Tips

### View all electrical symbols
```bash
./svg_gallery.sh ./examples/svg_symbols
```
This shows ~30 different electrical and logic symbols.

### Scale larger for detailed viewing
```bash
./svg_gallery.sh ./examples/svg_symbols 15
```

### Navigate quickly
Use `s N` command to jump: `s 15` goes to 15th symbol instantly

### Troubleshooting

If you get "Cannot connect to RM2":
1. Check RM2 is USB-connected or on network
2. For WiFi: Find IP with `sudo arp-scan -l | grep remarkable`
3. Try: `./svg_gallery.sh ./examples/svg_symbols 5 <YOUR_IP>`

If some symbols fail to render:
- Script auto-skips them
- Check terminal output for error details
- Redraw with 'r' to retry
