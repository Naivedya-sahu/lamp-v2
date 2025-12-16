#!/usr/bin/env python3
"""
symbol_ui_mode.py - Component Mode activation manager
Manages mode switching between normal Xochitl and component UI
Shows visual indicator, starts/stops services
"""

import sys
import subprocess
from pathlib import Path

# Configuration
MODE_FILE = Path("/home/root/.symbol_ui_mode")
SERVICE_NAME = "symbol_ui_main.service"
LAMP_BIN = "/opt/bin/lamp"

# Visual indicator coordinates (bottom-right corner)
INDICATOR_X1 = 1370
INDICATOR_Y1 = 1838
INDICATOR_X2 = 1404
INDICATOR_Y2 = 1872

def run_lamp_command(commands):
    """Send commands to lamp"""
    try:
        proc = subprocess.Popen(
            [LAMP_BIN],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        proc.communicate(input=commands)
    except Exception as e:
        print(f"Warning: Lamp command failed: {e}", file=sys.stderr)

def is_active():
    """Check if component mode is active"""
    return MODE_FILE.exists()

def show_indicator():
    """Draw green corner indicator"""
    commands = f"pen rectangle {INDICATOR_X1} {INDICATOR_Y1} {INDICATOR_X2} {INDICATOR_Y2}\n"
    run_lamp_command(commands)

def hide_indicator():
    """Erase corner indicator"""
    commands = f"eraser clear {INDICATOR_X1} {INDICATOR_Y1} {INDICATOR_X2} {INDICATOR_Y2}\n"
    run_lamp_command(commands)

def activate():
    """Activate component mode"""
    if is_active():
        print("Component mode already active", file=sys.stderr)
        return
    
    # Create mode indicator file
    MODE_FILE.touch()
    
    # Show visual indicator
    show_indicator()
    
    # Start main UI service
    try:
        subprocess.run(["systemctl", "start", SERVICE_NAME], check=True)
        print("Component mode activated")
    except subprocess.CalledProcessError as e:
        print(f"Error starting service: {e}", file=sys.stderr)
        # Cleanup on failure
        MODE_FILE.unlink(missing_ok=True)
        hide_indicator()

def deactivate():
    """Deactivate component mode"""
    if not is_active():
        print("Component mode already inactive", file=sys.stderr)
        return
    
    # Stop main UI service
    try:
        subprocess.run(["systemctl", "stop", SERVICE_NAME])
    except Exception as e:
        print(f"Warning: Failed to stop service: {e}", file=sys.stderr)
    
    # Hide visual indicator
    hide_indicator()
    
    # Remove mode indicator file
    MODE_FILE.unlink(missing_ok=True)
    
    print("Component mode deactivated")

def toggle():
    """Toggle component mode"""
    if is_active():
        deactivate()
    else:
        activate()

def status():
    """Print current mode status"""
    if is_active():
        print("Component mode: ACTIVE")
        # Check service status
        result = subprocess.run(
            ["systemctl", "is-active", "--quiet", SERVICE_NAME],
            capture_output=True
        )
        if result.returncode == 0:
            print("Main UI service: RUNNING")
        else:
            print("Main UI service: STOPPED (inconsistent state)")
    else:
        print("Component mode: INACTIVE")

def main():
    if len(sys.argv) < 2:
        print("Usage: symbol_ui_mode <command>", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  activate    - Activate component mode", file=sys.stderr)
        print("  deactivate  - Deactivate component mode", file=sys.stderr)
        print("  toggle      - Toggle mode on/off", file=sys.stderr)
        print("  status      - Show current status", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "activate":
        activate()
    elif command == "deactivate":
        deactivate()
    elif command == "toggle":
        toggle()
    elif command == "status":
        status()
    else:
        print(f"Error: Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
