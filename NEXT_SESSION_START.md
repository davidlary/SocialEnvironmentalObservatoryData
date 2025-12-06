# NEXT SESSION START - US County-Level Observatory Data System

**Date**: 2025-12-06
**Branch**: `phase1-core-framework`
**Latest Commit**: `604fa0e` - "ADD: Comprehensive Next Session Start Prompt"
**Framework**: Context-Preserving Framework v4.0.1 (22 rules MANDATORY)
**Directory**: `~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData`

---

## 🎯 IMMEDIATE NEXT TASK

**Per IMPLEMENTATION_PLAN.md Phase 3-5**: Implement next Priority 3 data source using EXACT file names specified in plan.

### Current Status
- ✅ **Phase 1-2**: Core framework complete (8 modules, all operational)
- ✅ **Phase 3**: Script 03 registry integration complete
- ✅ **Phase 4-5**: 3 sources operational (EPA AQS, IPUMS NHGIS, CSN)
- ⏳ **Next**: Continue Phase 4-5 with next Priority 3 source

### Next Source to Implement

**Follow sources_registry.json priority order. Next Priority 3 source with county_native=true:**

Check registry to identify next unimplemented Priority 3 source, then:

1. Research source (create `docs/{SOURCE_NAME}_IMPLEMENTATION_NOTES.md`)
2. Implement downloader (`src/downloaders/python/{source}_downloader.py`)
3. Update registry (`scripts/03_download_source.py`)
4. Create tests (`scripts/test_{source}.py`)
5. Download data (via `scripts/03_download_source.py --source {source}`)
6. Process to TSV (via `scripts/04_process_cached_data.py --source {source}`)
7. Generate maps (via `scripts/05_generate_maps.py --source {SOURCE}`)
8. Update `config/sources_registry.json` (status → operational)

---

## 📋 WORKFLOW: ONE SOURCE AT A TIME

**IMPLEMENTATION_PLAN.md Section "Implementation Modules" specifies:**

### Step 1: Research (1-2 hours)
**File**: `docs/{SOURCE_NAME}_IMPLEMENTATION_NOTES.md`

Document:
- Data access method (API/bulk/FTP)
- Authentication requirements
- Variable list with codes and units
- Temporal coverage (actual years available)
- Geographic coverage (verify county-native)
- Data format and structure
- Sample data downloaded and validated
- Implementation assessment (GREEN/YELLOW/RED)

**Validation**: Documentation complete, no blockers identified

**Commit**: Research complete with findings

### Step 2: Implement Downloader (2-4 hours)
**File**: `src/downloaders/python/{source}_downloader.py`

**Per IMPLEMENTATION_PLAN.md requirements:**
```python
"""
{Source Name} Downloader
[Brief description]
"""

from src.core.base_downloader import BaseDownloader
from src.core.logger import get_logger
from src.core.cache_manager import CacheManager
from src.core.retry_handler import retry_with_backoff
import pandas as pd
from typing import List, Dict, Optional

class {Source}Downloader(BaseDownloader):
    """
    Downloader for {Source Name}

    Data Source: [URL]
    Variables: [List]
    Temporal Coverage: [Years]
    Geographic: County-level
    """

    BASE_URL = "[FROM RESEARCH]"
    AVAILABLE_VARIABLES = [...]  # From research

    def __init__(self, cache_dir: str = "data/cache/{CATEGORY}/{source}",
                 logger=None):
        """Initialize downloader"""
        super().__init__(cache_dir, logger)
        # Implementation

    def get_available_variables(self) -> List[str]:
        """Return list of available variables"""
        return self.AVAILABLE_VARIABLES

    def get_available_years(self) -> List[int]:
        """Return list of available years"""
        # Implementation

    @retry_with_backoff(max_retries=3)
    def download(self, variable: str, year: int, **kwargs) -> pd.DataFrame:
        """
        Download data for specific variable and year

        Args:
            variable: Variable name
            year: Year to download
            **kwargs: Additional parameters

        Returns:
            DataFrame with columns: FIPS, value, year
        """
        # Check cache first
        cache_file = self._get_cache_path(variable, year)
        if self._is_cached(cache_file) and not kwargs.get('force_refresh'):
            return self._load_from_cache(cache_file)

        # Download from source
        data = self._download_from_source(variable, year)

        # Process to county level
        county_data = self._process_to_county(data)

        # Save to cache
        self._save_to_cache(county_data, cache_file)

        return county_data

    def _download_from_source(self, variable: str, year: int) -> pd.DataFrame:
        """Download raw data from source"""
        # Implementation based on research
        pass

    def _process_to_county(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process to county level with FIPS codes"""
        # Implementation based on data structure
        pass
```

**Validation**: Code follows IMPLEMENTATION_PLAN.md structure, inherits from BaseDownloader

**Commit**: Downloader implementation complete

### Step 3: Update Registry (15 minutes)
**File**: `scripts/03_download_source.py`

Add to imports:
```python
from src.downloaders.python.{source}_downloader import {Source}Downloader
```

