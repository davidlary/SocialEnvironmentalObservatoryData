# US County-Level Observatory Data Download System
## Comprehensive Implementation Plan v1.0

**Project**: Automated download, processing, and visualization of 43,000+ variables from 200+ data sources
**Geographic Coverage**: 3,143 US Counties
**Temporal Range**: 1940-Present (varies by source)
**Compute Resources**: 10 cores, 32GB RAM, 1.9TB disk
**Methodology**: Context-Preserving Framework v4.7.1
**Created**: 2025-11-21

---

## 🎯 PROJECT OBJECTIVES

1. **Download**: Acquire all 43,000+ variables from 200+ authoritative data sources
2. **Process**: Generate county-level TSV files (one per variable per year) with FIPS metadata
3. **Visualize**: Create choropleth maps (one per variable per year) showing county-level data
4. **Cache**: Store original data locally to minimize bandwidth and enable updates
5. **Maintain**: Support incremental updates to keep data current
6. **Recover**: Enable seamless recovery from any failure point

---

## 📋 SYSTEM ARCHITECTURE

### Core Design Principles

1. **Modular by Source Type**: Each data source has dedicated downloader module
2. **Hierarchical Processing**: Category → Source → Variable → Year → County
3. **Intelligent Caching**: Download once, process many times
4. **Parallel Processing**: Process years in parallel (10 cores), variables sequentially
5. **Comprehensive Logging**: Every operation logged with timestamps, success/failure
6. **Idempotent Operations**: Can rerun safely without duplicating work
7. **Graceful Degradation**: Failure of one variable doesn't stop others
8. **Progress Tracking**: JSON-based state tracking for resumability

### Data Flow Architecture

```
Data Sources (200+)
    ↓
[Downloader Modules] → Cache (original files)
    ↓
[Processors] → Extract/Transform/Aggregate to county level
    ↓
[TSV Generator] → data/processed/{Category}/{Variable}/{Year}_data.tsv
    ↓
[Map Generator] → data/processed/{Category}/{Variable}/{Year}_map.png
```

### Technology Stack

- **Language**: Python 3.9+
- **Data Processing**: pandas, numpy, xarray
- **GIS Operations**: geopandas, rasterio, pyproj, shapely
- **Mapping**: matplotlib, cartopy (or geoplot)
- **HTTP Requests**: requests, urllib3 (with retry logic)
- **Parallel Processing**: multiprocessing, concurrent.futures
- **Configuration**: JSON, YAML
- **Testing**: pytest
- **Logging**: Python logging module with rotating file handlers

---

## 📁 DIRECTORY STRUCTURE

