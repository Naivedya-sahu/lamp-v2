#!/bin/bash
# Simple font test using lamp directly - no rm2fb needed

echo "Font Test - Direct Rendering (no rm2fb)"
echo "========================================"
echo ""

# Test text at different positions
cat << 'EOF' > /tmp/font_test_commands.txt
pen down 100 100
pen move 200 100
pen move 200 200
pen move 100 200
pen move 100 100
pen up
EOF

echo "Testing lamp pen commands..."
if [ -n "$1" ]; then
    # Send to RM2
    cat /tmp/font_test_commands.txt | ssh root@$1 'cat > /tmp/lamp_test && /home/root/lamp < /tmp/lamp_test'
    echo "✓ Commands sent to RM2 at $1"
else
    echo "Dry run mode:"
    cat /tmp/font_test_commands.txt
    echo ""
    echo "To send to RM2:"
    echo "  $0 10.11.99.1"
fi

rm -f /tmp/font_test_commands.txt
