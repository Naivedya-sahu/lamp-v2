#!/usr/bin/env python3
"""
symbol_ui_controller.py - Symbol palette UI state controller
Manages UI state, renders palette, handles gestures, generates lamp commands
Updated with conflict-free zones and gestures
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Screen dimensions for reMarkable 2
SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

# Canvas area (left 72%)
CANVAS_WIDTH = 1004
CANVAS_X1 = 0
CANVAS_X2 = 1004

# UI panel (right 28%)
UI_PANEL_WIDTH = 400
UI_PANEL_X = 1004
UI_PANEL_Y = 0
UI_PANEL_HEIGHT = SCREEN_HEIGHT

# Item sizing
UI_ITEM_HEIGHT = 100
UI_VISIBLE_ITEMS = 16
UI_TEXT_SCALE = 4
UI_MARGIN = 30

@dataclass
class UIState:
    """UI state management"""
    palette_visible: bool = False
    selected_component: Optional[str] = None
    scroll_offset: int = 0
    rotation: int = 0  # 0, 90, 180, 270
    scale: float = 1.0
    history: List[Dict] = field(default_factory=list)
    component_list: List[str] = field(default_factory=list)

class SymbolUIController:
    def __init__(self, library_path: Path, state_file: Path):
        self.library_path = library_path
        self.state_file = state_file
        self.state = self.load_state()
        self.library = self.load_library()
        
        # Build component list
        if self.library and "components" in self.library:
            self.state.component_list = sorted(self.library["components"].keys())
    
    def load_library(self) -> Dict:
        """Load component library"""
        if not self.library_path.exists():
            print(f"Error: Library not found: {self.library_path}", file=sys.stderr)
            return {}
        
        try:
            with open(self.library_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading library: {e}", file=sys.stderr)
            return {}
    
    def load_state(self) -> UIState:
        """Load UI state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    state = UIState()
                    state.palette_visible = data.get("palette_visible", False)
                    state.selected_component = data.get("selected_component")
                    state.scroll_offset = data.get("scroll_offset", 0)
                    state.rotation = data.get("rotation", 0)
                    state.scale = data.get("scale", 1.0)
                    state.history = data.get("history", [])
                    return state
            except Exception as e:
                print(f"Warning: Failed to load state: {e}", file=sys.stderr)
        
        return UIState()
    
    def save_state(self):
        """Save UI state to file"""
        data = {
            "palette_visible": self.state.palette_visible,
            "selected_component": self.state.selected_component,
            "scroll_offset": self.state.scroll_offset,
            "rotation": self.state.rotation,
            "scale": self.state.scale,
            "history": self.state.history
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save state: {e}", file=sys.stderr)
    
    def send_lamp_commands(self, commands: List[str]):
        """Send commands to lamp via stdout"""
        for cmd in commands:
            print(cmd)
        sys.stdout.flush()
    
    def render_text(self, text: str, x: int, y: int, scale: int = 4) -> List[str]:
        """Generate lamp commands to render text using font glyphs"""
        commands = []
        
        if "font" not in self.library:
            return commands
        
        font = self.library["font"]
        cursor_x = x
        glyph_spacing = 25 * scale  # Adjusted spacing
        
        for char in text.upper():
            if char == " ":
                cursor_x += glyph_spacing
                continue
            
            if char not in font:
                # Try to handle common symbols
                cursor_x += glyph_spacing
                continue
            
            glyph = font[char]
            
            # Scale and translate glyph commands
            for cmd in glyph["commands"]:
                parts = cmd.split()
                
                if len(parts) >= 4 and parts[0] == "pen" and parts[1] in ["down", "move"]:
                    px = int(float(parts[2]) * scale) + cursor_x
                    py = int(float(parts[3]) * scale) + y
                    commands.append(f"pen {parts[1]} {px} {py}")
                
                elif len(parts) >= 5 and parts[0] == "pen" and parts[1] == "circle":
                    cx = int(float(parts[2]) * scale) + cursor_x
                    cy = int(float(parts[3]) * scale) + y
                    r = int(float(parts[4]) * scale)
                    commands.append(f"pen circle {cx} {cy} {r}")
                
                elif len(parts) >= 6 and parts[0] == "pen" and parts[1] == "line":
                    x1 = int(float(parts[2]) * scale) + cursor_x
                    y1 = int(float(parts[3]) * scale) + y
                    x2 = int(float(parts[4]) * scale) + cursor_x
                    y2 = int(float(parts[5]) * scale) + y
                    commands.append(f"pen line {x1} {y1} {x2} {y2}")
                
                elif len(parts) >= 6 and parts[0] == "pen" and parts[1] == "rectangle":
                    x1 = int(float(parts[2]) * scale) + cursor_x
                    y1 = int(float(parts[3]) * scale) + y
                    x2 = int(float(parts[4]) * scale) + cursor_x
                    y2 = int(float(parts[5]) * scale) + y
                    commands.append(f"pen rectangle {x1} {y1} {x2} {y2}")
                
                elif parts[0] == "pen" and parts[1] == "up":
                    commands.append("pen up")
            
            cursor_x += glyph_spacing
        
        return commands
    
    def render_palette(self) -> List[str]:
        """Render the component palette UI"""
        commands = []
        
        if not self.state.palette_visible:
            return commands
        
        # Draw panel border
        commands.append(f"pen rectangle {UI_PANEL_X} {UI_PANEL_Y} {SCREEN_WIDTH} {SCREEN_HEIGHT}")
        
        # Calculate visible range
        start_idx = self.state.scroll_offset
        end_idx = min(start_idx + UI_VISIBLE_ITEMS, len(self.state.component_list))
        
        # Render component list
        for i in range(start_idx, end_idx):
            component = self.state.component_list[i]
            y_pos = UI_PANEL_Y + UI_MARGIN + (i - start_idx) * UI_ITEM_HEIGHT
            
            # Highlight selected component
            if component == self.state.selected_component:
                highlight_x1 = UI_PANEL_X + 10
                highlight_y1 = y_pos - 5
                highlight_x2 = SCREEN_WIDTH - 10
                highlight_y2 = y_pos + 70
                commands.append(f"pen rectangle {highlight_x1} {highlight_y1} {highlight_x2} {highlight_y2}")
            
            # Render component name
            text_x = UI_PANEL_X + UI_MARGIN
            text_y = y_pos + 10
            text_cmds = self.render_text(component, text_x, text_y, scale=UI_TEXT_SCALE)
            commands.extend(text_cmds)
        
        # Draw scroll indicator if needed
        if len(self.state.component_list) > UI_VISIBLE_ITEMS:
            total_height = UI_PANEL_HEIGHT - 100
            indicator_height = int((UI_VISIBLE_ITEMS / len(self.state.component_list)) * total_height)
            indicator_y = int((self.state.scroll_offset / len(self.state.component_list)) * total_height) + 50
            
            indicator_x1 = SCREEN_WIDTH - 30
            indicator_x2 = SCREEN_WIDTH - 15
            commands.append(f"pen rectangle {indicator_x1} {indicator_y} {indicator_x2} {indicator_y + indicator_height}")
        
        return commands
    
    def toggle_palette(self):
        """Toggle palette visibility"""
        self.state.palette_visible = not self.state.palette_visible
        
        if self.state.palette_visible:
            commands = self.render_palette()
        else:
            # Erase palette area
            commands = [f"eraser clear {UI_PANEL_X} {UI_PANEL_Y} {SCREEN_WIDTH} {SCREEN_HEIGHT}"]
        
        self.send_lamp_commands(commands)
        self.save_state()
    
    def scroll_up(self):
        """Scroll component list up"""
        if self.state.scroll_offset > 0:
            self.state.scroll_offset -= 1
            commands = [f"eraser clear {UI_PANEL_X} {UI_PANEL_Y} {SCREEN_WIDTH} {SCREEN_HEIGHT}"]
            commands.extend(self.render_palette())
            self.send_lamp_commands(commands)
            self.save_state()
    
    def scroll_down(self):
        """Scroll component list down"""
        max_scroll = max(0, len(self.state.component_list) - UI_VISIBLE_ITEMS)
        if self.state.scroll_offset < max_scroll:
            self.state.scroll_offset += 1
            commands = [f"eraser clear {UI_PANEL_X} {UI_PANEL_Y} {SCREEN_WIDTH} {SCREEN_HEIGHT}"]
            commands.extend(self.render_palette())
            self.send_lamp_commands(commands)
            self.save_state()
    
    def select_component(self):
        """Select currently highlighted component"""
        if not self.state.component_list:
            return
        
        idx = self.state.scroll_offset
        if idx < len(self.state.component_list):
            self.state.selected_component = self.state.component_list[idx]
            commands = [f"eraser clear {UI_PANEL_X} {UI_PANEL_Y} {SCREEN_WIDTH} {SCREEN_HEIGHT}"]
            commands.extend(self.render_palette())
            self.send_lamp_commands(commands)
            self.save_state()
    
    def place_component(self):
        """Place selected component at tap location"""
        if not self.state.selected_component:
            return
        
        # Get tap coordinates from environment
        x = int(os.environ.get("TAP_X", 500))
        y = int(os.environ.get("TAP_Y", 500))
        
        component = self.library["components"].get(self.state.selected_component)
        if not component:
            return
        
        # Transform and place component
        commands = []
        scale = self.state.scale
        
        for cmd in component["commands"]:
            parts = cmd.split()
            
            if len(parts) >= 4 and parts[0] == "pen" and parts[1] in ["down", "move"]:
                px = int(float(parts[2]) * scale) + x
                py = int(float(parts[3]) * scale) + y
                commands.append(f"pen {parts[1]} {px} {py}")
            
            elif len(parts) >= 5 and parts[0] == "pen" and parts[1] == "circle":
                cx = int(float(parts[2]) * scale) + x
                cy = int(float(parts[3]) * scale) + y
                r = int(float(parts[4]) * scale)
                commands.append(f"pen circle {cx} {cy} {r}")
            
            elif len(parts) >= 6 and parts[0] == "pen" and parts[1] == "line":
                x1 = int(float(parts[2]) * scale) + x
                y1 = int(float(parts[3]) * scale) + y
                x2 = int(float(parts[4]) * scale) + x
                y2 = int(float(parts[5]) * scale) + y
                commands.append(f"pen line {x1} {y1} {x2} {y2}")
            
            elif len(parts) >= 6 and parts[0] == "pen" and parts[1] == "rectangle":
                x1 = int(float(parts[2]) * scale) + x
                y1 = int(float(parts[3]) * scale) + y
                x2 = int(float(parts[4]) * scale) + x
                y2 = int(float(parts[5]) * scale) + y
                commands.append(f"pen rectangle {x1} {y1} {x2} {y2}")
            
            elif parts[0] == "pen" and parts[1] == "up":
                commands.append("pen up")
        
        # Save to history
        self.state.history.append({
            "component": self.state.selected_component,
            "x": x,
            "y": y,
            "scale": self.state.scale,
            "rotation": self.state.rotation
        })
        
        self.send_lamp_commands(commands)
        self.save_state()
    
    def cancel_selection(self):
        """Cancel current selection"""
        self.state.selected_component = None
        commands = [f"eraser clear {UI_PANEL_X} {UI_PANEL_Y} {SCREEN_WIDTH} {SCREEN_HEIGHT}"]
        commands.extend(self.render_palette())
        self.send_lamp_commands(commands)
        self.save_state()
    
    def clear_screen(self):
        """Clear entire screen"""
        commands = [f"eraser clear 0 0 {SCREEN_WIDTH} {SCREEN_HEIGHT}"]
        self.state.history = []
        self.send_lamp_commands(commands)
        self.save_state()
    
    def scale_up(self):
        """Increase scale factor"""
        self.state.scale = min(3.0, self.state.scale + 0.25)
        self.save_state()
    
    def scale_down(self):
        """Decrease scale factor"""
        self.state.scale = max(0.25, self.state.scale - 0.25)
        self.save_state()
    
    def rotate_cw(self):
        """Rotate 90° clockwise"""
        self.state.rotation = (self.state.rotation + 90) % 360
        self.save_state()
    
    def rotate_ccw(self):
        """Rotate 90° counter-clockwise"""
        self.state.rotation = (self.state.rotation - 90) % 360
        self.save_state()

def main():
    if len(sys.argv) < 2:
        print("Usage: symbol_ui_controller <command>", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  toggle_palette, scroll_up, scroll_down, select_component", file=sys.stderr)
        print("  place_component, cancel_selection, clear_screen", file=sys.stderr)
        print("  scale_up, scale_down, rotate_cw, rotate_ccw", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Paths
    library_path = Path("/opt/etc/symbol_library.json")
    state_file = Path("/home/root/.symbol_ui_state.json")
    
    controller = SymbolUIController(library_path, state_file)
    
    # Execute command
    if hasattr(controller, command):
        method = getattr(controller, command)
        method()
    else:
        print(f"Error: Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
