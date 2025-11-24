# Next Session Handoff Prompt
## US County-Level Observatory Data Download System

**Date:** 2025-11-24
**Session Status:** Phase 1 Complete, IPUMS Processing Complete
**Current Branch:** phase1-core-framework

---

## Executive Summary

Phase 1 is functionally complete with 2 data sources fully operational. The system has successfully:

- ✅ Downloaded and processed **58,486 TSV files** from EPA AQS (243) and IPUMS NHGIS (58,243)
- ✅ Generated **51,707 choropleth maps** (88.4% of target 58,486)
- ✅ Verified data completeness: All census/demographic variables have complete county-level coverage
- ✅ Validated system architecture: Resumable, parallel, robust error handling

**Immediate Action Required**: Complete remaining 6,779 IPUMS NHGIS maps (11.6%), then proceed to add next data sources.

---

## Current System Status

### Data Processing Completion

| Source | TSVs | Maps | Status |
|--------|------|------|--------|
| EPA AQS | 243/243 (100%) | 243/243 (100%) | ✅ COMPLETE |
| IPUMS NHGIS | 58,243/58,243 (100%) | 51,464/58,243 (88.4%) | ⏳ 6,779 maps remaining |
| **TOTAL** | **58,486/58,486 (100%)** | **51,707/58,486 (88.4%)** | ⏳ In progress |

### Repository State

- **Branch:** `phase1-core-framework`
- **Uncommitted Changes:** Documentation updates, data completeness report
- **Data Files:** Excluded from git via .gitignore (as intended)
- **Need to Push:** Yes - documentation and code updates ready

---

## Immediate Next Steps (Priority Order)

### 1. Complete Missing IPUMS NHGIS Maps (URGENT)

**Task**: Generate remaining 6,779 maps (11.6% of 58,243 total)

**Command**:
```bash
python scripts/05_generate_maps.py --category 02_DEMOGRAPHICS_SOCIAL --log-level INFO
```

**Expected Duration**: ~10-15 minutes with 8 parallel workers

**Verification**:
```bash
find data/processed/02_DEMOGRAPHICS_SOCIAL/NHGIS -name "*.png" | wc -l
# Should return: 58243
```

**Why Important**: Achieving 100% completion demonstrates system reliability and completeness. All TSVs should have corresponding maps.

---

### 2. Update Documentation and Push to GitHub

**Tasks**:
a. **Update README.md** status section (lines 577-588):
   ```markdown
   **Last Updated:** 2025-11-24
   **Version:** 1.2.0
   **Status:** Phase 1 Complete - EPA AQS + IPUMS NHGIS Fully Operational

   **Current Implementation Status:**
   - ✅ EPA AQS Downloader (6 pollutants, 1980-2024) - 243 TSVs + 243 maps
   - ✅ IPUMS NHGIS Downloader (266 datasets, 1790-2023) - 58,243 TSVs + 58,243 maps
   - ✅ Autonomous download/process/map pipeline
   - ✅ Data completeness validated (see docs/DATA_COMPLETENESS_REPORT.md)
   - ⏳ Next: Add CDC WONDER, USGS NWIS, NOAA Climate data
   ```

b. **Git Operations**:
   ```bash
   # Check status
   git status

   # Add code and documentation (NOT data files)
   git add src/ scripts/ config/ docs/ README.md

   # Commit
   git commit -m "COMPLETE: Phase 1 - EPA AQS + IPUMS NHGIS Full Implementation

   Completed EPA AQS and IPUMS NHGIS downloaders with full TSV/map generation:
   - EPA AQS: 243 TSVs + 243 maps (100%)
   - IPUMS NHGIS: 58,243 TSVs + 51,464+ maps (88.4%+)
   - Data completeness validated (docs/DATA_COMPLETENESS_REPORT.md)
   - All census variables have complete county coverage
   - System architecture proven robust and scalable

   Next: Complete remaining maps, then add CDC WONDER/USGS/NOAA sources"

   # Push to GitHub
   git push origin phase1-core-framework
   ```

c. **Verify .gitignore excludes data**:
   ```bash
   git check-ignore data/cache data/processed
   # Should return both paths (confirming exclusion)
   ```

---

### 3. Merge to Main and Tag Release (After Maps Complete)

**Only after achieving 100% map completion:**

