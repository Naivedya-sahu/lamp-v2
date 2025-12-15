#!/bin/bash
# Complete setup and build script for genie_lamp
# This script checks dependencies and guides through the build process

set -e

echo "=== Genie-Lamp Build Setup ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Get absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAMP_V2_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
RMKIT_DIR="$LAMP_V2_DIR/resources/rmkit"

echo "Project Paths:"
echo "  Lamp v2: $LAMP_V2_DIR"
echo "  RMKit:   $RMKIT_DIR"
echo ""

# Check dependencies
echo "=== Checking Dependencies ==="
echo ""

# Check okp
if command -v okp &> /dev/null; then
    print_status 0 "okp compiler found"
    OKP_OK=1
else
    print_status 1 "okp compiler not found"
    OKP_OK=0
    echo "  Install with: pip install okp --break-system-packages"
    echo "  Or manually from: https://github.com/raisjn/okp"
fi

# Check ARM cross-compiler
if command -v arm-linux-gnueabihf-g++ &> /dev/null; then
    print_status 0 "ARM cross-compiler found"
    ARM_OK=1
else
    print_status 1 "ARM cross-compiler not found"
    ARM_OK=0
    echo "  Install on Ubuntu/Debian: sudo apt install g++-arm-linux-gnueabihf"
    echo "  Install on Arch: Install arm-linux-gnueabihf-gcc from AUR"
fi

echo ""

# Check rmkit structure
if [ -d "$RMKIT_DIR/src/rmkit" ]; then
    print_status 0 "RMKit framework found"
    RMKIT_OK=1
else
    print_status 1 "RMKit framework not found"
    RMKIT_OK=0
    print_warning "RMKit may need to be re-cloned or initialized"
fi

# Check if rmkit.h exists
if [ -f "$RMKIT_DIR/src/build/rmkit.h" ]; then
    print_status 0 "rmkit.h header exists"
    RMKIT_H_OK=1
else
    print_status 1 "rmkit.h needs to be built"
    RMKIT_H_OK=0
fi

echo ""
echo "=== Build Requirements Summary ==="
echo ""

if [ $OKP_OK -eq 1 ] && [ $ARM_OK -eq 1 ] && [ $RMKIT_OK -eq 1 ]; then
    echo -e "${GREEN}All dependencies satisfied!${NC}"
    echo ""

    # Create symlink if needed
    if [ ! -e "$RMKIT_DIR/src/genie_lamp" ]; then
        echo "Creating symlink..."
        ln -sf "$SCRIPT_DIR" "$RMKIT_DIR/src/genie_lamp"
        print_status 0 "Symlink created: $RMKIT_DIR/src/genie_lamp -> $SCRIPT_DIR"
    else
        if [ -L "$RMKIT_DIR/src/genie_lamp" ]; then
            print_status 0 "Symlink already exists"
        else
            print_warning "genie_lamp exists but is not a symlink - please check manually"
        fi
    fi

    echo ""
    echo "=== Building ==="
    echo ""

    # Build rmkit.h if needed
    if [ $RMKIT_H_OK -eq 0 ]; then
        echo "Building rmkit.h..."
        cd "$RMKIT_DIR"
        make rmkit.h
        print_status $? "rmkit.h built"
    fi

    # Build genie_lamp
    echo "Building genie_lamp..."
    cd "$RMKIT_DIR"
    make genie_lamp TARGET=rm

    if [ -f "$RMKIT_DIR/src/build/genie_lamp" ]; then
        print_status 0 "genie_lamp built successfully"
        echo ""
        echo "Binary location: $RMKIT_DIR/src/build/genie_lamp"
        echo ""
        echo "To deploy:"
        echo "  scp $RMKIT_DIR/src/build/genie_lamp root@10.11.99.1:/opt/bin/"
        echo "  scp $SCRIPT_DIR/lamp_test.conf root@10.11.99.1:/opt/etc/genie_lamp.conf"
    else
        print_status 1 "Build failed"
        exit 1
    fi

else
    echo -e "${RED}Missing dependencies - please install them first${NC}"
    echo ""
    echo "Quick setup commands:"
    echo ""
    if [ $OKP_OK -eq 0 ]; then
        echo "# Install okp (Python preprocessor):"
        echo "git clone https://github.com/raisjn/okp.git /tmp/okp"
        echo "mkdir -p ~/.local/bin ~/.local/lib/python3.11/site-packages"
        echo "cp /tmp/okp/scripts/okp ~/.local/bin/"
        echo "cp -r /tmp/okp/okp ~/.local/lib/python3.11/site-packages/"
        echo "export PATH=~/.local/bin:\$PATH"
        echo ""
    fi
    if [ $ARM_OK -eq 0 ]; then
        echo "# Install ARM cross-compiler:"
        echo "sudo apt install g++-arm-linux-gnueabihf  # Ubuntu/Debian"
        echo ""
    fi
    if [ $RMKIT_OK -eq 0 ]; then
        echo "# Re-initialize rmkit submodule:"
        echo "cd $LAMP_V2_DIR"
        echo "git submodule update --init --recursive"
        echo ""
    fi
    exit 1
fi
