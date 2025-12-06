# NEXT SESSION START - US County-Level Observatory Data System

**Date**: 2025-12-06
**Branch**: `phase1-core-framework`
**Latest Commit**: `6356ea7` - "COMPLETE: Phase 9 - CSN Implementation Complete, Maps Generated"
**Framework**: Context-Preserving Framework v4.0.1 (22 rules MANDATORY)
**Directory**: `~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData`

---

## 🚨 CRITICAL: Context-Preserving Framework v4.0.1 Compliance

**BEFORE ANY WORK**, you MUST:

1. ✅ **Verify CPF hooks are active**: Check `.claude/hooks/` directory exists
2. ✅ **Check settings**: Verify `.claude/settings.local.json` is configured
3. ✅ **Read CLAUDE.md**: All 22 CPF rules are MANDATORY
4. ✅ **Follow ONE_STEP_AT_A_TIME methodology**: Complete one step fully (implement/test/debug/fix/run/document) BEFORE starting next
5. ✅ **Display checkpoint box** BEFORE completing EVERY response (RULE 15)
6. ✅ **Display next steps** AT END of EVERY response (RULE 17)
7. ✅ **Adhere to IMPLEMENTATION_PLAN.md**: Follow file names, directory structure, and workflow EXACTLY as specified
8. ✅ **Test everything**: Write tests, >80% coverage, 100% passing (RULE 18)
9. ✅ **Commit after each step**: Backup to local git and push to GitHub after completing each implementation step
10. ✅ **Update documentation**: Keep README.md, NEXT_SESSION_PROMPT.md, and implementation notes current (RULE 19)

**CPF Hooks Status**: ✅ ACTIVE (verified at .claude/hooks/, .claude/settings.local.json)

---

## 📋 PROJECT SUMMARY

**System Goal**: Download, process, and visualize 43,000+ variables from **200+ authoritative sources** documented in companion repository `SocialEnvironmentalObservatoryDataList` for 3,143 US counties.

**Methodology**: ONE script that orchestrates everything (`scripts/03_download_source.py`) repeatedly run to keep datasets current. Each source fully implemented/tested/debugged/fixed/run/documented before proceeding to next.

**Current Implementation Status**:
- **Phases Complete**: 9 of 10 (90%) ✅
- **Operational Data Sources**: 3 fully operational (EPA AQS, IPUMS NHGIS, CSN)
- **Implemented Awaiting Data**: 1 (CDC EPHT Radon - API down for maintenance)
- **Total Variables Operational**: 58,583 (EPA AQS: 243, NHGIS: 58,243, CSN: 97)
- **Total Files Generated**: ~116,959 files (~36 GB)
  - Cached files: 340 CSV
  - TSV files: 58,583
  - Map files: 58,036 PNG (99% complete)
- **Next Priority**: THREE-PRONGED APPROACH (Options A + B + C)

---

## 🎯 IMMEDIATE NEXT ACTIONS: THREE-PRONGED STRATEGY

### Overview: Parallel Progress on Multiple Fronts

This session will pursue **THREE simultaneous objectives** to maximize progress while managing blockers:

1. **Option A**: Implement next Priority 3 source (IMPROVE or EPA NEI)
2. **Option B**: Monitor and complete CDC EPHT Radon if API returns
3. **Option C**: Prepare for Phase 10 (Final System Integration)

**Why Three Options?**:
- **Option A** ensures forward progress on new data sources
- **Option B** capitalizes on opportunity if CDC API becomes available
- **Option C** prepares documentation and integration work that can proceed regardless of blockers

**Execution Strategy**: Start with Option A (primary path), but remain ready to pivot to Option B if API returns. Begin Option C preparation tasks in parallel where appropriate.

---

## 🎯 OPTION A: IMPLEMENT NEXT PRIORITY 3 SOURCE (PRIMARY PATH)

### Recommended Source: IMPROVE Network

