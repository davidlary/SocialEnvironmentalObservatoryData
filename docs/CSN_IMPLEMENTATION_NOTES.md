# EPA Chemical Speciation Network (CSN) - Implementation Notes

**Date Created**: 2025-11-28
**Data Source**: EPA Chemical Speciation Network (CSN)
**Priority**: 3 (Priority 3 implementation)
**Status**: ✅ READY FOR IMPLEMENTATION (GREEN STATUS)

---

## EXECUTIVE SUMMARY

The EPA Chemical Speciation Network (CSN) provides PM2.5 chemical composition data from ~180 urban monitoring sites across the United States. Data is available from 2000-present (25-year record) and includes measurements of elemental carbon, organic carbon, sulfate, nitrate, ammonium, and trace elements. This source is **county-native** (sites are assignable to counties) and requires **no spatial aggregation**.

**Implementation Approach**: Download pre-generated annual CSV files from EPA AQS air data portal, similar to the existing EPA AQS criteria pollutant downloader.

**Recommendation**: ✅ **IMPLEMENT IMMEDIATELY** - Clean data access, county-native, complements existing EPA AQS criteria pollutants.

---

## 1. DATA SOURCE OVERVIEW

### Official Information

| Attribute | Value |
|-----------|-------|
| **Official Name** | EPA Chemical Speciation Network (CSN) |
| **Short Name** | CSN |
| **Agency** | U.S. Environmental Protection Agency |
| **Program** | Ambient Monitoring Technology Information Center (AMTIC) |
| **Status** | ✅ Operational (2000-present) |
| **Data Type** | PM2.5 chemical composition measurements |
| **Update Frequency** | Annual data releases |

### Purpose & Context

- **Primary Purpose**: Monitor PM2.5 chemical composition in urban areas
- **Regulatory Context**: Supports PM2.5 NAAQS (National Ambient Air Quality Standards)
- **Complementary Networks**:
  - CSN = Urban PM2.5 composition (2000-present)
  - IMPROVE = Rural PM2.5 composition (1988-present)
  - Together provide comprehensive U.S. PM2.5 speciation

### Why This Source Matters

1. **Only urban PM2.5 composition network** - Complements rural IMPROVE network
2. **County-native data** - Sites located in major urban counties
3. **Long record** - 25 years (2000-2025) of consistent measurements
4. **Multiple pollutants** - EC, OC, sulfate, nitrate, ammonium, 33 elements
5. **EPA data quality** - High-quality measurements with rigorous QA/QC
6. **Public health relevance** - PM2.5 composition affects health outcomes
7. **Clean Air Act** - Supports regulatory monitoring and trends analysis

---

## 2. GEOGRAPHIC & TEMPORAL COVERAGE

### Geographic Coverage

| Attribute | Value |
|-----------|-------|
| **Level** | Site-based (assignable to county) |
| **Sites** | ~180 urban monitoring sites |
| **County Native** | ✅ YES - Each site has county FIPS code |
| **Requires Aggregation** | NO - Sites are already county-assigned |
| **Spatial Completeness** | Major urban areas only (~20-30% of US counties) |
| **US Coverage** | All 50 states + DC (urban areas) |

### Temporal Coverage

| Attribute | Value |
|-----------|-------|
| **Start Year** | 2000 |
| **End Year** | 2025 (current) |
| **Total Years** | 25 years |
| **Sampling Frequency** | 24-hour samples, 1-in-3 days or 1-in-6 days |
| **Data Frequency** | Daily measurements |
| **Reporting Lag** | ~1 year (2024 data available mid-2025) |
| **Data Completeness** | High (>90% for active sites) |

### Expected Data Volume

**Estimated Rows**:
- 2024: 1,780,031 rows (14,119 KB compressed)
- 2023: 1,879,680 rows (14,881 KB compressed)
- 2022: 1,946,625 rows (15,411 KB compressed)
- Average: ~1.9 million rows/year × 25 years = **~47.5 million rows total**

**Estimated Variables**:
- ~40 chemical species (EC, OC, ions, 33 elements)
- 25 years (2000-2024)
- **Total: ~1,000 variable-years** (40 × 25)

**File Sizes**:
- Compressed: ~15 MB/year × 25 years = **~375 MB total compressed**
- Uncompressed: ~100 MB/year × 25 years = **~2.5 GB total uncompressed**

