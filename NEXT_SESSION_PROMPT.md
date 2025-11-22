# Next Session Prompt - US County-Level Observatory Data Download System

**Date Created**: 2025-11-22  
**Session Context**: Continuation after IPUMS NHGIS fixes and EPA AQS completion  
**Current Branch**: phase1-core-framework  
**Last Commit**: 7b5b2a2

---

## 🚨 IMMEDIATE TASKS - AUTONOMOUS EXECUTION REQUIRED

### Task 1: Fix EPA AQS TSV Processing (PRIORITY 1)

**Status**: EPA download COMPLETED (243 files), but TSV processing FAILED

**What Happened**:
- EPA AQS downloader successfully downloaded 243 cache files covering:
  - 6 pollutants: PM2.5, PM10, O3, NO2, SO2, CO
  - Years: 1980-2024 (45 years)
  - All US counties with data
- Automatic TSV processing failed at 22:24:40 on 2025-11-21

**Your Task**:
1. Check the error log: `cat logs/epa_autoprocess_20251121_220308.log`
2. Identify the specific error (likely: FIPS joining, data parsing, or file format issue)
3. Debug and fix the issue in `scripts/04_process_cached_data.py` or `src/core/tsv_generator.py`
4. Run manual processing: `python scripts/04_process_cached_data.py --source epa_aqs`
5. Verify success: Check for ~243-270 TSV files in `data/tsv/01_AIR_ATMOSPHERE/`
6. Generate maps: `python scripts/05_generate_maps.py --category 01_AIR_ATMOSPHERE`
7. Verify maps: Check for PNG files in `data/maps/01_AIR_ATMOSPHERE/`

**Expected Output**:
- ~243-270 TSV files (one per pollutant per year)
- ~243-270 PNG choropleth maps
- All files with standardized FIPS metadata columns

**Common Issues to Check**:
- FIPS code type mismatch (string vs int)
- Missing FIPS metadata file
- Data format parsing errors (CSV headers, delimiters)
- Empty dataframes causing joins to fail

---

### Task 2: Monitor/Fix/Run IPUMS NHGIS Downloader (PRIORITY 2)

**Status**: Autonomous downloader was running (PID 9184), but status unknown

**What Happened**:
- IPUMS NHGIS downloader started autonomously at 10:20:32 on 2025-11-22
- Two critical bugs were fixed:
  1. Table limit: Reduced from 1432 to 50 tables per extract
  2. URL extraction: Fixed dict handling for download links
- Log shows Batch 1 started, Batch 2 started, then log stopped at line 13
- Unknown if process is still running, completed, or failed

**Your Task**:
1. **Check Process Status**:
   ```bash
   ps aux | grep 9184
   ps aux | grep "97_autonomous_ipums"
   ```

2. **Check Log Files**:
   ```bash
   tail -100 logs/ipums_autonomous_master.log
   ls -lh logs/nhgis_batch*.log
   tail -100 logs/nhgis_batch1_*.log
   tail -100 logs/nhgis_batch2_*.log
   ```

3. **Count Downloaded Files**:
   ```bash
   find data/cache/02_DEMOGRAPHICS_SOCIAL/ipums_nhgis -name "*.zip" | wc -l
   ls -lh data/cache/02_DEMOGRAPHICS_SOCIAL/ipums_nhgis/
   ```

4. **Determine Next Action**:
   - If process still running: Monitor and wait
   - If process completed: Verify 266 files downloaded, proceed to processing
   - If process failed: Review logs, fix errors, restart from failed batch

5. **Restart If Needed**:
   ```bash
   nohup bash scripts/97_autonomous_ipums_downloader.sh > logs/ipums_restart_$(date +%Y%m%d_%H%M%S).log 2>&1 &
   echo $! # Note the PID
   ```

**Expected Output**:
- 266 ZIP files in `data/cache/02_DEMOGRAPHICS_SOCIAL/ipums_nhgis/`
- 5 batch log files showing success/failure counts
- Master log showing completion status

---

### Task 3: Process IPUMS NHGIS Data to TSV Format (PRIORITY 3)

**Status**: Not yet started, depends on Task 2 completion

**What to Do**:
1. **Understand NHGIS Data Format**:
   - Each ZIP contains: CSV data file + codebook + GIS files
   - CSV has county-level rows with FIPS codes (GISJOIN or GEOID format)
   - Multiple variables per file
   - Need to extract, parse, and standardize

2. **Implement NHGIS Processor**:
   - Create `scripts/04b_process_nhgis_data.py` (similar to EPA processor)
   - Or add NHGIS support to existing `scripts/04_process_cached_data.py`
   - Key steps:
     a. Extract ZIP files
     b. Parse NHGIS CSV format
     c. Convert GISJOIN to standard FIPS codes
     d. Split by variable and year
     e. Create standardized TSV files (with FIPS metadata columns)

3. **Run Processing**:
   ```bash
   python scripts/04_process_cached_data.py --source ipums_nhgis
   ```

4. **Generate Maps**:
   ```bash
   python scripts/05_generate_maps.py --category 02_DEMOGRAPHICS_SOCIAL
   ```

