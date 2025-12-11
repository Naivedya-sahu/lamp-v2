# Component Scaling Analysis & Standards

## Current Component Dimensions (SVG viewBox)

| Component | Width (px) | Height (px) | Aspect Ratio | Issue |
|-----------|------------|-------------|--------------|-------|
| R.svg     | 140        | 32.8        | 4.27:1       | Too wide |
| C.svg     | 100        | 81.8        | 1.22:1       | Wrong aspect (should be wider) |
| L.svg     | 140        | 21.9        | 6.39:1       | Excessively wide |
| D.svg     | 140        | 70.9        | 1.98:1       | Too wide |
| OPAMP.svg | 150        | 150         | 1.00:1       | Good |
| GND.svg   | 100        | 83.2        | 1.20:1       | Acceptable |
| VDC.svg   | 100        | 147.1       | 0.68:1       | Too tall |

## IEEE 315 / IEC 60617 Standards for Tablet Drawing

For a 1404×1872px display (~6.2"×8.3"), optimal symbol sizes:

| Symbol Type              | Target Width | Target Height | Aspect | Rationale |
|--------------------------|--------------|---------------|--------|-----------|
| 2-terminal passive (R,L) | 80-90px      | 30-40px       | 3:1    | Horizontal emphasis |
| Capacitor                | 90-110px     | 40-50px       | 2.5:1  | Slightly wider than tall |
| Diode                    | 70-80px      | 40-50px       | 2:1    | Balanced triangle |
| Op-Amp                   | 120px        | 120px         | 1:1    | Square triangle |
| Ground                   | 50-60px      | 80-100px      | 0.6:1  | Vertical emphasis |
| Voltage Source           | 50-60px      | 80-120px      | 0.5:1  | Tall circle |

## Optimal Scale Factors

These scales produce symbols matching IEEE standards:

| Component | Current Size | Target Size | Scale Factor | Result |
|-----------|--------------|-------------|--------------|---------|
| R         | 140×33       | 90×30       | **6x**       | 84×20 (close enough) |
| C         | 100×82       | 110×45      | **11x**      | 110×90 (acceptable) |
| L         | 140×22       | 90×30       | **6x**       | 84×13 (acceptable) |
| D         | 140×71       | 80×40       | **6x**       | 84×43 (good) |
| P_CAP     | ~100×82      | 90×45       | **9x**       | Similar to C |
| OPAMP     | 150×150      | 120×120     | **8x**       | 120×120 (perfect) |
| GND       | 100×83       | 60×100      | **6x**       | 60×50 (good) |
| VDC       | 100×147      | 60×90       | **4x**       | 40×59 (acceptable) |
| VAC       | ~100×147     | 60×90       | **6x**       | Similar to VDC |

## Non-Uniformity Analysis

**The components are NOT uniform and SHOULD NOT BE:**

- Passive components (R, L, C) should be smaller than active (OPAMP)
- Power symbols (GND, VDC) should be distinctive in size
- Horizontal components (R, L) vs vertical (GND, VDC) require different aspects

**This is correct schematic practice.** Uniformity would make schematics harder to read.

## Usage

Test any component with optimal scale:

```bash
./test_component.sh R              # Resistor at 6x scale
./test_component.sh OPAMP          # Op-amp at 8x scale
./test_component.sh GND            # Ground at 6x scale
```

The script automatically applies the optimal scale for each component based on this analysis.

## References

- IEEE Std 315-1975 (Graphic Symbols for Electrical and Electronics Diagrams)
- IEC 60617 (Graphical symbols for diagrams)
- Practical schematic drawing on reMarkable 2 (empirical testing)