---

## 3. VARIABLES MEASURED

### Core PM2.5 Components (Priority 1)

| Variable | Description | Units | AQS Param Code | Years | Priority |
|----------|-------------|-------|----------------|-------|----------|
| **PM2.5 Mass** | Gravimetric PM2.5 total mass | μg/m³ | 88502 | 2000-2025 | **HIGH** |
| **Elemental Carbon (EC)** | Black carbon | μg/m³ | 88380 | 2000-2025 | **HIGH** |
| **Organic Carbon (OC)** | Organic matter precursor | μg/m³ | 88320 | 2000-2025 | **HIGH** |
| **Sulfate (SO4)** | Secondary sulfate | μg/m³ | 88403 | 2000-2025 | **HIGH** |
| **Nitrate (NO3)** | Secondary nitrate | μg/m³ | 88306 | 2000-2025 | **HIGH** |
| **Ammonium (NH4)** | Neutralizing cation | μg/m³ | 88304 | 2000-2025 | **HIGH** |

### Major Ions (Priority 2)

| Variable | Description | Units | AQS Param Code | Years | Priority |
|----------|-------------|-------|----------------|-------|----------|
| **Chloride (Cl)** | Sea salt, road salt | μg/m³ | 88305 | 2000-2025 | MEDIUM |
| **Sodium (Na)** | Sea salt indicator | μg/m³ | 88191 | 2000-2025 | MEDIUM |
| **Calcium (Ca)** | Crustal element | μg/m³ | 88109 | 2000-2025 | MEDIUM |
| **Magnesium (Mg)** | Crustal element | μg/m³ | 88165 | 2000-2025 | MEDIUM |
| **Potassium (K)** | Biomass burning indicator | μg/m³ | 88159 | 2000-2025 | MEDIUM |

### Trace Elements by XRF (Priority 3)

33 elements measured by X-Ray Fluorescence (XRF), including:

| Element | Health/Environmental Significance | Priority |
|---------|-----------------------------------|----------|
| **Lead (Pb)** | Toxic metal, neurotoxin | HIGH |
| **Arsenic (As)** | Toxic metal, carcinogen | HIGH |
| **Chromium (Cr)** | Toxic metal, hexavalent form carcinogenic | HIGH |
| **Nickel (Ni)** | Respiratory irritant, potential carcinogen | MEDIUM |
| **Vanadium (V)** | Oil combustion tracer | MEDIUM |
| **Zinc (Zn)** | Industrial emissions | MEDIUM |
| **Copper (Cu)** | Brake wear tracer | MEDIUM |
| **Iron (Fe)** | Crustal element | LOW |
| **Silicon (Si)** | Crustal element | LOW |
| **Aluminum (Al)** | Crustal element | LOW |

**Note**: Full list of 33 elements available in CSN AQS Parameters PDF.

### Derived Variables (Optional)

Can be calculated from primary measurements:
- **OC/EC Ratio** - Primary vs secondary organic aerosols
- **Total Carbon (TC)** = OC + EC
- **Crustal Material** = Sum of Al, Si, Ca, Fe, Ti
- **Sea Salt** = Sum of Na, Cl
- **Total Sulfur** = Sulfate + SO2 (if available)

---

## 4. DATA ACCESS METHODS

### Method 1: Pre-Generated CSV Files (RECOMMENDED)

**Why This Method**:
- ✅ No API key required
- ✅ Bulk download (entire years)
- ✅ Standard CSV format
- ✅ Consistent file structure
- ✅ Fast downloads via HTTP

**Base URL**:
```
https://aqs.epa.gov/aqsweb/airdata/
```

**File Naming Convention**:
```
daily_SPEC_[YEAR].zip
```

**Examples**:
```
daily_SPEC_2024.zip  (1,780,031 rows, 14.1 MB)
daily_SPEC_2023.zip  (1,879,680 rows, 14.9 MB)
daily_SPEC_2022.zip  (1,946,625 rows, 15.4 MB)
```

**Year Range**: 2000-2024 (25 files)

