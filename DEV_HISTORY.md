# Development History

## Project Evolution

### lamp-eraser Base (Original)
Enhanced rmkit's lamp with programmatic eraser support for reMarkable tablets.

**Key Discovery**: reMarkable recognizes `BTN_TOOL_RUBBER` input events for eraser functionality.

**Implementation**: Patch rmkit lamp to emulate eraser events alongside existing pen events.

### Component Library System (v1.0 - 2025-12-06)
Added custom electrical component library management system.

## Eraser Support Development

### Discovery Phase
Using `evtest` on reMarkable tablet revealed:
```
Event: time 1234.567890, type 1 (EV_KEY), code 321 (BTN_TOOL_RUBBER), value 1
```

This showed the tablet natively supports eraser tool events.

### Implementation
Modified rmkit lamp to inject `BTN_TOOL_RUBBER` events:

**Drawing** (original):
```cpp
ev.push_back(input_event{ type:EV_KEY, code:BTN_TOOL_PEN, value: 1 })
```

**Erasing** (new):
```cpp
ev.push_back(input_event{ type:EV_KEY, code:BTN_TOOL_RUBBER, value: 1 })
```

### Features Added
- `eraser line` - Erase straight lines
- `eraser rectangle` - Erase rectangle outlines
- `eraser fill` - Fill area with eraser strokes (configurable spacing)
- `eraser clear` - Dense erasure (10px spacing)
- `eraser down/move/up` - Low-level control

### Benefits
- Dynamic self-clearing UIs
- Smooth menu transitions
- State-based interfaces
- Native xochitl integration
- No rm2fb dependency

## Component Library Development

### v1.0 (2025-12-06)

#### Created Files
- **component_library.py** (370 lines)
  - `SymbolExtractor` class for SVG parsing
  - `ComponentLibraryManager` for configuration
  - CLI interface for operations
  - Extracted 214 symbols from library

- **component_selector.py** (240 lines)
  - `ComponentSelector` class for browsing
  - Cycling support (next/previous)
  - Integration with svg_to_lamp.py
  - Interactive CLI mode

- **Configuration System**
  - `component_library_config.json` - Auto-generated with all 214 symbols
  - `component_library_config.example.json` - Example configurations
  - Default visibility: `viewed`
  - Supports custom names, categories, descriptions

- **Demo Script**
  - `examples/component_library_demo.sh` - Automated demonstration

#### Features Implemented
- Symbol extraction from grouped SVG elements
- Bounding box calculation for proper export
- Three visibility modes: `viewed`, `cycled`, `hidden`
- Individual SVG export with proper viewBox
- Configuration-based symbol management
- Interactive cycling interface
- Command-line tools for all operations

#### Integration
- Works with existing `svg_to_lamp.py`
- Compatible with reMarkable tablet drawing system
- Supports dynamic UI workflows

## Technical Architecture

### Symbol Extraction
- Uses `xml.etree.ElementTree` for SVG parsing
- Identifies symbols by `<g>` group elements with IDs
- Calculates bounding boxes from path, rect, and circle elements
- Exports standalone SVGs with proper namespaces

### Configuration Format
JSON-based for easy editing:
```json
{
  "symbols": {
    "g1087": {
      "visibility": "cycled",
      "name": "resistor",
      "category": "passive"
    }
  }
}
```

### Visibility States
- **viewed**: Always available in menu
- **cycled**: Rotate through with next/previous buttons
- **hidden**: Excluded from menus and exports

### Dependencies
- Python 3.x standard library only
- No external dependencies
- Integrates with existing svg_to_lamp.py

## Source Attribution

### Eraser Support
- Based on [rmkit](https://github.com/rmkit-dev/rmkit) by rmkit-dev
- Inspired by reMarkable input event analysis
- Patch file: `lamp_eraser.patch`

### Electrical Symbols Library
- Source: Wikimedia Commons
- License: CC0 Public Domain
- Primary Author: Filip Dominec
- Contributors: Omegatron, WvBraun, Zedh, Rainglasz, Guruleninn, WarX, and others
- Total symbols: 214
- Categories: Semiconductors, mechanical switches, transformers, sources, connectors, passive components

## Utilities Development

### svg_to_lamp.py (271 lines)
Converts SVG files to lamp drawing commands.

**Features**:
- Path parsing (M, L, H, V, C, Q, Z commands)
- Circle, rectangle, line elements
- Bezier curve approximation (10 segments)
- Scaling and offset transformation
- Namespace handling

### text_to_lamp.py (138 lines)
Renders text as vector strokes.

**Features**:
- A-Z uppercase letters (7-segment style)
- 0-9 digits
- Special symbols: +, -, Ω (ohm), μ (micro)
- Stroke-based font rendering

## Build System

**Cross-compilation**:
- ARM GNUEABI toolchain
- okp transpiler for .cpy files
- Builds on Linux/Mac, runs on reMarkable

**Scripts**:
- `build_lamp_enhanced.sh` - Apply patch and compile
- `test_eraser.sh` - Eraser functionality tests
- `test_gui_complete.sh` - GUI integration tests

## Testing Infrastructure

### Automated Tests
- Eraser basic operations
- Fill/clear area tests
- Dynamic UI transitions
- Menu state management

### Manual Testing
- Drawing and erasing combinations
- Component library workflow
- SVG conversion accuracy
- Tablet deployment verification

## Future Considerations

### Potential Enhancements
- Auto-categorization based on SVG structure
- Symbol search by name/category
- Batch visibility operations
- Custom sort orders for cycled symbols
- Symbol preview in terminal (ASCII art)
- Tablet button mapping integration
- Pressure-sensitive erasing
- Eraser width control

### Known Limitations
- reMarkable 1 untested
- Requires firmware 3.24+ for best results
- Symbol extraction limited to `<g>` groups
- No real-time preview in component selector

## Version History

| Version | Date | Features |
|---------|------|----------|
| 1.0 | 2025-12-06 | Initial release with eraser + component library |
| 0.9 | Pre-release | Eraser support only |
| 0.1 | Base | rmkit lamp fork |

## Contributors

- Eraser implementation: lamp-v2 project
- Component library: lamp-v2 project
- Base lamp tool: rmkit-dev
- SVG symbols: Wikimedia Commons contributors