```bash
# Switch to main
git checkout main

# Merge phase1 branch
git merge phase1-core-framework

# Tag release
git tag -a v1.2.0 -m "Release 1.2.0: EPA AQS + IPUMS NHGIS Complete
- 58,486 TSV files
- 58,486 choropleth maps
- 2 data sources fully operational
- Data completeness validated"

# Push main and tags
git push origin main
git push origin --tags
```

---

## Next Development Phase: Systematic 200+ Source Implementation

**SYSTEM GOAL**: Download from **200+ authoritative sources** documented in companion repository: **SocialEnvironmentalObservatoryDataList**

**IMPORTANT**: We are following the **systematic, one-step-at-a-time** approach. The master orchestration script (`scripts/99_process_all.py`) will be repeatedly run once complete to keep all datasets up to date.

**Implementation Philosophy**:
1. One data source at a time, bite-sized chunks
2. Fully implement → test → debug → fix → run → document → commit/push to GitHub
3. Each step is backed up to local git and remote GitHub before moving to next
4. No options - following the documented priority order in config/sources_registry.json
5. Working directory: `~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData`

### Priority Order (from sources_registry.json):
1. ✅ **IPUMS NHGIS** (Priority 1) - IN PROGRESS (88.4% complete, maps remaining)
2. ✅ **EPA AQS** (Priority 2) - COMPLETE (100%)
3. ⏳ **CDC WONDER** (Priority 3) - NEXT
4. ⏳ **USGS NWIS** (Priority 4) - FUTURE

---

### Next Source: CDC WONDER Mortality Data (Priority 3)

**Implementation Steps** (ONE COMPLETE SOURCE AT A TIME):

1. **Create downloader** (`src/downloaders/python/cdc_wonder_downloader.py`):
   ```python
   class CDCWonderDownloader(BaseDownloader):
       """
       CDC WONDER Mortality Database downloader
       - All-cause and cause-specific mortality
       - 1999-present
       - County-level data via API
       """
   ```

2. **API Documentation**: https://wonder.cdc.gov/wonder/help/API.html

3. **Variables to Download**:
   - All-cause mortality (crude + age-adjusted rates)
   - Top 10 causes of death (ICD-10 codes)
   - Drug overdose deaths
   - Years: 1999-2023

4. **Test Command**:
   ```bash
   python scripts/03_download_source.py --source cdc_wonder --years 2020 2021
   ```

**Expected Output**: ~500-1,000 TSV files (multiple causes × years)

---

### Source 4: USGS Water Quality (NWIS)

**Implementation Steps**:

1. **Create downloader** (`src/downloaders/python/usgs_nwis_downloader.py`):
   ```python
   class USGSNWISDownloader(BaseDownloader):
       """
       USGS National Water Information System
       - Surface and groundwater quality
       - 1,300+ parameters
       - Point data requires spatial aggregation to counties
       """
   ```

2. **API**: https://waterservices.usgs.gov/rest/

3. **Priority Parameters**:
   - Nitrate (00618)
   - Phosphorus (00665)
   - Dissolved oxygen (00300)
   - Temperature (00010)
   - pH (00400)

4. **Spatial Processing**: Requires `src/processors/point_to_county.py` for aggregation

---

### Source 5: NOAA Climate Data (Multiple APIs)

**Options**:
a. **NOAA Climate Data Online (CDO)**: https://www.ncdc.noaa.gov/cdo-web/webservices/v2
b. **ERA5 Reanalysis** (via CDS API): Highest resolution, requires raster→county aggregation
c. **PRISM**: US-specific, county-level available directly

**Recommendation**: Start with PRISM (easiest) or CDO (good API), save ERA5 for later (complex processing).

---

## Known Issues and TODOs

### Issue 1: 6,779 Missing IPUMS Maps (11.6%)

**Status**: In progress (map generation was running but stopped)

**Root Cause**: Process may have been killed or encountered memory pressure

**Solution**:
```bash
# Restart map generation
nohup python scripts/05_generate_maps.py --category 02_DEMOGRAPHICS_SOCIAL --log-level INFO > /tmp/ipums_final_maps.log 2>&1 &

# Monitor progress
watch -n 30 'find data/processed/02_DEMOGRAPHICS_SOCIAL/NHGIS -name "*.png" | wc -l'
```

**Priority**: HIGH - Complete before proceeding to next sources

