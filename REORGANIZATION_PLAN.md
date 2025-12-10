# Repository Reorganization Plan

**Date:** 2025-12-10
**Repository:** lamp-v2
**Purpose:** Transform from development chaos to production-ready structure

---

## Visual Comparison

### BEFORE (Current Structure)

```
lamp-v2/
├── README.md                           # Main docs
├── CIRCUIT_BUILDER_README.md          # Feature docs
├── Library.txt                         # Component index
├── circuit_builder.py                  # [PROD] Circuit renderer
├── component_definitions.py            # [PROD] Component library
├── component_definitions.json          # [CONFIG] Components
├── component_library.json              # [CONFIG] Visibility
├── svg_to_lamp_improved.py            # [PROD] SVG converter v3
├── svg_to_lamp_smart.py               # [?] SVG converter v2
├── svg_to_lamp_svgpathtools.py        # [?] SVG converter v1
├── main_with_eraser.cpy               # [BUILD] Source file
├── build_lamp_enhanced.sh             # [BUILD] Build script
├── send_lamp.sh                       # [UTIL] Deploy script
├── svg_gallery.sh                     # [UTIL] Gallery script
├── svg_to_rm2.sh                      # [UTIL] Conversion script
├── rc_vdc_circuit.lamp                # [EXAMPLE] Sample circuit
│
├── old/                               # [LEGACY] Phase 1 & 2
│   ├── DEV_HISTORY.md                 # ⭐ Important history!
│   ├── INSTALL.md                     # ⭐ Installation guide
│   ├── LICENSE                        # ⭐ License file!
│   ├── TEST_SCRIPTS_README.md
│   ├── SVG_GALLERY_README.md
│   ├── component_library.py           # [OLD] v1.0
│   ├── component_selector.py          # [OLD] Selector
│   ├── component_library_config.json  # [OLD] Config
│   ├── svg_to_lamp.py                 # [OLD] Original
│   ├── svg_2_lamp.py                  # [OLD] v2
│   ├── text_to_lamp.py                # [OLD] Text renderer
│   ├── lamp_eraser.patch              # ⭐ Critical patch!
│   └── test_*.sh                      # [OLD] Test scripts
│
├── claude/                            # [EXPERIMENTS] AI-assisted dev
│   ├── QUICKSTART.md                  # ⭐ Good quickstart!
│   ├── INSTALLATION.md                # Duplicate install docs
│   ├── CIRCUIT_ASSEMBLY_README.md
│   ├── SVG_PARSING_TECHNICAL.md       # ⭐ Technical notes
│   ├── COMPONENT_SCRIPTS_README.md
│   ├── ALL_FIXED_SVGS.md
│   ├── circuit_placer.py              # [EXP] Prototype
│   ├── netlist_parser.py              # [EXP] Parser
│   ├── component_library_builder.py   # [EXP] Builder
│   ├── svg_to_lamp_smart.py           # [EXP] Duplicate!
│   ├── svg_to_lamp_smartv2.py         # [EXP] v2
│   ├── test_*.sh                      # [EXP] Test scripts
│   ├── *.net                          # [EXP] Sample netlists
│   └── components/                    # [EXP] SVG files
│
├── examples/                          # [MIXED] Examples & library
│   ├── Electrical_symbols_library.svg # ⭐ 214 symbols! (450KB)
│   ├── Library.svg
│   ├── component_library_demo.sh      # [DEMO] Demo script
│   └── dynamic_ui_demo.sh             # [DEMO] UI demo
│
├── components/                        # [DUPLICATE] Individual SVGs
│   ├── R.svg, C.svg, L.svg, etc.     # Also in claude/components/
│   └── e/                            # Empty subdirectory
│
└── resources/                         # [MIXED] Docs + repos + tests
    ├── README.md
    ├── documentation/                 # Empty?
    ├── examples/                      # More examples
    ├── testing-utilities/             # Test utilities
    └── repos/
        └── rmkit/                     # ⭐ Full rmkit source tree!
```

### AFTER (Proposed Structure)

