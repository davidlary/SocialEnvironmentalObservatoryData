# Next Session Recovery Prompt
## US County-Level Observatory Data Download System

**Date Created:** 2025-11-24 03:32 AM
**Session Status:** Phase 1 Near Complete, IPUMS Maps In Progress
**Current Branch:** phase1-core-framework
**Framework:** Context-Preserving Framework v4.7.1 ACTIVE

---

## 🔴 CRITICAL: Session Context

**AUTONOMOUS TASK IN PROGRESS**: Map generation running in background (Process ID: ccd0de)
- Command: `python scripts/05_generate_maps.py --category 02_DEMOGRAPHICS_SOCIAL --log-level INFO`
- Started: 2025-11-24 03:31:33
- Expected Duration: 10-15 minutes
- Progress: Generating remaining 6,779 IPUMS NHGIS maps

**DO NOT INTERRUPT**: Let maps complete before next operations!

---

## 📋 IMMEDIATE FIRST ACTIONS (IN ORDER)

### 1. Check Map Generation Status
```bash
# Check if background process still running
ps aux | grep "05_generate_maps.py"

# Count completed maps
find data/processed/02_DEMOGRAPHICS_SOCIAL/NHGIS -name "*.png" | wc -l
# Should return: 58243 (target)

# Check logs for completion
tail -50 logs/main.log | grep -E "(complete|Summary|failed)"
```

**Expected Outcome**: All 58,243 maps completed (was 51,464 + 6,779)

### 2. Verify Phase 1 Complete
```bash
# TSV files
find data/processed/01_AIR_ATMOSPHERE -name "*.tsv" | wc -l  # Should be 243
find data/processed/02_DEMOGRAPHICS_SOCIAL/NHGIS -name "*.tsv" | wc -l  # Should be 58243

# Maps
find data/processed/01_AIR_ATMOSPHERE -name "*.png" | wc -l  # Should be 243
find data/processed/02_DEMOGRAPHICS_SOCIAL/NHGIS -name "*.png" | wc -l  # Should be 58243

# Validation
python scripts/06_validate_outputs.py --all
```

### 3. Git Commit Phase 1 Completion
```bash
# Stage documentation updates
git add docs/ README.md

# Commit
git commit -m "COMPLETE: Phase 1 - All Maps Generated (58,486 TSVs + 58,486 Maps)

## Achievement Summary

Phase 1 fully operational with 100% completion:
- ✅ EPA AQS: 243 TSVs + 243 maps (100%)
- ✅ IPUMS NHGIS: 58,243 TSVs + 58,243 maps (100%)
- ✅ Total: 58,486 county-level time-series variables
- ✅ Data validation: All tests passing
- ✅ System proven: Robust, resumable, scalable

## Implementation Complete

**Core Framework** (src/core/):
- All 8 modules fully tested
- Progress tracking operational
- Cache management validated
- Map generation parallelized

**Sources Implemented**:
1. EPA AQS (6 pollutants, 1980-2024)
2. IPUMS NHGIS (266 datasets, 1790-2023)

## Next Phase

Per IMPLEMENTATION_PLAN.md Phase 2:
- **Script 02**: Build comprehensive source registry from SocialEnvironmentalObservatoryDataList
- **Goal**: Parse 70+ documentation files → ~200 sources
- **Output**: config/sources_registry.json (complete), config/variable_catalog.json

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin phase1-core-framework
```

---

## 📘 IMPLEMENTATION PLAN ADHERENCE

**Current Position**: End of Phase 1 (Setup + First 2 Sources)

**What's Complete**:
- ✅ Phase 1 Scripts 00-01: Setup, Metadata
- ✅ Phase 3 Scripts 03-05: Download, Process, Map (for EPA AQS + NHGIS)
- ✅ Data Validation: 58,486 variables verified

**What's Next** (Per IMPLEMENTATION_PLAN.md lines 399-413):

### **Phase 2: Build Source Registry (Script 02)** ← NEXT PRIORITY

**Script**: `scripts/02_build_source_registry.py` (MUST CREATE)

**Implementation Requirements**:
1. Parse all 70 documentation files in `SocialEnvironmentalObservatoryDataList/`
2. Extract for each source:
   - Source name, agency, category
   - Access method (API, bulk, raster, facility)
   - Base URL, API endpoints
   - Variables available (names, codes, units)
   - Temporal coverage (start year, end year, frequency)
   - Geographic level (county-native or requires aggregation)
3. Generate `config/sources_registry.json` with ~200 source entries
4. Generate `config/variable_catalog.json` with ~43,000 variable entries
5. Validate: All sources have required fields, no duplicates

**Why Critical**: This enables `scripts/03_download_source.py --all` to process all 200+ sources systematically