Add to DOWNLOADER_REGISTRY:
```python
"{source}": {
    "class": {Source}Downloader,
    "category": "{CATEGORY}",
    "description": "{Description}",
    "source_id": "{REGISTRY_SOURCE_ID}",
}
```

Add to SOURCE_ID_MAPPINGS:
```python
"{REGISTRY_SOURCE_ID}": "{source}"
```

**Validation**: Script imports without errors, registry lookup works

**Commit**: Registry integration complete

### Step 4: Create Tests (30 minutes)
**File**: `scripts/test_{source}.py`

**Per IMPLEMENTATION_PLAN.md testing requirements:**
```python
"""
Test script for {Source} downloader
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.downloaders.python.{source}_downloader import {Source}Downloader
from src.core.logger import get_logger

def test_initialization():
    """Test 1: Initialize downloader"""
    downloader = {Source}Downloader()
    assert downloader is not None
    print("✅ Test 1 PASSED: Initialization")

def test_available_variables():
    """Test 2: Get available variables"""
    downloader = {Source}Downloader()
    variables = downloader.get_available_variables()
    assert len(variables) > 0
    print(f"✅ Test 2 PASSED: Found {len(variables)} variables")

def test_available_years():
    """Test 3: Get available years"""
    downloader = {Source}Downloader()
    years = downloader.get_available_years()
    assert len(years) > 0
    print(f"✅ Test 3 PASSED: Found years {min(years)}-{max(years)}")

def test_download_single_year():
    """Test 4: Download single year"""
    downloader = {Source}Downloader()
    variable = downloader.get_available_variables()[0]
    year = downloader.get_available_years()[-1]  # Most recent year

    data = downloader.download(variable, year)
    assert data is not None
    assert len(data) > 0
    assert 'FIPS' in data.columns
    print(f"✅ Test 4 PASSED: Downloaded {len(data)} counties")

def test_cache_functionality():
    """Test 5: Verify caching works"""
    downloader = {Source}Downloader()
    variable = downloader.get_available_variables()[0]
    year = downloader.get_available_years()[-1]

    # First download
    data1 = downloader.download(variable, year)

    # Second download (should use cache)
    data2 = downloader.download(variable, year)

    assert len(data1) == len(data2)
    print("✅ Test 5 PASSED: Cache working")

def test_data_validation():
    """Test 6: Validate data structure"""
    downloader = {Source}Downloader()
    variable = downloader.get_available_variables()[0]
    year = downloader.get_available_years()[-1]

    data = downloader.download(variable, year)

    # Check FIPS codes are valid (5-digit strings)
    assert data['FIPS'].str.len().eq(5).all()

    # Check for missing values
    assert data['value'].notna().sum() > 0

    print("✅ Test 6 PASSED: Data validation")

def test_error_handling():
    """Test 7: Error handling"""
    downloader = {Source}Downloader()

    # Try invalid variable
    try:
        data = downloader.download("INVALID_VARIABLE", 2020)
        print("❌ Test 7 FAILED: Should raise error for invalid variable")
    except:
        print("✅ Test 7 PASSED: Error handling works")

if __name__ == "__main__":
    print(f"Testing {Source}Downloader...")
    print("=" * 50)

    test_initialization()
    test_available_variables()
    test_available_years()
    test_download_single_year()
    test_cache_functionality()
    test_data_validation()
    test_error_handling()

    print("=" * 50)
    print("All tests passed! ✅")
```

**Validation**: All 7 tests pass

**Commit**: Tests passing

### Step 5: Download Full Dataset (30 minutes - 2 hours)
**Command**: `python scripts/03_download_source.py --source {source}`

**Per IMPLEMENTATION_PLAN.md Phase 3 workflow:**
- Downloads all variables for all years
- Caches each year separately
- Uses retry logic with exponential backoff
- Logs progress to `logs/main.log`

**Validation**: All cache files created, no errors in logs

**Commit**: Full dataset downloaded

### Step 6: Process to TSV (30 minutes)
**Command**: `python scripts/04_process_cached_data.py --source {source}`

**Per IMPLEMENTATION_PLAN.md Phase 3 workflow:**
- Scans cache directory
- Generates TSV files in `data/processed/{CATEGORY}/{SOURCE}/`
- Each TSV has structure: FIPS, state, county, value, year

**Validation**: All TSV files created with correct structure

**Commit**: TSV conversion complete

### Step 7: Generate Maps (1 hour)
**Command**: `python scripts/05_generate_maps.py --source {SOURCE}`

**Per IMPLEMENTATION_PLAN.md Phase 4 workflow:**
- Creates choropleth maps (quantile-based, 5 bins)
- Saves PNG files in same directory as TSV
- Parallel processing (8 workers)

**Validation**: All PNG maps created

**Commit**: Maps generated

### Step 8: Finalize (15 minutes)
**Update**: `config/sources_registry.json`

Change for this source:
```json
{
  "status": "operational",
  "implementation": {
    "downloader_class": "{Source}Downloader",
    "implemented": true,
    "test_status": "passed",
    "variable_count": [ACTUAL_COUNT]
  },
  "temporal_coverage": {
    "last_updated": "2025-12-06"
  }
}
```

**Update**: `NEXT_SESSION_PROMPT.md` with completion summary