```
SocialEnvironmentalObservatoryData/
│
├── config/                                    # Configuration files
│   ├── sources_registry.json                 # Master registry of all 200+ sources
│   ├── priority_order.json                   # Processing order (NHGIS first)
│   ├── api_credentials.json                  # API keys (gitignored)
│   └── processing_config.yaml                # Runtime configuration
│
├── src/                                       # Source code
│   ├── __init__.py
│   ├── core/                                  # Core framework
│   │   ├── __init__.py
│   │   ├── base_downloader.py                # Abstract base class for downloaders
│   │   ├── cache_manager.py                  # Cache management and validation
│   │   ├── progress_tracker.py               # Track completed work
│   │   ├── logger.py                         # Centralized logging
│   │   ├── tsv_generator.py                  # TSV file creation with FIPS metadata
│   │   ├── map_generator.py                  # Choropleth map generation
│   │   ├── metadata_manager.py               # FIPS codes, county boundaries
│   │   └── retry_handler.py                  # Exponential backoff retry logic
│   │
│   ├── downloaders/                           # Source-specific downloaders
│   │   ├── __init__.py
│   │   ├── nhgis_downloader.py               # NHGIS (manual + automated)
│   │   ├── epa_aqs_downloader.py             # EPA Air Quality System API
│   │   ├── cdc_wonder_downloader.py          # CDC WONDER API
│   │   ├── usgs_nwis_downloader.py           # USGS Water Quality
│   │   ├── census_api_downloader.py          # Census Bureau APIs
│   │   ├── bulk_csv_downloader.py            # Generic bulk CSV
│   │   ├── raster_downloader.py              # Gridded raster data (NLCD, ERA5)
│   │   ├── netcdf_downloader.py              # NetCDF files (ERA5, climate)
│   │   └── facility_downloader.py            # Point source data (TRI, Superfund)
│   │
│   ├── processors/                            # Data processors
│   │   ├── __init__.py
│   │   ├── county_aggregator.py              # Aggregate to county level
│   │   ├── raster_to_county.py               # Zonal statistics for rasters
│   │   ├── point_to_county.py                # Spatial join facilities to counties
│   │   ├── temporal_aggregator.py            # Annual/monthly aggregation
│   │   └── data_validator.py                 # Data quality checks
│   │
│   └── utils/                                 # Utility functions
│       ├── __init__.py
│       ├── api_client.py                     # Generic API client with rate limiting
│       ├── file_utils.py                     # File I/O helpers
│       ├── geo_utils.py                      # Geographic utilities
│       └── constants.py                      # Global constants
│
├── scripts/                                   # Executable scripts
│   ├── 00_setup_environment.py               # One-time setup (install deps, dirs)
│   ├── 01_download_metadata.py               # Download FIPS codes, boundaries
│   ├── 02_build_source_registry.py           # Parse data list docs to JSON registry
│   ├── 03_download_source.py                 # Main orchestrator (one source at a time)
│   ├── 04_process_cached_data.py             # Process cached files to TSV
│   ├── 05_generate_maps.py                   # Generate all maps
│   ├── 06_validate_outputs.py                # Validate TSV files and maps
│   ├── 07_update_data.py                     # Check for new years and update
│   └── 08_generate_report.py                 # Summary report of data coverage
│
├── data/                                      # Data storage
│   ├── cache/                                 # Original downloaded files
│   │   ├── 00_METADATA/                      # FIPS codes, boundaries
│   │   ├── 01_AIR_ATMOSPHERE/
│   │   │   ├── epa_aqs/
│   │   │   └── epa_nei/
│   │   ├── 02_WATER/
│   │   └── ... (all 25 categories)
│   │
│   ├── processed/                             # Final TSV files and maps
│   │   ├── 00_METADATA/
│   │   │   └── fips_county_metadata.tsv      # Master FIPS reference
│   │   ├── 01_AIR_ATMOSPHERE/
│   │   │   ├── PM25_Annual_Mean/
│   │   │   │   ├── 2015_PM25_Annual_Mean.tsv
│   │   │   │   ├── 2015_PM25_Annual_Mean.png
│   │   │   │   ├── 2016_PM25_Annual_Mean.tsv
│   │   │   │   ├── 2016_PM25_Annual_Mean.png
│   │   │   │   └── ... (one per year available)
│   │   │   └── ... (one directory per variable)
│   │   └── ... (all 25 categories)
│   │
│   └── metadata/                              # Geographic reference files
│       ├── county_boundaries_2020.gpkg        # County shapefile
│       ├── fips_codes_master.csv              # Official FIPS codes
│       └── variable_metadata.json             # Variable descriptions, units
│
├── logs/                                      # Log files
│   ├── main.log                               # Master log (rotating)
│   ├── errors.log                             # Errors only
│   ├── downloads/                             # Download logs by source
│   │   ├── nhgis_20251121_143022.log
│   │   └── ...
│   └── processing/                            # Processing logs
│       └── ...
│
├── progress/                                  # Progress tracking
│   ├── download_progress.json                # Track completed downloads
│   ├── processing_progress.json              # Track completed processing
│   └── map_progress.json                     # Track completed maps
│
├── tests/                                     # Unit and integration tests
│   ├── __init__.py
│   ├── test_downloaders/
│   │   ├── test_base_downloader.py
│   │   ├── test_nhgis_downloader.py
│   │   └── ...
│   ├── test_processors/
│   │   ├── test_county_aggregator.py
│   │   └── ...
│   ├── test_core/
│   │   ├── test_cache_manager.py
│   │   ├── test_tsv_generator.py
│   │   └── test_map_generator.py
│   └── fixtures/                              # Test data
│       └── sample_data.csv
│
├── docs/                                      # Documentation
│   ├── ARCHITECTURE.md                       # System architecture
│   ├── DATA_SOURCES.md                       # Data source documentation
│   ├── API_REFERENCE.md                      # Code API reference
│   ├── DEPLOYMENT.md                         # Deployment guide
│   └── TROUBLESHOOTING.md                    # Common issues and solutions
│
├── .gitignore                                 # Git ignore patterns
├── requirements.txt                           # Python dependencies
├── setup.py                                   # Package setup
├── README.md                                  # Project README
├── IMPLEMENTATION_PLAN.md                     # This file
└── CHANGELOG.md                               # Version history

```

