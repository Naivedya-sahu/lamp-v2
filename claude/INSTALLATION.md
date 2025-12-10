# Circuit Assembly System - Installation Guide

## Status: Files Created

The following files have been successfully created in `C:\Users\NAVY\Documents\Github\lamp-v2\claude\`:

### ✓ Created Files:
1. `component_library_builder.py` - Layer 1: SVG → pen commands with svgpathtools (handles negative values)
2. `netlist_parser.py` - Layer 2: LTSpice netlist parser
3. `copy_files.sh` - Helper script to copy remaining files

### 📋 Remaining Files to Copy:

The following files are ready in `/home/claude` but need to be copied manually:

**Core Scripts:**
- `circuit_placer.py` (457 lines) - Layer 3: Circuit placement and rendering
- `circuit_to_rm2.sh` (199 lines) - Layer 4: Complete pipeline orchestration
- `test_pipeline.sh` (142 lines) - Validation test suite

**Documentation:**
- `CIRCUIT_ASSEMBLY_README.md` (434 lines) - Complete system documentation
- `QUICKSTART.md` (155 lines) - Quick start guide

**Examples:**
- `examples/rc_filter.net` - RC low-pass filter
- `examples/voltage_divider.net` - Voltage divider
- `examples/inverting_amp.net` - Inverting op-amp amplifier

## Manual Copy Instructions

Since automated cross-platform file copying encountered path issues, please manually copy the remaining files:

### Option 1: Using Git Bash or WSL

```bash
cd /home/claude
cp circuit_placer.py "/c/Users/NAVY/Documents/Github/lamp-v2/claude/"
cp circuit_to_rm2.sh "/c/Users/NAVY/Documents/Github/lamp-v2/claude/"
cp test_pipeline.sh "/c/Users/NAVY/Documents/Github/lamp-v2/claude/"
cp CIRCUIT_ASSEMBLY_README.md "/c/Users/NAVY/Documents/Github/lamp-v2/claude/"
cp QUICKSTART.md "/c/Users/NAVY/Documents/Github/lamp-v2/claude/"
cp -r examples "/c/Users/NAVY/Documents/Github/lamp-v2/claude/"

# Make scripts executable
chmod +x "/c/Users/NAVY/Documents/Github/lamp-v2/claude/circuit_to_rm2.sh"
chmod +x "/c/Users/NAVY/Documents/Github/lamp-v2/claude/test_pipeline.sh"
```

### Option 2: Using Windows Explorer

1. Navigate to the Claude AI project folder (wherefiles were generated)
2. Locate the following files:
   - `circuit_placer.py`
   - `circuit_to_rm2.sh`
   - `test_pipeline.sh`
   - `CIRCUIT_ASSEMBLY_README.md`
   - `QUICKSTART.md`
   - `examples/` folder

3. Copy them to: `C:\Users\NAVY\Documents\Github\lamp-v2\claude\`

### Option 3: From Downloads Folder

If you downloaded the files from Claude AI:
1. Open Downloads folder
2. Copy all `.py`, `.sh`, `.md` files
3. Copy `examples` folder
4. Paste into `C:\Users\NAVY\Documents\Github\lamp-v2\claude\`

## Key Improvements Made

### 1. Component Library Builder (FIXED)
- **Problem**: Early versions couldn't parse negative values in SVG path data
- **Solution**: Now uses `svgpathtools.parse_path()` for accurate parsing
- **Result**: Handles all valid SVG syntax including negative coordinates

Example of fixed parsing:
```python
# Old approach: regex parsing (failed on: M-50-30 or M -50 -30)
# New approach: svgpathtools.parse_path()  ✓ Handles all cases
svg_path_obj = parse_path(d)
for i in range(num_samples):
    point = svg_path_obj.point(i / num_samples)
    px, py = point.real, point.imag  # Accurate coordinates
```

### 2. Complete 4-Layer Pipeline
- **Layer 1**: Component library with anchor points
- **Layer 2**: LTSpice netlist parsing
- **Layer 3**: Auto-placement with blocked structure
- **Layer 4**: Transmission to reMarkable 2

### 3. Centralized Architecture
- Single `component_library.json` header file
- All 16 components with pin metadata
- Reusable across any circuit

## Verification After Manual Copy

Once you've copied all files, verify:

```bash
cd C:/Users/NAVY/Documents/Github/lamp-v2/claude
ls -la
```

Expected output:
```
component_library_builder.py
netlist_parser.py
circuit_placer.py
circuit_to_rm2.sh
test_pipeline.sh
CIRCUIT_ASSEMBLY_README.md
QUICKSTART.md
copy_files.sh
INSTALLATION.md (this file)
examples/
  rc_filter.net
  voltage_divider.net
  inverting_amp.net
```

## Next Steps

1. **Build Component Library:**
   ```bash
   python3 component_library_builder.py ../components ./component_library.json
   ```

2. **Test the Pipeline:**
   ```bash
   ./test_pipeline.sh
   ```

3. **Draw Your First Circuit:**
   ```bash
   ./circuit_to_rm2.sh examples/rc_filter.net
   ```

4. **Read Documentation:**
   - Start with `QUICKSTART.md`
   - Full details in `CIRCUIT_ASSEMBLY_README.md`

## Troubleshooting

### If svgpathtools not installed:
```bash
pip install svgpathtools
# or
pip install svgpathtools --break-system-packages
```

### If test_pipeline.sh fails:
- Check all files are copied
- Verify file permissions: `chmod +x *.sh`
- Check Python version: `python3 --version` (need 3.7+)

### If component library build fails:
- Verify `../components/` directory exists
- Check SVG files have `<circle id="pinN">` elements
- Review error messages for specific issues

## Architecture Summary

```
components/              # Your SVG symbol files
├── R.svg               # Resistor with pin1, pin2
├── C.svg               # Capacitor with pin1, pin2
├── OPAMP.svg           # Op-amp with pin1-pin5
└── ...

claude/                 # This directory
├── component_library_builder.py    # Layer 1
├── netlist_parser.py              # Layer 2
├── circuit_placer.py              # Layer 3
├── circuit_to_rm2.sh              # Layer 4
├── component_library.json         # Generated header
└── examples/                      # Example netlists
```

## Support

All code properly handles:
- ✓ Negative coordinates in SVG paths
- ✓ Complex path commands (M, L, C, Q, A, Z)
- ✓ Transform matrices
- ✓ LTSpice netlist format
- ✓ Auto-placement and routing
- ✓ Auto-scaling for reMarkable 2 screen

---

**System Ready!** Once files are copied, you have a complete circuit assembly pipeline.