**Why IMPROVE First?**:
1. ✅ **County-Native**: Direct county-level data, no aggregation needed
2. ✅ **Long Time Series**: 1988-2025 (37 years of data)
3. ✅ **Complementary to CSN**: Similar PM2.5 composition, rural/remote sites (CSN = urban)
4. ✅ **No API Key**: Public HTTP downloads, no authentication barriers
5. ✅ **CSV Format**: Standard format, easy processing
6. ✅ **Air Quality Category**: Completes Priority 3 air quality sources

**Alternative**: EPA National Emissions Inventory (NEI)
- County-native, triennial data 1990-2023
- Comprehensive emissions by pollutant and source sector
- Larger scope but more complex data structure

### Implementation Workflow for IMPROVE (7 Steps)

Follow IMPLEMENTATION_PLAN.md Section 5 exactly. ONE step at a time.

#### Step 1: Research IMPROVE Data Source (1-2 hours)

**File to Create**: `docs/IMPROVE_IMPLEMENTATION_NOTES.md`

**Research Tasks**:
1. Visit IMPROVE website: http://views.cira.colostate.edu/fed/DataWizard/
2. Identify data access method (bulk download URL, API, FTP)
3. Document data format and structure
4. Identify all available variables (PM2.5 composition, visibility, etc.)
5. Determine temporal coverage (confirm 1988-2025)
6. Check geographic coverage (site locations, county assignments)
7. Identify any authentication requirements
8. Document file formats and data dictionary
9. Test download of sample file (single year/site)
10. Create implementation plan outline

**Documentation Requirements**:
- Data access URL and method
- Complete variable list with units
- Temporal coverage details
- Geographic coverage (site-to-county mapping)
- Data format specifications
- Sample data structure
- Expected output (TSV count, file sizes)
- Implementation blockers (if any)
- Assessment: GREEN/YELLOW/RED status

**Validation**: Documentation complete, sample data downloaded, no blockers identified

**Commit**: After completing documentation with message format:
```
RESEARCH: IMPROVE Network - Priority 3 Source Analysis Complete

## Research Phase Complete
[Summary of findings]

## Files Created
- docs/IMPROVE_IMPLEMENTATION_NOTES.md ([N] lines)

## Key Findings
[Data access method, variables, coverage, assessment]

## Next Steps
[Implementation plan outline]
```

#### Step 2: Implement IMPROVEDownloader Class (2-3 hours)

**File to Create**: `src/downloaders/python/improve_downloader.py`

**Implementation Requirements**:
1. Inherit from `BaseDownloader` class
2. Implement required methods:
   - `__init__()`: Initialize with cache directory, logger
   - `get_available_variables()`: Return list of all IMPROVE variables
   - `get_available_years()`: Return list of available years
   - `download(variable, year, **kwargs)`: Download data for specific variable/year
   - `_validate_data()`: Validate downloaded data structure
3. Implement caching logic (check cache before download)
4. Implement retry logic with exponential backoff
5. Add rate limiting (be polite to data provider)
6. Add progress tracking integration
7. Handle site-to-county mapping
8. Aggregate daily → annual means at county level
9. Add comprehensive error handling
10. Add docstrings for all methods