**Download Strategy**:
1. Iterate years 2000-2024
2. Download `daily_SPEC_{year}.zip` via HTTPS
3. Extract CSV from ZIP
4. Parse CSV with Polars (fast)
5. Filter to CSN sites only (if needed)
6. Aggregate to county level (already county-assigned)
7. Cache processed data

### Method 2: EPA AQS API (Alternative)

**API Endpoint**:
```
https://aqs.epa.gov/data/api/
```

**API Documentation**:
https://aqs.epa.gov/aqsweb/documents/data_api.html

**Authentication**:
- Requires API key (free signup)
- Email: davidlary@me.com
- Key: greyheron63 (existing EPA AQS key can be reused)

**Advantages**:
- Granular queries (specific sites, dates, parameters)
- Real-time data availability
- JSON format

**Disadvantages**:
- Slower than bulk downloads
- Rate limits (10 req/sec, 500/hour)
- Requires multiple API calls for complete dataset

**Recommendation**: Use **Method 1 (Pre-Generated CSV)** for initial download, Method 2 for updates.

### Method 3: EPA Data Mart (Not Recommended)

EPA also provides data through the Environmental Dataset Gateway, but this requires:
- Complex web interface navigation
- No programmatic access
- Not suitable for automation

---

## 5. FILE FORMAT & DATA STRUCTURE

### CSV File Structure (daily_SPEC_YYYY.zip)

**Column Names** (partial list, ~50 columns total):

| Column | Description | Example |
|--------|-------------|---------|
| `State Code` | State FIPS code | "06" (California) |
| `County Code` | County FIPS code (3-digit) | "037" (Los Angeles) |
| `Site Num` | Site number within county | "1103" |
| `Parameter Code` | AQS parameter code | "88101" (PM2.5) |
| `POC` | Parameter Occurrence Code | "1" |
| `Latitude` | Site latitude | "34.066" |
| `Longitude` | Site longitude | "-118.227" |
| `Datum` | Coordinate datum | "NAD83" |
| `Parameter Name` | Pollutant name | "PM2.5 - Local Conditions" |
| `Date Local` | Sample date | "2024-01-15" |
| `Time Local` | Sample time | "00:00" |
| `Sample Duration` | Duration of sample | "24 HOUR" |
| `Pollutant Standard` | Applicable standard | "PM25 24-hour 2006" |
| `Units of Measure` | Measurement units | "Micrograms/cubic meter (LC)" |
| `Arithmetic Mean` | Mean concentration | "12.5" |
| `1st Max Value` | Daily maximum | "12.5" |
| `AQI` | Air Quality Index | "52" |
| `Method Type` | Measurement method | "FEM" |
| `Method Code` | Method identifier | "170" |
| `Method Name` | Full method name | "Gravimetric" |
| `Local Site Name` | Site name | "Los Angeles-North Main Street" |
| `Address` | Street address | "1630 N. Main Street" |
| `State Name` | State name | "California" |
| `County Name` | County name | "Los Angeles" |
| `City Name` | City name | "Los Angeles" |

**Key Fields for County Aggregation**:
- `State Code` + `County Code` = 5-digit County FIPS
- `Date Local` = Sample date
- `Parameter Code` = Chemical species identifier
- `Arithmetic Mean` = Concentration value
- `Units of Measure` = Units

### Data Quality Flags

| Column | Description |
|--------|-------------|
| `Qualifier` | Data quality flags (e.g., "LE" = less than detection) |
| `Null Data Code` | Reason for missing data |
| `Observation Count` | Number of observations in sample |
| `Observation Percent` | Completeness percentage |

---

## 6. IMPLEMENTATION PLAN

### Phase 1: Research (COMPLETE)

✅ **Status**: COMPLETE
- Identified data source (EPA AQS pre-generated files)
- Determined access method (bulk CSV downloads)
- Catalogued variables (~40 chemical species)
- Verified county-native status (YES)
- Assessed data quality (HIGH)
- No blockers identified

### Phase 2: Downloader Implementation

**File**: `src/downloaders/python/csn_downloader.py`

**Class**: `CSNDownloader(BaseDownloader)`