**Commit**: Source implementation complete

---

## 🔧 EXACT FILE NAMES PER IMPLEMENTATION_PLAN.md

**Core Modules** (already complete):
- `src/core/base_downloader.py`
- `src/core/cache_manager.py`
- `src/core/logger.py`
- `src/core/metadata_manager.py`
- `src/core/progress_tracker.py`
- `src/core/retry_handler.py`
- `src/core/tsv_generator.py`
- `src/core/map_generator.py`

**Scripts** (already complete):
- `scripts/00_setup_environment.py`
- `scripts/01_download_metadata.py`
- `scripts/02_build_source_registry.py`
- `scripts/03_download_source.py`
- `scripts/04_process_cached_data.py`
- `scripts/05_generate_maps.py`

**Configuration** (already complete):
- `config/sources_registry.json`
- `config/priority_order.json`

**Downloader Modules** (3 complete, continue with Priority 3):
- ✅ `src/downloaders/python/epa_aqs_downloader.py`
- ✅ `src/downloaders/python/nhgis_downloader.py`
- ✅ `src/downloaders/python/csn_downloader.py`
- ⏳ Next: `src/downloaders/python/{next_source}_downloader.py`

**Test Scripts** (3 complete, create for next source):
- ✅ `scripts/test_epa_aqs.py`
- ✅ `scripts/test_nhgis.py`
- ✅ `scripts/test_csn.py`
- ⏳ Next: `scripts/test_{next_source}.py`

**Documentation** (3 complete, create for next source):
- ✅ `docs/EPA_AQS_IMPLEMENTATION_NOTES.md`
- ✅ `docs/NHGIS_IMPLEMENTATION_NOTES.md`
- ✅ `docs/CSN_IMPLEMENTATION_NOTES.md`
- ⏳ Next: `docs/{NEXT_SOURCE}_IMPLEMENTATION_NOTES.md`

---

## 🚨 CRITICAL: ONE_STEP_AT_A_TIME METHODOLOGY

**From IMPLEMENTATION_PLAN.md and CPF v4.0.1:**

1. Complete Step 1 (Research) FULLY before moving to Step 2
2. Complete Step 2 (Implementation) FULLY before moving to Step 3
3. Complete Step 3 (Registry) FULLY before moving to Step 4
4. Complete Step 4 (Tests) FULLY before moving to Step 5
5. Complete Step 5 (Download) FULLY before moving to Step 6
6. Complete Step 6 (TSV) FULLY before moving to Step 7
7. Complete Step 7 (Maps) FULLY before moving to Step 8
8. Complete Step 8 (Finalize) FULLY before considering source complete

**If ANY step fails**:
- Debug immediately
- Fix the issue completely
- Re-run tests to validate fix
- Document the fix
- Only then proceed to next step

**Do NOT**:
- Skip steps
- Move to next step before current step is 100% working
- Create placeholder implementations
- Leave TODO comments for later

---

## 📊 CURRENT STATUS

**Phases Complete**: 9 of 10 (90%)

**Operational Sources**: 3
- EPA AQS: 243 variables (1980-2024)
- IPUMS NHGIS: 58,243 variables (1790-2023)
- CSN: 97 variables (2007-2024)

**Total Variables Operational**: 58,583

**Total Files Generated**: ~116,959 files (~36 GB)
- Cached: 340 CSV
- TSV: 58,583
- Maps: 58,036 PNG

**Priority 3 Sources Remaining** (county-native only):
1. IMPROVE Network (`01_IMPROVE_NETWORK_INTERAGENCY_MO`)
2. EPA NEI (`01_EPA_NATIONAL_EMISSIONS_INVENTO`)
3. EPA MOVES (`01_EPA_MOVES_MODEL_MOTOR_VEHICLE_`)

**Also Monitor**: CDC EPHT Radon (Priority 2, implementation complete, awaiting API)

---

## 🚀 SESSION START COMMANDS

### 1. Check Status
```bash
cd ~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData
git status
git log --oneline -5
```

### 2. Identify Next Source
```bash
# Find next Priority 3, county_native=true, unimplemented source
jq -r '.sources[] | select(.priority == 3 and .geographic_coverage.county_native == true and .implementation.implemented == false) | "\(.source_id): \(.name)"' config/sources_registry.json | head -5
```

### 3. Start Research
```bash
# Create documentation file for identified source
touch docs/{SOURCE_NAME}_IMPLEMENTATION_NOTES.md

# Begin research at source URL
```

### 4. Check CDC EPHT API (Quick Check)
```bash
# If API returns during session, pause and complete (30 min)
curl -s "https://ephtracking.cdc.gov/apigateway/api/v1/getMeasures" | head -50
```

---

## 📝 SESSION GOAL

**Complete ONE full source implementation** following IMPLEMENTATION_PLAN.md exactly:
1. Research → Document → Assess
2. Implement → Test → Debug → Fix
3. Download → Process → Map
4. Validate → Document → Commit

**Result**: One additional operational source, system ready for next source

---

**START HERE**: Run the "Identify Next Source" command above, then begin Step 1 (Research) for that source.