**Code Structure**:
```python
"""
IMPROVE Network Downloader
Downloads PM2.5 composition and visibility data from IMPROVE monitoring sites
"""

import os
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from src.core.base_downloader import BaseDownloader
from src.core.logger import get_logger
from src.core.cache_manager import CacheManager
from src.core.retry_handler import retry_with_backoff

class IMPROVEDownloader(BaseDownloader):
    """
    Downloader for IMPROVE (Interagency Monitoring of Protected Visual Environments) Network

    Data Source: http://views.cira.colostate.edu/fed/
    Variables: PM2.5 composition (EC, OC, sulfate, nitrate, etc.), visibility
    Temporal Coverage: 1988-2025 (37 years)
    Geographic: Rural/remote monitoring sites mapped to counties
    Update Frequency: Annual
    """

    BASE_URL = "[TO BE DETERMINED FROM RESEARCH]"
    AVAILABLE_VARIABLES = [
        # To be populated from research
    ]

    def __init__(self, cache_dir: str = "data/cache/01_AIR_ATMOSPHERE/improve",
                 logger=None):
        """Initialize IMPROVE downloader"""
        super().__init__(cache_dir, logger)
        # Implementation

    def get_available_variables(self) -> List[str]:
        """Return list of available IMPROVE variables"""
        # Implementation

    def get_available_years(self) -> List[int]:
        """Return list of available years (1988-2025)"""
        # Implementation

    @retry_with_backoff(max_retries=3)
    def download(self, variable: str, year: int, **kwargs) -> pd.DataFrame:
        """
        Download IMPROVE data for specific variable and year

        Args:
            variable: IMPROVE variable name (e.g., 'ec', 'oc', 'sulfate')
            year: Year to download (1988-2025)
            **kwargs: Additional parameters (force_refresh, etc.)

        Returns:
            DataFrame with county-level annual means
        """
        # Implementation

    def _map_sites_to_counties(self, site_data: pd.DataFrame) -> pd.DataFrame:
        """Map IMPROVE site locations to FIPS county codes"""
        # Implementation

    def _aggregate_to_county(self, daily_data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate daily site data to annual county means"""
        # Implementation
```

**Validation**: Code follows IMPLEMENTATION_PLAN.md structure, inherits from BaseDownloader, all methods implemented

**Commit**: After implementation with message format:
```
ADD: IMPROVE Network Downloader - Priority 3 Implementation

## Implementation Complete

Implemented IMPROVEDownloader class for Priority 3 air quality source.

## Files Created
- src/downloaders/python/improve_downloader.py ([N] lines)

## Features Implemented
[List of features]

## Variables Supported
[List of variables]

## Data Coverage
[Geographic and temporal coverage]

## Next Steps
- Update scripts/03_download_source.py registry
- Create test script
```

#### Step 3: Update scripts/03_download_source.py Registry (15 minutes)

**File to Modify**: `scripts/03_download_source.py`

**Changes Required**:

1. Add import:
```python
from src.downloaders.python.improve_downloader import IMPROVEDownloader
```

2. Add to DOWNLOADER_REGISTRY:
```python
"improve": {
    "class": IMPROVEDownloader,
    "category": "01_AIR_ATMOSPHERE",
    "description": "IMPROVE Network - PM2.5 composition and visibility at rural sites",
    "source_id": "01_IMPROVE_NETWORK_INTERAGENCY_MO",
}
```

3. Add to SOURCE_ID_MAPPINGS:
```python
"01_IMPROVE_NETWORK_INTERAGENCY_MO": "improve"
```

**Validation**:
- Script imports without errors
- Registry lookup works: `python scripts/03_download_source.py --source improve --help`

**Commit**: After successful registry integration

#### Step 4: Create and Run Test Script (30 minutes)

**File to Create**: `scripts/test_improve.py`

**Test Cases** (minimum 7 tests):
1. Test downloader initialization
2. Test `get_available_variables()` returns list
3. Test `get_available_years()` returns 1988-2025
4. Test download single year (e.g., 2023)
5. Test cache functionality (second download uses cache)
6. Test data validation (check columns, FIPS codes)
7. Test county aggregation (daily → annual)

**Validation**: All 7 tests pass

**Commit**: After all tests pass

#### Step 5: Download Full IMPROVE Dataset (1-2 hours)

**Command**:
```bash
cd ~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData

# Option 1: Download all variables, all years
python scripts/03_download_source.py --source improve

# Option 2: Download specific variables for testing
python scripts/03_download_source.py --source improve \
  --variable ec,oc,sulfate,nitrate \
  --years 2020 2021 2022 2023 2024
```

**Expected Output**:
- Cache files in `data/cache/01_AIR_ATMOSPHERE/improve/`
- Expected size: Variable depending on data volume
- Expected duration: 30-60 minutes (depends on data size)

**Validation**:
- Check cache directory has all expected files
- Verify no download errors in logs
- Spot-check sample data for valid FIPS codes

**Commit**: After successful full download

