#!/bin/bash
# Complete automated build script for genie_lamp
# Installs all dependencies and builds the binary

set -e

echo "================================"
echo "Genie-Lamp Complete Build Script"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Get paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAMP_V2_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
RMKIT_DIR="$LAMP_V2_DIR/resources/rmkit"

echo "Step 1: Install ARM Cross-Compiler"
echo "-----------------------------------"

if command -v arm-linux-gnueabihf-g++ &> /dev/null; then
    print_status 0 "ARM compiler already installed"
else
    echo "Installing ARM cross-compiler..."
    sudo apt update
    sudo apt install -y g++-arm-linux-gnueabihf

    if command -v arm-linux-gnueabihf-g++ &> /dev/null; then
        print_status 0 "ARM compiler installed successfully"
    else
        print_status 1 "ARM compiler installation failed"
        echo "Please install manually: sudo apt install g++-arm-linux-gnueabihf"
        exit 1
    fi
fi

echo ""
echo "Step 2: Install okp (if needed)"
echo "-------------------------------"

if command -v okp &> /dev/null; then
    print_status 0 "okp already installed"
else
    echo "Installing okp from source..."
    cd /tmp
    rm -rf okp 2>/dev/null || true
    git clone https://github.com/raisjn/okp.git

    mkdir -p ~/.local/bin ~/.local/lib/python3.11/site-packages
    cp okp/scripts/okp ~/.local/bin/
    cp -r okp/okp ~/.local/lib/python3.11/site-packages/
    chmod +x ~/.local/bin/okp

    export PATH=~/.local/bin:$PATH

    # Install Python dependencies
    pip3 install future --break-system-packages --quiet

    if command -v okp &> /dev/null; then
        print_status 0 "okp installed successfully"
    else
        print_status 1 "okp installation failed"
        exit 1
    fi
fi

# Ensure okp is in PATH
export PATH=~/.local/bin:$PATH

echo ""
echo "Step 3: Create Symlink"
echo "----------------------"

cd "$RMKIT_DIR"
if [ -L "src/genie_lamp" ]; then
    print_status 0 "Symlink already exists"
else
    ln -sf ../../src/genie_lamp src/genie_lamp
    print_status 0 "Symlink created"
fi

echo ""
echo "Step 4: Build rmkit.h"
echo "---------------------"

if [ -f "src/build/rmkit.h" ]; then
    print_status 0 "rmkit.h already exists"
else
    echo "Building rmkit.h..."
    make rmkit.h
    print_status 0 "rmkit.h built"
fi

echo ""
echo "Step 5: Build genie_lamp"
echo "------------------------"

echo "Compiling genie_lamp for reMarkable 2..."
make genie_lamp TARGET=rm

if [ -f "src/build/genie_lamp" ]; then
    print_status 0 "genie_lamp compiled successfully!"
    echo ""
    echo "Binary info:"
    ls -lh src/build/genie_lamp
    file src/build/genie_lamp
else
    print_status 1 "Build failed"
    exit 1
fi

echo ""
echo "================================"
echo "BUILD COMPLETE!"
echo "================================"
echo ""
echo "Binary location: $RMKIT_DIR/src/build/genie_lamp"
echo ""
echo "Next steps:"
echo "  1. Deploy to device:"
echo "     scp $RMKIT_DIR/src/build/genie_lamp root@10.11.99.1:/opt/bin/"
echo "     scp $SCRIPT_DIR/lamp_test.conf root@10.11.99.1:/opt/etc/genie_lamp.conf"
echo ""
echo "  2. Run on device:"
echo "     ssh root@10.11.99.1 /opt/bin/genie_lamp /opt/etc/genie_lamp.conf"
echo ""
echo "  3. Test gesture:"
echo "     3-finger tap → draws a square"
echo ""
