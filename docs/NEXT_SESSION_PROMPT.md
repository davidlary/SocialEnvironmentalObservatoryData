# NEXT SESSION RECOVERY PROMPT
## US County-Level Observatory Data Download System

**Date**: 2025-11-24 04:00 UTC
**Branch**: phase1-core-framework
**Last Commit**: 2226882 (ADD: Script 02 - Source Registry Builder)
**Framework**: Context-Preserving Framework v4.7.1 MANDATORY
**Directory**: ~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData

---

## 🚨 CRITICAL FIRST: Read These Files

**MANDATORY BEFORE ANY WORK**:
1. **CLAUDE.md** - Contains all 22 CPF rules (RFC 2119 MUST/SHALL keywords binding)
2. **IMPLEMENTATION_PLAN.md** lines 414-453 - Phase 3 requirements
3. **README.md** lines 100-136 - Quick start and current status

**Framework Hooks**: ✅ ACTIVE (.claude/hooks/, .claude/settings.local.json)

---

## ✅ COMPLETED THIS SESSION

### Phase 1: Data Collection ✅
- EPA AQS: 243 TSVs + 243 maps
- IPUMS NHGIS: 58,243 TSVs + 51,707 maps
- **Total**: 58,486 TSVs + 51,950 maps = 110,436 files (~34 GB)
- **Commit**: 1efd4f5 | **Status**: Pushed to GitHub

### Phase 2: Source Registry Builder ✅
- **Script**: scripts/02_build_source_registry.py (520 lines)
- **Input**: 62 markdown files from companion repo
- **Output**: config/sources_registry.json (104 sources, 8 categories)
- **Output**: config/variable_catalog.json (placeholder)
- **Commit**: 2226882 | **Status**: Pushed to GitHub

### Bug Fixes ✅
- Fixed src/__init__.py: `import core` → `from . import core`
- Fixed src/core/__init__.py: `import core.logger` → `from . import logger`

---

## 🎯 NEXT TASK: Phase 3 - Enhance Script 03

**File**: scripts/03_download_source.py
**Status**: EXISTS, works for --source epa_aqs and --source nhgis
**Needs**: Enhancement per IMPLEMENTATION_PLAN.md lines 414-453

### Required Enhancements

**1. Registry Integration**
- Read config/sources_registry.json
- Dynamically load source configurations
- Dynamically instantiate downloader classes

**2. Add --category Flag**
```bash
python scripts/03_download_source.py --category 01_AIR_ATMOSPHERE
# Downloads all sources in specified category
```

**3. Add --all Flag**
```bash
python scripts/03_download_source.py --all
# Downloads all sources in priority order (1→5)
# Skips blocked/restricted sources
```

**4. Priority-Based Processing**
- Process sources by priority: 1 (highest) → 5 (lowest)
- Skip sources with status == "blocked" or "restricted"
- Skip sources with no downloader_class defined (log warning)

---

## 📋 IMPLEMENTATION CHECKLIST (ONE AT A TIME)

### Task 1: Registry Integration
- [ ] Read IMPLEMENTATION_PLAN.md lines 414-453 for exact requirements
- [ ] Read current scripts/03_download_source.py structure
- [ ] Add function to load sources from config/sources_registry.json
- [ ] Add dynamic downloader class instantiation
- [ ] Test with existing sources (epa_aqs, nhgis)
- [ ] Test error handling (source with no downloader)
- [ ] Document changes
- [ ] Git commit with proper format
- [ ] Git push

### Task 2: Add --category Flag
- [ ] Add argparse --category argument
- [ ] Filter sources by category from registry
- [ ] Implement category processing loop
- [ ] Test: python scripts/03_download_source.py --category 01_AIR_ATMOSPHERE
- [ ] Verify priority order respected within category
- [ ] Document changes
- [ ] Git commit + push

### Task 3: Add --all Flag
- [ ] Add argparse --all argument
- [ ] Implement priority-ordered processing
- [ ] Add source filtering (skip blocked/restricted/no-downloader)
- [ ] Add dry-run mode for testing
- [ ] Test: python scripts/03_download_source.py --all --dry-run
- [ ] Document changes
- [ ] Git commit + push

---

## 🔧 Context-Preserving Framework v4.7.1 Compliance

