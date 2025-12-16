# Quick Start Guide - Component Library System

Get the interactive component UI running on your reMarkable 2 in 10 minutes.

## Prerequisites

**On Development Machine:**
- Python 3.9+ with `svgpathtools` installed
- Bash shell
- SSH access to RM2

**On reMarkable 2:**
- SSH enabled (Settings > Storage > USB web interface)
- `lamp` binary at `/opt/bin/lamp`
- `genie_lamp` binary at `/opt/bin/genie_lamp`
- USB or WiFi connection

## Quick Install

From `src/comp_lib/` directory:

```bash
# Make scripts executable
chmod +x deploy.sh build/*.sh test/*.sh

# Run deployment (default IP: 10.11.99.1)
./deploy.sh

# Or specify custom IP
./deploy.sh 192.168.1.100
```

**That's it!** System is now active on your RM2.

## First Use

### 1. Activate Component Mode

On your reMarkable 2:

**Place all 5 fingers on screen and tap simultaneously**

- Green corner indicator appears (bottom-right)
- System is now in Component Mode
- Xochitl is temporarily disabled

### 2. Open the Palette

**4-finger tap** anywhere on screen

- Vertical list appears on right side showing components:
  ```
  R    ← First item highlighted
  C
  L
  D
  ...
  ```

### 3. Navigate the List

**3-finger swipe up/down** in palette area (right side)

- List scrolls
- Highlight moves to different components

### 4. Select a Component

**2-finger tap** in palette area

- Highlighted component becomes selected
- Highlight box intensifies

### 5. Place the Component

**2-finger tap** anywhere on left side (canvas)

- Selected component appears where you tapped
- Ready to place another

### 6. Adjust Scale

**3-finger swipe left/right** on canvas

- Left = smaller (0.25x - 3.0x)
- Right = larger
- Next placement uses new scale

### 7. Clear Everything

**4-finger swipe up**

- All drawings erased
- Palette remains if open

### 8. Deactivate Mode

**4-finger swipe down**

- Everything clears
- Green corner disappears
- Returns to normal Xochitl

## Gesture Quick Reference

### Mode Control (Always Active)
| Gesture | Action |
|---------|--------|
| 5-finger tap | Activate component mode |
| 4-finger swipe down | Deactivate mode |

### UI Control (Active in Mode Only)
| Gesture | Zone | Action |
|---------|------|--------|
| 4-finger tap | Anywhere | Toggle palette |
| 3-finger swipe up/down | Palette | Scroll list |
| 2-finger tap | Palette | Select component |
| 2-finger tap | Canvas | Place component |
| 3-finger swipe left/right | Canvas | Scale down/up |
| 4-finger swipe up | Anywhere | Clear screen |

**Zones:**
- Palette = Right 28% of screen (1004px to 1404px)
- Canvas = Left 72% of screen (0px to 1004px)

## Why These Gestures?

**No Xochitl conflicts:**
- No 1-finger taps (avoids writing interference)
- No 2-finger swipes (avoids zoom/page navigation)
- No 3-finger taps (avoids undo/redo)
- Operates as dedicated mode with unique activation

## Troubleshooting

### Mode won't activate (5-finger tap does nothing)

```bash
# Check activation service
ssh root@10.11.99.1 systemctl status symbol_ui_activation.service

# View logs
ssh root@10.11.99.1 journalctl -u symbol_ui_activation.service -f

# Restart service
ssh root@10.11.99.1 systemctl restart symbol_ui_activation.service
```

### Palette not appearing (4-finger tap does nothing)

```bash
# Check if mode is active
ssh root@10.11.99.1 test -f /home/root/.symbol_ui_mode && echo "Mode active" || echo "Mode inactive"

# Activate mode manually
ssh root@10.11.99.1 /opt/bin/symbol_ui_mode activate

# Test controller directly
ssh root@10.11.99.1 "/opt/bin/symbol_ui_controller toggle_palette | /opt/bin/lamp"
```

