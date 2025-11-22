# Next Session Continuation Prompt

## Context

You are continuing development of the **US County-Level Observatory Data Download System**, a comprehensive system to download, process, and visualize 43,000+ variables from 200+ data sources for 3,234 US counties.

**Current Status:** Phase 1 (Core Framework) is COMPLETE. EPA AQS downloader is implemented but NOT YET RUN with real data.

## What Has Been Completed

### ✅ Phase 1: Core Framework (100% Complete)
- All core modules implemented and tested (logger, cache_manager, progress_tracker, metadata_manager, etc.)
- Setup scripts working (00_setup_environment.py, 01_download_metadata.py)
- Metadata downloaded: 3,234 US counties with boundaries
- Base downloader abstract class ready for all sources

### ✅ EPA AQS Implementation (95% Complete)
- **Downloader**: `src/downloaders/python/epa_aqs_downloader.py` - FULLY IMPLEMENTED
  - Supports 6 criteria pollutants: PM2.5, PM10, O3, NO2, SO2, CO
  - Years: 1980-2024 (varies by pollutant)
  - API integration with rate limiting and retry logic
- **Processor**: `src/processors/epa_aqs_processor.py` - FULLY IMPLEMENTED
  - Converts API responses to standardized TSV files
  - County-level aggregation with FIPS metadata
- **Scripts**:
  - `scripts/03_download_source.py` - Main downloader orchestrator
  - `scripts/04_process_cached_data.py` - TSV processor
  - `scripts/05_generate_maps.py` - Map generator
- **Testing**: End-to-end pipeline test passes for TSV generation

### ⚠️ Known Issue
- Map generator has minor FIPS/GEOID type mismatch (line 152 in `src/core/map_generator.py`)
- Easy fix: Ensure GEOID is converted to zero-padded string before merge