**Expected Output**:
- Thousands of TSV files (266 datasets × multiple variables × multiple years)
- Thousands of PNG choropleth maps
- All files in `data/tsv/02_DEMOGRAPHICS_SOCIAL/` and `data/maps/02_DEMOGRAPHICS_SOCIAL/`

---

## 📊 CURRENT DATA STATUS

### Downloaded Cache Files

| Source | Category | Files | Size | Status |
|--------|----------|-------|------|--------|
| EPA AQS | 01_AIR_ATMOSPHERE | 243 | ~50 MB | ✅ COMPLETE |
| IPUMS NHGIS | 02_DEMOGRAPHICS_SOCIAL | ??? | ??? MB | ⚠️ UNKNOWN |

### Processed TSV Files

| Source | TSV Files | Maps | Status |
|--------|-----------|------|--------|
| EPA AQS | 0 | 0 | ❌ PROCESSING FAILED |
| IPUMS NHGIS | 0 | 0 | ⏳ NOT STARTED |

---

## 🔧 CRITICAL FIXES APPLIED IN PREVIOUS SESSION

### Fix 1: IPUMS Table Limit (src/downloaders/python/ipums_nhgis_downloader.py:273-285)

**Problem**: Requesting all 1432 tables overwhelmed NHGIS server  
**Solution**: Limit to 50 tables per extract  
**Test**: 2023_ACS1 downloaded successfully (1.1 MB)

```python
MAX_TABLES_PER_EXTRACT = 50

if len(data_tables) > MAX_TABLES_PER_EXTRACT:
    logger.warning(
        f"Dataset {dataset} has {len(data_tables)} tables, "
        f"limiting to first {MAX_TABLES_PER_EXTRACT} tables"
    )
    data_tables = data_tables[:MAX_TABLES_PER_EXTRACT]
```

### Fix 2: IPUMS URL Extraction (src/downloaders/python/ipums_nhgis_downloader.py:369-382)

**Problem**: Download link returned as dict, not string  
**Solution**: Extract 'url' field from dict  
**Test**: Download succeeded after fix

```python
if isinstance(data_link_info, dict):
    data_url = data_link_info.get("url")
    if data_url:
        logger.info(f"Extract #{extract_number} complete!")
        return data_url
```

---

## 📁 CRITICAL FILE LOCATIONS

### Logs to Check
- `logs/epa_autoprocess_20251121_220308.log` - EPA processing error details
- `logs/ipums_autonomous_master.log` - IPUMS master process log
- `logs/nhgis_batch1_*.log` through `logs/nhgis_batch5_*.log` - Batch-specific logs
- `logs/main.log` - General system log
- `logs/errors.log` - All errors

### Cache Directories
- `data/cache/01_AIR_ATMOSPHERE/epa_aqs/` - EPA AQS downloaded files (243 files)
- `data/cache/02_DEMOGRAPHICS_SOCIAL/ipums_nhgis/` - IPUMS NHGIS ZIP files (??? files)

### Output Directories
- `data/tsv/01_AIR_ATMOSPHERE/` - EPA TSV files (currently empty)
- `data/tsv/02_DEMOGRAPHICS_SOCIAL/` - IPUMS TSV files (currently empty)
- `data/maps/01_AIR_ATMOSPHERE/` - EPA maps (currently empty)
- `data/maps/02_DEMOGRAPHICS_SOCIAL/` - IPUMS maps (currently empty)

### Metadata Files
- `data/metadata/fips_codes.csv` - 3,234 US counties with FIPS codes
- `data/metadata/county_boundaries_2020.gpkg` - County shapefiles (127 MB, not in git)
- `data/metadata/nhgis_download_batches.json` - 266 NHGIS datasets organized into 5 batches

---

## ✅ SUCCESS CRITERIA

### Task 1 Success (EPA Processing)
- [ ] Error identified and fixed
- [ ] ~243-270 TSV files created in `data/tsv/01_AIR_ATMOSPHERE/`
- [ ] All TSV files have standardized columns: FIPS, County, State, Year, Value, Variable
- [ ] ~243-270 PNG maps created in `data/maps/01_AIR_ATMOSPHERE/`
- [ ] No errors in logs
- [ ] Commit changes with message: "FIX: EPA AQS TSV processing - [description of fix]"

### Task 2 Success (IPUMS Monitoring)
- [ ] Process status determined (running/completed/failed)
- [ ] 266 ZIP files downloaded (or progress documented)
- [ ] All batch logs reviewed
- [ ] Any errors identified and fixed
- [ ] If restarted, new PID documented

### Task 3 Success (IPUMS Processing)
- [ ] Processor implemented and tested
- [ ] Thousands of TSV files created in `data/tsv/02_DEMOGRAPHICS_SOCIAL/`
- [ ] All TSV files have standardized columns
- [ ] Thousands of PNG maps created
- [ ] No errors in logs
- [ ] Commit changes with message: "ADD: IPUMS NHGIS TSV processing and map generation"

---

