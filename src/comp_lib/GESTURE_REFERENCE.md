# Gesture Reference Guide

Complete gesture map for Component Library UI system.

## Design Principle

**Conflict-Free Operation**: All gestures use 2+ fingers and avoid Xochitl's patterns:
- Xochitl uses: 2-finger swipes (zoom/page), 3-finger tap (undo)
- We use: 5-finger tap (mode), 4-finger gestures, 3-finger swipes, 2-finger taps

## Mode System

### Normal Mode (Default)
- Xochitl gestures work normally
- Only activation gesture is active
- Writing/reading unaffected

### Component Mode (Activated)
- Main UI gestures active
- Green corner indicator visible
- Xochitl gestures disabled

## Activation Gestures (Always Available)

| Gesture | Action | Visual Feedback |
|---------|--------|-----------------|
| **5-finger tap** | Enter Component Mode | Green corner appears |
| **4-finger swipe down** | Exit Component Mode | Green corner disappears |

## Main UI Gestures (When Component Mode Active)

### Palette Control

| Gesture | Zone | Action |
|---------|------|--------|
| **4-finger tap** | Anywhere | Show/hide palette |
| **3-finger swipe up** | Palette (right 28%) | Scroll list up |
| **3-finger swipe down** | Palette (right 28%) | Scroll list down |
| **2-finger tap** | Palette (right 28%) | Select component |

### Component Placement

| Gesture | Zone | Action |
|---------|------|--------|
| **2-finger tap** | Canvas (left 72%) | Place component |
| **3-finger swipe right** | Canvas | Scale up |
| **3-finger swipe left** | Canvas | Scale down |
| **3-finger swipe down** | Canvas | Undo |

### System Actions

| Gesture | Zone | Action |
|---------|------|--------|
| **4-finger swipe up** | Anywhere | Clear screen |
| **2-finger swipe down** | Anywhere | Cancel selection |

## Screen Zones

```
┌─────────────────────────┬──────────────┐
│                         │              │
│                         │              │
│     CANVAS ZONE         │   PALETTE    │
│     (0 to 1004px)       │   ZONE       │
│     72% of screen       │   (1004-1404)│
│                         │   28% width  │
│                         │              │
│  2-finger tap: Place    │  4-finger:   │
│  3-finger swipe: Scale  │    Toggle    │
│  3-finger down: Undo    │  3-finger:   │
│                         │    Scroll    │
│                         │  2-finger:   │
│                         │    Select    │
└─────────────────────────┴──────────────┘
```

## Gesture Details

### 5-Finger Tap (Mode Activation)
- **How**: Place all 5 fingers on screen simultaneously, then lift
- **Why 5 fingers**: Extremely unique, won't trigger during writing
- **Feedback**: Immediate green corner indicator (34×34px)
- **Alternative**: If difficult, can trigger from button (see manual)

### 4-Finger Gestures
- **Tap**: Quick simultaneous touch with 4 fingers
- **Swipe**: 4 fingers moving together in same direction
- **Minimum distance**: 200px for swipes

### 3-Finger Gestures  
- **Swipes only** (no 3-finger taps to avoid Xochitl conflict)
- **Zones matter**: Same gesture does different things in different zones
- **Minimum distance**: 100px in palette, 150px in canvas

### 2-Finger Gestures
- **Taps only** (no 2-finger swipes to avoid Xochitl zoom/page)
- **Duration**: Quick tap, not hold
- **Zone-dependent**: Tap location determines action

## Workflow Examples

### Example 1: Place a Resistor

```
1. 5-finger tap anywhere
   → Green corner appears (Component Mode active)

2. 4-finger tap anywhere
   → Palette appears on right side

3. 3-finger swipe down in palette
   → Scroll to "R" (resistor)

4. 2-finger tap in palette
   → "R" is selected (highlighted)

5. 2-finger tap at (500, 600) in canvas
   → Resistor appears at that location

6. 4-finger swipe down anywhere
   → Exit Component Mode, green corner disappears
```

### Example 2: Build Circuit with Scaling

```
1. 5-finger tap → Activate
2. 4-finger tap → Show palette
3. Select "VDC" (voltage source)
4. 3-finger swipe right in canvas twice → Scale up 2×
5. 2-finger tap at (200, 400) → Place voltage source
6. Select "R" (resistor)
7. 3-finger swipe left in canvas once → Scale down 1×
8. 2-finger tap at (500, 400) → Place resistor
9. Continue adding components...
10. 4-finger swipe down → Exit mode
```

