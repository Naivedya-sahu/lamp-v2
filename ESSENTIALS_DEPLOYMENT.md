# ELXNK ESSENTIALS - Deployment Package

## ESSENTIAL FILES FOR ELXNK

This document lists the minimal essential files needed for a working Elxnk system on reMarkable 2.

### CORE BINARIES & SOURCE

#### 1. lamp (Drawing Engine)
```
resources/rmkit/src/lamp/
├── main.cpy            # Core lamp implementation
├── Makefile            # Build configuration
├── README.md           # Lamp documentation
└── example.in          # Example input

Supporting build files:
resources/rmkit/Makefile
resources/rmkit/src/common.make
resources/rmkit/src/actions.make
resources/rmkit/src/vendor/stb/    # Graphics library
```

**Build**: `cd resources/rmkit && make lamp TARGET=rm`
**Deploy**: Binary to `/opt/bin/lamp`

#### 2. genie_lamp (Gesture Detector)
```
src/genie_lamp/
├── main.cpp                # Standalone gesture detector
├── Makefile                # Simple ARM cross-compile
├── genie_lamp.conf         # Example config (3-finger tap)
├── ui.conf                 # UI control gestures
├── genie_lamp.service      # Systemd service file
└── README.txt              # Quick start guide
```

**Build**: `cd src/genie_lamp && make`
**Deploy**:
- Binary: `/opt/bin/genie_lamp`
- Config: `/opt/etc/genie_lamp.conf` or `/opt/etc/genie_ui.conf`
- Service: `/etc/systemd/system/genie_lamp.service`

### ASSETS

#### 3. Component Library (16 SVG files)
```
assets/components/
├── R.svg           # Resistor
├── C.svg           # Capacitor
├── L.svg           # Inductor
├── D.svg           # Diode
├── ZD.svg          # Zener Diode
├── GND.svg         # Ground
├── VDC.svg         # DC Voltage Source
├── VAC.svg         # AC Voltage Source
├── OPAMP.svg       # Op-Amp
├── NPN_BJT.svg     # NPN Transistor
├── PNP_BJT.svg     # PNP Transistor
├── N_MOSFET.svg    # N-Channel MOSFET
├── P_MOSFET.svg    # P-Channel MOSFET
├── P_CAP.svg       # Polarized Capacitor
├── SW_OP.svg       # Switch Open
└── SW_CL.svg       # Switch Closed
```

**Deploy**: `/home/root/lamp-v2/assets/components/`

#### 4. Font Glyphs (37 SVG files)
```
assets/font/
├── segoe path_A.svg through segoe path_Z.svg  (26 files)
└── segoe path_0.svg through segoe path_9.svg  (10 files)
```

**Deploy**: `/home/root/lamp-v2/assets/font/`

### UTILITIES

#### 5. SVG & UI Scripts
```
scripts/
├── svg2lamp.sh             # SVG to lamp converter
├── component_library.sh    # Component manager
├── font_render.sh          # Text renderer
├── ui_state.sh             # UI state machine
└── test_render_all.sh      # Test rendering script
```

**Deploy**: `/home/root/lamp-v2/scripts/`
**Permissions**: `chmod +x scripts/*.sh`

### TESTING

#### 6. RM2 Test Scripts
```
assets/testing-utilities/
├── rm2_diagnostic.sh       # Device diagnostics
├── test_crosscompile.sh    # Cross-compile test
└── rm2-features.txt        # Feature documentation
```

**Deploy**: `/home/root/lamp-v2/assets/testing-utilities/`

### DOCUMENTATION

#### 7. Essential Documentation
```
README.md                   # Project overview
BUILD_INSTRUCTIONS.txt      # Genie build guide
UI_SYSTEM_README.txt        # UI system documentation
CONTEXT_DATASET.md          # Complete project context
LICENSE                     # MIT License
```

**Deploy**: `/home/root/lamp-v2/` (optional, for reference)

## DEPLOYMENT STRUCTURE

On reMarkable 2, the final structure should be:

```
/opt/bin/
├── lamp                    # Drawing engine binary
└── genie_lamp              # Gesture detector binary

/opt/etc/
├── genie_lamp.conf         # Default gesture config
└── genie_ui.conf           # UI control config

/etc/systemd/system/
└── genie_lamp.service      # Service definition

/home/root/lamp-v2/
├── assets/
│   ├── components/         # 16 SVG components
│   └── font/               # 37 SVG font glyphs
└── scripts/                # 5 bash utilities
```

