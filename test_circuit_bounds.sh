#!/bin/bash

# Test that all circuits render within screen bounds

SCREEN_WIDTH=1404
SCREEN_HEIGHT=1872

echo "=========================================="
echo "  Circuit Bounding Box Validation Test"
echo "=========================================="
echo ""

PASS_COUNT=0
FAIL_COUNT=0

for CIRCUIT in examples/ece_circuits/*.net; do
    CIRCUIT_NAME=$(basename "$CIRCUIT")
    echo -n "Testing $CIRCUIT_NAME... "
    
    # Run circuit and capture output
    OUTPUT=$(python3 src/circuit_to_rm2.py "$CIRCUIT" --dry-run 2>&1)
    
    # Extract component positions
    POSITIONS=$(echo "$OUTPUT" | grep "^Drawing" | sed 's/Drawing.*at (\([0-9]*\), \([0-9]*\))/\1 \2/')
    
    # Check if any position is out of bounds
    OUT_OF_BOUNDS=0
    while read -r X Y; do
        if [ -n "$X" ] && [ -n "$Y" ]; then
            if [ "$X" -lt 0 ] || [ "$X" -gt "$SCREEN_WIDTH" ]; then
                OUT_OF_BOUNDS=1
            fi
            if [ "$Y" -lt 0 ] || [ "$Y" -gt "$SCREEN_HEIGHT" ]; then
                OUT_OF_BOUNDS=1
            fi
        fi
    done <<< "$POSITIONS"
    
    if [ $OUT_OF_BOUNDS -eq 1 ]; then
        echo "❌ FAIL (out of bounds)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    else
        echo "✅ PASS"
        PASS_COUNT=$((PASS_COUNT + 1))
    fi
done

echo ""
echo "=========================================="
echo "  Results: $PASS_COUNT passed, $FAIL_COUNT failed"
echo "=========================================="

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ All circuits render within bounds!"
    exit 0
else
    echo "❌ Some circuits out of bounds"
    exit 1
fi