#### Step 6: Convert to Standardized TSV Format (30 minutes)

**Option 1**: Use existing conversion script if it supports IMPROVE format

**Option 2**: Create IMPROVE-specific conversion script

**File to Create** (if needed): `scripts/convert_improve_to_tsv.py`

**Command**:
```bash
python scripts/04_process_cached_data.py --source improve
# OR
python scripts/convert_improve_to_tsv.py
```

**Expected Output**:
- TSV files in `data/processed/01_AIR_ATMOSPHERE/IMPROVE/`
- File format: `{variable}_{year}_{frequency}_data.tsv`
- Expected count: Variable count × year count

**Validation**:
- TSV files have correct structure (FIPS, state, county, value, year)
- Spot-check data values are reasonable
- All counties with data are present

**Commit**: After successful TSV generation

#### Step 7: Generate Choropleth Maps (1 hour)

**Command**:
```bash
python scripts/05_generate_maps.py --source IMPROVE
```

**Expected Output**:
- PNG maps in `data/processed/01_AIR_ATMOSPHERE/IMPROVE/`
- File format: `{variable}_{year}_{frequency}_map.png`
- Expected count: Same as TSV count

**Validation**:
- All PNG files created successfully
- Spot-check maps for visual quality
- Verify color scales are appropriate

**Commit**: After successful map generation

#### Step 8: Final Documentation and Registry Update (30 minutes)

**Files to Update**:

1. **config/sources_registry.json**:
```json
{
  "source_id": "01_IMPROVE_NETWORK_INTERAGENCY_MO",
  "status": "operational",  // Change from current status
  "implementation": {
    "downloader_class": "IMPROVEDownloader",
    "implemented": true,
    "test_status": "passed",
    "variable_count": [ACTUAL_COUNT]
  },
  "temporal_coverage": {
    "start_year": [ACTUAL_START],
    "end_year": [ACTUAL_END],
    "last_updated": "2025-12-06"
  },
  "access_method": {
    "type": [ACTUAL_TYPE],
    "url": [ACTUAL_URL],
    "authentication": [ACTUAL_AUTH]
  }
}
```

2. **NEXT_SESSION_PROMPT.md**: Add Phase 10 section documenting IMPROVE completion

**Final Commit**:
```
COMPLETE: IMPROVE Network Implementation - Priority 3 Source Operational

## Phase 10: IMPROVE Implementation Complete

Fourth operational data source successfully implemented.

## Implementation Summary
[Full details]

## System Status
- Operational Sources: 4 (EPA AQS, NHGIS, CSN, IMPROVE)
- Total Variables: [NEW_TOTAL]
- Total Files: [NEW_TOTAL]

## Next Steps
[Next Priority 3 source or Phase 10 final integration]
```

---

## 🎯 OPTION B: COMPLETE CDC EPHT RADON (OPPORTUNISTIC)

**Status**: Implementation complete, awaiting API availability

**Current Blocker**: CDC EPHT API has been down for "planned maintenance" since 2025-11-28 (8+ days)

### Monitoring Strategy

**Check API Status Regularly**:
```bash
# Quick API check
curl -s "https://ephtracking.cdc.gov/apigateway/api/v1/getMeasures" | head -50

# If no error message, API is back
```

### If API Returns During Session

**Immediate Actions** (30 minutes total):

1. **Test API Availability** (5 minutes):
```bash
cd ~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData
export CDC_EPHT_API_KEY=$(grep CDC_EPHT_API_KEY .env | cut -d'=' -f2)
python scripts/test_cdc_epht_radon.py
```

2. **Download Full Dataset** (15 minutes):
```bash
python scripts/03_download_source.py --source cdc_epht_radon \
  --variable radon_testing \
  --years 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022
```

Expected output: 10 cache files (one per year) in `data/cache/05_RADIATION/cdc_epht_radon/`

3. **Convert to TSV** (5 minutes):
```bash
python scripts/04_process_cached_data.py --source cdc_epht_radon
```