```
lamp-v2/
├── README.md                          # ⭐ Concise overview + links
├── QUICKSTART.md                      # ⭐ 5-minute getting started
├── CHANGELOG.md                       # Version history
├── LICENSE                            # Promoted from old/
├── REPO_ANALYSIS.md                   # This analysis
├── REORGANIZATION_PLAN.md             # This plan
│
├── docs/                              # 📚 All documentation
│   ├── README.md                      # Documentation map
│   ├── user-guide/
│   │   ├── installation.md            # From old/INSTALL.md + claude/
│   │   ├── eraser-commands.md         # Extracted from README
│   │   ├── component-library.md       # Library usage guide
│   │   ├── circuit-builder.md         # From CIRCUIT_BUILDER_README.md
│   │   └── examples.md                # Example workflows
│   ├── development/
│   │   ├── architecture.md            # System design
│   │   ├── svg-parsing.md             # From claude/SVG_PARSING_TECHNICAL.md
│   │   ├── component-system.md        # Component design
│   │   └── contributing.md            # How to contribute
│   └── history/
│       ├── development-phases.md      # From old/DEV_HISTORY.md
│       └── design-decisions.md        # Why choices were made
│
├── src/                               # 💻 Source code (production)
│   ├── core/                          # Core functionality
│   │   ├── svg_to_lamp.py             # ← svg_to_lamp_improved.py (canonical)
│   │   ├── circuit_builder.py         # ← circuit_builder.py
│   │   ├── component_definitions.py   # ← component_definitions.py
│   │   └── __init__.py
│   ├── tools/                         # Utility tools
│   │   ├── component_selector.py      # From old/
│   │   ├── netlist_parser.py          # From claude/
│   │   ├── text_to_lamp.py            # From old/
│   │   └── __init__.py
│   └── build/                         # Build system
│       ├── build_lamp_enhanced.sh     # ← build_lamp_enhanced.sh
│       ├── main_with_eraser.cpy       # ← main_with_eraser.cpy
│       └── patches/
│           └── lamp_eraser.patch      # ← old/lamp_eraser.patch
│
├── config/                            # ⚙️ Configuration files
│   ├── component_library.json         # ← component_library.json (canonical)
│   ├── component_definitions.json     # ← component_definitions.json
│   └── examples/
│       └── custom_config.json         # Example configuration
│
├── assets/                            # 🎨 Static assets
│   ├── symbols/
│   │   ├── Electrical_symbols_library.svg  # ← examples/...svg
│   │   └── individual/                # Individual extracted symbols
│   │       ├── R.svg                  # ← components/R.svg
│   │       ├── C.svg
│   │       ├── L.svg
│   │       └── ...
│   └── examples/                      # Example files
│       ├── rc_vdc_circuit.lamp        # ← rc_vdc_circuit.lamp
│       ├── component_library_demo.sh  # ← examples/...
│       └── dynamic_ui_demo.sh         # ← examples/...
│
├── tests/                             # 🧪 Testing infrastructure
│   ├── test_eraser.sh                 # From old/
│   ├── test_components.sh             # Consolidated tests
│   ├── test_circuit_builder.py        # New test
│   └── README.md                      # Test documentation
│
├── scripts/                           # 🔧 Utility scripts
│   ├── deploy_to_tablet.sh            # Renamed from send_lamp.sh
│   ├── send_lamp.sh                   # ← send_lamp.sh
│   ├── svg_gallery.sh                 # ← svg_gallery.sh
│   └── svg_to_rm2.sh                  # ← svg_to_rm2.sh
│
├── archive/                           # 📦 Historical development
│   ├── README.md                      # Archive overview
│   ├── phase1-eraser/                 # Eraser foundation
│   │   └── legacy/                    # ← old/ directory
│   │       ├── DEV_HISTORY.md
│   │       ├── component_library.py
│   │       └── ...
│   ├── phase2-components/             # Component library v1.0
│   │   └── (extracted from old/)
│   ├── phase3-circuits/               # Circuit builder dev
│   │   └── (extracted from claude/)
│   └── experiments/                   # Experimental code
│       ├── README.md                  # Experiment context
│       ├── ai-assisted/               # ← claude/ directory
│       │   ├── circuit_placer.py
│       │   ├── svg_to_lamp_smart.py
│       │   └── ...
│       └── svg-converters/            # Alternative implementations
│           ├── svg_to_lamp_smart.py
│           └── svg_to_lamp_svgpathtools.py
│
└── vendor/                            # 📚 External dependencies
    └── resources/                     # ← resources/ directory
        └── repos/
            └── rmkit/                 # rmkit source code
```