---

## 🗂️ FILE SPECIFICATIONS

### Configuration Files

#### `config/sources_registry.json`
```json
{
  "version": "1.0",
  "last_updated": "2025-11-21",
  "sources": [
    {
      "id": "nhgis",
      "name": "IPUMS NHGIS",
      "priority": 1,
      "category": "00_METADATA",
      "description": "Pre-harmonized demographic, social, economic, housing data",
      "access_method": "manual_extract",
      "requires_account": true,
      "base_url": "https://data2.nhgis.org/",
      "temporal_coverage": {"start": 1790, "end": 2024, "frequency": "varies"},
      "geographic_level": "county",
      "estimated_variables": 10000,
      "downloader_module": "nhgis_downloader",
      "notes": "Requires manual extract definition; 389 time series tables + 1,300+ ACS tables"
    },
    {
      "id": "epa_aqs",
      "name": "EPA Air Quality System",
      "priority": 2,
      "category": "01_AIR_ATMOSPHERE",
      "access_method": "api",
      "base_url": "https://aqs.epa.gov/data/api/",
      "api_key_required": true,
      "rate_limit": {"requests_per_second": 5, "requests_per_hour": 500},
      "temporal_coverage": {"start": 1980, "end": 2024, "frequency": "annual"},
      "geographic_level": "county",
      "estimated_variables": 200,
      "downloader_module": "epa_aqs_downloader"
    }
  ]
}
```

#### `config/priority_order.json`
```json
{
  "processing_order": [
    "00_METADATA",
    "01_AIR_ATMOSPHERE",
    "02_WATER",
    "03_LAND_SOIL_GEOLOGY",
    "04_TOXIC_CHEMICALS",
    "05_RADIATION",
    "06_CLIMATE_WEATHER",
    "07_BUILT_ENVIRONMENT",
    "08_INFRASTRUCTURE",
    "09_OCCUPATIONAL",
    "10_AGRICULTURE_FOOD",
    "11_INFECTIOUS_DISEASE",
    "12_MORTALITY_DISEASE",
    "13_HEALTH_STATUS",
    "14_HEALTHCARE_SYSTEM",
    "15_DEMOGRAPHICS",
    "16_SOCIOECONOMIC",
    "17_SOCIAL_DETERMINANTS",
    "18_EDUCATION",
    "19_ECONOMIC_INDICATORS",
    "20_ENERGY_UTILITIES",
    "21_WILDFIRE_HAZARDS",
    "22_FLOOD_HAZARDS",
    "23_INTERNATIONAL_SOURCES"
  ],
  "skip_categories": ["25_PAID_RESTRICTED_DATA"]
}
```

#### `config/processing_config.yaml`
```yaml
# Processing configuration
parallel:
  max_workers: 8  # Leave 2 cores free for system
  timeout_seconds: 3600  # 1 hour per year download

cache:
  enabled: true
  max_age_days: 365  # Re-download if older than 1 year
  validate_checksums: true

output:
  tsv_format:
    delimiter: "\t"
    encoding: "utf-8"
    include_header: true
    na_value: "NA"

  map_format:
    dpi: 300
    format: "png"
    figsize: [12, 8]
    colormap: "YlOrRd"
    quantiles: 5  # Quantile-based color bins

logging:
  level: "INFO"
  max_bytes: 10485760  # 10MB
  backup_count: 10
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

retry:
  max_attempts: 3
  backoff_factor: 2  # Exponential backoff
  timeout: 30
```

