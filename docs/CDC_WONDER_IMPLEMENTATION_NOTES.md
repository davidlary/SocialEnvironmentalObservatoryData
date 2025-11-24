# CDC WONDER / CDC Mortality Data Implementation Notes

**Date:** 2025-11-24
**Status:** Deprioritized - County-level data unavailable for recent years
**Priority:** 3 (per sources_registry.json)
**Decision:** Skip this source for now; move to NHGIS (Priority 1)

---

## Executive Summary

**CRITICAL FINDING**: County-level CDC mortality data is NOT available through simple public access methods for recent years (2017+).

**Key Limitations Discovered**:
1. **CDC WONDER API** - No county-level access (national only)
2. **Compressed Mortality Files** - Public files end at 2016 (7 years outdated)
3. **NBER Repository** - County codes removed from 2005+ files
4. **CDC WONDER Web** - County access requires web scraping (~17 hours with rate limits)
5. **Restricted Data** - Requires formal NCHS application (4-6 weeks approval)

**RECOMMENDATION**: **Deprioritize this source**
- Rationale: Public county-level data ends at 2016, automated access very difficult
- Alternative: Focus on Priority 1 sources (EPA AQS, NHGIS) that have complete modern data
- Future: Revisit if project gains institutional support for restricted data access

---

## Original Plan vs. Reality

### Original Plan (from IMPLEMENTATION_PLAN.md)
```
Priority 3: CDC WONDER Mortality Database
- API: https://wonder.cdc.gov/wonder/help/API.html
- Variables: All-cause mortality, top 10 causes, drug overdoses
- Years: 1999-2023
- Expected: ~500-1,000 TSV files
```

### Actual Findings

**CDC WONDER API Limitations** (discovered 2025-11-24):
- ❌ **No county-level access via API** - Only national data
- ❌ **No state-level access via API** - Only national data
- ❌ **Cannot group by location fields** - Region, Division, State, County all prohibited
- ✅ **National data available** - Can query national mortality trends by cause

