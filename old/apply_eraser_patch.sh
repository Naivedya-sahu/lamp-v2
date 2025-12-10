#!/bin/bash
# Manual patch application for lamp eraser support
# Run this from lamp-v2 directory

set -e

LAMP_FILE="resources/repos/rmkit/src/lamp/main.cpy"

echo "=== Manual Eraser Patch Application ==="

# Backup
echo "Creating backup..."
cp "$LAMP_FILE" "$LAMP_FILE.backup"

# Find line numbers
LINE_PEN_UP=$(grep -n "^def btn_press" "$LAMP_FILE" | head -1 | cut -d: -f1)
LINE_PEN_RECT=$(grep -n "^void pen_draw_line" "$LAMP_FILE" | head -1 | cut -d: -f1)
LINE_ACTION=$(grep -n 'else if tool == "finger":' "$LAMP_FILE" | head -1 | cut -d: -f1)

echo "Found insertion points:"
echo "  - Eraser functions before line $LINE_PEN_UP (def btn_press)"
echo "  - Eraser drawing functions before line $LINE_PEN_RECT (pen_draw_line)"
echo "  - Eraser commands before line $LINE_ACTION (finger tool)"

# Create temporary file with eraser functions
cat > /tmp/eraser_funcs.txt << 'EOFFUNCS'

// ============================================
// ERASER SUPPORT
// ============================================

vector<input_event> eraser_clear():
  vector<input_event> ev
  ev.push_back(input_event{ type:EV_ABS, code:ABS_X, value: -1 })
  ev.push_back(input_event{ type:EV_ABS, code:ABS_DISTANCE, value: -1 })
  ev.push_back(input_event{ type:EV_ABS, code:ABS_PRESSURE, value: -1})
  ev.push_back(input_event{ type:EV_ABS, code:ABS_Y, value: -1 })
  ev.push_back(input_event{ type:EV_SYN, code:SYN_REPORT, value:1 })
  return ev

vector<input_event> eraser_down(int x, y, points=10):
  vector<input_event> ev
  ev.push_back(input_event{ type:EV_SYN, code:SYN_REPORT, value:1 })
  ev.push_back(input_event{ type:EV_KEY, code:BTN_TOOL_RUBBER, value: 1 })
  ev.push_back(input_event{ type:EV_KEY, code:BTN_TOUCH, value: 1 })
  ev.push_back(input_event{ type:EV_ABS, code:ABS_Y, value: get_pen_x(x) })
  ev.push_back(input_event{ type:EV_ABS, code:ABS_X, value: get_pen_y(y) })
  ev.push_back(input_event{ type:EV_ABS, code:ABS_DISTANCE, value: 0 })
  ev.push_back(input_event{ type:EV_ABS, code:ABS_PRESSURE, value: 4000 })
  ev.push_back(input_event{ type:EV_SYN, code:SYN_REPORT, value:1 })
  for int i = 0; i < points; i++:
    ev.push_back(input_event{ type:EV_ABS, code:ABS_PRESSURE, value: 4000 })
    ev.push_back(input_event{ type:EV_ABS, code:ABS_PRESSURE, value: 4001 })
    ev.push_back(input_event{ type:EV_SYN, code:SYN_REPORT, value:1 })
  return ev

vector<input_event> eraser_move(int ox, oy, x, y, int points=10):
  ev := eraser_down(ox, oy)
  double dx = float(x - ox) / float(points)
  double dy = float(y - oy) / float(points)
  ev.push_back(input_event{ type:EV_SYN, code:SYN_REPORT, value:1 })
  for int i = 0; i <= points; i++:
    ev.push_back(input_event{ type:EV_ABS, code:ABS_Y, value: get_pen_x(ox + (i*dx)) })
    ev.push_back(input_event{ type:EV_ABS, code:ABS_X, value: get_pen_y(oy + (i*dy)) })
    ev.push_back(input_event{ type:EV_SYN, code:SYN_REPORT, value:1 })
  return ev

vector<input_event> eraser_up():
  vector<input_event> ev
  ev.push_back(input_event{ type:EV_SYN, code:SYN_REPORT, value:1 })
  ev.push_back(input_event{ type:EV_KEY, code:BTN_TOOL_RUBBER, value: 0 })
  ev.push_back(input_event{ type:EV_KEY, code:BTN_TOUCH, value: 0 })
  ev.push_back(input_event{ type:EV_SYN, code:SYN_REPORT, value:1 })
  return ev