### Core Module Files

#### `src/core/base_downloader.py`
Abstract base class defining interface for all downloaders:
- `download()`: Download data for specific variable/year
- `get_available_years()`: Query available years for variable
- `validate_cache()`: Check if cached data is valid
- `get_metadata()`: Return variable metadata

#### `src/core/cache_manager.py`
Manages local cache:
- `check_cache(source, variable, year)`: Check if data cached and valid
- `save_to_cache(data, source, variable, year)`: Save downloaded data
- `get_cache_path(source, variable, year)`: Return cache file path
- `clean_old_cache(max_age_days)`: Remove stale cache files
- `validate_cache_integrity()`: Verify cache not corrupted

#### `src/core/progress_tracker.py`
Tracks completion state:
- `mark_downloaded(source, variable, year)`: Mark year as downloaded
- `mark_processed(source, variable, year)`: Mark year as processed
- `mark_mapped(source, variable, year)`: Mark map as created
- `get_pending_work(source)`: Return list of incomplete work
- `save_checkpoint()`: Persist progress to disk
- `load_checkpoint()`: Resume from last checkpoint

#### `src/core/logger.py`
Centralized logging:
- `setup_logging()`: Initialize logging system
- `log_download(source, variable, year, status)`: Log download attempt
- `log_error(error, context)`: Log error with full context
- `log_progress(completed, total)`: Log progress percentage

#### `src/core/tsv_generator.py`
Generate TSV files with FIPS metadata:
- `create_tsv(data, variable, year, output_path)`: Create TSV file
- `add_fips_metadata(df)`: Join FIPS codes, county names, state names
- `validate_tsv(file_path)`: Verify TSV structure
- Column order: `FIPS, State_FIPS, County_FIPS, State_Name, County_Name, Year, Variable_Value, Unit`

#### `src/core/map_generator.py`
Generate choropleth maps:
- `create_map(tsv_path, output_path, variable_metadata)`: Create map from TSV
- `load_county_boundaries()`: Load shapefile once (cached)
- `apply_colormap(data, bins)`: Apply quantile-based color scheme
- `add_map_elements(fig, ax, title, legend)`: Title, legend, colorbar
- `save_map(fig, output_path, dpi)`: Save high-resolution PNG

#### `src/core/metadata_manager.py`
Manage FIPS codes and boundaries:
- `download_fips_codes()`: Download official Census FIPS list
- `download_county_boundaries(year)`: Download TIGER/Line shapefile
- `load_fips_lookup()`: Return pandas DataFrame of FIPS codes
- `validate_fips(fips_list)`: Check for invalid FIPS codes

---

## 🔄 PROCESSING WORKFLOW

### Phase 1: Setup and Metadata (Scripts 00-01)

**Script**: `scripts/00_setup_environment.py`
1. Check Python version (>=3.9)
2. Install dependencies from `requirements.txt`
3. Create directory structure
4. Verify write permissions
5. Initialize progress tracking files
6. Create initial log files

**Script**: `scripts/01_download_metadata.py`
1. Download Census FIPS codes (3,143 counties)
2. Download TIGER/Line county boundaries (2020 vintage)
3. Create master FIPS lookup table with metadata:
   - FIPS (5-digit string)
   - State FIPS (2-digit string)
   - County FIPS (3-digit string)
   - State name
   - County name
   - State abbreviation
4. Save to `data/metadata/fips_codes_master.csv`
5. Save boundaries to `data/metadata/county_boundaries_2020.gpkg`
6. Validate: 3,143 records, all FIPS unique

### Phase 2: Build Source Registry (Script 02)

**Script**: `scripts/02_build_source_registry.py`
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

### Phase 3: Download and Process (Script 03-04)

**Script**: `scripts/03_download_source.py` (Main orchestrator)

**Command line interface**:
```bash
python scripts/03_download_source.py --source nhgis
python scripts/03_download_source.py --category 01_AIR_ATMOSPHERE
python scripts/03_download_source.py --all  # Process all sources in priority order
```