Expected output: ~80 TSV files in `data/processed/05_RADIATION/CDC_EPHT_RADON/`

4. **Generate Maps** (5 minutes):
```bash
python scripts/05_generate_maps.py --source CDC_EPHT_RADON
```

Expected output: ~80 PNG maps

5. **Update Registry** (5 minutes):
   - Change status in sources_registry.json from "ready_for_implementation" to "operational"
   - Update variable_count to actual count
   - Update temporal_coverage.last_updated to current date

6. **Commit**:
```
COMPLETE: CDC EPHT Radon - Priority 2 Source Operational

## API Returned - Data Download Complete

CDC EPHT API returned after [X] days of maintenance.

## Implementation Summary
- Variables: 8 (radon testing metrics)
- Years: 2013-2022 (10 years)
- Files: ~80 TSV + ~80 maps

## System Status
- Operational Sources: 4 or 5 (depending on IMPROVE status)
- Priority 2 Complete: ✅
```

### Parallel Monitoring

**While working on Option A**, periodically check API (every 1-2 hours):
- Use quick curl command above
- If API returns, pause Option A work, complete CDC EPHT first (30 min), then resume Option A

---

## 🎯 OPTION C: PREPARE FOR PHASE 10 (BACKGROUND TASKS)

**Phase 10 Goal**: Final system integration, documentation, and testing

### Tasks That Can Start Now

These tasks don't require new data sources and can proceed in parallel:

#### Task C1: Create System Documentation (1-2 hours)

**File to Create/Update**: `README.md`

**Content Sections**:
1. Project Overview and Goals
2. System Architecture Diagram
3. Data Sources Overview (table with all operational sources)
4. Installation and Setup Instructions
5. Usage Examples (how to run scripts)
6. Data Output Structure
7. API Keys and Authentication
8. Troubleshooting Common Issues
9. Contributing Guidelines
10. Citation and Acknowledgments

**Validation**: README is comprehensive and user-friendly

**Commit**: After README is complete

#### Task C2: Create Variable Catalog Export (30 minutes)

**File to Create**: `scripts/06_export_variable_catalog.py`

**Purpose**: Export complete catalog of all operational variables to shareable format

**Output**:
```
data/exports/variable_catalog_full.csv
data/exports/variable_catalog_by_source.csv
data/exports/variable_catalog_by_category.csv
```

**Columns**:
- variable_id
- variable_name
- source_id
- source_name
- category
- units
- temporal_coverage (start_year, end_year)
- geographic_coverage
- description
- file_path (to TSV)
- map_path (to PNG)

**Validation**: Catalog includes all 58,583+ operational variables

**Commit**: After catalog export works

#### Task C3: Create Data Quality Report (1 hour)

**File to Create**: `scripts/07_generate_quality_report.py`

**Purpose**: Generate comprehensive data quality report for all operational sources

**Report Sections**:
1. **Completeness**: % of counties with data for each variable
2. **Temporal Coverage**: Years available vs expected for each source
3. **Data Validation**: Check for outliers, missing values, invalid FIPS codes
4. **File Integrity**: Verify all expected TSV and PNG files exist
5. **Size Statistics**: File sizes, total storage used
6. **Processing Statistics**: Success rates, error rates

**Output**:
```
data/exports/data_quality_report.html
data/exports/data_quality_summary.json
```

**Validation**: Report runs successfully for all operational sources

**Commit**: After quality report works

#### Task C4: Update Implementation Plan Status (30 minutes)

**File to Update**: `IMPLEMENTATION_PLAN.md`

**Updates**:
- Mark completed phases as ✅ COMPLETE
- Update phase percentages
- Add actual implementation notes to each phase
- Document lessons learned
- Update timelines with actual durations
- Add troubleshooting notes for future sources

**Validation**: Implementation plan is accurate and current

**Commit**: After plan is updated

#### Task C5: Create Quick Start Guide (30 minutes)

**File to Create**: `docs/QUICK_START_GUIDE.md`