**Source**:
- [CDC WONDER API Documentation](https://wonder.cdc.gov/wonder/help/wonder-api.html)
- [CDC WONDER on data.gov](https://catalog.data.gov/dataset/wide-ranging-online-data-for-epidemiologic-research-wonder)
- [GitHub CDC WONDER API examples](https://github.com/alipphardt/cdc-wonder-api)

**Quote from official documentation**:
> "Only national data are available for query by the API. Queries for mortality statistics from the National Vital Statistics System cannot limit or group results by any location field, such as Region, Division, State or County."

---

## Available Data Sources for County-Level Mortality

### Option 1: Compressed Mortality Files (CMF) - **RECOMMENDED**

**Coverage**: 1968-2016 (county-level)
**Access**: FTP download (public, no authentication)
**URL**: `ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NVSS/cmf/`

**Files**:
- `mort9916.zip` - 1999-2016 mortality data (ICD-10), ~75 MB
- `pop9916.zip` - 1999-2016 population data, ~15 MB
- `mort7998.zip` - 1979-1998 mortality data (ICD-9), ~32 MB
- `pop7998.zip` - 1979-1998 population data, ~5 MB
- `mort6878.zip` - 1968-1978 mortality data (ICD-8), ~32 MB
- `pop6878.zip` - 1968-1978 population data, ~5 MB

**Pros**:
- ✅ Public access, no restrictions
- ✅ County-level FIPS codes included
- ✅ Bulk download (single file per period)
- ✅ Covers 1999-2016 (18 years of ICD-10 data)
- ✅ Standardized format across years

**Cons**:
- ❌ Fixed-width format (requires parsing)
- ❌ Only goes to 2016 (7 years out of date)
- ❌ Limited cause-of-death groupings (113 ICD-10 groups, not all codes)
- ❌ Documentation sparse/404 errors

**Variables**:
- County FIPS code
- Year
- Age group (19 groups)
- Race (4 categories)
- Hispanic origin (2 categories)
- Sex (2 categories)
- Cause of death (113 ICD-10 selected cause groupings)
- Death count

**Implementation Status**:
- ✅ Downloader class created (`src/downloaders/python/cdc_mortality_downloader.py`)
- ✅ FTP connection tested successfully
- ⏳ File parser partially implemented
- ❌ Record layout documentation not found (404 errors)
- ⏳ Need to reverse-engineer format or find working docs

---

### Option 2: CDC WONDER Web Interface Automation

**Coverage**: 1999-2023 (county-level via web only)
**Access**: Web form → automated form submission
**URL**: https://wonder.cdc.gov/ucd-icd10.html

**Pros**:
- ✅ Most recent data (through 2023)
- ✅ County-level available
- ✅ More detailed cause codes (all ICD-10)
- ✅ Can query specific causes

**Cons**:
- ❌ No API - requires web scraping
- ❌ Rate limits (recommended: 1 query per 2 minutes)
- ❌ Data suppression (<10 deaths = suppressed)
- ❌ Manual query construction required
- ❌ Fragile (web UI changes break automation)
- ❌ Large download volume (~500-1,000 queries for all causes/years)

**Estimated Time**: 500 queries × 2 minutes = ~17 hours download time

**Implementation Complexity**: HIGH
- Requires Selenium/Playwright for form automation
- XML request construction
- Response parsing (XML format)
- Error handling for suppressed data
- Resume capability for 17-hour downloads

**Recommendation**: **Use only if CMF insufficient** (i.e., need 2017-2023 data urgently)

---

### Option 3: NBER Mortality Data Repository

**Coverage**: 1959-2021 (county codes 1982-2004 only)
**Access**: Direct HTTP download
**URL**: https://data.nber.org/mortality/

**Pros**:
- ✅ Public access
- ✅ Multiple formats (CSV, Stata, SAS, ASCII)
- ✅ Well-documented
- ✅ County codes for 1982-2004

**Cons**:
- ❌ County codes removed 2005+ (privacy restrictions)
- ❌ Overlaps with CMF (1999-2004)
- ❌ No advantage over CMF for ICD-10 period

**Use Case**: **Historical data only** (pre-1999) or **backup source** for 1999-2004

---

### Option 4: Restricted-Use Data (NCHS Application)

**Coverage**: 1989-2023 (full county detail)
**Access**: Application to NCHS required
**URL**: https://www.cdc.gov/nchs/nvss/nvss-restricted-data.htm
**Email**: nvssrestricteddata@cdc.gov

**Process**:
1. Submit Project Review Form
2. Include CVs of all researchers
3. Justify need for county-level data
4. Wait 4-6 weeks for approval
5. Access data at NCHS or Federal Research Data Center

**Pros**:
- ✅ Complete county-level data (1989-2023)
- ✅ All ICD codes (not just 113 groups)
- ✅ No suppression
- ✅ Most comprehensive option

**Cons**:
- ❌ Requires formal application
- ❌ 4-6 week approval time
- ❌ Must use data at secure facility
- ❌ Cannot redistribute data
- ❌ Not suitable for automated pipeline

**Recommendation**: **Future enhancement** if project requires 2017-2023 county data and has institutional support

---

## Recommended Implementation Strategy

### Phase 1: Implement CMF Downloader (1999-2016) - **IMMEDIATE**

**Timeline**: 1-2 days
**Priority**: HIGH

**Tasks**:
1. ✅ Create `CDCMortalityDownloader` class (done)
2. ⏳ Complete fixed-width file parser
   - Find or reverse-engineer record layout
   - Test with small sample (1999 data)
   - Validate against known totals
3. ⏳ Implement county aggregation
   - Sum deaths across age/race/sex groups
   - Calculate rates per 100,000
   - Join with FIPS metadata
4. ⏳ Generate TSV files
   - One file per cause × year
   - Format: `FIPS,County,State,Year,DeathCount,Rate,Population`
5. ⏳ Generate maps
   - Use existing `map_generator.py`
   - Choropleth by mortality rate
6. ⏳ Test and validate
   - Compare totals with CDC published data
   - Check for missing counties
   - Verify rates calculation

**Expected Output**:
- **Years**: 1999-2016 (18 years)
- **Causes**: 113 ICD-10 groups + "All causes" = 114 variables
- **Files**: 114 causes × 18 years = **2,052 TSV files**
- **Maps**: 2,052 PNG files
- **Total size**: ~500 MB TSVs + ~3 GB maps = **~3.5 GB**

---

### Phase 2: Evaluate Need for 2017-2023 Data - **FUTURE**

**Decision Point**: After Phase 1 complete

**Options**:
1. **Skip 2017-2023** - 1999-2016 provides 18 years of trends
2. **Wait for CMF update** - CDC may release 2017-2020 eventually
3. **Apply for restricted data** - If institutional support available
4. **Implement CDC WONDER automation** - Last resort, high complexity

**Recommendation**: **Skip 2017-2023 for now**
- Rationale: 18 years (1999-2016) sufficient for trend analysis
- Can revisit if user explicitly needs recent data
- Systematic approach: complete working sources before adding complex ones

---

## Implementation Blockers and Solutions

### Blocker 1: CMF Documentation Not Found

**Issue**: Official documentation PDFs return 404 errors
- https://www.cdc.gov/NCHS/data/mortab/cmf_documentation_1999-2007.pdf (404)
- https://wonder.cdc.gov/wonder/help/CMF/TechnicalAppendix1999.pdf (404)

**Solutions**:
1. **Reverse-engineer format** - Download sample file, inspect hex dump
2. **Use NBER documentation** - Their format may match CDC
3. **Contact CDC** - Email cwus@cdc.gov for documentation
4. **Use existing parsers** - Check R/Python packages (e.g., `mortyr` R package)

**Action**: Try reverse-engineering first (fastest), then check existing parsers

---

### Blocker 2: Fixed-Width Format Complexity

**Issue**: CMF uses fixed-width format (24 bytes per record for 1999-2016)

**Challenges**:
- Need exact byte positions for each field
- Binary encoding for some fields (death count is 8-byte integer)
- Millions of records per file (~21 million for 1999-2016)

**Solutions**:
1. **Use struct.unpack()** - Python built-in for binary parsing
2. **Process in chunks** - Read 1M records at a time (memory efficiency)
3. **Use Polars** - Fast columnar processing after parsing
4. **Test on small sample** - Validate format with first 1,000 records

**Action**: Implement chunked parser with struct.unpack(), validate with sample

---

## Updated sources_registry.json Entry

**Current** (Priority 3):
```json
{
  "id": "cdc_wonder_mortality",
  "name": "CDC WONDER Mortality Database",
  "priority": 3,
  "access_method": "api",
  "temporal_coverage": {"start": 1999, "end": 2023},
  "status": "planned"
}
```

**Proposed** (Updated based on findings):
```json
{
  "id": "cdc_cmf",
  "name": "CDC Compressed Mortality Files",
  "priority": 3,
  "category": "12_MORTALITY_DISEASE",
  "description": "County-level mortality by cause of death (ICD-10 113 selected causes)",
  "access_method": "ftp",
  "requires_account": false,
  "base_url": "ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NVSS/cmf/",
  "temporal_coverage": {
    "start": 1999,
    "end": 2016,
    "frequency": "annual",
    "note": "ICD-10 period; earlier periods (1968-1998) available with ICD-8/9"
  },
  "geographic_level": "county",
  "estimated_variables": 114,
  "estimated_files": 2052,
  "downloader_module": "python/cdc_mortality_downloader.py",
  "notes": "Fixed-width format; 113 cause groups + all-cause; 2017+ requires web scraping or restricted data",
  "status": "in_progress"
}
```

---

## Next Steps (Ordered by Priority)

1. **[IMMEDIATE]** Complete CMF file parser
   - Reverse-engineer or find record layout
   - Implement chunked parsing
   - Test with 1999 data (smallest file)

2. **[HIGH]** Validate parser output
   - Compare county totals with published CDC data
   - Check for parsing errors (malformed records)
   - Verify FIPS codes match county boundaries

3. **[MEDIUM]** Implement county aggregation
   - Sum across demographics (age/race/sex)
   - Calculate crude and age-adjusted rates
   - Handle suppression/missing data

4. **[MEDIUM]** Generate TSV files and maps
   - Use existing `tsv_generator.py` and `map_generator.py`
   - One TSV per cause × year
   - Choropleth maps by mortality rate

5. **[LOW]** Documentation and testing
   - Update README with CDC CMF source
   - Add unit tests for parser
   - Document limitations (2016 end date)

6. **[FUTURE]** Evaluate 2017-2023 options
   - Only if user explicitly requests recent data
   - Weigh complexity vs. value
   - Consider waiting for CMF update

---

## Estimated Timeline

**Phase 1 (CMF 1999-2016)**:
- File parser completion: 4-6 hours
- Testing and validation: 2-3 hours
- County aggregation: 2-3 hours
- TSV/map generation: 1-2 hours (mostly automated)
- **Total: 10-15 hours (1-2 days)**

**Phase 2 (2017-2023, if needed)**:
- CDC WONDER automation: 8-12 hours development
- Download time: ~17 hours (rate-limited)
- **Total: 25-30 hours (3-4 days)**

---

## Sources and References

### Primary Documentation
- [CDC WONDER](https://wonder.cdc.gov/)
- [CDC WONDER API Documentation](https://wonder.cdc.gov/wonder/help/wonder-api.html)
- [Compressed Mortality Files](https://wonder.cdc.gov/wonder/help/cmf.html)
- [NCHS Vital Statistics Online](https://www.cdc.gov/nchs/data_access/vitalstatsonline.htm)

### Data Sources
- [CDC FTP Site (CMF)](ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NVSS/cmf/)
- [NBER Mortality Data](https://www.nber.org/research/data/mortality-data-vital-statistics-nchs-multiple-cause-death-data)
- [Restricted-Use Data Application](https://www.cdc.gov/nchs/nvss/nvss-restricted-data.htm)

### Code Examples
- [GitHub: CDC WONDER API Examples](https://github.com/alipphardt/cdc-wonder-api)
- [Sebastian Daza: Reading CDC Mortality Files in R](https://sdaza.com/blog/2016/read-mortality-data/)

---

## Final Decision and Next Steps

**Date**: 2025-11-24
**Decision**: **Skip CDC mortality data for current phase**

### Rationale

1. **Data Recency Issues**:
   - Public CMF files only available through 2016 (7 years outdated)
   - Newer data requires restricted access or complex web scraping
   - Other priority sources have current data through 2023-2024

2. **Implementation Complexity vs. Value**:
   - CMF parser would take 1-2 days to complete
   - Web scraping would add 3-4 days + 17 hours download time
   - Limited value given outdated endpoint (2016)

3. **Project Goals Priority**:
   - Goal: 200+ current environmental/social indicators
   - Focus resources on high-value sources with modern data
   - EPA AQS and NHGIS (Priority 1) provide current data easily

4. **Future Path Forward**:
   - If mortality data becomes critical, three options exist:
     a. Apply for NCHS restricted data (institutional project)
     b. Wait for updated CMF release (CDC may update 2017-2020)
     c. Implement CDC WONDER web scraping (last resort)
   - Revisit decision after completing Priority 1-2 sources

### Status Update

- ✅ Research complete: All options evaluated
- ✅ Downloader skeleton created: `src/downloaders/python/cdc_mortality_downloader.py`
- ✅ Documentation complete: This file documents all findings
- ❌ Parser incomplete: Not worth completing for 2016 endpoint
- ❌ Full implementation: Deprioritized pending data access resolution

### Next Action

**Move to Priority 1 source: NHGIS (census/demographic data)**
- NHGIS has county-level data through 2022
- Well-documented API with modern access methods
- Higher priority per sources_registry.json
- Better return on implementation effort

---

**Last Updated**: 2025-11-24 04:00 AM
**Status**: Research complete - Source deprioritized
**Next Action**: Begin NHGIS implementation (Priority 1)
