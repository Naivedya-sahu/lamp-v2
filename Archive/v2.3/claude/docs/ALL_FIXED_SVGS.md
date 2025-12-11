# Fixed SVG Components - Copy and Save

All SVGs have been corrected for:
- No transform matrices
- Properly centered content
- Adequate viewBox margins
- Correct pin placement

---

## R.svg (Resistor)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="140" height="40" viewBox="0 0 140 40" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="R">
    <!-- Resistor zigzag pattern -->
    <path d="M 5,20 H 25 L 32,5 L 46,35 L 60,5 L 74,35 L 88,5 L 102,35 L 109,20 H 135"
          style="fill:none;stroke:#000000;stroke-width:3.5;stroke-linecap:round;stroke-linejoin:miter"/>
    <!-- Connection pins -->
    <circle id="pin1" cx="5" cy="20" r="1" fill="#000000"/>
    <circle id="pin2" cx="135" cy="20" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## C.svg (Capacitor)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="90" viewBox="0 0 100 90" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="C">
    <!-- Top wire -->
    <path d="M 50,5 V 35" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Top plate -->
    <path d="M 25,35 H 75" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <!-- Bottom plate -->
    <path d="M 25,55 H 75" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <!-- Bottom wire -->
    <path d="M 50,55 V 85" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Connection pins -->
    <circle id="pin1" cx="50" cy="5" r="1" fill="#000000"/>
    <circle id="pin2" cx="50" cy="85" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## L.svg (Inductor)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="140" height="40" viewBox="0 0 140 40" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="L">
    <!-- Inductor coils -->
    <path d="M 5,20 H 15 C 15,5 30,5 30,20 C 30,5 45,5 45,20 C 45,5 60,5 60,20 C 60,5 75,5 75,20 C 75,5 90,5 90,20 C 90,5 105,5 105,20 C 105,5 120,5 120,20 H 135"
          style="fill:none;stroke:#000000;stroke-width:3.5;stroke-linecap:round;stroke-linejoin:round"/>
    <!-- Connection pins -->
    <circle id="pin1" cx="5" cy="20" r="1" fill="#000000"/>
    <circle id="pin2" cx="135" cy="20" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## P_CAP.svg (Polarized Capacitor)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="100" viewBox="0 0 100 100" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="P_CAP">
    <!-- Top wire -->
    <path d="M 50,5 V 35" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Top plate (straight) -->
    <path d="M 25,35 H 75" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <!-- Bottom plate (curved) -->
    <path d="M 25,50 Q 50,60 75,50" style="fill:none;stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <!-- Bottom wire -->
    <path d="M 50,50 V 95" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Plus symbol (top, indicating positive terminal) -->
    <path d="M 60,20 H 70" style="stroke:#000000;stroke-width:2.5;stroke-linecap:butt"/>
    <path d="M 65,15 V 25" style="stroke:#000000;stroke-width:2.5;stroke-linecap:butt"/>
    <!-- Connection pins -->
    <circle id="pin1" cx="50" cy="5" r="1" fill="#000000"/>
    <circle id="pin2" cx="50" cy="95" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## D.svg (Diode)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="110" height="70" viewBox="0 0 110 70" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="D">
    <!-- Left wire -->
    <path d="M 5,35 H 35" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Diode triangle (pointing right) -->
    <path d="M 35,15 L 35,55 L 70,35 Z" style="fill:#000000;stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <!-- Cathode bar -->
    <path d="M 70,15 L 70,55" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <!-- Right wire -->
    <path d="M 70,35 H 105" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Connection pins -->
    <circle id="pin1" cx="5" cy="35" r="1" fill="#000000"/>
    <circle id="pin2" cx="105" cy="35" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## ZD.svg (Zener Diode)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="110" height="70" viewBox="0 0 110 70" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="ZD">
    <!-- Left wire -->
    <path d="M 5,35 H 35" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Diode triangle (pointing right) -->
    <path d="M 35,15 L 35,55 L 70,35 Z" style="fill:#000000;stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <!-- Cathode bar with Z-bend -->
    <path d="M 70,15 L 70,55" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <path d="M 70,15 L 76,20" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <path d="M 70,55 L 64,50" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <!-- Right wire -->
    <path d="M 70,35 H 105" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Connection pins -->
    <circle id="pin1" cx="5" cy="35" r="1" fill="#000000"/>
    <circle id="pin2" cx="105" cy="35" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## OPAMP.svg (Operational Amplifier)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="130" height="110" viewBox="0 0 130 110" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="OPAMP">
    <!-- Main triangle -->
    <path d="M 20,15 L 20,95 L 105,55 Z" 
          style="fill:none;stroke:#000000;stroke-width:3.5;stroke-linecap:round;stroke-linejoin:miter"/>
    <!-- Input wires -->
    <path d="M 5,35 H 20" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <path d="M 5,75 H 20" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Output wire -->
    <path d="M 105,55 H 125" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Power supply wires -->
    <path d="M 58,15 V 5" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <path d="M 58,95 V 105" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Plus symbol (non-inverting input) -->
    <path d="M 28,32 H 34" style="stroke:#000000;stroke-width:2;stroke-linecap:butt"/>
    <path d="M 31,29 V 35" style="stroke:#000000;stroke-width:2;stroke-linecap:butt"/>
    <!-- Minus symbol (inverting input) -->
    <path d="M 28,75 H 34" style="stroke:#000000;stroke-width:2;stroke-linecap:butt"/>
    <!-- Connection pins -->
    <circle id="pin1" cx="5" cy="75" r="1" fill="#000000"/>
    <circle id="pin2" cx="5" cy="35" r="1" fill="#000000"/>
    <circle id="pin3" cx="125" cy="55" r="1" fill="#000000"/>
    <circle id="pin4" cx="58" cy="105" r="1" fill="#000000"/>
    <circle id="pin5" cx="58" cy="5" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## GND.svg (Ground)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="90" viewBox="0 0 100 90" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="GND">
    <!-- Vertical line from pin -->
    <path d="M 50,5 V 35" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Horizontal lines (descending size) -->
    <path d="M 20,35 H 80" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <path d="M 28,50 H 72" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <path d="M 36,65 H 64" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <path d="M 42,80 H 58" style="stroke:#000000;stroke-width:3.5;stroke-linecap:square"/>
    <!-- Connection pin -->
    <circle id="pin1" cx="50" cy="5" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## VDC.svg (DC Voltage Source)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="80" height="130" viewBox="0 0 80 130" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="VDC">
    <!-- Top wire -->
    <path d="M 40,5 V 32" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Circle -->
    <circle cx="40" cy="65" r="30" style="fill:none;stroke:#000000;stroke-width:3.5"/>
    <!-- Bottom wire -->
    <path d="M 40,95 V 125" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Plus symbol (top) -->
    <path d="M 35,48 H 45" style="stroke:#000000;stroke-width:2.5;stroke-linecap:butt"/>
    <path d="M 40,43 V 53" style="stroke:#000000;stroke-width:2.5;stroke-linecap:butt"/>
    <!-- Minus symbol (bottom) -->
    <path d="M 35,82 H 45" style="stroke:#000000;stroke-width:2.5;stroke-linecap:butt"/>
    <!-- Connection pins -->
    <circle id="pin1" cx="40" cy="5" r="1" fill="#000000"/>
    <circle id="pin2" cx="40" cy="125" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## VAC.svg (AC Voltage Source)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="80" height="130" viewBox="0 0 80 130" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="VAC">
    <!-- Top wire -->
    <path d="M 40,5 V 32" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Circle -->
    <circle cx="40" cy="65" r="30" style="fill:none;stroke:#000000;stroke-width:3.5"/>
    <!-- Bottom wire -->
    <path d="M 40,95 V 125" style="stroke:#000000;stroke-width:3.5;stroke-linecap:round"/>
    <!-- Sine wave inside circle -->
    <path d="M 25,65 Q 30,53 35,65 T 45,65 T 55,65" 
          style="fill:none;stroke:#000000;stroke-width:2.5;stroke-linecap:round"/>
    <!-- Connection pins -->
    <circle id="pin1" cx="40" cy="5" r="1" fill="#000000"/>
    <circle id="pin2" cx="40" cy="125" r="1" fill="#000000"/>
  </g>
</svg>
```

---

## Usage with svg_to_lamp_smart.py

Save each SVG to `components_fixed/` directory, then render:

```bash
python3 svg_to_lamp_smart.py components_fixed/R.svg 8
python3 svg_to_lamp_smart.py components_fixed/OPAMP.svg 10
python3 svg_to_lamp_smart.py components_fixed/P_CAP.svg 10 --show-pins
```

All components now have proper margins and will render centered on RM2.
