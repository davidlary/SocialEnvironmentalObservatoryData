# CDC Environmental Public Health Tracking Network - Radon Testing
## Implementation Research Notes

**Date**: 2025-11-24
**Source ID**: 05_CDC_ENVIRONMENTAL_HEALTH_TRACK
**Category**: 05_RADIATION
**Priority**: 2
**Status**: Research Complete - Ready for Implementation

---

## Executive Summary

The CDC Environmental Public Health Tracking Network (EPHT) provides **actual radon test results** at the county level from 2013-present. This is the **best available source** for recent, empirical radon data (not modeled or predicted).

**Key Advantages**:
- ✅ Actual test results (not predictions)
- ✅ County-level geographic resolution
- ✅ Annual updates (data through 2022)
- ✅ Standardized national database
- ✅ Free RESTful API access
- ✅ Large sample size (6+ million tests compiled 1993-2021; 11.9M tests 1988-2022)

**Implementation Status**: **GREEN** - Straightforward API access with clear documentation

---

## Data Source Details

### Official Information
- **Name**: Environmental Public Health Tracking Network - Radon Testing Indicator
- **Agency**: Centers for Disease Control and Prevention (CDC)
- **Base URL**: https://ephtracking.cdc.gov/
- **API Base**: https://ephtracking.cdc.gov/apigateway/api/v1/
- **API Documentation**: https://ephtracking.cdc.gov/apihelp
- **Contact**: ephtrackingsupport@cdc.gov

### Geographic Coverage
- **States**: 46 states + DC (county-level data where available)
- **21 Contributing States** (2014-2023): AK, CO, CT, FL, IL, KS, LA, MN, MO, NE, NJ, NY, NC, OR, PA, RI, TN, UT, VT, WA, WI
- **Counties**: Variable by state (counties with <10 tests are suppressed)

### Temporal Coverage
- **Historical**: Some data back to 1988 (varies by state)
- **Primary Period**: 2013-present (national lab data)
- **Most Recent**: Data through 2022 available
- **Update Frequency**: Annual (1-2 year lag typical)

### Data Sources Compiled by CDC
1. CDC Tracking Program-funded states (21 states)
2. Six national radon testing laboratories:
   - AccuStar Labs
   - Air Chek, Inc.
   - Kansas State University
   - PRO-LAB
   - Radon.com
   - University Analytical Laboratories
3. State radon programs (where data sharing agreements exist)

---

## Variables Available (County-Level)

### Primary Metrics

| Variable | Description | Units | Priority |
|----------|-------------|-------|----------|
| `num_tests` | Total radon tests conducted in county | Count | High |
| `mean_radon` | Average radon concentration | pCi/L | High |
| `median_radon` | Median radon concentration | pCi/L | High |
| `pct_above_4` | Percent exceeding EPA action level (4 pCi/L) | Percent | High |
| `pct_above_2_7` | Percent exceeding WHO guideline (2.7 pCi/L) | Percent | Medium |
| `test_type` | Short-term (<90 days) vs long-term (≥90 days) | Categorical | Medium |
| `test_location` | Basement, first floor, living area | Categorical | Low |
| `test_year` | Year of testing | Year | High |

### Stratifications Available
- By county (FIPS code)
- By year (annual data)
- By test duration (short-term <90 days, long-term ≥90 days)
- By test location (basement, first floor, living area)

### Data Suppression Rules
- **<10 tests**: County data suppressed for privacy
- **Indication**: Asterisk (*) or "Data not available"

---

## API Access Method

### Authentication
- **API Key**: Required (free)
- **Registration**: Email trackingsupport@cdc.gov or use API help page
- **Storage**: Can be stored in environment variable or .Renviron file

### API Structure

**Measure ID for Radon**: `479`

**Base Endpoint Pattern**:
```
https://ephtracking.cdc.gov/apigateway/api/v1/getCoreHolder/{contentAreaId}/{stateId}/{countyId}
```

**Query Parameters**:
- `apiToken`: API key (required if not using registered IP)
- `measureId`: 479 (radon testing)
- `stratificationLevelId`: Geographic level
  - 1 = County level
- `isSmoothed`: false (we want raw data)
- `year`: Specific year or range

### Example API Calls

**1. Get all counties in a state for a specific year**:
```
https://ephtracking.cdc.gov/apigateway/api/v1/getCoreHolder/479/17/0?apiToken=YOUR_KEY&measureId=479&stratificationLevelId=1&isSmoothed=false&year=2021
```
- `17` = Illinois state FIPS
- `0` = All counties in state