**Content**:
1. **Prerequisites**: Python version, disk space, API keys
2. **Installation**: Step-by-step setup
3. **First Run**: Download a single variable
4. **Common Workflows**:
   - Download all data for a source
   - Update existing data
   - Generate new maps
   - Export variable catalog
5. **Next Steps**: Links to full documentation

**Validation**: Guide is clear and concise (<500 lines)

**Commit**: After guide is complete

#### Task C6: Performance Optimization Analysis (1 hour)

**File to Create**: `docs/PERFORMANCE_ANALYSIS.md`

**Analysis Topics**:
1. Current processing times per source
2. Bottlenecks identified (download, processing, mapping)
3. Memory usage patterns
4. Disk I/O optimization opportunities
5. Parallelization opportunities
6. Cache efficiency
7. Recommendations for future optimization

**Validation**: Analysis is data-driven with actual metrics

**Commit**: After analysis is complete

---

## 📊 SUCCESS CRITERIA FOR THIS SESSION

At the end of this session, you should have accomplished **at least one** of:

### Option A Success:
- ✅ IMPROVE Network fully researched (docs/IMPROVE_IMPLEMENTATION_NOTES.md created)
- ✅ IMPROVEDownloader implemented and tested
- ✅ Full IMPROVE dataset downloaded, processed, and mapped
- ✅ Registry updated to mark IMPROVE as operational
- ✅ System now has 4 operational sources (EPA AQS, NHGIS, CSN, IMPROVE)

### Option B Success (if API returns):
- ✅ CDC EPHT Radon data fully downloaded (10 years)
- ✅ TSV files generated (~80 files)
- ✅ Maps generated (~80 PNG files)
- ✅ Registry updated to mark CDC EPHT as operational
- ✅ Priority 2 complete

### Option C Success:
- ✅ README.md comprehensive and user-friendly
- ✅ Variable catalog export script working
- ✅ Data quality report script working
- ✅ Implementation plan updated with actual progress
- ✅ Quick start guide created
- ✅ Performance analysis documented

### Ideal Session Outcome:
- ✅ **Option A complete** (IMPROVE operational)
- ✅ **Option B complete** (CDC EPHT operational, if API returns)
- ✅ **Option C: 2-3 background tasks complete** (README, catalog, quality report)
- ✅ **Result**: System has 4-5 operational sources, documentation current, ready for next Priority 3 source or Phase 10 final integration

---

## 🔧 ENVIRONMENT AND API KEYS

**API Keys Configured**:
```bash
# .env file (excluded from git)
EPA_AQS_API_KEY=greyheron63
EPA_AQS_EMAIL=davidlary@me.com
IPUMS_API_KEY=[STORED_IN_ENV]
CDC_EPHT_API_KEY=B74AFD5D-8F5D-4E94-B4EB-1E59EE081FDD
```

**Load Environment**:
```bash
source .env
# OR
export $(cat .env | xargs)
```

**Verify API Keys**:
```bash
echo $EPA_AQS_API_KEY
echo $CDC_EPHT_API_KEY
```

---

## 📝 CRITICAL REMINDERS FOR THIS SESSION

1. **ONE_STEP_AT_A_TIME**: Complete each implementation step fully before moving to next
2. **Test Everything**: Write tests, >80% coverage, 100% passing
3. **Commit Often**: After each completed step, commit with descriptive message
4. **Follow File Names**: Use exact file names from IMPLEMENTATION_PLAN.md
5. **Update Documentation**: Keep NEXT_SESSION_PROMPT.md current after each step
6. **Check API Status**: Monitor CDC EPHT API every 1-2 hours during session
7. **Display Checkpoints**: Use checkpoint box before EVERY response completion
8. **Display Next Steps**: Show next steps at END of EVERY response
9. **Stay Focused**: If working on IMPROVE (Option A), complete it fully before starting another source
10. **Be Opportunistic**: If CDC EPHT API returns, pause current work, complete CDC EPHT (30 min), then resume

---

## 🎯 RECOMMENDED SESSION START SEQUENCE