### Example 3: Mistake Recovery

```
1. Placed wrong component
2. 3-finger swipe down in canvas → Undo
3. Select correct component
4. 2-finger tap → Place correctly

OR:

1. Made several mistakes
2. 4-finger swipe up → Clear entire screen
3. Start over
```

## Gesture Detection Timing

| Gesture Type | Detection Time | User Perception |
|--------------|----------------|-----------------|
| Tap | ~50ms | Instant |
| Swipe start | ~100ms | Very fast |
| Command execution | ~150ms | Fast |
| **Total latency** | **~300ms** | Acceptable |

## Gesture Tips

### For Best Recognition:

**Taps:**
- Touch all fingers simultaneously
- Lift together quickly
- Don't hold (< 0.5 seconds)

**Swipes:**
- Keep fingers in contact with screen
- Move smoothly in one direction
- Lift together at end
- Minimum distance: 100-200px depending on gesture

**Zones:**
- Palette zone is right 28% of screen
- Canvas zone is left 72% of screen
- Zone boundaries are soft, not pixel-perfect

### If Gestures Not Detecting:

1. **Check mode**: Green corner visible = Component Mode active
2. **Finger count**: Count fingers carefully (5 for activation!)
3. **Zone**: Make sure you're in the correct zone
4. **Distance**: Swipes need minimum distance
5. **Speed**: Not too fast, not too slow

## Gesture Conflicts Matrix

| Our Gesture | Xochitl Gesture | Conflict? |
|-------------|-----------------|-----------|
| 5-finger tap | (none) | ✓ Safe |
| 4-finger any | (none) | ✓ Safe |
| 3-finger swipe | (none) | ✓ Safe |
| 3-finger tap | Undo | ✗ Avoided |
| 2-finger tap | (none) | ✓ Safe |
| 2-finger swipe | Zoom/Page | ✗ Avoided |
| 1-finger tap | Write | ✗ Avoided |

**Result**: Zero conflicts with Xochitl when properly implemented.

## Advanced: Custom Gestures

To add custom gestures, edit `/opt/etc/symbol_ui_main.conf`:

```conf
# Example: 3-finger tap in canvas to rotate component
gesture=tap
fingers=3
zone=0.0 0.0 0.72 1.0
command=/opt/bin/symbol_ui_controller rotate_cw
duration=0
```

Then restart: `systemctl restart symbol_ui_main.service`

## Troubleshooting Gestures

### Activation Not Working
```bash
# Check activation service
ssh root@10.11.99.1 systemctl status symbol_ui_activation.service

# Test manually
ssh root@10.11.99.1 /opt/bin/symbol_ui_mode activate
```

### Main Gestures Not Working
```bash
# Check if in Component Mode
ssh root@10.11.99.1 test -f /home/root/.symbol_ui_mode && echo "Active" || echo "Inactive"

# Check main service
ssh root@10.11.99.1 systemctl status symbol_ui_main.service
```

### Specific Gesture Not Detected
```bash
# View gesture config
ssh root@10.11.99.1 cat /opt/etc/symbol_ui_main.conf | grep -A5 "YOUR_GESTURE"

# Monitor input events
ssh root@10.11.99.1 cat /dev/input/event2
```

## Reference Card (Printable)

```
╔══════════════════════════════════════════╗
║     COMPONENT LIBRARY UI GESTURES        ║
╠══════════════════════════════════════════╣
║ MODE CONTROL                             ║
║  5-finger tap        → Activate          ║
║  4-finger swipe ↓    → Deactivate        ║
╠══════════════════════════════════════════╣
║ PALETTE (Right Side)                     ║
║  4-finger tap        → Show/Hide         ║
║  3-finger swipe ↑↓   → Scroll            ║
║  2-finger tap        → Select            ║
╠══════════════════════════════════════════╣
║ CANVAS (Left Side)                       ║
║  2-finger tap        → Place             ║
║  3-finger swipe →←   → Scale             ║
║  3-finger swipe ↓    → Undo              ║
╠══════════════════════════════════════════╣
║ SYSTEM                                   ║
║  4-finger swipe ↑    → Clear All         ║
║  2-finger swipe ↓    → Cancel            ║
╚══════════════════════════════════════════╝
```