### 🚫 Blocker: NO REAL DATA DOWNLOADED YET
- EPA AQS downloader is implemented but **NOT RUN**
- Requires API credentials (free signup at https://aqs.epa.gov/data/api/signup)

## Critical Requirements for This Session

### MANDATORY RULES (from user):
1. **NO SYNTHETIC DATA** - Only real data downloads
2. **FULL DOWNLOADS ONLY** - Every variable, every year available
3. **COMPLETE EACH DOWNLOADER** before moving to next:
   - Download ALL data
   - Process ALL to TSVs
   - Generate ALL maps
   - Verify completeness
   - Then and ONLY then move to next downloader
4. **Follow CPF v4.7.1** completely (Context-Preserving Framework rules in this directory)
5. **Parallel processing** for years within each variable

## Your Tasks for This Session

### TASK 1: Fix Map Generator (5 minutes)
**File**: `src/core/map_generator.py` line ~152

**Problem**: Type mismatch between FIPS (string) and GEOID (int64)

**Fix**: In `_load_county_boundaries()` method, convert GEOID to string when loading:
```python
def _load_county_boundaries(self) -> gpd.GeoDataFrame:
    if self.county_boundaries is None:
        logger.info("Loading county boundaries for mapping")
        self.county_boundaries = get_county_boundaries()

        # Convert GEOID to zero-padded string for merging with FIPS
        self.county_boundaries['GEOID'] = (
            self.county_boundaries['GEOID']
            .astype(str)
            .str.zfill(5)
        )

        if self.county_boundaries.crs != CRS_US_ALBERS:
            self.county_boundaries = self.county_boundaries.to_crs(CRS_US_ALBERS)

    return self.county_boundaries
```

Then remove the temporary fix at line 152-153.

**Test**: Run `python tests/test_epa_aqs_pipeline.py` - should pass 100%

### TASK 2: Get EPA AQS API Credentials
**Action**: User must provide or you must prompt for:
1. EPA_AQS_API_KEY (from https://aqs.epa.gov/data/api/signup)
2. EPA_AQS_EMAIL (email used for signup)

**Set environment variables**:
```bash
export EPA_AQS_API_KEY="key_from_user"
export EPA_AQS_EMAIL="user.email@example.com"
```

### TASK 3: Download FULL EPA AQS Dataset
**Command**:
```bash
python scripts/03_download_source.py --source epa_aqs
```

**This will download**:
- PM2.5: 1999-2024 (26 years) × 56 states = ~1,456 files
- PM10: 1988-2024 (37 years) × 56 states = ~2,072 files
- O3: 1980-2024 (45 years) × 56 states = ~2,520 files
- NO2: 1980-2024 (45 years) × 56 states = ~2,520 files
- SO2: 1980-2024 (45 years) × 56 states = ~2,520 files
- CO: 1980-2024 (45 years) × 56 states = ~2,520 files
- **Total: ~13,608 API calls, ~2-4 hours with rate limiting**

**Monitor**: Watch for errors, handle retries, ensure ALL data downloads

### TASK 4: Process ALL EPA AQS Data to TSVs
**Command**:
```bash
python scripts/04_process_cached_data.py --source epa_aqs
```

**Expected output**:
- ~270 TSV files (6 pollutants × ~40-45 years each)
- Each TSV: county-level data with FIPS metadata
- Location: `data/processed/01_AIR_ATMOSPHERE/{pollutant}/`

### TASK 5: Generate ALL EPA AQS Maps
**Command**:
```bash
python scripts/05_generate_maps.py --all
```

**Expected output**:
- ~270 PNG maps (one per TSV file)
- 300 DPI, choropleth with quantile classification
- Same location as TSV files

### TASK 6: Verify EPA AQS Completion
**Check**:
```bash
# Count files
find data/processed/01_AIR_ATMOSPHERE -name "*.tsv" | wc -l
find data/processed/01_AIR_ATMOSPHERE -name "*.png" | wc -l

# Check one example
ls -lh data/processed/01_AIR_ATMOSPHERE/PM25/
```

**Expected**: All files present, reasonable sizes, no errors

### TASK 7: Commit EPA AQS Work
**After verification**:
```bash
git add -A
git commit -m "DATA: Complete EPA AQS dataset downloaded and processed

Downloaded and processed FULL EPA AQS dataset:
- 6 pollutants (PM2.5, PM10, O3, NO2, SO2, CO)
- All available years (1980-2024, varies by pollutant)
- All 56 US states/territories
- Total: ~13,608 API calls completed

Output:
- ~270 TSV files with county-level data
- ~270 choropleth maps (300 DPI PNG)
- All data validated and verified

Next: Implement next downloader

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### TASK 8: Implement Next Downloader
**Priority order** (from `IMPLEMENTATION_PLAN.md`):
1. ✅ EPA AQS (DONE in this session)
2. **NEXT: USGS NWIS** (water quality)
   - API-based, no account needed
   - 1,300+ parameters
   - Station-level data → requires county aggregation
3. Then: CDC WONDER mortality
4. Then: Census ACS demographics
5. Continue through all 200+ sources

**For USGS NWIS**:
- Create `src/downloaders/python/usgs_nwis_downloader.py`
- Inherits from `BaseDownloader`
- API: https://waterservices.usgs.gov/rest/
- Download ALL parameters, ALL available years
- Process to TSVs, generate ALL maps
- Only then move to next source

## Important Notes

### Context-Preserving Framework v4.7.1
- Follow ALL rules in `docs/core/PROTOCOL_CORE_RULES.md`
- Use TodoWrite tool to track progress
- Update todos as you complete tasks
- Display checkpoint after every operation

### Data Philosophy
- **NO placeholders** - full implementations only
- **NO synthetic data** - real data or nothing
- **COMPLETE before proceeding** - verify all files generated
- **Parallel where possible** - process years in parallel

### File Locations
- Cache: `data/cache/{category}/{source}/`
- Processed: `data/processed/{category}/{variable}/`
- Each variable directory contains: `{year}_{variable}.tsv` and `{year}_{variable}.png`

### Progress Tracking
All progress is tracked in `progress/*.json` files for resumability.

### Code Quality
- Comprehensive docstrings
- Type hints throughout
- Error handling at every level
- Logging for all operations
- Tests for each component

## Session Checklist

- [ ] Fix map generator GEOID type issue
- [ ] Test pipeline end-to-end (should pass 100%)
- [ ] Get EPA AQS API credentials from user
- [ ] Download FULL EPA AQS dataset (~2-4 hours)
- [ ] Process ALL cached EPA AQS data to TSVs
- [ ] Generate ALL EPA AQS maps
- [ ] Verify completeness (count files, check samples)
- [ ] Commit EPA AQS completion
- [ ] Implement USGS NWIS downloader (full implementation)
- [ ] Download FULL USGS NWIS dataset
- [ ] Process and map USGS NWIS data
- [ ] Continue with next source...

## Starting Commands

```bash
# 1. Fix map generator
# (Edit src/core/map_generator.py as described above)

# 2. Test fix
python tests/test_epa_aqs_pipeline.py

# 3. Set credentials (user must provide)
export EPA_AQS_API_KEY="..."
export EPA_AQS_EMAIL="..."

# 4. Download EPA AQS data (THIS IS THE MAIN TASK)
python scripts/03_download_source.py --source epa_aqs

# 5. Process to TSVs
python scripts/04_process_cached_data.py --source epa_aqs

# 6. Generate maps
python scripts/05_generate_maps.py --all

# 7. Verify
find data/processed/01_AIR_ATMOSPHERE -type f | wc -l
```

## Success Criteria

This session is successful when:
1. ✅ Map generator type issue fixed
2. ✅ EPA AQS: ALL 6 pollutants downloaded (all years, all states)
3. ✅ EPA AQS: ALL TSV files generated (~270 files)
4. ✅ EPA AQS: ALL maps generated (~270 maps)
5. ✅ EPA AQS: Work committed to git
6. ✅ Next downloader (USGS NWIS) fully implemented
7. ✅ USGS NWIS: ALL data downloaded
8. ✅ USGS NWIS: ALL TSVs and maps generated
9. Ready to continue with downloader #3

## Remember

- **REAL DATA ONLY** - no synthetic, no samples, no tests with fake data
- **COMPLETE EACH SOURCE** before moving to next
- **VERIFY COMPLETENESS** - count files, check samples
- **PARALLEL PROCESSING** - use all available CPU cores for years
- **FOLLOW CPF v4.7.1** - all rules apply

Good luck! The foundation is solid. Now it's time to download the real data.