**Workflow for each source**:
1. Load source configuration from registry
2. Initialize source-specific downloader module
3. Get list of variables for source
4. For each variable:
   a. Get available years
   b. Check progress tracker for completed years
   c. For incomplete years:
      - Check cache (if valid, skip download)
      - If not cached or stale:
        * Download data with retry logic
        * Save to cache
        * Validate downloaded data
   d. Log progress
5. On completion, mark source as downloaded
6. On error, log error and continue to next variable

**Parallel processing strategy**:
```python
# Sequential over variables (easier debugging)
for variable in variables:
    years = get_available_years(variable)

    # Parallel over years (utilize 8 cores)
    with multiprocessing.Pool(8) as pool:
        results = pool.starmap(download_year,
                               [(variable, year) for year in years])
```

**Script**: `scripts/04_process_cached_data.py`

**Workflow**:
1. Scan cache directory for downloaded files
2. For each cached file:
   a. Check if already processed (TSV exists and is newer)
   b. If not processed:
      - Load cached data
      - Apply source-specific processor
      - Aggregate to county level (if needed)
      - Join FIPS metadata
      - Generate TSV file in `data/processed/{Category}/{Variable}/`
      - Validate TSV structure
   c. Mark as processed in progress tracker
3. Log summary: X variables processed, Y TSV files created

### Phase 4: Map Generation (Script 05)

**Script**: `scripts/05_generate_maps.py`

**Command line interface**:
```bash
python scripts/05_generate_maps.py --variable PM25_Annual_Mean
python scripts/05_generate_maps.py --category 01_AIR_ATMOSPHERE
python scripts/05_generate_maps.py --all
```

**Workflow**:
1. Load county boundaries shapefile (once, cached in memory)
2. Scan `data/processed/` for TSV files
3. For each TSV file without corresponding map:
   a. Load TSV data
   b. Merge with county boundaries on FIPS
   c. Create choropleth map:
      - Quantile-based color bins (5 bins)
      - Color scheme: YlOrRd (yellow-orange-red)
      - Title: "{Variable Name} - {Year}"
      - Legend with value ranges
      - Colorbar with units
   d. Save PNG to same directory as TSV
   e. Mark as mapped in progress tracker
4. Log summary: X maps created

**Map parallelization**:
```python
# Parallel map generation (embarrassingly parallel)
with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(create_map, tsv_path)
               for tsv_path in tsv_files]
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
```

### Phase 5: Validation and Reporting (Scripts 06-08)

**Script**: `scripts/06_validate_outputs.py`
1. Scan `data/processed/` for TSV files
2. For each TSV:
   - Validate structure (required columns present)
   - Validate FIPS codes (all valid, no duplicates)
   - Check for missing values
   - Verify data types
3. For each map:
   - Verify file exists and is readable
   - Check file size (>0 bytes)
4. Generate validation report
5. Log errors for manual review

**Script**: `scripts/07_update_data.py`
1. For each source in registry:
   a. Query for latest available year
   b. Compare with local data
   c. If new years available:
      - Download new years only
      - Process to TSV
      - Generate maps
2. Update progress tracker
3. Log summary of updates

**Script**: `scripts/08_generate_report.py`
1. Generate summary statistics:
   - Total sources processed
   - Total variables downloaded
   - Total TSV files created
   - Total maps generated
   - Temporal coverage by category
   - Data completeness (% of expected files)
2. Create HTML report with:
   - Summary tables
   - Coverage heatmap (variables × years)
   - Sample maps
3. Save to `docs/DATA_COVERAGE_REPORT.html`

---

## 🧩 IMPLEMENTATION MODULES

### Module 1: NHGIS Downloader (Priority 1)

**File**: `src/downloaders/nhgis_downloader.py`

**Challenge**: NHGIS requires manual extract definition through web interface

**Approach**:
1. **Semi-automated workflow**:
   - User creates extract at https://data2.nhgis.org/
   - System monitors download directory for ZIP file
   - Automatically unzips and processes CSV files

2. **Extract organization**:
   - Create one extract per decade (1790-1890, 1900-1950, 1960-1990, 2000-2020, ACS 2010-2023)
   - Each extract downloads as ZIP containing CSV files

