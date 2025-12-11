#!/bin/bash
#
# Copy all circuit assembly files from /home/claude to lamp-v2/claude directory
# Run this script to complete the file installation
#

set -e

SOURCE_DIR="/home/claude"
DEST_DIR="C:/Users/NAVY/Documents/Github/lamp-v2/claude"

echo "Copying circuit assembly system files..."
echo "Source: $SOURCE_DIR"
echo "Destination: $DEST_DIR"
echo ""

# Copy Python scripts
echo "Copying Python scripts..."
cp "$SOURCE_DIR/circuit_placer.py" "$DEST_DIR/"
cp "$SOURCE_DIR/test_pipeline.sh" "$DEST_DIR/"
echo "✓ Scripts copied"

# Copy shell scripts
echo "Copying shell scripts..."
cp "$SOURCE_DIR/circuit_to_rm2.sh" "$DEST_DIR/"
chmod +x "$DEST_DIR/circuit_to_rm2.sh"
chmod +x "$DEST_DIR/test_pipeline.sh"
echo "✓ Shell scripts copied and made executable"

# Copy documentation
echo "Copying documentation..."
cp "$SOURCE_DIR/CIRCUIT_ASSEMBLY_README.md" "$DEST_DIR/"
cp "$SOURCE_DIR/QUICKSTART.md" "$DEST_DIR/"
echo "✓ Documentation copied"

# Copy examples
echo "Copying example netlists..."
cp -r "$SOURCE_DIR/examples" "$DEST_DIR/"
echo "✓ Examples copied"

echo ""
echo "=========================================="
echo "All files copied successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. cd C:/Users/NAVY/Documents/Github/lamp-v2/claude"
echo "  2. ./test_pipeline.sh"
echo "  3. Read QUICKSTART.md for usage"
echo ""