## 🎯 NEXT STEPS AFTER IMMEDIATE TASKS

### Phase 1 Completion
1. Verify all Phase 1 sources working:
   - ✅ EPA AQS (air quality)
   - ✅ IPUMS NHGIS (demographics)
   - ⏳ CDC WONDER (mortality) - not yet started
   - ⏳ USGS NWIS (water quality) - not yet started

2. Update documentation:
   - README.md with completion status
   - AUTONOMOUS_OPERATIONS_STATUS.md with final results
   - Create PHASE1_COMPLETION_SUMMARY.md

3. Git commit and push:
   - Commit all fixes and processing code
   - Push to GitHub (no large files)
   - Tag release: `git tag v1.1.0-phase1-complete`

### Phase 2: Additional Sources
4. CDC WONDER Mortality (Priority 1):
   - Implement downloader for mortality data
   - Category: 03_HEALTH_DISEASE

5. USGS NWIS Water Quality (Priority 2):
   - Implement downloader for water quality data
   - Category: 04_WATER_HYDROLOGY

6. ERA5 Climate Reanalysis (Priority 3):
   - Implement downloader for climate data
   - Category: 05_CLIMATE_WEATHER

### Phase 3: Data Integration
7. Master TSV compilation:
   - Combine all sources into master county-level database
   - Create DuckDB database for efficient querying
   - Generate summary statistics

8. Quality control:
   - Check for missing data
   - Validate FIPS codes
   - Generate data coverage reports

9. Documentation:
   - Data dictionary
   - User guide
   - API documentation (if needed)

---

## 🐛 COMMON DEBUGGING TIPS

### FIPS Code Issues
- FIPS codes must be 5-digit strings with leading zeros: "01001" not "1001"
- County FIPS = State FIPS (2 digits) + County FIPS (3 digits)
- Some territories have non-standard FIPS codes
- Check for type mismatches: string vs int

### API Issues
- EPA AQS: Check API key in environment or config file
- IPUMS NHGIS: Check API key in environment or config file
- Rate limiting: EPA allows 10 req/sec, IPUMS allows 100 req/min
- Timeouts: Increase for large datasets

### Processing Issues
- Empty dataframes: Check if data was actually downloaded
- Join failures: Verify FIPS code formats match
- Memory issues: Process in batches for large datasets
- File format issues: Check CSV headers, delimiters, encoding

### Git Issues
- Large files (>100MB): Add to .gitignore, use git filter-branch if already committed
- Push failures: Check file sizes with `git ls-files -z | xargs -0 du -h | sort -h`

---

## 📝 MONITORING COMMANDS

### Check Running Processes
```bash
ps aux | grep python
ps aux | grep autonomous
```

### Check Recent Logs
```bash
tail -100 logs/main.log
tail -100 logs/errors.log
tail -100 logs/ipums_autonomous_master.log
```

### Count Downloaded Files
```bash
find data/cache -name "*.json" | wc -l  # EPA files
find data/cache -name "*.zip" | wc -l   # IPUMS files
```

### Count Processed Files
```bash
find data/tsv -name "*.tsv" | wc -l
find data/maps -name "*.png" | wc -l
```

### Check Disk Space
```bash
du -sh data/cache/
du -sh data/tsv/
du -sh data/maps/
df -h .
```

---

## 🚀 QUICK START COMMANDS FOR NEXT SESSION

```bash
# Navigate to project
cd /Users/davidlary/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryData

# Check git status
git status
git log --oneline -5

# Task 1: Fix EPA processing
cat logs/epa_autoprocess_20251121_220308.log
# [Fix the error]
python scripts/04_process_cached_data.py --source epa_aqs
python scripts/05_generate_maps.py --category 01_AIR_ATMOSPHERE

# Task 2: Check IPUMS status
ps aux | grep 9184
tail -100 logs/ipums_autonomous_master.log
find data/cache/02_DEMOGRAPHICS_SOCIAL/ipums_nhgis -name "*.zip" | wc -l

# Task 3: Process IPUMS (after downloads complete)
python scripts/04_process_cached_data.py --source ipums_nhgis
python scripts/05_generate_maps.py --category 02_DEMOGRAPHICS_SOCIAL

# Verify results
find data/tsv -name "*.tsv" | wc -l
find data/maps -name "*.png" | wc -l

# Commit and push
git add -A
git commit -m "FIX: [description]"
git push origin phase1-core-framework
```

---

## 📖 REFERENCE DOCUMENTATION

- **README.md**: Main project documentation
- **config/sources_registry.json**: List of all 100+ data sources
- **docs/sources/epa_aqs.md**: EPA AQS documentation
- **docs/sources/ipums_nhgis.md**: IPUMS NHGIS documentation
- **AUTONOMOUS_OPERATIONS_STATUS.md**: Operational status guide
- **SESSION_HANDOFF_2025-11-21.md**: Previous session notes

---

**END OF NEXT SESSION PROMPT**

**Autonomous Execution**: Read this entire document, execute Tasks 1-3 in order, verify success criteria, commit changes, and provide status update.
