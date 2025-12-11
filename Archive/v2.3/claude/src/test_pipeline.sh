#!/bin/bash
#
# Test Circuit Assembly Pipeline
# Validates all layers without requiring RM2 connection
#

set -e

echo "=========================================="
echo "Circuit Assembly Pipeline Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED=0

# Test function
test_component() {
    local test_name="$1"
    local test_cmd="$2"
    
    echo -ne "${BLUE}Testing: ${test_name}...${NC} "
    
    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test Layer 1: Component Library Builder
echo "=== Layer 1: Component Library Builder ==="
echo ""

# Check if script exists
test_component "Script exists" "test -f component_library_builder.py"

# Check Python dependencies
test_component "Python available" "python3 --version"

# Test with mock components (if available)
if [ -d "./components" ]; then
    test_component "Components directory found" "test -d ./components"
    
    # Count SVG files
    SVG_COUNT=$(find ./components -name "*.svg" 2>/dev/null | wc -l)
    if [ $SVG_COUNT -gt 0 ]; then
        echo -e "${BLUE}Found $SVG_COUNT component SVG files${NC}"
        test_component "Build library" "python3 component_library_builder.py ./components ./test_library.json"
        
        if [ -f ./test_library.json ]; then
            echo -e "${BLUE}Library generated successfully${NC}"
            test_component "Library is valid JSON" "python3 -m json.tool ./test_library.json"
            rm ./test_library.json
        fi
    else
        echo -e "${RED}⚠ No SVG files found in ./components${NC}"
    fi
else
    echo -e "${RED}⚠ Components directory not found${NC}"
fi

echo ""

# Test Layer 2: Netlist Parser
echo "=== Layer 2: Netlist Parser ==="
echo ""

test_component "Script exists" "test -f netlist_parser.py"

# Create test netlist
cat > test_netlist.net << 'EOF'
* Test Circuit
V1 N1 0 5V
R1 N1 N2 10k
C1 N2 0 100nF
EOF

test_component "Parse test netlist" "python3 netlist_parser.py test_netlist.net"

rm test_netlist.net

echo ""

# Test Layer 3: Circuit Placer
echo "=== Layer 3: Circuit Placer & Renderer ==="
echo ""

test_component "Script exists" "test -f circuit_placer.py"

# Only test if library exists
if [ -f ./component_library.json ]; then
    # Create test netlist
    cat > test_netlist.net << 'EOF'
* Test Circuit
V1 N1 0 5V
R1 N1 N2 10k
C1 N2 0 100nF
EOF
    
    test_component "Place and render circuit" "python3 circuit_placer.py test_netlist.net ./component_library.json 1.0"
    
    rm test_netlist.net
else
    echo -e "${RED}⚠ Component library not found, skipping placer test${NC}"
fi

echo ""

# Test Layer 4: Orchestration
echo "=== Layer 4: Orchestration Script ==="
echo ""

test_component "Script exists" "test -f circuit_to_rm2.sh"
test_component "Script is executable" "test -x circuit_to_rm2.sh"

echo ""

# Summary
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo ""
    echo "Pipeline is ready. To use:"
    echo "  1. Create a netlist file (e.g., circuit.net)"
    echo "  2. Run: ./circuit_to_rm2.sh circuit.net"
else
    echo -e "${RED}$FAILED test(s) failed${NC}"
    echo ""
    echo "Please fix the issues above before using the pipeline."
fi
echo "=========================================="

exit $FAILED
