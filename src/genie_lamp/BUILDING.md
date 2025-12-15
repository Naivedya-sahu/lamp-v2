# Building genie_lamp - Complete Guide

This guide covers all dependencies, common issues, and solutions for building genie_lamp.

## Quick Start

```bash
cd src/genie_lamp
./setup_and_build.sh
```

The script will check all dependencies and guide you through the setup.

## Dependencies

### 1. okp (Required)

**What it is:** Python-based C++ preprocessor that converts `.cpy` files to C++

**Installation Option A - From Source (Recommended for Debian issues):**
```bash
# Clone okp
git clone https://github.com/raisjn/okp.git /tmp/okp

# Install manually to user directory
mkdir -p ~/.local/bin ~/.local/lib/python3.11/site-packages
cp /tmp/okp/scripts/okp ~/.local/bin/
cp -r /tmp/okp/okp ~/.local/lib/python3.11/site-packages/
chmod +x ~/.local/bin/okp

# Add to PATH
export PATH=~/.local/bin:$PATH
echo 'export PATH=~/.local/bin:$PATH' >> ~/.bashrc

# Test
okp --version
```

**Installation Option B - pip (may fail on Debian 12+):**
```bash
pip install okp --break-system-packages
```

**Why pip might fail:**
- Debian/Ubuntu use "externally managed" Python
- setuptools version conflicts
- Use Option A for guaranteed success

### 2. ARM Cross-Compiler (Required)

**What it is:** Toolchain to compile for ARM architecture (reMarkable 2)

**Installation:**
```bash
# Ubuntu/Debian
sudo apt install g++-arm-linux-gnueabihf

# Arch Linux
yay -S arm-linux-gnueabihf-gcc  # or from AUR

# Verify
arm-linux-gnueabihf-g++ --version
```

### 3. RMKit Framework (Should be present)

**What it is:** UI framework and build system

**If missing:**
```bash
cd /path/to/lamp-v2
git submodule update --init --recursive
```

## Build Process

### Step 1: Run Setup Script

```bash
cd src/genie_lamp
./setup_and_build.sh
```

This will:
1. Check all dependencies
2. Create symlink in rmkit/src/
3. Build rmkit.h if needed
4. Build genie_lamp binary

### Step 2: Manual Build (if script fails)

```bash
# From lamp-v2 root directory

# 1. Create symlink
cd resources/rmkit
ln -sf ../../src/genie_lamp src/

# 2. Build rmkit.h (first time only)
make rmkit.h

# 3. Build genie_lamp
make genie_lamp TARGET=rm

# 4. Binary location
ls -lh src/build/genie_lamp
```

## Common Issues

### Issue 1: "okp: command not found"

**Cause:** okp not in PATH or not installed

**Solution:**
```bash
# Check installation
which okp

# If not found, reinstall using Option A above
git clone https://github.com/raisjn/okp.git /tmp/okp
mkdir -p ~/.local/bin ~/.local/lib/python3.11/site-packages
cp /tmp/okp/scripts/okp ~/.local/bin/
cp -r /tmp/okp/okp ~/.local/lib/python3.11/site-packages/
export PATH=~/.local/bin:$PATH
```

### Issue 2: "arm-linux-gnueabihf-g++: No such file or directory"

**Cause:** ARM cross-compiler not installed

**Solution:**
```bash
sudo apt install g++-arm-linux-gnueabihf
```

### Issue 3: Symlink errors

**Cause:** Multiple symlink creation attempts or wrong working directory

**Solution:**
```bash
# Remove old symlink
rm resources/rmkit/src/genie_lamp 2>/dev/null || true

# Create fresh symlink (from lamp-v2 root)
cd resources/rmkit
ln -sf ../../src/genie_lamp src/

# Verify
ls -la src/genie_lamp
# Should show: src/genie_lamp -> ../../src/genie_lamp
```

### Issue 4: "error: install_layout" when installing okp via pip

**Cause:** Python setuptools compatibility issue in Debian 12+

**Solution:** Use manual installation (Option A above) instead of pip

### Issue 5: "No rule to make target 'genie_lamp'"

**Cause:** Symlink not created or not in rmkit/src directory

**Solution:**
```bash
# Verify rmkit sees genie_lamp
cd resources/rmkit
ls src/ | grep genie

# Should see: genie_lamp

# If not, recreate symlink
ln -sf ../../src/genie_lamp src/
```

### Issue 6: Build script runs from wrong directory

**Cause:** Script uses relative paths instead of absolute

**Solution:** Both scripts now use absolute paths via `$SCRIPT_DIR`

```bash
# Can run from anywhere:
bash /path/to/src/genie_lamp/setup_and_build.sh

# Or
cd src/genie_lamp
./setup_and_build.sh
```

## Directory Structure

```
lamp-v2/
├── src/
│   └── genie_lamp/              # Source (our fork)
│       ├── main.cpy
│       ├── gesture_parser.cpy
│       ├── lamp_test.conf
│       ├── setup_and_build.sh   # Main build script
│       └── build_and_deploy.sh  # Deployment script
└── resources/
    └── rmkit/
        ├── src/
        │   ├── genie_lamp -> ../../src/genie_lamp  # Symlink!
        │   ├── rmkit/
        │   ├── lamp/
        │   └── ...
        └── build/
            └── genie_lamp       # Compiled binary
```

## Deployment

After successful build:

```bash
# Copy binary to device
scp resources/rmkit/src/build/genie_lamp root@10.11.99.1:/opt/bin/

# Copy configuration
scp src/genie_lamp/lamp_test.conf root@10.11.99.1:/opt/etc/genie_lamp.conf

# Run on device
ssh root@10.11.99.1 /opt/bin/genie_lamp /opt/etc/genie_lamp.conf
```

## Testing

Test gestures (after deployment):

1. **3-finger tap** → Draws a square
2. **2-finger swipe right** → Draws a circle
3. **2-finger swipe left** → Draws a rectangle
4. **2-finger swipe up** → Draws a line
5. **2-finger swipe down** → Erases area

## Docker Build (Alternative)

If you have Docker but not ARM toolchain:

```bash
cd resources/rmkit
docker build --tag rmkit:rm . -f docker/Dockerfile.rm
docker run --rm -v $(pwd):/src rmkit:rm make genie_lamp TARGET=rm
```

## Verification Checklist

Before building:
- [ ] `okp --version` works
- [ ] `arm-linux-gnueabihf-g++ --version` works
- [ ] `resources/rmkit/src/rmkit/` exists
- [ ] Symlink `resources/rmkit/src/genie_lamp` points to `src/genie_lamp`

After building:
- [ ] `resources/rmkit/src/build/genie_lamp` exists
- [ ] Binary is ~100KB+ in size
- [ ] `file` shows: "ELF 32-bit LSB executable, ARM"

## Getting Help

If you encounter other issues:

1. Check `setup_and_build.sh` output for specific errors
2. Verify all checkboxes above
3. Try manual build process step-by-step
4. Check rmkit documentation: `resources/rmkit/docs/BUILDING.md`
