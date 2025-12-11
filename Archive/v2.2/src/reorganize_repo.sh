#!/bin/bash
#
# Repository Reorganization Script
# lamp-v2 - Preserve git history while restructuring
#
# Usage: ./reorganize_repo.sh [--dry-run]
#

set -e  # Exit on error

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo "=== DRY RUN MODE - No changes will be made ==="
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_phase() {
    echo -e "\n${BLUE}=== PHASE $1: $2 ===${NC}\n"
}

log_action() {
    echo -e "${GREEN}→${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Execute command with dry-run support
execute() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] $@"
    else
        "$@"
    fi
}

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    log_error "Not in a git repository!"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    log_warning "You have uncommitted changes. Please commit or stash them first."
    git status --short
    exit 1
fi

# Confirm with user
if [ "$DRY_RUN" = false ]; then
    echo -e "${YELLOW}This script will reorganize the repository structure.${NC}"
    echo "All git history will be preserved using 'git mv'."
    echo ""
    read -p "Continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# ============================================================================
# PHASE 1: Create Directory Structure
# ============================================================================
log_phase 1 "Creating New Directory Structure"

directories=(
    "docs/user-guide"
    "docs/development"
    "docs/history"
    "src/core"
    "src/tools"
    "src/build"
    "src/build/patches"
    "config/examples"
    "assets/symbols/individual"
    "assets/examples"
    "tests"
    "scripts"
    "archive/phase1-eraser"
    "archive/phase2-components"
    "archive/phase3-circuits"
    "archive/experiments"
    "vendor"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        log_action "Creating directory: $dir"
        execute mkdir -p "$dir"
    fi
done

# ============================================================================
# PHASE 2: Archive Historical Development
# ============================================================================
log_phase 2 "Archiving Historical Development"

# Archive old/ directory (Phase 1 & 2 legacy)
if [ -d "old" ]; then
    log_action "Archiving old/ → archive/phase1-eraser/legacy/"
    execute git mv old archive/phase1-eraser/legacy
fi

# Archive claude/ directory (AI-assisted experiments)
if [ -d "claude" ]; then
    log_action "Archiving claude/ → archive/experiments/ai-assisted/"
    execute git mv claude archive/experiments/ai-assisted
fi

# ============================================================================
# PHASE 3: Consolidate Production Code
# ============================================================================
log_phase 3 "Consolidating Production Code"

# Move core Python modules
if [ -f "circuit_builder.py" ]; then
    log_action "Moving circuit_builder.py → src/core/"
    execute git mv circuit_builder.py src/core/
fi

if [ -f "component_definitions.py" ]; then
    log_action "Moving component_definitions.py → src/core/"
    execute git mv component_definitions.py src/core/
fi

# Choose canonical SVG converter (svg_to_lamp_improved.py)
if [ -f "svg_to_lamp_improved.py" ]; then
    log_action "Moving svg_to_lamp_improved.py → src/core/svg_to_lamp.py"
    execute git mv svg_to_lamp_improved.py src/core/svg_to_lamp.py
fi

# Archive alternative SVG converters
svg_alternatives=("svg_to_lamp_smart.py" "svg_to_lamp_svgpathtools.py")
for alt in "${svg_alternatives[@]}"; do
    if [ -f "$alt" ]; then
        log_action "Archiving $alt → archive/experiments/svg-converters/"
        execute mkdir -p archive/experiments/svg-converters
        execute git mv "$alt" archive/experiments/svg-converters/
    fi
done

# Move main.cpy if exists
if [ -f "main_with_eraser.cpy" ]; then
    log_action "Moving main_with_eraser.cpy → src/build/"
    execute git mv main_with_eraser.cpy src/build/
fi

# ============================================================================
# PHASE 4: Organize Configuration Files
# ============================================================================
log_phase 4 "Organizing Configuration Files"

if [ -f "component_library.json" ]; then
    log_action "Moving component_library.json → config/"
    execute git mv component_library.json config/
fi

if [ -f "component_definitions.json" ]; then
    log_action "Moving component_definitions.json → config/"
    execute git mv component_definitions.json config/
fi

# Archive duplicate .lamp and .net files as examples
if [ -f "rc_vdc_circuit.lamp" ]; then
    log_action "Moving rc_vdc_circuit.lamp → assets/examples/"
    execute git mv rc_vdc_circuit.lamp assets/examples/
fi

# ============================================================================
# PHASE 5: Organize Build System
# ============================================================================
log_phase 5 "Organizing Build System"

if [ -f "build_lamp_enhanced.sh" ]; then
    log_action "Moving build_lamp_enhanced.sh → src/build/"
    execute git mv build_lamp_enhanced.sh src/build/
fi

# Note: lamp_eraser.patch is in old/, will be in archive now
# We should copy (not move) it to src/build/patches/
if [ ! "$DRY_RUN" = true ] && [ -f "archive/phase1-eraser/legacy/lamp_eraser.patch" ]; then
    log_action "Copying lamp_eraser.patch → src/build/patches/"
    cp archive/phase1-eraser/legacy/lamp_eraser.patch src/build/patches/
    git add src/build/patches/lamp_eraser.patch
fi

# ============================================================================
# PHASE 6: Organize Scripts
# ============================================================================
log_phase 6 "Organizing Utility Scripts"

scripts_to_move=(
    "send_lamp.sh"
    "svg_gallery.sh"
    "svg_to_rm2.sh"
)

for script in "${scripts_to_move[@]}"; do
    if [ -f "$script" ]; then
        log_action "Moving $script → scripts/"
        execute git mv "$script" scripts/
    fi
done

# ============================================================================
# PHASE 7: Organize Assets
# ============================================================================
log_phase 7 "Organizing Assets"

# Move examples/ directory to assets/
if [ -d "examples" ]; then
    log_action "Moving examples/ → assets/examples/"
    # Move contents instead of directory itself
    if [ ! "$DRY_RUN" = true ]; then
        for item in examples/*; do
            if [ -e "$item" ]; then
                git mv "$item" assets/examples/
            fi
        done
        rmdir examples 2>/dev/null || true
    else
        echo "[DRY-RUN] git mv examples/* assets/examples/"
        echo "[DRY-RUN] rmdir examples"
    fi
fi

# Move individual component SVGs
if [ -d "components" ]; then
    log_action "Moving components/ → assets/symbols/individual/"
    if [ ! "$DRY_RUN" = true ]; then
        for item in components/*; do
            if [ -e "$item" ]; then
                git mv "$item" assets/symbols/individual/
            fi
        done
        rmdir components 2>/dev/null || true
    else
        echo "[DRY-RUN] git mv components/* assets/symbols/individual/"
        echo "[DRY-RUN] rmdir components"
    fi
fi

# Move resources/ if it exists
if [ -d "resources" ]; then
    log_action "Moving resources/ → vendor/resources/"
    execute git mv resources vendor/
fi

# ============================================================================
# PHASE 8: Organize Documentation
# ============================================================================
log_phase 8 "Organizing Documentation"

# Keep README.md and CIRCUIT_BUILDER_README.md at root temporarily
# They'll be manually reorganized in next phase

log_action "Documentation files identified for manual consolidation:"
echo "  - README.md (root)"
echo "  - CIRCUIT_BUILDER_README.md (root)"
echo "  - archive/phase1-eraser/legacy/*.md"
echo "  - archive/experiments/ai-assisted/*.md"

# ============================================================================
# PHASE 9: Create Archive README files
# ============================================================================
log_phase 9 "Creating Archive Documentation"

# Create archive/README.md
cat > archive/README.md <<'EOF'
# Archive Directory

This directory contains the historical development phases of lamp-v2.

## Structure

- **phase1-eraser/** - Original eraser implementation and early component library
- **phase2-components/** - Component library v1.0 development
- **phase3-circuits/** - Circuit builder experiments
- **experiments/** - AI-assisted development iterations

## Purpose

These archives preserve the complete development history while keeping the main repository clean and organized.

### phase1-eraser/
The foundation of lamp-v2:
- Discovery of BTN_TOOL_RUBBER events
- Initial eraser patch implementation
- Early documentation and testing scripts

### experiments/ai-assisted/
Developmental iterations assisted by AI:
- Multiple SVG parser implementations
- Component placement experiments
- Circuit assembly prototypes
- Technical documentation from development process

All successful experiments were promoted to production code in `src/`.

## Using Archived Code

If you need to reference historical implementations:
1. Check git history: `git log --follow <file>`
2. Review archived READMEs for context
3. Compare with current implementation in `src/`

## Note

Nothing in this archive is currently used by the production system. All active code is in `src/`, `config/`, `assets/`, and `scripts/`.
EOF

if [ ! "$DRY_RUN" = true ]; then
    git add archive/README.md
fi

# Create experiments README
cat > archive/experiments/README.md <<'EOF'
# Development Experiments

This directory contains experimental code from AI-assisted development sessions.

## ai-assisted/
Prototypes and iterations developed with Claude AI:
- SVG parsing experiments (multiple approaches)
- Circuit placement algorithms
- Component library builders
- Netlist parsers

### What Succeeded
The following experiments were promoted to production:
- `svg_to_lamp_smart.py` → Influenced `src/core/svg_to_lamp.py`
- `circuit_placer.py` → Evolved into `src/core/circuit_builder.py`
- `component_library_builder.py` → Merged into `src/core/component_definitions.py`

### Historical Value
These files document:
- Design decisions and trade-offs
- Alternative approaches considered
- Iterative refinement process
- Technical learning and discovery

## Browsing Tips
- Check commit messages for context
- Review technical docs (*.md files)
- Compare with final implementations in `src/`
EOF

if [ ! "$DRY_RUN" = true ]; then
    git add archive/experiments/README.md
fi

# ============================================================================
# PHASE 10: Summary
# ============================================================================
log_phase 10 "Reorganization Complete"

echo ""
echo "Directory structure created:"
echo ""
if [ ! "$DRY_RUN" = true ]; then
    tree -L 2 -d --charset ascii
else
    echo "[DRY-RUN] tree output would be shown here"
fi

echo ""
log_action "Reorganization complete!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Test that scripts still work (update paths if needed)"
echo "  3. Consolidate documentation in docs/"
echo "  4. Update README.md with new structure"
echo "  5. Commit changes: git commit -m 'Reorganize repository structure'"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo "Run this script with --dry-run to preview changes first"
fi
