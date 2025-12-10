# Quick Start Guide - Circuit Assembly System

## 5-Minute Setup

### Step 1: Copy Files to Your Project

Copy these files to your `lamp-v2` directory:

```bash
cp component_library_builder.py ~/Documents/Github/lamp-v2/
cp netlist_parser.py ~/Documents/Github/lamp-v2/
cp circuit_placer.py ~/Documents/Github/lamp-v2/
cp circuit_to_rm2.sh ~/Documents/Github/lamp-v2/
cp -r examples ~/Documents/Github/lamp-v2/
```

### Step 2: Test the Pipeline

```bash
cd ~/Documents/Github/lamp-v2
./test_pipeline.sh
```

All tests should pass ✓

### Step 3: Build Component Library

```bash
python3 component_library_builder.py ./components ./component_library.json
```

Expected output:
```
Building component library from 16 symbols...
  ✓ R: 2 pins, 45 commands
  ✓ C: 2 pins, 32 commands
  ...
  
✓ Component library exported to ./component_library.json
  Total components: 16
  Total pins: 48
  Total pen commands: 627
```

### Step 4: Draw Your First Circuit

Create `my_circuit.net`:

```
* My First Circuit - RC Filter
V1 IN 0 5V
R1 IN OUT 10k
C1 OUT 0 100nF
```

Draw it:

```bash
./circuit_to_rm2.sh my_circuit.net
```

Output:
```
==========================================
Circuit to reMarkable 2 Pipeline
==========================================
Netlist: my_circuit.net
Scale: auto
Target: 10.11.99.1
Mode: raw

Testing SSH connection...
✓ Connected

✓ Component library up to date

[Layer 2 & 3] Parsing netlist and placing circuit...
Circuit dimensions: 400.0 x 200.0
Scale factor: 2.35x
✓ Generated 156 pen commands

[Layer 4] Using raw pen commands

Sending to reMarkable 2...

✓ Circuit drawn successfully!

Commands sent: 156
Check your reMarkable 2 screen
==========================================
Pipeline Complete
==========================================
```

## Usage Examples

### Voltage Divider
```bash
./circuit_to_rm2.sh examples/voltage_divider.net
```

### With Custom Scale
```bash
./circuit_to_rm2.sh examples/rc_filter.net 1.5
```

### Over WiFi
```bash
./circuit_to_rm2.sh my_circuit.net auto 192.168.1.123
```

## Netlist Syntax Cheat Sheet

```
Component  Format                Example
─────────  ────────────────────  ─────────────────────
Resistor   R<n> n+ n- value      R1 N1 N2 10k
Capacitor  C<n> n+ n- value      C1 N2 0 100nF
Inductor   L<n> n+ n- value      L1 N3 N4 10mH
Voltage    V<n> n+ n- value      V1 VIN 0 5V
Diode      D<n> anode cathode    D1 N5 N6
OpAmp      U<n> + - Vcc Vee Out  U1 0 N7 15V -15V N8
Ground     0 or GND              (special node)
```

## Common Issues

### "Cannot connect to RM2"
- Check USB cable
- Verify IP: `ssh root@10.11.99.1` (password on screen)

### "Component not found"
- Add component SVG to `./components/`
- Rebuild library: `python3 component_library_builder.py ./components`

### "Circuit too large"
- Use smaller scale: `./circuit_to_rm2.sh circuit.net 0.5`
- Simplify netlist

## Next Steps

- Read full documentation: `CIRCUIT_ASSEMBLY_README.md`
- Try example circuits in `./examples/`
- Create your own component SVGs
- Experiment with complex circuits

## Support

If something doesn't work:
1. Run `./test_pipeline.sh` to diagnose
2. Check error messages carefully
3. Verify all dependencies installed
4. Review CIRCUIT_ASSEMBLY_README.md troubleshooting section

**Happy circuit drawing! 🎨⚡**