**2. Get specific county**:
```
https://ephtracking.cdc.gov/apigateway/api/v1/getCoreHolder/479/17/031?apiToken=YOUR_KEY&measureId=479&stratificationLevelId=1&isSmoothed=false&year=2021
```
- `17` = Illinois state FIPS
- `031` = Cook County FIPS suffix

**3. Get all available years for a state**:
```
Loop through years 2013-2022 or use temporal items endpoint
```

### API Response Format
- **Format**: JSON
- **Structure**: Array of objects with:
  - `countyFips`: 5-digit FIPS code
  - `geoValue`: Geographic name
  - `dataValue`: Measurement value
  - `year`: Data year
  - Additional stratification fields

### Helper Endpoints

**List available measures**:
```
https://ephtracking.cdc.gov/apigateway/api/v1/measures
```

**List available geographic items**:
```
https://ephtracking.cdc.gov/apigateway/api/v1/geographic/479/{stateId}
```

**List available temporal items**:
```
https://ephtracking.cdc.gov/apigateway/api/v1/temporal/479/{stateId}
```

---

## Implementation Plan

### Phase 1: API Key Setup
1. Email trackingsupport@cdc.gov to request API key
2. Store in environment variable `CDC_EPHT_API_KEY`
3. Add to .env file (excluded from git)

### Phase 2: Metadata Discovery
1. Query measures endpoint to verify radon measure ID (479)
2. List available states with radon data
3. For each state:
   - List available counties
   - List available years
4. Create metadata cache of available data

### Phase 3: Data Download
1. Iterate through all states (51 total including DC)
2. For each state:
   - Query all counties (countyId=0)
   - For each available year (2013-2022+)
   - Handle rate limiting (if any)
3. Parse JSON responses
4. Convert to standardized TSV format with FIPS codes

### Phase 4: Data Validation
1. Verify FIPS codes match metadata
2. Check for missing counties (suppression due to <10 tests)
3. Validate value ranges:
   - Radon levels: 0-100 pCi/L reasonable (flag >100)
   - Percentages: 0-100
   - Test counts: >0
4. Log data quality metrics

### Phase 5: Output Generation
1. Generate TSV files: `{year}_radon_testing.tsv`
2. Include all available variables
3. Merge with FIPS metadata (county names, state names)
4. Create data dictionary
5. Generate summary statistics
6. Create choropleth maps (optional)

---

## Data Quality Considerations

### Strengths
- ✅ Actual test results (not modeled)
- ✅ Large sample size (millions of tests)
- ✅ Standardized across laboratories
- ✅ Recent data (annually updated)
- ✅ Nationally consistent methodology

### Limitations
- ⚠️ **Selection bias**: Voluntary testing; homeowners in high-radon areas more likely to test
- ⚠️ **Not representative**: Does not represent all homes in county
- ⚠️ **Privacy suppression**: Counties with <10 tests excluded
- ⚠️ **Variable coverage**: Some counties have few tests
- ⚠️ **Lag time**: Data typically 1-2 years behind current year
- ⚠️ **Test type mix**: Combination of short-term and long-term tests

### Use Case Appropriateness
- ✅ **Good for**: Comparing radon risk across counties, validating EPA radon zones
- ⚠️ **Caution**: Not a random sample; cannot estimate population exposure
- ❌ **Not for**: Individual home predictions, precise prevalence estimates

---

## Comparison to Other Radon Sources

| Source | Type | Coverage | Recency | Pros | Cons |
|--------|------|----------|---------|------|------|
| **CDC EPHT** | Actual tests | 46 states, county | 2013-2022 | Real data, recent, free API | Selection bias, suppression |
| EPA Radon Zones | Model | All counties | 1993 (static) | Complete coverage | Outdated, categorical only |
| State Programs | Actual tests | Varies | Varies | Often larger samples | Inconsistent access, formats |
| LBNL Model | Bayesian model | All counties | 1993 | Quantitative predictions | Outdated, not updated |

**Recommendation**: Use CDC EPHT as **primary source** for radon data. Supplement with EPA Zones for complete county coverage (for counties with suppressed CDC data).

---

## Implementation Code Outline