3. **Processing**:
   - Parse CSV files (standard NHGIS format)
   - Map NHGIS codes to FIPS codes
   - Handle boundary changes (use crosswalks)
   - Split by variable and year
   - Generate TSV files

**Implementation steps**:
1. Create NHGIS account and get API key (if available)
2. Document required extracts (389 time series tables)
3. Implement CSV parser for NHGIS format
4. Implement NHGIS-to-FIPS code mapping
5. Test with one extract (e.g., 2020 ACS 5-year)

### Module 2: EPA AQS API Downloader

**File**: `src/downloaders/epa_aqs_downloader.py`

**API Endpoints**:
- Annual summary data: `/annualData/byCounty`
- Parameters: PM2.5 (88101), PM10 (81102), O3 (44201), NO2 (42602), SO2 (42401), CO (42101)

**Implementation**:
```python
class EPAAQSDownloader(BaseDownloader):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://aqs.epa.gov/data/api"
        self.rate_limiter = RateLimiter(5)  # 5 req/sec

    def download_variable_year(self, parameter_code, year, state_fips):
        """Download one parameter for one year for one state"""
        endpoint = f"{self.base_url}/annualData/byCounty"
        params = {
            "email": self.email,
            "key": self.api_key,
            "param": parameter_code,
            "bdate": f"{year}0101",
            "edate": f"{year}1231",
            "state": state_fips
        }
        response = self.rate_limiter.call(requests.get, endpoint, params=params)
        return response.json()

    def download_all_years(self, parameter_code):
        """Download all available years for parameter (parallelized by year)"""
        years = range(1980, 2025)  # EPA AQS coverage
        states = [f"{i:02d}" for i in range(1, 57)]  # All state FIPS

        with multiprocessing.Pool(8) as pool:
            results = pool.starmap(
                self.download_variable_year,
                [(parameter_code, year, state)
                 for year in years for state in states]
            )
        return results
```

### Module 3: Raster-to-County Aggregator

**File**: `src/processors/raster_to_county.py`

**Purpose**: Aggregate high-resolution rasters (NLCD 30m, ERA5 31km) to county-level means

**Implementation**:
```python
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from rasterstats import zonal_stats

class RasterToCountyAggregator:
    def __init__(self, county_boundaries_path):
        self.counties = gpd.read_file(county_boundaries_path)

    def aggregate_raster(self, raster_path, statistic='mean'):
        """
        Aggregate raster to county level using zonal statistics

        Args:
            raster_path: Path to GeoTIFF file
            statistic: 'mean', 'sum', 'max', 'min', 'median'

        Returns:
            DataFrame with FIPS and aggregated values
        """
        stats = zonal_stats(
            self.counties,
            raster_path,
            stats=[statistic],
            geojson_out=False,
            all_touched=False  # Only include pixels with center in polygon
        )

        df = pd.DataFrame(stats)
        df['FIPS'] = self.counties['GEOID']
        return df[['FIPS', statistic]]
```

**Application**: Used for NLCD land cover, ERA5 climate, PRISM temperature, etc.

### Module 4: Facility-to-County Aggregator

**File**: `src/processors/point_to_county.py`

**Purpose**: Aggregate facility-level data (TRI, Superfund) to county summaries

**Implementation**:
```python
import geopandas as gpd
from shapely.geometry import Point

class FacilityToCountyAggregator:
    def __init__(self, county_boundaries_path):
        self.counties = gpd.read_file(county_boundaries_path)

    def aggregate_facilities(self, facility_df, value_column):
        """
        Aggregate facility-level data to county level

        Args:
            facility_df: DataFrame with 'latitude', 'longitude', value_column
            value_column: Column to aggregate (e.g., 'total_releases')

        Returns:
            DataFrame with FIPS and aggregated values
        """
        # Create GeoDataFrame from facility coordinates
        geometry = [Point(xy) for xy in zip(facility_df.longitude,
                                             facility_df.latitude)]
        facilities_gdf = gpd.GeoDataFrame(facility_df,
                                          geometry=geometry,
                                          crs='EPSG:4326')

        # Spatial join facilities to counties
        joined = gpd.sjoin(facilities_gdf, self.counties,
                          how='left', predicate='within')

        # Aggregate by county
        county_summary = joined.groupby('GEOID').agg({
            value_column: 'sum',
            'facility_id': 'count'  # Number of facilities
        }).reset_index()

        county_summary.columns = ['FIPS', 'total_value', 'facility_count']
        return county_summary
```

