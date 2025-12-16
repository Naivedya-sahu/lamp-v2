#!/usr/bin/env python3
"""
symbol_ui_controller.py - Symbol palette UI state controller
Manages UI state, renders palette, handles gestures, generates lamp commands
Updated for conflict-free gesture operation with proper zones
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import os

# Screen dimensions for reMarkable 2
SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

# UI layout constants - Updated for 72/28 split
UI_PANEL_WIDTH = 400
UI_PANEL_X = 1004  # Left edge of palette (72% of screen)
UI_PANEL_Y = 0
UI_PANEL_HEIGHT = SCREEN_HEIGHT

CANVAS_WIDTH = 1004  # Canvas area width
CANVAS_HEIGHT = SCREEN_HEIGHT

UI_ITEM_HEIGHT = 100  # Larger for touch friendliness
UI_VISIBLE_ITEMS = 16  # More items visible
UI_TEXT_SCALE = 4      # Larger text
UI_MARGIN = 30         # Bigger margins

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
        
        with open(self.library_path, 'r') as f:
            return json.load(f)
    
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
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def send_lamp_commands(self, commands: List[str]):
        """Send commands to lamp via stdin"""
        # Direct output to stdout for piping to lamp
        print("\n".join(commands))
        sys.stdout.flush()
    
    def render_text(self, text: str, x: int, y: int, scale: int = 4) -> List[str]:
        """Generate lamp commands to render text using font glyphs"""
        commands = []
        
        if "font" not in self.library:
            return commands
        
        font = self.library["font"]
        cursor_x = x
        glyph_spacing = 25 * scale
        
        for char in text.upper():
            if char == " ":
                cursor_x += glyph_spacing
                continue
            
            if char not in font:
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
                
                elif parts[0] == "pen" and parts[1] == "up":
                    commands.append("pen up")
            
            cursor_x += glyph_spacing
        
        return commands
    
    def render_palette(self) -> List[str]:
        """Render the component palette UI"""
        commands = []
        
        if not self.state.palette_visible:
            return commands
        
        # Draw panel background border
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
                commands.append(f"pen rectangle {UI_PANEL_X + 10} {y_pos - 5} {SCREEN_WIDTH - 10} {y_pos + 75}")
            
            # Render component name
            text_cmds = self.render_text(component, UI_PANEL_X + UI_MARGIN, y_pos + 20, scale=UI_TEXT_SCALE)
            commands.extend(text_cmds)
        
        # Draw scroll indicator
        if len(self.state.component_list) > UI_VISIBLE_ITEMS:
            scroll_height = int((UI_VISIBLE_ITEMS / len(self.state.component_list)) * UI_PANEL_HEIGHT)
            scroll_y = int((self.state.scroll_offset / len(self.state.component_list)) * UI_PANEL_HEIGHT)
            commands.append(f"pen rectangle {SCREEN_WIDTH - 20} {scroll_y} {SCREEN_WIDTH - 10} {scroll_y + scroll_height}")
        
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
        """Place selected component at tap location (read from env vars)"""
        if not self.state.selected_component:
            return
        
        # Get tap coordinates from environment (set by gesture handler)
        x = int(os.environ.get("TAP_X", 500))
        y = int(os.environ.get("TAP_Y", 500))
        
        component = self.library["components"].get(self.state.selected_component)
        if not component:
            return
        
        # Transform and place component
        commands = []
        for cmd in component["commands"]:
            parts = cmd.split()
            
            # Apply scale transforms (rotation TODO)
            if len(parts) >= 4 and parts[0] == "pen" and parts[1] in ["down", "move"]:
                px = int(float(parts[2]) * self.state.scale) + x
                py = int(float(parts[3]) * self.state.scale) + y
                commands.append(f"pen {parts[1]} {px} {py}")
            
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
    
    def undo(self):
        """Undo last placement"""
        if not self.state.history:
            return
        
        last = self.state.history.pop()
        # TODO: Implement smart erase of last component
        self.save_state()
    
    def save_drawing(self):
        """Save current drawing state"""
        drawing_file = Path("/home/root/.symbol_ui_drawing.json")
        with open(drawing_file, 'w') as f:
            json.dump(self.state.history, f, indent=2)
    
    def load_drawing(self):
        """Load and replay saved drawing"""
        drawing_file = Path("/home/root/.symbol_ui_drawing.json")
        if not drawing_file.exists():
            return
        
        with open(drawing_file, 'r') as f:
            history = json.load(f)
        
        # Clear and replay
        self.clear_screen()
        # TODO: Replay all components from history

def main():
    if len(sys.argv) < 2:
        print("Usage: symbol_ui_controller <command>", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  toggle_palette, scroll_up, scroll_down, select_component", file=sys.stderr)
        print("  place_component, cancel_selection, clear_screen", file=sys.stderr)
        print("  scale_up, scale_down, rotate_cw, rotate_ccw", file=sys.stderr)
        print("  undo, save_drawing, load_drawing", file=sys.stderr)
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