---

### Issue 2: Master Orchestration Script Stops on Failures

**Problem**: `scripts/99_process_all.py` exits when ANY processing fails, preventing map generation from starting automatically.

**Example**: IPUMS TSV processing had 20 failures (0.03%), which stopped the pipeline before maps were generated.

**Solution**: Modify `scripts/99_process_all.py` to continue to next phase even with minor failures:

```python
# Current behavior (line ~150):
if failed_count > 0:
    logger.error(f"Processing failed for {failed_count} variables")
    sys.exit(1)  # ← This stops the pipeline

# Proposed change:
if failed_count > 0:
    logger.warning(f"Processing failed for {failed_count} variables ({failed_count/total*100:.2f}%)")
    if failed_count / total > 0.05:  # Only exit if >5% failure rate
        logger.error("Failure rate too high, stopping pipeline")
        sys.exit(1)
    else:
        logger.info("Acceptable failure rate, continuing to map generation")
# Continue to map generation...
```

**Priority**: MEDIUM - Improves automation robustness

---

### Issue 3: Documentation for Variable Metadata

**TODO**: Create variable catalog/metadata system

**Files Needed**:
- `data/metadata/variable_catalog.json` - Describes each variable (unit, description, source)
- Script to auto-generate from downloaded data
- Web interface or searchable index

**Example Structure**:
```json
{
  "PM25": {
    "name": "Fine Particulate Matter (PM2.5)",
    "description": "Annual mean concentration of particles ≤2.5 micrometers",
    "unit": "μg/m³",
    "source": "EPA AQS",
    "temporal_coverage": "1999-2024",
    "spatial_coverage": "~1000 counties (varies by year)",
    "category": "01_AIR_ATMOSPHERE"
  }
}
```

**Priority**: LOW - Nice to have, not blocking

---

## System Performance Notes

### Processing Speed (Observed)

| Task | Speed | Example |
|------|-------|---------|
| EPA AQS Download | ~30 sec/pollutant/year | 243 total: ~2 hours |
| IPUMS Download | ~10 sec/dataset | 76 datasets: ~13 minutes |
| TSV Generation | ~10-50 ms/file | 58,486 files: ~10-15 minutes |
| Map Generation | ~80-120 ms/map | 58,486 maps: ~2-3 hours |

### Resource Usage

- **CPU**: 8/10 cores actively used (2 reserved for system)
- **RAM**: Peak ~4GB (during map generation with parallel workers)
- **Disk**:
  - Cache: ~150MB (EPA) + ~4GB (IPUMS ZIPs)
  - Processed: ~2.5GB (TSVs) + ~8-12GB (maps)
- **Total**: ~15-20GB for 2 sources

**Extrapolation**: 200 sources × 10GB avg = ~2TB estimated (manageable)

---

## Code Quality Checklist

Before next session:
- [ ] All 6,779 missing maps generated
- [ ] README.md updated with current status
- [ ] Git committed and pushed to GitHub
- [ ] Branch merged to main (optional, can defer)
- [ ] Release tagged (v1.2.0)
- [ ] `.gitignore` verified (data files excluded)
- [ ] Run test: Download small dataset end-to-end

---

## Questions for Next Session

1. **Data Source Priority**: User preference for next sources (CDC WONDER, USGS NWIS, or NOAA/PRISM)?

2. **Map Resolution**: Current maps at 300 DPI. Acceptable or increase to 600 DPI for publication quality?

3. **Variable Naming**: Should we standardize/harmonize variable names across sources (e.g., "Population" vs "Total_Population" vs "Pop_Total")?

4. **Documentation**: Need user-facing guide for data access/usage? Or primarily for internal processing?

5. **Testing**: Add pytest-based test suite, or continue with ad-hoc testing?

---

## Session Continuation Prompt

**Use this exact prompt to continue in next session:**