### Components not placing

```bash
# Test placement manually
ssh root@10.11.99.1 "TAP_X=500 TAP_Y=500 /opt/bin/symbol_ui_controller place_component | /opt/bin/lamp"

# Check library exists
ssh root@10.11.99.1 ls -lh /opt/etc/symbol_library.json
```

### Mode stuck active

```bash
# Force deactivate
ssh root@10.11.99.1 /opt/bin/symbol_ui_mode deactivate

# Check status
ssh root@10.11.99.1 /opt/bin/symbol_ui_mode status
```

## Progressive Testing

If deployment fails or gestures don't work, test each stage:

```bash
cd test/

# Stage 1: Build validation
./test_stage1_library.sh

# Stage 2: RM2 connectivity
./test_stage2_connectivity.sh 10.11.99.1

# Stage 3: Mode manager
./test_stage3_mode.sh 10.11.99.1

# Stage 4: Controller logic
./test_stage4_controller.sh 10.11.99.1

# Stage 5: Gesture integration
./test_stage5_gestures.sh 10.11.99.1

# Stage 6: Full system
./test_stage6_full.sh 10.11.99.1
```

Each stage validates specific functionality.

## Component Library

**16 Circuit Components:**
- R, C, L - Passive components
- D, ZD - Diodes
- GND - Ground
- VDC, VAC - Voltage sources
- OPAMP - Op-amp
- NPN_BJT, PNP_BJT - BJT transistors
- N_MOSFET, P_MOSFET - MOSFETs
- P_CAP - Polarized capacitor
- SW_OP, SW_CL - Switches

**62 Font Glyphs:**
- 0-9 (digits)
- A-Z (uppercase)
- a-z (lowercase)

## Common Questions

**Q: Why 5-finger tap for activation?**
A: Unique gesture that won't accidentally trigger during normal writing/drawing.

**Q: Can I write while in component mode?**
A: Not recommended. The system captures gestures before Xochitl. Deactivate mode first.

**Q: How do I know if mode is active?**
A: Green corner indicator (bottom-right 34×34px square).

**Q: What happens to my drawings when I deactivate?**
A: They remain on screen. Mode only controls the UI, not your drawn content.

**Q: Can I use this alongside other apps?**
A: Yes, but only one instance of genie_lamp can run at a time.

## Updating

### After modifying gestures:

```bash
scp config/symbol_ui_main.conf root@10.11.99.1:/opt/etc/
ssh root@10.11.99.1 systemctl restart symbol_ui_main.service
```

### After modifying controller:

```bash
scp src/symbol_ui_controller.py root@10.11.99.1:/opt/bin/symbol_ui_controller
```

### After adding components:

```bash
# Rebuild library
python3 build/build_library.py ../../assets/components ../../assets/font symbol_library.json

# Redeploy
scp symbol_library.json root@10.11.99.1:/opt/etc/
```

## Uninstalling

```bash
ssh root@10.11.99.1 "
  systemctl stop symbol_ui_activation.service symbol_ui_main.service
  systemctl disable symbol_ui_activation.service symbol_ui_main.service
  rm /etc/systemd/system/symbol_ui_*.service
  rm /opt/bin/symbol_ui_mode /opt/bin/symbol_ui_controller
  rm /opt/etc/symbol_library.json
  rm /opt/etc/symbol_ui_*.conf
  rm /home/root/.symbol_ui_*
  systemctl daemon-reload
"
```

## Next Steps

1. **Practice gestures**: Try all gestures from quick reference
2. **Experiment with scale**: Place same component at different scales
3. **Read full docs**: See `README.md` and `ARCHITECTURE.md`
4. **Check test scripts**: Understand each system component
5. **Add custom components**: Create SVGs and rebuild library

## Support

- Full docs: `README.md`
- Technical details: `ARCHITECTURE.md`
- Testing guide: `test/` directory
- Main lamp-v2: `../../README.md`

---

**Get drawing circuits on your reMarkable 2!**