### Critical Rules (See CLAUDE.md for All 22)
1. **RULE 2**: ONE_STEP_AT_A_TIME - No exceptions
2. **RULE 3**: Follow IMPLEMENTATION_PLAN.md - No options
3. **RULE 15**: Display checkpoint box BEFORE completing response
4. **RULE 16**: Git commit format (see examples: 1efd4f5, 2226882)
5. **RULE 17**: Display next steps AT END of response

### Checkpoint Box Format
```
═══════════════════════════════════════════════════════════════════════
📊 STATE TRACKING CHECKPOINT (AUTOMATIC - RULES 14-17)
═══════════════════════════════════════════════════════════════════════
✅ Operation logged: [type]
✅ State updated: [timestamp]
✅ Context tracked: [N]K tokens ([X.X]%)
✅ Threshold check: [SAFE/WARNING/CRITICAL]
✅ Git status: [commit hash]
═══════════════════════════════════════════════════════════════════════
```

---

## 📁 KEY FILES

### Must Read
- IMPLEMENTATION_PLAN.md (lines 414-453 for Phase 3)
- CLAUDE.md (22 mandatory rules)
- config/sources_registry.json (104 sources)
- scripts/03_download_source.py (current implementation)

### Scripts Status
```
scripts/00_setup_environment.py          ✅ Complete
scripts/01_download_metadata.py          ✅ Complete
scripts/02_build_source_registry.py      ✅ Complete (NEW)
scripts/03_download_source.py            ⏳ Needs enhancement
scripts/04_process_cached_data.py        ✅ Complete
scripts/05_generate_maps.py              ✅ Complete
```

---

## 🚫 CRITICAL DON'TS

❌ DO NOT ask "what should we do next?" or provide options
❌ DO NOT deviate from IMPLEMENTATION_PLAN.md
❌ DO NOT skip testing before committing
❌ DO NOT combine multiple tasks
❌ DO NOT refactor unnecessarily
❌ DO NOT ignore CPF rules

---

## ✅ CRITICAL DO'S

✅ Read IMPLEMENTATION_PLAN.md lines 414-453 for exact requirements
✅ Follow ONE_STEP_AT_A_TIME methodology
✅ Test everything before committing
✅ Use proper git commit format (see examples)
✅ Display checkpoint box before completing response
✅ Display next steps at end of response
✅ Update this file at end of session

---

## 📊 STATISTICS

**Sources in Registry**: 104 (from 62 markdown files)
**Sources Operational**: 2 (EPA AQS, NHGIS)
**Sources Priority 2**: 1 (ready for implementation)
**Sources Priority 3**: 26 (operational, ready)
**Sources Blocked**: 5 (data access issues)
**Variables Operational**: 58,486 county-level indicators
**Files Generated**: 110,436 (TSVs + maps)
**Data Size**: ~34 GB

---

## 🔗 GIT STATUS

**Branch**: phase1-core-framework
**Remote**: https://github.com/davidlary/SocialEnvironmentalObservatoryData.git
**Last Commit**: 2226882
**Status**: Clean (all changes committed and pushed)

---

## 🎬 SUGGESTED SESSION START

```
I see from NEXT_SESSION_PROMPT.md that Phase 1 (data collection) and
Phase 2 (source registry) are complete. Next task is Phase 3 per
IMPLEMENTATION_PLAN.md lines 414-453: enhance scripts/03_download_source.py
with --category and --all flags.

Current situation:
✅ Phase 0-2 complete (58,486 variables, 104 sources in registry)
⏳ Phase 3: Enhance Script 03 with registry integration

Following Context-Preserving Framework v4.7.1 (22 rules mandatory).
Following ONE_STEP_AT_A_TIME methodology.

Task 1: Add registry integration to Script 03
- Read IMPLEMENTATION_PLAN.md lines 414-453
- Read current Script 03 structure
- Implement dynamic source loading from registry
- Test with existing sources
- Document and commit

Starting now...
```

---

**Last Updated**: 2025-11-24T04:00:00Z
**Context**: 100K tokens used (50% - SAFE)
**Framework**: v4.7.1 ACTIVE
**Next**: Enhance Script 03 per IMPLEMENTATION_PLAN.md lines 414-453