---

## 📊 PROGRESS TRACKING

### `progress/download_progress.json`
```json
{
  "last_updated": "2025-11-21T14:30:00Z",
  "sources": {
    "nhgis": {
      "status": "completed",
      "variables": {
        "total_population": {
          "completed_years": [1990, 2000, 2010, 2020],
          "failed_years": [],
          "pending_years": []
        }
      }
    },
    "epa_aqs": {
      "status": "in_progress",
      "variables": {
        "PM25_annual": {
          "completed_years": [2020, 2021, 2022],
          "failed_years": [2023],
          "pending_years": [2024]
        }
      }
    }
  }
}
```

### Recovery Strategy

**If script interrupted**:
1. Load `progress/download_progress.json`
2. Resume from first incomplete variable
3. Skip already-completed years
4. Retry failed years with backoff

**If cache corrupted**:
1. `cache_manager.validate_cache_integrity()` detects corruption
2. Delete corrupted file
3. Re-download from source
4. Validate new download

---

## 🧪 TESTING STRATEGY

### Unit Tests
- Test each downloader module independently
- Mock API responses for deterministic testing
- Test cache manager with temporary directories
- Test TSV generator with sample data
- Test map generator with minimal dataset

### Integration Tests
- End-to-end test with one small source (e.g., radon zones)
- Verify: download → cache → process → TSV → map
- Validate output format matches specification

### Validation Tests
- Load random sample of TSV files
- Verify FIPS codes are valid
- Check for data anomalies (negative values where impossible)
- Verify maps render correctly

---

## 📈 ESTIMATED TIMELINE

**Phase 1: Core Framework (Week 1-2)**
- Setup environment and directories: 2 hours
- Implement core modules (base_downloader, cache_manager, logger): 8 hours
- Implement metadata manager (FIPS codes, boundaries): 4 hours
- Implement TSV generator: 4 hours
- Implement map generator: 6 hours
- Testing core modules: 6 hours
**Subtotal: 30 hours**

**Phase 2: NHGIS Implementation (Week 3)**
- NHGIS downloader (semi-automated): 8 hours
- NHGIS processor: 6 hours
- Testing with sample extract: 4 hours
- Process full NHGIS dataset: 8 hours (mostly automated)
**Subtotal: 26 hours**

**Phase 3: API-Based Sources (Week 4-6)**
- EPA AQS downloader: 6 hours
- CDC WONDER downloader: 6 hours
- Census API downloader: 6 hours
- USGS NWIS downloader: 6 hours
- Testing and validation: 6 hours
**Subtotal: 30 hours**

**Phase 4: Raster Sources (Week 7-9)**
- Raster downloader (NLCD, ERA5): 8 hours
- Raster-to-county processor: 8 hours
- NetCDF handler (ERA5): 6 hours
- Testing with sample rasters: 4 hours
- Process major raster datasets: 12 hours
**Subtotal: 38 hours**

**Phase 5: Remaining Sources (Week 10-14)**
- Facility-level downloaders (TRI, Superfund): 8 hours
- Bulk CSV downloaders: 8 hours
- Process all remaining sources: 40 hours (automated, monitoring)
**Subtotal: 56 hours**

**Phase 6: Validation and Documentation (Week 15-16)**
- Comprehensive validation: 8 hours
- Generate coverage report: 4 hours
- Documentation: 8 hours
- Bug fixes and refinement: 12 hours
**Subtotal: 32 hours**

**Total Estimated Development Time: ~210 hours (5-6 weeks of full-time work)**

**Note**: Actual download and processing time for all 43,000 variables will be much longer (weeks to months of automated runtime), but human intervention required only during initial setup and monitoring.

---

## 🚨 RISK MITIGATION

### Risk 1: API Rate Limits
**Mitigation**:
- Implement rate limiter with configurable delays
- Cache all downloads
- Retry with exponential backoff
- Process during off-peak hours if limits strict

