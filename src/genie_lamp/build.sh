#!/bin/bash
# Simple build script - run from anywhere
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../../resources/rmkit"

echo "Building genie_lamp..."
export PATH=~/.local/bin:$PATH
make genie_lamp TARGET=rm

echo ""
echo "✓ Done! Binary at: resources/rmkit/src/build/genie_lamp"