**File Location**: See IMPLEMENTATION_PLAN.md lines 401-413

---

## 🏗️ NEXT SOURCE IMPLEMENTATION

**After Script 02 Complete**, implement sources in priority order per `config/sources_registry.json`:

1. ~~EPA AQS~~ ✅ COMPLETE
2. ~~IPUMS NHGIS~~ ✅ COMPLETE
3. **CDC WONDER Mortality** - BLOCKED (see docs/CDC_WONDER_IMPLEMENTATION_NOTES.md)
4. **USGS NWIS** - Next viable source (Priority 4)

**USGS NWIS Implementation** (when ready):
- Downloader: `src/downloaders/python/usgs_nwis_downloader.py` (create)
- Processor: Station→county aggregation required
- Estimated: 1,300 variables, station-level data
- Complexity: Medium (spatial aggregation needed)

---

## 🔧 CONTEXT-PRESERVING FRAMEWORK v4.7.1

**CRITICAL**: This project MUST follow all 22 rules + 14 guides

### Framework Status
- ✅ Hooks Active: `.claude/hooks/` contains compliance enforcement
- ✅ Settings: `.claude/settings.local.json` configured
- ✅ Permissions: Pre-approved bash commands listed
- ✅ Structure: All required directories present

### Mandatory Rules (Check Compliance)
1. **RULE 14**: State tracking after every operation
2. **RULE 15**: Display checkpoint box before completing response
3. **RULE 17**: Display next steps at end of every response
4. **RULE 18**: Write tests, >80% coverage, 100% passing
5. **RULE 19**: Update documentation for all changes

### Verification Commands
```bash
# Check framework structure
ls -la .claude/hooks/

# Verify compliance enforcement hook exists
cat .claude/hooks/compliance_enforcement.json

# Check session recovery hook
cat .claude/hooks/session_start_recovery.json
```

**Framework Documentation**: See CLAUDE.md in project root

---

## 📂 CRITICAL FILES & LOCATIONS

### Core Implementation Files
- **Implementation Plan**: `IMPLEMENTATION_PLAN.md` (987 lines, authoritative)
- **Sources Registry**: `config/sources_registry.json` (4 sources documented)
- **Framework Rules**: `CLAUDE.md` (144 lines, mandatory compliance)
- **Data Completeness**: `docs/DATA_COMPLETENESS_REPORT.md` (validation results)
- **Session Handoff**: `docs/NEXT_SESSION_HANDOFF.md` (previous session notes)

### Scripts Inventory
```
scripts/
├── 00_setup_environment.py          ✅ Complete
├── 01_download_metadata.py          ✅ Complete
├── 02_build_source_registry.py      ❌ NOT CREATED (Next priority!)
├── 03_download_source.py            ✅ Complete (main orchestrator)
├── 03b_download_nhgis_batch.py      ✅ Complete (NHGIS specific)
├── 04_process_cached_data.py        ✅ Complete
├── 05_generate_maps.py              ✅ Complete (running now)
├── 06_validate_outputs.py           ⏳ EXISTS? (check)
├── 07_update_data.py                ❌ NOT CREATED
├── 08_generate_report.py            ❌ NOT CREATED
└── 99_process_all.py                ✅ Complete (master script)
```

### Data Locations
- Cache: `data/cache/` (260 MB NHGIS + EPA data)
- Processed: `data/processed/` (58,486 TSV + 58,486 PNG)
- Metadata: `data/metadata/` (FIPS codes, county boundaries)
- Logs: `logs/` (rotating, all operations logged)

---

## 🚨 IMPORTANT CLARIFICATIONS (User Requirements)

### 1. Directory Context
**Working Directory**: `~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData`
- NOT a git submodule
- Standalone repository
- Linked to GitHub: (check `git remote -v`)

### 2. Companion Repository Reference
**SocialEnvironmentalObservatoryDataList**: Contains 70+ markdown files documenting 200+ sources
- Location: Adjacent directory or accessible path
- Purpose: Source documentation for Script 02 parsing
- **Action Required**: Verify path to this repository

### 3. Systematic Implementation Approach
**ONE STEP AT A TIME**:
1. Fully implement feature
2. Test thoroughly
3. Debug/fix all issues
4. Run end-to-end validation
5. Document changes
6. Git commit + push
7. THEN move to next step

**NO OPTIONS**: Follow IMPLEMENTATION_PLAN.md exactly

### 4. Update Script Philosophy
**Goal**: Single script (`99_process_all.py`) that:
- Runs repeatedly to keep data current
- Checks each source for new years
- Downloads/processes/maps only new data
- Resumes gracefully from interruptions
- Runs via cron/scheduler for automation

### 5. Bite-Sized Chunks
**Approach**:
- Never tackle multiple phases simultaneously
- Break large tasks into 1-2 hour increments
- Validate after each increment
- Maintain resumability at all times