**Methods**:
```python
def __init__(self, category: str = "01_AIR_ATMOSPHERE")
def get_available_years(self, variable: str) -> List[int]
def download_variable_year(self, variable: str, year: int, force_refresh: bool = False) -> Optional[Path]
def get_metadata(self, variable: str) -> Dict[str, Any]
def _download_spec_file(self, year: int) -> Path
def _extract_zip(self, zip_path: Path) -> Path
def _filter_parameter(self, df: pl.DataFrame, parameter_code: str) -> pl.DataFrame
def _aggregate_to_county(self, df: pl.DataFrame) -> pl.DataFrame
```

**Download Strategy**:
1. Check cache for existing `daily_SPEC_{year}.csv`
2. If not cached or force_refresh:
   a. Download `daily_SPEC_{year}.zip` from EPA
   b. Extract CSV
   c. Store in cache
3. Load CSV with Polars
4. Filter to requested parameter code
5. Aggregate to county level (mean by county-year-parameter)
6. Return county-aggregated DataFrame

**Rate Limiting**:
- No rate limits for pre-generated files (static HTTP downloads)
- Implement 1-second delay between downloads for politeness

**Error Handling**:
- HTTP errors: Retry with exponential backoff (via RetryHandler)
- ZIP extraction errors: Log and skip year
- Data parsing errors: Log and return None
- Missing years: Gracefully return empty DataFrame

### Phase 3: Registry Integration

**File**: `scripts/03_download_source.py`

**Changes Required**:
1. Import CSNDownloader
2. Add to `DOWNLOADER_REGISTRY`:
```python
"csn": {
    "class": CSNDownloader,
    "category": "01_AIR_ATMOSPHERE",
    "description": "EPA Chemical Speciation Network (CSN) - PM2.5 composition",
    "source_id": "01_CHEMICAL_SPECIATION_NETWORK_CS",
},
```
3. Add to `SOURCE_ID_MAPPINGS`:
```python
"01_CHEMICAL_SPECIATION_NETWORK_CS": "csn",
```

**Variables Specification** (for `--variable` flag):
```python
CSN_VARIABLES = {
    "pm25": "88502",
    "ec": "88380",
    "oc": "88320",
    "sulfate": "88403",
    "nitrate": "88306",
    "ammonium": "88304",
    "chloride": "88305",
    "sodium": "88191",
    # ... (full list of 40+ parameters)
}
```

### Phase 4: Testing

**File**: `scripts/test_csn.py`

**Test Cases**:
1. Initialize CSNDownloader
2. Get available years for "pm25" (should return 2000-2024)
3. Download single year (e.g., 2023)
4. Verify cache file exists
5. Load and validate data structure
6. Check county FIPS codes are valid
7. Verify aggregation to county level

**Expected Output**:
```
✅ CSNDownloader initialized
✅ Available years: 2000-2024 (25 years)
✅ Downloaded 2023: daily_SPEC_2023.csv (1,879,680 rows)
✅ Filtered to PM2.5 (88502): 50,000 rows
✅ Aggregated to counties: 3,000 county-years
✅ All county FIPS codes valid
```

### Phase 5: Full Download

**Command**:
```bash
python scripts/03_download_source.py \
  --source csn \
  --variable pm25,ec,oc,sulfate,nitrate,ammonium \
  --years 2000 2001 ... 2024
```

**Expected Duration**:
- 25 years × ~15 MB/year = ~375 MB download
- ~10-20 minutes total (depends on EPA server speed)

**Expected Cache Files**:
```
data/cache/01_AIR_ATMOSPHERE/csn/
├── daily_SPEC_2000.csv
├── daily_SPEC_2001.csv
├── ...
└── daily_SPEC_2024.csv
```

### Phase 6: Processing to TSV

**Command**:
```bash
python scripts/04_process_cached_data.py --source csn
```

**Expected Output**:
```
data/processed/01_AIR_ATMOSPHERE/CSN/
├── CSN_PM25_2000.tsv
├── CSN_PM25_2001.tsv
├── ...
├── CSN_EC_2000.tsv
├── CSN_OC_2000.tsv
├── ...
└── [~1,000 TSV files total (40 vars × 25 years)]
```

**TSV Format**:
```
FIPS	State_FIPS	County_FIPS	State_Name	County_Name	Year	Value	Unit
06037	06	037	California	Los Angeles	2023	12.5	μg/m³
```

### Phase 7: Map Generation

**Command**:
```bash
python scripts/05_generate_maps.py --category 01_AIR_ATMOSPHERE --source CSN
```