---

## Key Improvements

### 1. Clear Separation of Concerns

| Directory | Purpose | Old Location |
|-----------|---------|--------------|
| `src/` | Production code | Root + old/ + claude/ |
| `docs/` | Documentation | Root + old/ + claude/ |
| `config/` | Configuration | Root + old/ + claude/ |
| `assets/` | Static files | examples/ + components/ |
| `tests/` | Testing | old/ + claude/ |
| `scripts/` | Utilities | Root |
| `archive/` | History | old/ + claude/ |
| `vendor/` | External | resources/ |

### 2. Eliminated Duplication

| File Type | Before | After | Archived |
|-----------|--------|-------|----------|
| SVG converters | 7 files | 1 canonical | 6 in archive |
| component_library.json | 4 files | 1 canonical | 3 in archive |
| Documentation | 35+ files | ~12 consolidated | Rest in archive |
| Test scripts | 15+ scattered | ~5 organized | Old tests archived |

### 3. Improved Discoverability

**User Journey:**
1. **First visit:** `README.md` → Overview + feature list
2. **Getting started:** `QUICKSTART.md` → 5-minute tutorial
3. **Deep dive:** `docs/user-guide/` → Comprehensive guides
4. **Development:** `docs/development/` → Architecture and design
5. **History:** `docs/history/` + `archive/` → Full development story

**Developer Journey:**
1. **Browse code:** `src/` → Clear structure by purpose
2. **Run tests:** `tests/` → All tests in one place
3. **Build:** `src/build/` → Build system isolated
4. **Configure:** `config/` → All configs together
5. **Experiment:** `archive/experiments/` → See historical approaches

---

## Migration Details

### Files by Action

#### MOVE (with git mv - preserves history)
```bash
# Production code
circuit_builder.py → src/core/
component_definitions.py → src/core/
svg_to_lamp_improved.py → src/core/svg_to_lamp.py

# Configuration
component_library.json → config/
component_definitions.json → config/

# Build system
build_lamp_enhanced.sh → src/build/
main_with_eraser.cpy → src/build/

# Scripts
send_lamp.sh → scripts/
svg_gallery.sh → scripts/
svg_to_rm2.sh → scripts/

# Assets
examples/* → assets/examples/
components/* → assets/symbols/individual/

# Archives
old/ → archive/phase1-eraser/legacy/
claude/ → archive/experiments/ai-assisted/

# Vendor
resources/ → vendor/resources/
```

#### COPY (preserve in archive + production)
```bash
old/lamp_eraser.patch → src/build/patches/lamp_eraser.patch
```

#### CREATE NEW
```bash
docs/README.md
docs/user-guide/*.md
docs/development/*.md
docs/history/*.md
archive/README.md
archive/experiments/README.md
QUICKSTART.md
CHANGELOG.md
tests/README.md
```

#### CONSOLIDATE (multiple → one)
```bash
# Installation docs
old/INSTALL.md + claude/INSTALLATION.md → docs/user-guide/installation.md

# Circuit builder docs
CIRCUIT_BUILDER_README.md + claude/CIRCUIT_ASSEMBLY_README.md → docs/user-guide/circuit-builder.md

# Development history
old/DEV_HISTORY.md → docs/history/development-phases.md

# Technical notes
claude/SVG_PARSING_TECHNICAL.md → docs/development/svg-parsing.md
```

---

## Execution Steps