### Python Class Structure
```python
class CDCEPHTRadonDownloader(BaseDownloader):
    """Download radon testing data from CDC Environmental Public Health Tracking Network."""

    BASE_URL = "https://ephtracking.cdc.gov/apigateway/api/v1"
    RADON_MEASURE_ID = 479
    CONTENT_AREA_ID = 479

    def __init__(self):
        super().__init__(
            source_id="05_CDC_ENVIRONMENTAL_HEALTH_TRACK",
            source_name="CDC Environmental Public Health Tracking - Radon",
            category="05_RADIATION"
        )
        self.api_key = os.getenv("CDC_EPHT_API_KEY")

    def fetch_available_data(self):
        """Discover which states, counties, years have data."""
        # Query temporal endpoint for years
        # Query geographic endpoint for states/counties
        pass

    def download_state_year(self, state_fips, year):
        """Download all counties for a state-year."""
        url = f"{self.BASE_URL}/getCoreHolder/{self.CONTENT_AREA_ID}/{state_fips}/0"
        params = {
            "apiToken": self.api_key,
            "measureId": self.RADON_MEASURE_ID,
            "stratificationLevelId": 1,
            "isSmoothed": False,
            "year": year
        }
        # Make request, parse JSON, return dataframe
        pass

    def process_data(self, raw_data):
        """Convert JSON to standardized TSV format."""
        # Parse JSON array
        # Extract relevant fields
        # Merge with FIPS metadata
        # Return polars DataFrame
        pass

    def validate_data(self, df):
        """Validate data quality."""
        # Check FIPS codes
        # Validate value ranges
        # Flag anomalies
        pass

    def run(self):
        """Main download workflow."""
        # 1. Fetch available data metadata
        # 2. For each state-year combination:
        #    - Download data
        #    - Process and validate
        #    - Save to cache
        # 3. Generate TSV outputs
        # 4. Generate maps
        pass
```

---

## Expected Output Files

### Data Files
```
data/processed/05_RADIATION/CDC_EPHT_RADON/
├── 2013_radon_testing.tsv
├── 2014_radon_testing.tsv
├── ...
├── 2022_radon_testing.tsv
└── metadata/
    ├── data_dictionary.json
    ├── coverage_summary.tsv
    └── quality_metrics.tsv
```

### TSV Schema
```
fips_code (str): 5-digit county FIPS
state_name (str): State name
county_name (str): County name
year (int): Testing year
num_tests (int): Number of tests
mean_radon_pci_l (float): Mean radon level
median_radon_pci_l (float): Median radon level
pct_above_4_pci_l (float): Percent ≥4 pCi/L
pct_above_2_7_pci_l (float): Percent ≥2.7 pCi/L
test_type (str): Short-term/Long-term (if available)
test_location (str): Location type (if available)
```

---

## Next Steps

1. ✅ **Research complete** - This document
2. ⏳ **API key acquisition** - Email trackingsupport@cdc.gov
3. ⏳ **Implement downloader** - Create `cdc_epht_radon_downloader.py`
4. ⏳ **Test with single state** - Verify API access and data parsing
5. ⏳ **Full download** - All states, all years
6. ⏳ **Documentation** - Update registry, generate summary statistics
7. ⏳ **Commit and push** - Phase 1 completion

---

## References

### Primary Documentation
- **CDC EPHT Main Portal**: https://ephtracking.cdc.gov/
- **Radon Data Page**: https://www.cdc.gov/environmental-health-tracking/php/data-research/radon-testing.html
- **API Help**: https://ephtracking.cdc.gov/apihelp
- **GitHub Repository**: https://github.com/CDCgov/EPHTracking

### Supporting Resources
- **R Package (EPHTrackR)**: https://github.com/CDCgov/EPHTrackR
- **API Assistant Tool**: https://ephtracking-api.surge.sh/
- **Radon Monitoring Report**: https://ephtracking.cdc.gov/RadonMonitoring-DataCollection-US.pdf
- **Comprehensive Radon Documentation**: ~/Dropbox/Environments/Code/GetData/SocialEnvironmentalObservatoryDataList/05_RADIATION/RADON_OIL_GAS_ENERGY_COMPREHENSIVE.md

### Contact
- **Technical Support**: ephtrackingsupport@cdc.gov
- **API Questions**: trackingsupport@cdc.gov

---

## Implementation Blockers: NONE

All requirements for implementation are clear and accessible:
- ✅ API is public and documented
- ✅ No authentication complexity (just need API key via email)
- ✅ Data format is standard JSON
- ✅ Example code available in companion repository
- ✅ Measure IDs and endpoints documented

**Status**: **READY FOR IMPLEMENTATION** 🟢

---

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Next Review**: After API key acquisition