**Expected Output**:
```
data/processed/01_AIR_ATMOSPHERE/CSN/
├── CSN_PM25_2000.png
├── CSN_PM25_2001.png
├── ...
└── [~1,000 maps total]
```

**Map Specifications**:
- Format: PNG
- DPI: 300 (publication quality)
- Colormap: "YlOrRd" (yellow-orange-red for pollutants)
- Counties with data: Colored by value
- Counties without data: Light gray

### Phase 8: Documentation & Commit

**Updates Required**:
1. Update `config/sources_registry.json`:
   - Change status: "operational" → "operational"
   - Add variable_count: ~1,000
   - Add implementation.downloader_class: "CSNDownloader"
   - Add implementation.implemented: true

2. Update `NEXT_SESSION_PROMPT.md`:
   - Add CSN to operational sources
   - Update total variable count
   - Update total file count

3. Git commit:
```bash
git add -A
git commit -m "ADD: EPA CSN Downloader - Priority 3 Implementation Complete

Implemented Chemical Speciation Network (CSN) downloader for PM2.5 composition data.

Files Added:
- src/downloaders/python/csn_downloader.py (400 lines)
- scripts/test_csn.py (50 lines)
- docs/CSN_IMPLEMENTATION_NOTES.md (500 lines)

Files Modified:
- scripts/03_download_source.py (added CSN to registry)
- config/sources_registry.json (updated CSN entry)

Data Downloaded:
- 25 years (2000-2024)
- ~40 variables (EC, OC, sulfate, nitrate, etc.)
- ~1,000 TSV files
- ~1,000 maps

Total: ~2,000 new files

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 7. DATA QUALITY ASSESSMENT

### Strengths

1. ✅ **EPA-operated network** - Rigorous QA/QC protocols
2. ✅ **Long record** - 25 years (2000-2025)
3. ✅ **Multiple species** - Comprehensive PM2.5 composition
4. ✅ **Urban focus** - Complements rural IMPROVE network
5. ✅ **County-native** - No spatial aggregation needed
6. ✅ **Public availability** - Free, bulk downloads
7. ✅ **Standardized methods** - Consistent across sites and years
8. ✅ **High completeness** - >90% data capture

### Limitations

1. ⚠️ **Urban only** - Limited to major urban areas (~20-30% of counties)
2. ⚠️ **Incomplete county coverage** - Not all counties have CSN sites
3. ⚠️ **1-year lag** - Data released ~1 year after collection
4. ⚠️ **Sampling frequency** - Not continuous (1-in-3 or 1-in-6 days)
5. ⚠️ **Site changes** - Some sites added/removed over time
6. ⚠️ **Below detection limit** - Some species have detection limits

### Comparison to Alternatives

**vs. IMPROVE Network**:
- CSN: Urban, 2000-present, ~180 sites
- IMPROVE: Rural, 1988-present, ~160 sites
- **Complementary**: Use both for complete US coverage

**vs. EPA AQS Criteria Pollutants**:
- CSN: PM2.5 composition (EC, OC, ions, elements)
- AQS: Criteria pollutants (PM2.5 mass, O3, NO2, SO2, CO)
- **Complementary**: CSN provides composition, AQS provides total mass

**vs. Satellite Data (e.g., MODIS AOD)**:
- CSN: Ground-based, chemical composition, high accuracy
- Satellite: Spatially complete, column AOD, lower accuracy
- **Complementary**: CSN validates satellite retrievals

### Recommended Use Cases

1. **Urban PM2.5 composition trends** - Long-term trends in EC, OC, sulfate, nitrate
2. **Source apportionment** - Identify PM2.5 sources (traffic, power plants, etc.)
3. **Health studies** - Link PM2.5 composition to health outcomes
4. **Regulatory monitoring** - Support PM2.5 NAAQS attainment
5. **Clean Air Act effectiveness** - Track pollution reductions
6. **Climate research** - Black carbon (EC) is a climate forcer

---

## 8. IMPLEMENTATION BLOCKERS

### NONE IDENTIFIED ✅

All requirements are met:
- ✅ Data access method clear (pre-generated CSV files)
- ✅ No authentication required (public HTTP downloads)
- ✅ Data format well-documented (CSV with headers)
- ✅ County FIPS codes available (in data files)
- ✅ Years available (2000-2024, 25 years)
- ✅ Variables catalogued (~40 chemical species)
- ✅ No API rate limits (static file downloads)
- ✅ Compatible with existing framework (similar to EPA AQS)

**Status**: ✅ **READY FOR IMMEDIATE IMPLEMENTATION**

---

## 9. NEXT STEPS

1. ⏳ Implement `CSNDownloader` class in `src/downloaders/python/csn_downloader.py`
2. ⏳ Add CSN to `scripts/03_download_source.py` registry
3. ⏳ Create `scripts/test_csn.py` test script
4. ⏳ Test with single year (2023) to validate approach
5. ⏳ Download full dataset (2000-2024, all variables)
6. ⏳ Process to TSV format (expected ~1,000 files)
7. ⏳ Generate maps (expected ~1,000 PNG files)
8. ⏳ Update `config/sources_registry.json` status to operational
9. ⏳ Commit with detailed statistics

**Estimated Implementation Time**: 2-3 hours for complete cycle

---

## 10. REFERENCES

### Primary Sources

- [EPA Chemical Speciation Network (CSN)](https://www.epa.gov/amtic/chemical-speciation-network-csn)
- [CSN Parameters Reported to AQS](https://www.epa.gov/amtic/chemical-speciation-network-parameters-reported-air-quality-system-aqs)
- [EPA AQS Pre-Generated Data Files](https://aqs.epa.gov/aqsweb/airdata/download_files.html)
- [EPA AQS API Documentation](https://aqs.epa.gov/aqsweb/documents/data_api.html)

### Supporting Documentation

- [CSN General Information](https://www.epa.gov/amtic/chemical-speciation-network-csn-general-information-0)
- [PM2.5 Speciation Sampling Methods](https://aqs.epa.gov/aqsweb/documents/codetables/methods_speciation.html)
- [CSN and IMPROVE Network Description (2014 Paper)](https://www.tandfonline.com/doi/full/10.1080/10962247.2014.956904)
- Companion Repository: `SocialEnvironmentalObservatoryDataList/01_AIR_ATMOSPHERE/ATMOSPHERIC_EMISSIONS_CHEMISTRY_COMPREHENSIVE.md`

---

**Last Updated**: 2025-11-28
**Author**: Claude Code
**Status**: ✅ READY FOR IMPLEMENTATION
**Next Action**: Implement CSNDownloader class
**Blockers**: NONE

---

## APPENDIX A: Full CSN Parameter List

(To be populated from EPA CSN AQS Parameters PDF - 40+ parameters)

**Priority 1 (Core 6)**:
1. PM2.5 Mass (88502)
2. Elemental Carbon (88380)
3. Organic Carbon (88320)
4. Sulfate (88403)
5. Nitrate (88306)
6. Ammonium (88304)

**Priority 2 (Major Ions)**:
7. Chloride (88305)
8. Sodium (88191)
9. Calcium (88109)
10. Magnesium (88165)
11. Potassium (88159)

**Priority 3 (Trace Elements)**:
12-44. 33 elements measured by XRF (Al, Si, P, S, Cl, K, Ca, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn, Ga, As, Se, Br, Rb, Sr, Y, Zr, Mo, Pd, Ag, Cd, In, Sn, Sb, Ba, Pb)

**Note**: Full parameter codes available in EPA CSN AQS Parameters PDF (July 2020, 71 KB).

---

## APPENDIX B: Expected Data Statistics

**Per Year** (example: 2023):
- Raw CSV rows: 1,879,680
- Unique sites: ~180
- Unique counties: ~150-200 (urban counties)
- Parameters: ~40
- File size (compressed): 14.9 MB
- File size (uncompressed): ~100 MB

**Total (2000-2024, 25 years)**:
- Raw CSV rows: ~47.5 million
- TSV files: ~1,000 (40 vars × 25 years)
- Map files: ~1,000
- Total files: ~2,000
- Total size: ~375 MB compressed, ~2.5 GB uncompressed

**After County Aggregation**:
- Counties per year: ~150-200 (only urban counties with CSN sites)
- TSV rows per file: ~150-200
- Total TSV rows: ~200,000 (across all 1,000 files)
