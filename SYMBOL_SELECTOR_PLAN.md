# Symbol Selector - Native RM2 Circuit Drawing Tool

## Overview
Pivot from complex auto-layout circuit system to simple manual symbol placement tool.

## Architecture

### 1. Native Binary (C++ using rmkit)
- **Location**: `src/symbol_selector/main.cpy`
- **Build target**: Native ARM binary for RM2
- **Framework**: rmkit (similar to genie)

### 2. UI Layout

```
┌─────────────────────────────────────────────────┐
│                                                 │
│                                                 │
│         Main Drawing Canvas                     │
│         (Component placement area)              │
│                                                 │
│                                                 │
│                                    ┌──────────┐ │
│                                    │ Symbol   │ │
│                                    │ Palette  │ │
│                                    │          │ │
│                                    │ [R] [C]  │ │
│                                    │ [L] [V]  │ │
│                                    │ [GND]    │ │
│                                    │ [OPAMP]  │ │
│                                    │ etc...   │ │
│                                    └──────────┘ │
└─────────────────────────────────────────────────┘
Bottom-right corner: Symbol selection palette
```

### 3. Features

#### Phase 1: Symbol Selection & Placement
- [ ] Bottom-right palette with 16 component symbols
- [ ] Text labels using embedded font
- [ ] Tap to select symbol
- [ ] Tap canvas to place selected symbol
- [ ] Visual feedback for selected symbol

#### Phase 2: Gesture Control (genie integration)
- [ ] Two-finger swipe right: Open symbol palette
- [ ] Two-finger swipe left: Close palette
- [ ] Two-finger tap: Copy last placed symbol
- [ ] Three-finger tap: Delete symbol at touch point

#### Phase 3: Symbol Manipulation
- [ ] Tap and hold: Select placed symbol
- [ ] Drag: Move selected symbol
- [ ] Rotate gesture: Rotate symbol (90° increments)
- [ ] Pinch: Delete selected symbol

#### Phase 4: Wiring (manual)
- [ ] Wire mode toggle button
- [ ] Draw straight lines between pins
- [ ] Snap to nearby pins

## Technical Implementation

### Symbol Storage
Use existing SVG-to-relative-coordinates system:
- Component library: `src/component_library.json`
- Renderer: `src/svg_to_lamp_relative.py`
- Each symbol pre-rendered at fixed size (e.g., 100x100)

### Font Integration
1. Convert OTF font to C header using `xxd` or similar
2. Embed in rmkit style: `unsigned char font_data[] = {...}`
3. Use with stb_truetype for text rendering

### Data Structure
```cpp
struct PlacedSymbol {
    string component_type;  // "R", "C", etc.
    int x, y;               // Center position
    int rotation;           // 0, 90, 180, 270
    float scale;            // Default: 1.0
};

vector<PlacedSymbol> placed_symbols;
```

### File Format (Simple JSON)
```json
{
  "symbols": [
    {"type": "R", "x": 500, "y": 600, "rotation": 0},
    {"type": "OPAMP", "x": 800, "y": 700, "rotation": 90}
  ],
  "wires": [
    {"from": [500, 600], "to": [800, 700]}
  ]
}
```

## Build System

### Makefile Addition
```makefile
symbol_selector: src/symbol_selector/main.cpy
	cd resources/rmkit && make symbol_selector
	cp resources/rmkit/build/symbol_selector symbol_selector.arm
```

### Dependencies
- rmkit UI framework ✓
- stb_truetype (for font) ✓
- Component SVG library ✓
- lamp (for rendering) ✓

## Development Steps

1. **Font Conversion**: Convert OTF → C header
2. **Basic UI**: Create rmkit app with bottom-right palette
3. **Symbol Rendering**: Integrate svg_to_lamp_relative.py output
4. **Touch Handling**: Implement tap-to-place
5. **Gesture Integration**: Add genie-style gesture recognition
6. **Symbol Manipulation**: Drag, rotate, delete
7. **File I/O**: Save/load circuit layouts
8. **Wire Drawing**: Simple point-to-point wires

## Why This Approach Is Better

1. **Simplicity**: Manual placement is intuitive
2. **Control**: User has full control over layout
3. **Textbook-style**: Can recreate exact textbook diagrams
4. **Native**: Fast, responsive on RM2 hardware
5. **No complex rules**: No grammar/layout engine needed
6. **Reuses work**: Leverages existing SVG library and rendering

## Next Immediate Steps

1. Get OTF font file from user
2. Convert font to C header
3. Create basic symbol_selector app skeleton
4. Implement symbol palette UI
5. Test on RM2