**Step 1**: Check CDC EPHT API status (2 minutes)
```bash
curl -s "https://ephtracking.cdc.gov/apigateway/api/v1/getMeasures" | head -50
```

**Step 2**: If API is back, complete Option B first (30 minutes), then proceed to Step 3

**Step 3**: Start Option A - Research IMPROVE Network (1-2 hours)
- Create docs/IMPROVE_IMPLEMENTATION_NOTES.md
- Document data access, variables, coverage
- Download sample data
- Assess GREEN/YELLOW/RED status

**Step 4**: If IMPROVE is GREEN, implement IMPROVEDownloader (2-3 hours)

**Step 5**: Test, download, process, map IMPROVE data (2-3 hours)

**Step 6**: While long-running tasks execute (downloads, maps), start Option C background tasks
- Update README.md
- Create variable catalog export
- Create data quality report

**Step 7**: Final documentation, registry updates, commit, push

**Total Session Time Estimate**: 6-8 hours for complete Option A + Option C tasks

---

## 🚀 QUICK START COMMANDS

### Check System Status
```bash
cd ~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData
git status
git log --oneline -5
python scripts/03_download_source.py --help
```

### Check API Status
```bash
# CDC EPHT API
curl -s "https://ephtracking.cdc.gov/apigateway/api/v1/getMeasures" | head -50
```

### Start Option A: IMPROVE Research
```bash
# Create documentation file
touch docs/IMPROVE_IMPLEMENTATION_NOTES.md

# Open in editor and begin research
# Visit: http://views.cira.colostate.edu/fed/DataWizard/
```

### Start Option B: CDC EPHT (if API is back)
```bash
export CDC_EPHT_API_KEY=$(grep CDC_EPHT_API_KEY .env | cut -d'=' -f2)
python scripts/03_download_source.py --source cdc_epht_radon --variable radon_testing --years 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022
```

### Start Option C: Documentation Tasks
```bash
# Update README
nano README.md

# Create variable catalog export script
touch scripts/06_export_variable_catalog.py
```

---

## 📚 KEY REFERENCE DOCUMENTS

**Essential Reading**:
- `IMPLEMENTATION_PLAN.md` - Complete implementation workflow
- `CLAUDE.md` - CPF rules and enforcement
- `docs/CSN_IMPLEMENTATION_NOTES.md` - Example of completed research document
- `src/downloaders/python/csn_downloader.py` - Example downloader implementation
- `scripts/03_download_source.py` - Registry and orchestration script

**Companion Repository**:
- `~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryDataList` - Source documentation

**Priority 3 Sources in Registry**:
- IMPROVE Network: `01_IMPROVE_NETWORK_INTERAGENCY_MO` (recommended next)
- EPA NEI: `01_EPA_NATIONAL_EMISSIONS_INVENTO` (alternative)
- CSN: `01_CHEMICAL_SPECIATION_NETWORK_CS` (✅ COMPLETE)
- EPA MOVES: `01_EPA_MOVES_MODEL_MOTOR_VEHICLE_` (future)

---

## 🎉 PROJECT MILESTONES

- ✅ **Phase 0**: Project setup and planning (COMPLETE)
- ✅ **Phase 1**: Metadata foundation (COMPLETE)
- ✅ **Phase 2**: Source registry builder (COMPLETE)
- ✅ **Phase 3**: Script registry integration (COMPLETE)
- ✅ **Phase 4**: EPA AQS operational (COMPLETE)
- ✅ **Phase 5**: IPUMS NHGIS operational (COMPLETE)
- ✅ **Phase 6**: CDC EPHT implementation (AWAITING API)
- ✅ **Phase 7**: Progress tracking (COMPLETE)
- ✅ **Phase 8**: CSN research (COMPLETE)
- ✅ **Phase 9**: CSN implementation (COMPLETE)
- ⏳ **Phase 10**: Next Priority 3 source (IMPROVE) + CDC EPHT completion + System integration ← **THIS SESSION**

---

**Let's begin! Start with checking CDC EPHT API status, then proceed with IMPROVE Network research.**