### Step 1: Pre-flight Checks
```bash
# Ensure clean working tree
git status

# Create backup branch
git branch backup-before-reorganization

# Ensure we're on the right branch
git checkout claude/analyze-organize-repo-01VtuYbC41VhEdaK2m4dtHwx
```

### Step 2: Run Reorganization Script
```bash
# Dry run first (see what would happen)
./reorganize_repo.sh --dry-run

# Review output, then execute
./reorganize_repo.sh
```

### Step 3: Manual Documentation Consolidation
```bash
# Create consolidated docs (manual editing required)
# Merge related documentation into coherent guides
```

### Step 4: Update Path References
```bash
# Search for hardcoded paths
grep -r "old/" src/
grep -r "claude/" src/
grep -r "examples/" src/

# Update imports
# Update script paths
# Update documentation links
```

### Step 5: Testing
```bash
# Test build system
cd src/build && ./build_lamp_enhanced.sh

# Test scripts
scripts/svg_gallery.sh --help

# Verify Python imports
python3 -c "from src.core import svg_to_lamp"
```

### Step 6: Commit
```bash
git add .
git commit -m "Reorganize repository structure

- Move production code to src/
- Consolidate documentation in docs/
- Archive historical development phases
- Eliminate duplicate files
- Establish clear directory structure

All git history preserved using git mv.

See REPO_ANALYSIS.md and REORGANIZATION_PLAN.md for details."
```

### Step 7: Push
```bash
git push -u origin claude/analyze-organize-repo-01VtuYbC41VhEdaK2m4dtHwx
```

---

## Risk Mitigation

### Backup Strategy
1. **Git branch:** `backup-before-reorganization` created before any changes
2. **Git reflog:** Can recover any state for 30+ days
3. **Remote backup:** Push backup branch to GitHub before reorganization

### Rollback Plan
```bash
# If something goes wrong:
git reset --hard backup-before-reorganization

# Or use reflog:
git reflog
git reset --hard HEAD@{n}  # where n is the commit before reorganization
```

### Validation Checklist
- [ ] All files accounted for (none deleted accidentally)
- [ ] Git history preserved (check with `git log --follow`)
- [ ] Build system works
- [ ] Python imports work
- [ ] Scripts execute correctly
- [ ] Documentation links valid
- [ ] Tests run successfully

---

## Post-Reorganization Tasks

### Immediate (Day 1)
1. Update all path references in code
2. Fix imports in Python files
3. Update script paths
4. Test build process
5. Validate critical workflows

### Short-term (Week 1)
1. Write new QUICKSTART.md
2. Consolidate user documentation
3. Create documentation map (docs/README.md)
4. Update main README.md
5. Write CHANGELOG.md

### Medium-term (Month 1)
1. Add CI/CD workflows (.github/workflows/)
2. Set up automated testing
3. Add linting configuration
4. Create contributing guidelines
5. Tag release: v2.0-reorganized

---

## Success Metrics

After reorganization, we should achieve:

✅ **Clarity:** New contributor understands structure in < 5 minutes
✅ **Efficiency:** No duplicate files with unclear purposes
✅ **History:** All development phases documented and archived
✅ **Onboarding:** QUICKSTART.md gets users running in < 10 minutes
✅ **Maintainability:** Clear where to add new features
✅ **Professionalism:** Repository looks production-ready

---

## Questions & Answers

### Q: Will this break anything?
**A:** No. All active code paths will be updated. Git history is preserved.

### Q: What if we need something from archive/?
**A:** Everything in archive/ has full git history. Can always extract and restore.

### Q: Why not delete old files?
**A:** They document the development journey and design decisions. Archiving > deleting.

### Q: How long will this take?
**A:** ~30 minutes for script execution, ~2-4 hours for documentation consolidation.

### Q: Can we roll back?
**A:** Yes, easily. Backup branch + git reflog provide multiple rollback options.

---

## Next Step

**DECISION POINT:** Review this plan and:

1. **Approve:** Run `./reorganize_repo.sh --dry-run` to preview
2. **Modify:** Adjust plan based on concerns
3. **Defer:** Wait for better time

**Recommendation:** Proceed with dry-run to validate approach.