// ============================================
EOFFUNCS

# Create eraser drawing functions
cat > /tmp/eraser_draw.txt << 'EOFDRAW'

// Eraser drawing functions
void eraser_draw_rectangle(int x1, y1, x2, y2):
  if x2 == -1:
    x2 = pen_x
    y2 = pen_y
  debug "ERASING RECT", x1, y1, x2, y2
  act_on_line("eraser down " + to_string(x1) + " " + to_string(y1))
  act_on_line("eraser move " + to_string(x1) + " " + to_string(y2))
  act_on_line("eraser move " + to_string(x2) + " " + to_string(y2))
  act_on_line("eraser move " + to_string(x2) + " " + to_string(y1))
  act_on_line("eraser move " + to_string(x1) + " " + to_string(y1))
  act_on_line("eraser up ")

void eraser_draw_line(int x1, y1, x2, y2):
  if x2 == -1:
    x2 = pen_x
    y2 = pen_y
  debug "ERASING LINE", x1, y1, x2, y2
  act_on_line("eraser down " + to_string(x1) + " " + to_string(y1))
  act_on_line("eraser move " + to_string(x2) + " " + to_string(y2))
  act_on_line("eraser up")

void eraser_fill_area(int x1, y1, x2, y2, int spacing=20):
  debug "ERASING AREA", x1, y1, x2, y2
  for int y = y1; y <= y2; y += spacing:
    act_on_line("eraser down " + to_string(x1) + " " + to_string(y))
    act_on_line("eraser move " + to_string(x2) + " " + to_string(y))
    act_on_line("eraser up")

EOFDRAW

# Create eraser command parsing
cat > /tmp/eraser_cmds.txt << 'EOFCMDS'

  // ERASER TOOL
  else if tool == "eraser":
    if action == "down":
      ss >> x >> y
      write_events(pen_fd, eraser_down(x, y))
      pen_x = x
      pen_y = y
    else if action == "move":
      ss >> x >> y
      write_events(pen_fd, eraser_move(pen_x, pen_y, x, y))
      pen_x = x
      pen_y = y
    else if action == "up":
      write_events(pen_fd, eraser_up())
    else if action == "line":
      ss >> ox >> oy >> x >> y
      eraser_draw_line(ox, oy, x, y)
    else if action == "rectangle":
      ss >> ox >> oy >> x >> y
      eraser_draw_rectangle(ox, oy, x, y)
    else if action == "fill":
      ss >> ox >> oy >> x >> y
      int spacing = 20
      if len(tokens) == 7:
        spacing = stoi(tokens[6])
      eraser_fill_area(ox, oy, x, y, spacing)
    else if action == "clear":
      ss >> ox >> oy >> x >> y
      eraser_fill_area(ox, oy, x, y, 10)

EOFCMDS

# Apply patches using sed
echo "Inserting eraser functions..."
sed -i "${LINE_PEN_UP}r /tmp/eraser_funcs.txt" "$LAMP_FILE"

# Recalculate line numbers after first insertion
LINE_PEN_RECT=$(grep -n "^void pen_draw_line" "$LAMP_FILE" | head -1 | cut -d: -f1)
echo "Inserting eraser drawing functions..."
sed -i "$((LINE_PEN_RECT))r /tmp/eraser_draw.txt" "$LAMP_FILE"

# Recalculate line numbers after second insertion
LINE_ACTION=$(grep -n 'else if tool == "finger":' "$LAMP_FILE" | head -1 | cut -d: -f1)
echo "Inserting eraser command parsing..."
sed -i "$((LINE_ACTION))r /tmp/eraser_cmds.txt" "$LAMP_FILE"

# Verify
echo ""
echo "✓ Patch applied successfully!"
echo ""
echo "Verification:"
grep -c "BTN_TOOL_RUBBER" "$LAMP_FILE" && echo "  ✓ Eraser tool references found"
grep -c "eraser_down" "$LAMP_FILE" && echo "  ✓ Eraser functions found"
grep -c "eraser_fill_area" "$LAMP_FILE" && echo "  ✓ Eraser drawing functions found"

echo ""
echo "Backup saved to: $LAMP_FILE.backup"
echo "Ready to build!"