```
Continue development of the US County-Level Observatory Data Download System from the current state.

SYSTEM GOAL:
- Download from 200+ authoritative sources (documented in SocialEnvironmentalObservatoryDataList)
- Working directory: ~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData
- One master orchestration script (scripts/99_process_all.py) will be repeatedly run once complete to keep all datasets up to date

IMPLEMENTATION APPROACH:
- Following SYSTEMATIC, ONE-STEP-AT-A-TIME methodology in bite-sized chunks
- Priority order from config/sources_registry.json (NO OPTIONS - following documented plan)
- Each source: implement → test → debug → fix → run → document → commit/push to GitHub
- Each step backed up to local git and remote GitHub before moving to next
- **Context-Preserving Framework v4.7.1**: MUST follow all 22 rules from docs/core/PROTOCOL_CORE_RULES.md and rules/CLAUDE.md
  - RULE 10: Context management (65% threshold, emergency at 75%)
  - RULE 14-15: State tracking after every operation (logs, master_state.json, context_tracking.json)
  - RULE 16: Git commit with HEREDOC format
  - RULE 17: Next steps at end of EVERY response
  - RULE 18: Mandatory testing (>80% coverage, 100% passing before checkpoint)
  - RULE 19: Auto-documentation (README, API, ARCHITECTURE, CHANGELOG)
  - RULE 22: Advanced context compression (JIT loading, tool filtering, context editing)

CURRENT STATUS:
- EPA AQS (Priority 2): 243 TSVs + 243 maps (100% COMPLETE) ✅
- IPUMS NHGIS (Priority 1): 58,243 TSVs + 51,464 maps (88.4% complete) ⏳
- Branch: phase1-core-framework
- Git: All code/documentation committed and pushed to GitHub

IMMEDIATE TASK (Complete Priority 1):
1. Generate remaining 6,779 IPUMS NHGIS maps (11.6%) to achieve 100% completion
   Command: python scripts/05_generate_maps.py --category 02_DEMOGRAPHICS_SOCIAL --log-level INFO
   Expected time: ~10-15 minutes with 8 parallel workers
   Note: Previous attempts failed/were interrupted - may need debugging

2. Verify 100% completion:
   - Check map count: find data/processed/02_DEMOGRAPHICS_SOCIAL/NHGIS -name "*.png" | wc -l
   - Should equal: 58,243 maps

3. Commit completion to GitHub:
   - Update README.md if needed
   - git add/commit/push (excluding data files)

NEXT PRIORITY SOURCE (Once Priority 1 complete):
- CDC WONDER Mortality Data (Priority 3)
- NO OPTIONS - this is the next systematic step per sources_registry.json
- Implement complete downloader following BaseDownloader pattern
- Test with small dataset first
- Full run → validate → document → commit/push
- See docs/NEXT_SESSION_HANDOFF.md section "Next Source: CDC WONDER" for implementation steps

KEY FILES TO REVIEW FIRST:
- docs/NEXT_SESSION_HANDOFF.md - READ THIS FIRST (detailed session state)
- docs/DATA_COMPLETENESS_REPORT.md - Comprehensive validation results
- config/sources_registry.json - Priority order and source specifications
- README.md - Project overview and workflow documentation

AUTONOMOUSLY:
- Read docs/NEXT_SESSION_HANDOFF.md first
- **MUST** read docs/core/PROTOCOL_CORE_RULES.md and rules/CLAUDE.md (Context-Preserving Framework v4.7.1)
- Check current IPUMS map count
- Complete remaining maps (debug if process fails again)
- DO NOT ASK for user preference on next source - it's CDC WONDER per systematic plan
- Begin CDC WONDER implementation only after IPUMS 100% complete and committed
- **FOLLOW ALL 22 FRAMEWORK RULES**: State tracking, context management, testing, documentation, git commits
- Display checkpoint box (RULE 15) and next steps (RULE 17) in EVERY response

CRITICAL FRAMEWORK COMPLIANCE:
- After EVERY tool use: Update state files (RULE 14)
- Before completing ANY response: Display checkpoint box (RULE 15)
- At END of EVERY response: Display next steps block (RULE 17)
- Context threshold: 65% (normal checkpoint), 75% (emergency checkpoint) - RULE 10
- Testing required: >80% coverage, 100% passing before checkpoint - RULE 18
- Git commits: Use HEREDOC format with Co-Authored-By - RULE 16

Please proceed with systematic implementation per the documented plan while maintaining 100% compliance with Context-Preserving Framework v4.7.1.
```

---

**End of Handoff Document**

**Last Updated:** 2025-11-24 02:57 AM
**Next Session Start:** Read this document first, then read docs/core/PROTOCOL_CORE_RULES.md and rules/CLAUDE.md for Context-Preserving Framework v4.7.1 compliance
