COMPONENT LIBRARY UI SYSTEM
===========================

ARCHITECTURE OVERVIEW (Simple Terms):

  Touch Screen → genie_lamp → Gesture Detection → State Machine → lamp Drawing
                                      ↓
                                  Update State
                                      ↓
                            Redraw UI with new state

WHAT IT DOES:
- Shows a UI box in bottom right corner (1000,1400 to 1404,1872)
- Lists electronic components from assets/components/
- Uses font glyphs from assets/font/ for text
- Navigate with gestures (page up/down, select)
- Preview selected component above the list
- All drawing done with lamp (pen commands)

COMPONENTS:

1. svg2lamp.sh
   - Converts SVG files to lamp pen commands
   - Handles M (move), L (line), C (curve) path commands
   - Supports offset and scaling

2. component_library.sh
   - Manages 16 electronic components (R, C, L, D, etc.)
   - Lists, counts, and renders components
   - Integrates with svg2lamp.sh

3. font_render.sh
   - Renders text using SVG font glyphs (A-Z, 0-9)
   - Automatic spacing and positioning
   - Scalable text rendering

4. ui_state.sh (STATE MACHINE)
   - Manages UI state (current page, selected item, mode)
   - State stored in /tmp/genie_ui/state.txt
   - Commands: init, redraw, next_page, prev_page, next_item, prev_item, select

   STATE VARIABLES:
   - page: Current page number (0-based)
   - selected: Currently selected item index
   - mode: "list" or "preview"

5. test_render_all.sh
   - Test script to render all components and fonts
   - Demonstrates rendering and erasing
   - Useful for testing lamp integration

6. ui.conf
   - Gesture configuration for genie_lamp
   - Maps gestures to UI commands

GESTURE CONTROLS:

  4-finger tap: Show/Refresh UI
  2-finger tap: Next Page
  3-finger tap: Select Component (toggle preview)
  5-finger tap: Next Item in List

STATE MACHINE FLOW:

  [INIT] → Build component list → Set defaults (page=0, selected=0, mode=list)
     ↓
  [IDLE] ← Wait for gesture
     ↓
  Gesture Detected → Update State → Redraw UI
     ↓
  [LIST MODE]
     - Show components on current page
     - Highlight selected item
     - Show page number
     ↓
  [PREVIEW MODE] (after selection)
     - Show list + preview of selected component above
     - Component drawn at larger scale

UI LAYOUT (Bottom Right Box):

  ┌─────────────────────────────┐  ← UI_Y (1400)
  │  PG 1/4              │
  │                             │
  │  [Preview Area]             │  ← Component preview when selected
  │      ╔═══╗                  │
  │      ║ R ║                  │
  │      ╚═══╝                  │
  │                             │
  ├─────────────────────────────┤
  │  > 1 R                      │  ← Selected item (marked with >)
  │    2 C                      │
  │    3 L                      │
  │    4 D                      │
  │    5 GND                    │
  └─────────────────────────────┘  ← UI_Y + UI_HEIGHT (1872)
  ↑                             ↑
  UI_X                    UI_X + UI_WIDTH
  (1000)                       (1404)

SETUP & USAGE:

1. Initialize UI:
   bash /home/user/lamp-v2/scripts/ui_state.sh init
   bash /home/user/lamp-v2/scripts/ui_state.sh redraw

2. Test rendering:
   bash /home/user/lamp-v2/scripts/test_render_all.sh

3. Deploy gesture config:
   scp src/genie_lamp/ui.conf root@10.11.99.1:/opt/etc/genie_ui.conf

4. Run genie with UI config:
   ssh root@10.11.99.1 /opt/bin/genie_lamp /opt/etc/genie_ui.conf

5. Or update systemd service to use ui.conf:
   Edit /etc/systemd/system/genie_lamp.service
   Change: ExecStart=/opt/bin/genie_lamp /opt/etc/genie_ui.conf
   Then: systemctl daemon-reload && systemctl restart genie_lamp

MANUAL TESTING:

# Show UI
bash scripts/ui_state.sh init
bash scripts/ui_state.sh redraw

# Navigate
bash scripts/ui_state.sh next_page
bash scripts/ui_state.sh prev_page
bash scripts/ui_state.sh next_item
bash scripts/ui_state.sh prev_item

# Select/Preview
bash scripts/ui_state.sh select

# Check state
bash scripts/ui_state.sh state

COMPONENT LIST (16 items):

1. C       - Capacitor
2. D       - Diode
3. GND     - Ground
4. L       - Inductor
5. NPN_BJT - NPN Transistor
6. N_MOSFET - N-Channel MOSFET
7. OPAMP   - Op-Amp
8. PNP_BJT - PNP Transistor
9. P_CAP   - Polarized Capacitor
10. P_MOSFET - P-Channel MOSFET
11. R       - Resistor
12. SW_CL   - Switch Closed
13. SW_OP   - Switch Open
14. VAC     - AC Voltage Source
15. VDC     - DC Voltage Source
16. ZD      - Zener Diode

With 5 items per page = 4 pages total

DEPENDENCIES:
- lamp (modified version with erase support)
- bash, sed, awk, bc (standard Linux tools)
- genie_lamp (gesture detector)
- No jq required!

FILES:
  scripts/svg2lamp.sh           SVG to lamp converter
  scripts/component_library.sh  Component manager
  scripts/font_render.sh        Text renderer
  scripts/ui_state.sh           State machine
  scripts/test_render_all.sh    Test script
  src/genie_lamp/ui.conf        Gesture config
  assets/components/*.svg       Component library
  assets/font/*.svg             Font glyphs
