# Test Scripts - Fallback System

Direct lamp command scripts that work without Python dependencies.

## Scripts

### test_components_simple.sh
**Purpose**: Basic test - 3 components, bottom right
**Dependencies**: None (pure bash + SSH)

```bash
./test_components_simple.sh [RM2_IP]
```

**What it does:**
- Draws resistor (zigzag)
- Draws capacitor (parallel plates)
- Draws ground symbol
- Tests eraser fill
- All at bottom right: (850,1600) to (1350,1850)

### test_components_labeled.sh
**Purpose**: Complete test with labels
**Dependencies**: None (pure bash + SSH)

```bash
./test_components_labeled.sh [RM2_IP]
```

**What it does:**
- Draws test area bounding box
- Draws 3 components with labels (R, C, GND)
- Adds title text
- Tests eraser fill (8px spacing)
- Tests eraser clear (3px spacing)

### test_components_ssh.sh
**Purpose**: Advanced test with arithmetic scaling
**Dependencies**: bc (for coordinate scaling)

```bash
./test_components_ssh.sh [RM2_IP]
```

**What it does:**
- Draws components with configurable scaling
- More accurate coordinate calculations
- Full eraser test

## Default Settings

**RM2 Screen**: 1404×1872 pixels

**Test Area** (bottom right):
- X: 850 to 1350 (500px wide)
- Y: 1600 to 1850 (250px tall)

**Component Positions**:
```
Resistor:   (900, 1650)
Capacitor:  (900, 1730)
Ground:     (1050, 1650) or (1200, 1650)
```

**IP Addresses**:
- USB: `10.11.99.1` (default)
- WiFi: Check Settings → Help → Copyrights

## Usage Examples

### Basic Test
```bash
# USB connection
./test_components_simple.sh

# WiFi connection
./test_components_simple.sh 192.168.1.XXX
```

### With Labels
```bash
./test_components_labeled.sh
```

### Custom IP
```bash
RM2_IP=192.168.1.100 ./test_components_simple.sh
```

## What This Tests

### Drawing
- ✓ Basic shapes (lines, rectangles)
- ✓ Complex paths (zigzag resistor)
- ✓ Multi-line symbols (capacitor, ground)
- ✓ Text/labels (simple letter strokes)

### Erasing
- ✓ Fill (area erase with spacing)
- ✓ Clear (dense erase for complete removal)
- ✓ Both spacing options (8px and 3px)

### Integration
- ✓ SSH connectivity
- ✓ Lamp binary deployment
- ✓ Command sequencing
- ✓ Coordinate system

## Fallback System

**Use when:**
- Python scripts fail
- svg_to_lamp.py has issues
- text_to_lamp.py doesn't work
- Need quick manual test
- Debugging coordinate problems

**Advantages:**
- No Python required
- No SVG parsing
- Direct lamp commands
- Easy to debug
- Fast execution
- Minimal dependencies

## Troubleshooting

### "Cannot connect"
```bash
# Test SSH
ssh root@10.11.99.1 'echo Connected'

# Find WiFi IP
# On RM2: Settings → Help → Copyrights (bottom)
```

### "lamp not found"
```bash
# Check lamp location
ssh root@10.11.99.1 'which lamp'
ssh root@10.11.99.1 'ls -la /opt/bin/lamp'

# Deploy lamp
scp resources/repos/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/
```

### Nothing appears on screen
```bash
# Wake screen
# Tap RM2 screen

# Check lamp process
ssh root@10.11.99.1 'ps aux | grep lamp'

# Try manual command
ssh root@10.11.99.1 'echo "pen line 100 100 500 500" | /opt/bin/lamp'
```

### Components in wrong location
- Check RM2 screen is 1404×1872
- Verify lamp uses display coordinates (not touch coordinates)
- Bottom right starts at ~850,1600
- Adjust X/Y values in script

## Modifying Scripts

### Change Position
Edit these variables:
```bash
RESISTOR_X=900    # Move left/right
RESISTOR_Y=1650   # Move up/down
```

### Change Size
Edit scale or coordinate offsets:
```bash
# Instead of: pen move 940 1650
# Use:        pen move 960 1650  (20px bigger)
```

### Add Component
Copy a draw function and change coordinates:
```bash
echo "Drawing inductor..."
lamp_cmd "pen circle 1200 1800 30"  # Coil representation
```

## Integration with Python Tools

These scripts complement the Python tools:

**If Python works:**
```bash
python3 svg_to_lamp.py symbol.svg 900 1650 2.0 | ssh root@10.11.99.1 /opt/bin/lamp
```

**If Python fails:**
```bash
./test_components_simple.sh  # Use hardcoded commands
```

## Performance

**Execution time**: ~3-5 seconds
**Network**: SSH overhead ~100-200ms per command
**Drawing**: ~10-20ms per stroke

**Optimization tip**: Combine multiple commands in one SSH session:
```bash
ssh root@$RM2_IP "$LAMP" << EOF
pen down 900 1650
pen move 1000 1650
pen up
EOF
```

## Notes

- Scripts use `set -e` - will stop on first error
- Interactive prompts allow inspection between steps
- Sleep delays prevent command queue overflow
- Color output (green/blue) for better visibility
- All coordinates are display pixels (not Wacom units)

## License

Same as lamp-v2 project (MIT)