### Risk 2: Large File Downloads (ERA5 NetCDF)
**Mitigation**:
- Download one year at a time
- Verify checksums before processing
- Implement resume capability for partial downloads
- Monitor disk space (1.9TB available)

### Risk 3: GIS Processing Memory Issues
**Mitigation**:
- Process rasters in chunks (windowed reading)
- Use Dask for out-of-core processing if needed
- Free memory after each variable
- Monitor memory usage

### Risk 4: Source API/Format Changes
**Mitigation**:
- Version all downloader modules
- Log API response schemas
- Implement data validation after download
- Alert on unexpected formats

### Risk 5: Missing or Incomplete Data
**Mitigation**:
- Log all missing data cases
- Generate completeness report by source
- Don't fail entire pipeline for one variable
- Create "data availability" metadata file

---

## 📝 SUCCESS CRITERIA

1. ✅ All 200+ data sources successfully queried
2. ✅ All 43,000+ variables documented in registry
3. ✅ TSV files created for every variable × year combination (where data exists)
4. ✅ Every TSV file includes: FIPS, State_FIPS, County_FIPS, State_Name, County_Name, Year, Value, Unit
5. ✅ Every TSV file has corresponding map showing county-level choropleth
6. ✅ All original data cached locally for future updates
7. ✅ Progress tracking enables resume from any interruption
8. ✅ Comprehensive logs enable troubleshooting
9. ✅ System can detect and download new years automatically
10. ✅ Data coverage report shows completeness by category

---

## 🎯 NEXT STEPS

Following Context-Preserving Framework v4.7.1, I will proceed with implementation in bite-sized, testable increments:

### Immediate Next Steps (Today)

1. **Initialize project structure** (30 min)
   - Create all directories
   - Create `requirements.txt`
   - Create `.gitignore`

2. **Implement `scripts/00_setup_environment.py`** (1 hour)
   - Verify Python version
   - Install dependencies
   - Initialize directories and progress files

3. **Implement `scripts/01_download_metadata.py`** (2 hours)
   - Download FIPS codes
   - Download county boundaries
   - Create master FIPS lookup
   - Validate 3,143 counties

4. **Implement `src/core/metadata_manager.py`** (1.5 hours)
   - FIPS loading
   - Boundary loading
   - Validation functions

5. **Test metadata components** (1 hour)
   - Unit tests for metadata_manager
   - Verify FIPS codes correct
   - Verify boundaries load properly

**End of Day 1**: Metadata infrastructure complete and tested

### Day 2: Core Framework

6. Implement `src/core/logger.py`
7. Implement `src/core/cache_manager.py`
8. Implement `src/core/progress_tracker.py`
9. Test core framework modules

### Day 3-4: TSV and Map Generation

10. Implement `src/core/tsv_generator.py`
11. Implement `src/core/map_generator.py`
12. Create sample data and test end-to-end

### Day 5-7: NHGIS Implementation

13. Implement `src/downloaders/nhgis_downloader.py`
14. Test with one NHGIS extract
15. Process full NHGIS dataset

**By end of Week 1**: NHGIS (10,000+ variables) fully processed with TSVs and maps

---

## 📄 DELIVERABLES

At project completion, you will have:

1. **Data Files**:
   - ~43,000+ TSV files (one per variable per year)
   - ~43,000+ PNG maps (one per TSV)
   - Master FIPS metadata file
   - County boundaries shapefile

2. **Code**:
   - Modular Python codebase (~20,000 lines)
   - 200+ unit tests
   - Comprehensive documentation

3. **Configuration**:
   - Complete source registry JSON
   - Variable catalog JSON
   - Processing configuration YAML

4. **Documentation**:
   - Architecture guide
   - Data source reference
   - API documentation
   - Troubleshooting guide
   - Data coverage report (HTML)

5. **Logs**:
   - Complete download history
   - Error logs for manual review
   - Progress tracking for resumability

---

**Ready to proceed with autonomous implementation starting with Phase 1: Core Framework.**

**Awaiting confirmation to begin or any adjustments to the plan.**
