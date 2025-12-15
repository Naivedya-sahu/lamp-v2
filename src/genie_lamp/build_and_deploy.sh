#!/bin/bash
# Build and deploy genie_lamp to reMarkable 2

set -e

echo "=== Genie-Lamp Build and Deploy Script ==="
echo ""

# Get absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAMP_V2_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOST="${HOST:-10.11.99.1}"
RMKIT_DIR="$LAMP_V2_DIR/resources/rmkit"
BUILD_DIR="$RMKIT_DIR/build"
GENIE_LAMP_DIR="$SCRIPT_DIR"

echo "Step 1: Creating symlink in rmkit src..."
cd "$RMKIT_DIR"
if [ ! -L "src/genie_lamp" ]; then
    ln -sf "../../src/genie_lamp" src/
    echo "  ✓ Symlink created"
else
    echo "  ✓ Symlink already exists"
fi

echo ""
echo "Step 2: Building genie_lamp for RM2..."
cd src/genie_lamp
make -f ../../Makefile compile TARGET=rm

if [ ! -f "$BUILD_DIR/genie_lamp" ]; then
    echo "  ✗ Build failed - binary not found"
    exit 1
fi
echo "  ✓ Build successful"

echo ""
echo "Step 3: Deploying to reMarkable 2 at $HOST..."

# Stop any running instances
ssh root@$HOST "killall -9 genie_lamp 2>/dev/null || true"
echo "  ✓ Stopped running instances"

# Copy binary
scp "$BUILD_DIR/genie_lamp" root@$HOST:/opt/bin/
echo "  ✓ Binary deployed"

# Copy test config
scp "$GENIE_LAMP_DIR/lamp_test.conf" root@$HOST:/opt/etc/genie_lamp.conf
echo "  ✓ Config deployed"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "To run on device:"
echo "  ssh root@$HOST /opt/bin/genie_lamp /opt/etc/genie_lamp.conf"
echo ""
echo "To run in background:"
echo "  ssh root@$HOST \"/opt/bin/genie_lamp /opt/etc/genie_lamp.conf &\""
echo ""
echo "Test gestures:"
echo "  - 3-finger tap: Draw square"
echo "  - 2-finger swipe right: Draw circle"
echo "  - 2-finger swipe left: Draw rectangle"
echo "  - 2-finger swipe up: Draw line"
echo "  - 2-finger swipe down: Erase area"
