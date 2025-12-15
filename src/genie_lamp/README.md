# genie_lamp - Gesture Launcher with Lamp Integration

A fork of rmkit's genie gesture launcher that **removes the rm2fb dependency** and integrates with lamp for programmatic drawing on reMarkable 2.

## Key Differences from Original Genie

1. **No rm2fb Required**: Uses fixed screen dimensions (1404x1872) instead of querying framebuffer
2. **Lamp Integration**: Built-in helper function for executing lamp drawing commands
3. **Optimized for Drawing**: Test configuration demonstrates gesture-triggered drawing

## Why This Fork?

The original genie requires rm2fb to be running for framebuffer access. This fork:
- Removes that dependency for simpler deployment
- Is specifically designed for lamp command integration
- Facilitates testing of gesture detection with visual feedback via lamp

## Building

From the lamp-v2 root directory:

```bash
# Create symlink in rmkit src
cd resources/rmkit
ln -sf ../../src/genie_lamp src/

# Build
cd src/genie_lamp
make -f ../../Makefile compile TARGET=rm

# Copy to device
scp ../../build/genie_lamp root@10.11.99.1:/opt/bin/
```

## Configuration

Config file format is the same as original genie. Example:

```
# Three-finger tap to draw a square
gesture=tap
fingers=3
command=echo -e "pen down 500 500\npen move 900 500\npen move 900 900\npen move 500 900\npen move 500 500\npen up" | /opt/bin/lamp
duration=0
```

### Config Options

- **gesture**: `swipe` or `tap`
- **command**: Shell command to run (use lamp commands)
- **fingers**: Number of fingers (1-5)
- **zone**: Touch zone as normalized coordinates `x1 y1 x2 y2` (0.0-1.0)

Swipe-specific:
- **direction**: `up`, `down`, `left`, or `right`
- **distance**: Minimum swipe distance in pixels

Tap-specific:
- **duration**: Minimum hold time in seconds (0 for instant tap)

## Installation

```bash
# Copy binary
scp ../../build/genie_lamp root@10.11.99.1:/opt/bin/

# Copy test config
scp lamp_test.conf root@10.11.99.1:/opt/etc/genie_lamp.conf
```

## Usage

```bash
# Run with default config
ssh root@10.11.99.1 /opt/bin/genie_lamp /opt/etc/genie_lamp.conf

# Or in background
ssh root@10.11.99.1 "/opt/bin/genie_lamp /opt/etc/genie_lamp.conf &"
```

## Test Gestures (lamp_test.conf)

The included test configuration demonstrates:

1. **3-finger tap**: Draw a square (500,500 to 900,900)
2. **2-finger swipe right**: Draw a circle
3. **2-finger swipe left**: Draw a rectangle
4. **2-finger swipe up**: Draw a diagonal line
5. **2-finger swipe down**: Erase area
6. **1-finger long press (left side)**: Draw small square
7. **1-finger long press (right side)**: Draw small circle

## Lamp Command Integration

The gesture_parser includes a `run_lamp_commands()` helper function:

```cpp
void run_lamp_commands(string lamp_cmds):
  string cmd = "echo -e \"" + lamp_cmds + "\" | /opt/bin/lamp &"
  _ := system(c_str)
```

You can use this in custom gesture handlers or simply use shell commands in the config file.

## Lamp Commands Reference

Common lamp commands for gestures:

```bash
# Draw square
pen down X1 Y1
pen move X2 Y1
pen move X2 Y2
pen move X1 Y2
pen move X1 Y1
pen up

# Draw circle
pen circle CX CY R R

# Draw rectangle (shorthand)
pen rectangle X1 Y1 X2 Y2

# Draw line
pen line X1 Y1 X2 Y2

# Erase area
eraser clear X1 Y1 X2 Y2
```

## Architecture Notes

- Screen dimensions hardcoded to RM2 (1404x1872)
- No framebuffer access needed
- Touch input handling via rmkit's input system
- Lamp commands executed via shell system() calls
- Gesture detection runs independently of display updates

## Limitations

- Fixed screen dimensions (RM2 only)
- Zone coordinates still use normalized 0.0-1.0 format (converted to pixels)
- No visual feedback except through lamp drawing commands

## License

Same as rmkit (MIT License)
