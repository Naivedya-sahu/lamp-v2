#!/usr/bin/env python3
"""
symbol_ui_mode.py - Component Mode activation manager
Manages transition between Normal Mode and Component Mode
"""

import sys
import subprocess
from pathlib import Path
import time

# Configuration
MODE_FILE = Path("/home/root/.symbol_ui_mode")
SERVICE_NAME = "symbol_ui_main.service"
LAMP_BIN = "/opt/bin/lamp"

# Screen dimensions
SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

# Visual indicator (bottom-right corner, 34x34px green square)
INDICATOR_X1 = SCREEN_WIDTH - 34
INDICATOR_Y1 = SCREEN_HEIGHT - 34
INDICATOR_X2 = SCREEN_WIDTH
INDICATOR_Y2 = SCREEN_HEIGHT

def is_active():
    """Check if Component Mode is active"""
    return MODE_FILE.exists()

def draw_indicator():
    """Draw green corner indicator"""
    cmd = f'echo "pen rectangle {INDICATOR_X1} {INDICATOR_Y1} {INDICATOR_X2} {INDICATOR_Y2}" | {LAMP_BIN}'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def erase_indicator():
    """Erase corner indicator"""
    cmd = f'echo "eraser clear {INDICATOR_X1} {INDICATOR_Y1} {INDICATOR_X2} {INDICATOR_Y2}" | {LAMP_BIN}'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def activate():
    """Enter Component Mode"""
    if is_active():
        print("Already in Component Mode", file=sys.stderr)
        return
    
    print("Activating Component Mode...", file=sys.stderr)
    
    # Create mode indicator file
    MODE_FILE.touch()
    
    # Start main UI service
    result = subprocess.run(
        ["systemctl", "start", SERVICE_NAME],
        capture_output=True
    )
    
    if result.returncode != 0:
        print(f"Warning: Failed to start service: {result.stderr.decode()}", file=sys.stderr)
    
    # Small delay for service startup
    time.sleep(0.5)
    
    # Draw visual indicator
    draw_indicator()
    
    print("Component Mode ACTIVE", file=sys.stderr)

def deactivate():
    """Exit Component Mode"""
    if not is_active():
        print("Already in Normal Mode", file=sys.stderr)
        return
    
    print("Deactivating Component Mode...", file=sys.stderr)
    
    # Erase visual indicator first (immediate feedback)
    erase_indicator()
    
    # Stop main UI service
    result = subprocess.run(
        ["systemctl", "stop", SERVICE_NAME],
        capture_output=True
    )
    
    if result.returncode != 0:
        print(f"Warning: Failed to stop service: {result.stderr.decode()}", file=sys.stderr)
    
    # Remove mode indicator file
    if MODE_FILE.exists():
        MODE_FILE.unlink()
    
    print("Component Mode INACTIVE", file=sys.stderr)

def toggle():
    """Toggle between Normal Mode and Component Mode"""
    if is_active():
        deactivate()
    else:
        activate()

def status():
    """Print current mode status"""
    if is_active():
        print("Component Mode: ACTIVE")
        # Check if service is actually running
        result = subprocess.run(
            ["systemctl", "is-active", SERVICE_NAME],
            capture_output=True
        )
        service_status = result.stdout.decode().strip()
        print(f"Main Service: {service_status}")
    else:
        print("Component Mode: INACTIVE")
    
    # Check activation service
    result = subprocess.run(
        ["systemctl", "is-active", "symbol_ui_activation.service"],
        capture_output=True
    )
    activation_status = result.stdout.decode().strip()
    print(f"Activation Service: {activation_status}")

def main():
    if len(sys.argv) < 2:
        print("Usage: symbol_ui_mode {activate|deactivate|toggle|status}", file=sys.stderr)
        print("\nCommands:", file=sys.stderr)
        print("  activate    - Enter Component Mode", file=sys.stderr)
        print("  deactivate  - Exit Component Mode", file=sys.stderr)
        print("  toggle      - Switch between modes", file=sys.stderr)
        print("  status      - Show current mode", file=sys.stderr)
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
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print("Use: activate, deactivate, toggle, or status", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