## BUILD ORDER

1. **Build lamp:**
   ```bash
   cd resources/rmkit
   make lamp TARGET=rm
   # Output: resources/rmkit/src/build/lamp
   ```

2. **Build genie_lamp:**
   ```bash
   cd src/genie_lamp
   make
   # Output: src/genie_lamp/genie_lamp
   ```

3. **Prepare assets:**
   ```bash
   # Assets are already in SVG format, no build needed
   # Just verify they exist:
   ls -1 assets/components/*.svg | wc -l  # Should be 16
   ls -1 assets/font/*.svg | wc -l        # Should be 37
   ```

4. **Make scripts executable:**
   ```bash
   chmod +x scripts/*.sh
   ```

## DEPLOYMENT STEPS

### One-time Setup:
```bash
# Create deployment directory on RM2
ssh root@10.11.99.1 mkdir -p /home/root/lamp-v2/{assets/components,assets/font,scripts}
```

### Deploy Binaries:
```bash
cd src/genie_lamp
make install  # Deploys genie_lamp + config + service

# Manually deploy lamp:
scp resources/rmkit/src/build/lamp root@10.11.99.1:/opt/bin/
```

### Deploy Assets & Scripts:
```bash
scp -r assets/components/*.svg root@10.11.99.1:/home/root/lamp-v2/assets/components/
scp -r assets/font/*.svg root@10.11.99.1:/home/root/lamp-v2/assets/font/
scp scripts/*.sh root@10.11.99.1:/home/root/lamp-v2/scripts/
ssh root@10.11.99.1 chmod +x /home/root/lamp-v2/scripts/*.sh
```

### Enable Service:
```bash
cd src/genie_lamp
make enable
make start
```

## VERIFICATION

On reMarkable 2:
```bash
# Check binaries
which lamp genie_lamp

# Check service
systemctl status genie_lamp

# Count assets
ls /home/root/lamp-v2/assets/components/*.svg | wc -l
ls /home/root/lamp-v2/assets/font/*.svg | wc -l

# Test lamp
echo "pen down 500 500" | lamp
echo "pen move 600 600" | lamp
echo "pen up" | lamp

# Initialize UI
bash /home/root/lamp-v2/scripts/ui_state.sh init
bash /home/root/lamp-v2/scripts/ui_state.sh redraw
```

## FILE COUNT SUMMARY

- **Binaries**: 2 (lamp, genie_lamp)
- **Config files**: 2 (genie_lamp.conf, ui.conf)
- **Service files**: 1 (genie_lamp.service)
- **Component SVGs**: 16
- **Font SVGs**: 37
- **Scripts**: 5
- **Test utilities**: 2
- **Documentation**: 5
- **Build dependencies**: ~20 files (rmkit build system)

**Total essential files**: ~90 files
**Total size**: ~5MB (including binaries)

## NON-ESSENTIAL FILES

These can be excluded from minimal deployment:

- resources/rmkit/src/* (except lamp/)
- .git/ directory
- Build artifacts (.o files, intermediate builds)
- Development tools
- Old/backup files
- Documentation images
- Extra documentation beyond essentials

## DEPENDENCIES ON REMARKABLE 2

**Required:**
- Linux kernel with input API
- bash (built-in)
- systemd (built-in)
- bc (for calculations in scripts)
- Standard GNU tools: sed, awk, grep

**NOT Required:**
- rm2fb (not used)
- fbink (not used)
- jq (not available, not used)
- Python (not needed at runtime)
- Any Toltec packages

## MINIMAL INSTALL

For absolute minimal installation (no UI, just lamp):
- lamp binary
- genie_lamp binary + basic config
- No scripts, no assets needed

For minimal UI install:
- All of the above
- All scripts
- All assets (components + fonts)

## NOTES

- All paths in scripts are dynamic (detect PROJECT_ROOT)
- Scripts work from any location
- Service runs genie_lamp at startup
- Gestures control UI via script calls
- State stored in /tmp/genie_ui/ (volatile, recreated on boot)

---
Last updated: 2025-12-17
Branch: elxnk-essentials
Purpose: Deployment reference for Elxnk project