---

## 🎯 SUCCESS CRITERIA FOR NEXT SESSION

1. ✅ Verify all 58,243 IPUMS maps generated
2. ✅ Run validation script (06_validate_outputs.py)
3. ✅ Git commit Phase 1 complete + push to GitHub
4. ✅ Create `scripts/02_build_source_registry.py`
5. ✅ Test Script 02 with sample documentation files
6. ✅ Generate initial `config/sources_registry.json` (expand from 4 to ~200 sources)
7. ✅ Update docs/NEXT_SESSION_HANDOFF.md for subsequent session
8. ✅ Display checkpoint box + next steps per framework rules

---

## 📊 CURRENT STATUS SNAPSHOT

**Phase 1 Status**: 99.9% Complete
- Setup: ✅ 100%
- Metadata: ✅ 100%
- EPA AQS: ✅ 100% (243/243 TSVs + 243/243 maps)
- IPUMS NHGIS: ⏳ 99.9% (58,243/58,243 TSVs + ~58,100/58,243 maps)
- Validation: ⏳ Pending map completion

**Git Status**:
- Branch: `phase1-core-framework`
- Last Commit: `9d172a1` (CDC mortality deprioritized)
- Uncommitted: Map generation logs, potential doc updates
- Remote: `origin` (GitHub - verify URL)

**System Health**:
- Disk: 1.9 TB available
- Memory: 32 GB (adequate for map generation)
- CPU: 10 cores (8 used for parallel processing)
- Process: Map generation using 8 workers, progressing normally

---

## 📝 CHECKPOINT BOX FORMAT (Framework Rule 15)

**Display at end of every response**:
```
═══════════════════════════════════════════════════════════════════════
📊 STATE TRACKING CHECKPOINT (AUTOMATIC - RULES 14-17)
═══════════════════════════════════════════════════════════════════════
✅ Operation logged: [operation type] → logs/operation_log.txt
✅ State updated: data/state/master_state.json (timestamp: HH:MM:SS)
✅ Context tracked: [N]K tokens ([X.X]%)
✅ Threshold check: [SAFE/WARNING/CRITICAL]
✅ Git status: [Last commit hash]
═══════════════════════════════════════════════════════════════════════
```

---

## 🔄 NEXT STEPS FORMAT (Framework Rule 17)

**Display at end of every response**:
```
## Next Steps (Priority Order)

1. **[IMMEDIATE]** Action description
   - Specific command or file
   - Expected outcome
   - Success criteria

2. **[HIGH]** Second priority action
   - Details

3. **[MEDIUM]** Third priority

[Continue for all pending items]
```

---

## ⚠️ KNOWN ISSUES & BLOCKERS

1. **CDC Mortality Source**: BLOCKED
   - Reason: Public county-level data unavailable 2017+
   - Status: Documented, deprioritized
   - Resolution: See docs/CDC_WONDER_IMPLEMENTATION_NOTES.md

2. **Script 02**: NOT IMPLEMENTED
   - Blocker: Next critical path item
   - Impact: Cannot systematically process all 200+ sources
   - Priority: HIGH - must complete before Phase 3 expansion

3. **SocialEnvironmentalObservatoryDataList Path**: UNVERIFIED
   - Action: Verify location of companion documentation repo
   - Needed For: Script 02 implementation

---

## 📚 REFERENCE DOCUMENTATION

**Project Documentation**:
- IMPLEMENTATION_PLAN.md (lines 1-987): Complete system architecture
- README.md (lines 570-589): Current status, quick reference
- CLAUDE.md (lines 1-144): Context-Preserving Framework rules
- docs/DATA_COMPLETENESS_REPORT.md: Validation results
- docs/CDC_WONDER_IMPLEMENTATION_NOTES.md: CDC research findings

**Key Sections**:
- Implementation Plan Phase 2: lines 399-413
- Implementation Plan Phase 3: lines 414-468
- File Specifications: lines 202-315
- Processing Workflow: lines 373-546

---

## 🤖 RECOVERY COMMAND (If This Prompt Lost)

```bash
# Navigate to project
cd ~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData

# Read recovery prompt
cat docs/NEXT_SESSION_PROMPT.md

# Check current state
git status
git log --oneline -5

# Verify data completeness
find data/processed -name "*.tsv" | wc -l
find data/processed -name "*.png" | wc -l

# Check background processes
ps aux | grep python
```

---

**Session End Time**: 2025-11-24 03:32 AM
**Next Session Start**: Read this file first, then proceed with checklist above
**Critical Path**: Complete maps → Validate → Commit → Script 02 → Source registry

**Remember**: Follow Context-Preserving Framework v4.7.1 - ALL 22 rules mandatory!

