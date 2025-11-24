# US County-Level Observatory Data Download System
## Automated Download, Processing, and Visualization System

**Version:** 1.0.0
**Created:** 2025-11-21
**Architecture:** Python/R/Polars Hybrid
**Compliance:** Context-Preserving Framework v4.7.1

---

## 🎯 Project Overview

This system **automatically downloads, processes, and visualizes** county-level data from 200+ authoritative sources, creating:

- **43,000+ variables** covering environmental, health, demographic, and socioeconomic data
- **3,143 US counties** (complete coverage including territories)
- **Temporal range:** 1940-Present (varies by source)
- **Standardized TSV files** with FIPS metadata for every variable×year
- **Choropleth maps** visualizing spatial distribution for every TSV file

### Key Features

✅ **Fully Automated:** One command downloads, processes, and maps data
✅ **Intelligent Caching:** Downloads once, reuses efficiently
✅ **Resumable:** Interrupt anytime, resume exactly where you left off
✅ **Parallel Processing:** Utilizes all CPU cores for speed
✅ **Error Recovery:** Robust retry logic with exponential backoff
✅ **Progress Tracking:** Always know what's completed and what's pending
✅ **Standardized Output:** Every TSV file has identical structure with FIPS metadata
✅ **Publication-Quality Maps:** Beautiful choropleth visualizations

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
python scripts/00_setup_environment.py
```

This will:
- Check Python version (>=3.9 required)
- Install all dependencies from `requirements.txt`
- Create directory structure
- Initialize progress tracking

### 2. Download Essential Metadata

```bash
# Download FIPS codes and county boundaries
python scripts/01_download_metadata.py
```

This downloads:
- Official Census FIPS codes (3,234 counties including territories)
- TIGER/Line county boundaries (2020 vintage, 127 MB)
- Validates metadata completeness

### 3. Configure API Credentials (**REQUIRED for EPA AQS**)

**EPA AQS data requires API credentials.** Sign up (free, takes 2 minutes):

1. **Get EPA AQS API Key**: https://aqs.epa.gov/data/api/signup
   - Enter your email address
   - You'll receive an API key immediately by email
   - You need BOTH the API key AND your email address

2. **Set environment variables** (recommended):
```bash
export EPA_AQS_API_KEY="your_key_from_email"
export EPA_AQS_EMAIL="your.email@example.com"
```

OR **use config file**:
```bash
# Copy credentials template
cp config/api_credentials_template.json config/api_credentials.json

# Edit config/api_credentials.json and add your keys
# This file is gitignored and will never be committed
```

**IPUMS NHGIS API Key** (required for IPUMS NHGIS data):

1. **Get IPUMS API Key**: https://account.ipums.org/api_keys
   - Log in with your IPUMS account (or create one - free)
   - Request an API key
   - You need BOTH the API key AND your email address

2. **Set environment variables** (recommended):
```bash
export IPUMS_NHGIS_API_KEY="your_key_here"
export IPUMS_NHGIS_EMAIL="your.email@example.com"
```

OR **use config file**: Add to `config/api_credentials.json`

**Other data sources** (optional, for future use):
- **Census Bureau**: https://api.census.gov/data/key_signup.html
- **NASA Earthdata**: https://urs.earthdata.nasa.gov/users/new

### 4. Start Downloading Data

```bash
# Download EPA Air Quality data (all pollutants, all years)
python scripts/03_download_source.py --source epa_aqs

# Download specific parameter and years
python scripts/03_download_source.py --source epa_aqs --variable PM25 --years 2020 2021 2022

# Force re-download (ignore cache)
python scripts/03_download_source.py --source epa_aqs --force-refresh
```

**Available sources:**
- `epa_aqs` - EPA Air Quality System (PM2.5, PM10, O3, NO2, SO2, CO) - **IMPLEMENTED**
- `ipums_nhgis` - IPUMS NHGIS Census/Demographic Data (266 datasets, 1790-2023) - **IMPLEMENTED**
- More sources coming soon...

### 5. Process Data to TSV Format

```bash
# Process cached downloads to county-level TSV files
python scripts/04_process_cached_data.py
```

### 6. Generate Maps

```bash
# Generate choropleth maps for all TSV files
python scripts/05_generate_maps.py --all
```

---

## 📁 Directory Structure

```
SocialEnvironmentalObservatoryData/
│
├── config/                          # Configuration files
│   ├── sources_registry.json       # All 200+ sources (auto-generated)
│   └── processing_config.yaml      # Runtime configuration
│
├── src/                             # Source code
│   ├── core/                        # Core framework (10 modules)
│   │   ├── logger.py               # Comprehensive logging
│   │   ├── metadata_manager.py     # FIPS codes, boundaries
│   │   ├── cache_manager.py        # Intelligent caching
│   │   ├── progress_tracker.py     # Resumability
│   │   ├── retry_handler.py        # Robust downloads
│   │   ├── tsv_generator.py        # TSV creation
│   │   ├── map_generator.py        # Choropleth maps
│   │   └── base_downloader.py      # Downloader base class
│   │
│   ├── downloaders/                 # Source-specific downloaders
│   │   ├── python/                  # Python-based downloaders
│   │   │   ├── epa_aqs_downloader.py
│   │   │   ├── cdc_wonder_downloader.py
│   │   │   └── ...
│   │   └── r/                       # R-based downloaders
│   │       ├── nhgis_downloader.R   # IPUMS NHGIS (ipumsr)
│   │       ├── nass_downloader.R    # USDA NASS (rnassqs)
│   │       └── ...
│   │
│   ├── processors/                  # Data processors
│   │   ├── county_aggregator.py    # Aggregate to county level
│   │   ├── raster_to_county.py     # Zonal statistics
│   │   └── point_to_county.py      # Spatial joins
│   │
│   └── utils/                       # Utilities
│       ├── constants.py             # Global constants
│       ├── file_utils.py            # Polars-based I/O
│       └── geo_utils.py             # GIS operations
│
├── scripts/                         # Executable scripts
│   ├── 00_setup_environment.py     # One-time setup
│   ├── 01_download_metadata.py     # Download FIPS/boundaries
│   ├── 02_build_source_registry.py # Parse data list docs
│   ├── 03_download_source.py       # Main downloader
│   ├── 04_process_cached_data.py   # Cache → TSV
│   ├── 05_generate_maps.py         # TSV → PNG maps
│   └── 07_update_data.py           # Check for new years
│
├── data/
│   ├── cache/                       # Original downloaded files
│   │   ├── 00_METADATA/
│   │   ├── 01_AIR_ATMOSPHERE/
│   │   └── ...
│   │
│   ├── processed/                   # Final TSV + map files
│   │   ├── 01_AIR_ATMOSPHERE/
│   │   │   └── PM25_Annual_Mean/
│   │   │       ├── 2020_PM25_Annual_Mean.tsv
│   │   │       ├── 2020_PM25_Annual_Mean.png
│   │   │       └── ...
│   │   └── ...
│   │
│   └── metadata/                    # FIPS codes, boundaries
│       ├── fips_codes_master.tsv
│       └── county_boundaries_2020.gpkg
│
├── logs/                            # Comprehensive logs
│   ├── main.log                     # Main log (rotating)
│   ├── errors.log                   # Errors only
│   └── downloads/                   # Per-source logs
│
├── progress/                        # Progress tracking (resumability)
│   ├── download_progress.json
│   ├── processing_progress.json
│   └── map_progress.json
│
├── requirements.txt                 # Python dependencies
├── IMPLEMENTATION_PLAN.md           # Detailed implementation plan
└── README.md                        # This file
```

---

## 📊 Output Format

### TSV Files

Every TSV file has **identical structure** with required columns:

| Column | Type | Description |
|--------|------|-------------|
| FIPS | string | 5-digit FIPS code (zero-padded) |
| State_FIPS | string | 2-digit state code |
| County_FIPS | string | 3-digit county code |
| State_Name | string | Full state name |
| County_Name | string | Full county name |
| State_Abbrev | string | 2-letter state abbreviation |
| Year | integer | Year |
| Value | float | Measured value |
| Unit | string | Unit of measurement |

**Example:**
```
FIPS	State_FIPS	County_FIPS	State_Name	County_Name	State_Abbrev	Year	Value	Unit
48453	48	453	Texas	Travis County	TX	2020	8.5	μg/m³
06037	06	037	California	Los Angeles County	CA	2020	12.3	μg/m³
```

### Map Files

- **Format:** PNG (300 DPI)
- **Projection:** US Albers Equal Area
- **Colors:** Quantile-based classification (5 bins)
- **Includes:** Title, legend, colorbar, statistics box
- **Missing data:** Gray color for counties without data

---

## 🔧 Technology Stack

### Core Technologies

- **Python 3.9+**: Main language
- **R 4.0+**: For sources with excellent R packages (NHGIS, NASS)
- **Polars**: Rust-based DataFrames (10-100x faster than pandas)
- **Geopandas**: Geospatial operations
- **Matplotlib**: Mapping and visualization

### Key Libraries

```
# Data Processing
polars>=0.19.0          # Blazing fast DataFrames
pandas>=2.1.0           # Compatibility with geospatial libs
numpy>=1.24.0
xarray>=2023.1.0        # NetCDF/HDF5 (ERA5 climate data)
pyarrow>=14.0.0         # Arrow format

# GIS and Spatial
geopandas>=0.14.0       # Geospatial DataFrames
rasterio>=1.3.9         # Raster I/O
shapely>=2.0.2          # Geometric operations
rasterstats>=0.19.0     # Zonal statistics

# HTTP and APIs
requests>=2.31.0        # HTTP requests
aiohttp>=3.9.0          # Async HTTP
tenacity>=8.2.3         # Retry logic

# Logging
loguru                  # Beautiful, structured logs
```

---

## 🗺️ Data Sources

The system downloads from **200+ authoritative sources** documented in the companion repository:

**[SocialEnvironmentalObservatoryDataList](../SocialEnvironmentalObservatoryDataList/)**

### Priority Sources (Implementation Order)

1. **IPUMS NHGIS** (10,000+ variables)
   - Pre-harmonized demographic, social, economic, housing data
   - 1790-2024 time series + ACS tables
   - R package: `ipumsr`

2. **EPA Air Quality System (AQS)** (~200 variables)
   - Criteria pollutants (PM2.5, O3, NO2, SO2, CO)
   - 1980-2024
   - API-based

3. **CDC WONDER Mortality** (1,000+ variables)
   - All-cause and cause-specific mortality
   - 1999-present
   - API-based

4. **USGS Water Quality (NWIS)** (1,300+ parameters)
   - Surface and groundwater quality
   - 1901-present
   - API-based

5. **ERA5 Climate Reanalysis** (240 variables)
   - Highest-resolution global climate data
   - 1940-present, hourly
   - NetCDF format

*And 195+ more sources...*

---

## 🔄 Workflow

### Download Workflow

```
1. Check progress tracker
   ↓
2. Get list of pending years
   ↓
3. For each pending year:
   a. Check cache (skip if valid)
   b. Download from source
   c. Save to cache
   d. Mark as downloaded
   ↓
4. Update progress tracker
```

### Processing Workflow

```
1. Scan cache for downloaded files
   ↓
2. For each cached file:
   a. Load data
   b. Aggregate to county level (if needed)
   c. Join with FIPS metadata
   d. Generate TSV file
   e. Mark as processed
   ↓
3. Update progress tracker
```

### Mapping Workflow

```
1. Scan processed dir for TSV files
   ↓
2. For each TSV without map:
   a. Load TSV data
   b. Merge with county boundaries
   c. Create choropleth map
   d. Save PNG
   e. Mark as mapped
   ↓
3. Update progress tracker
```

---

## 🚨 Error Recovery

The system is designed for **seamless recovery** after any interruption:

### Progress Tracking

All progress stored in JSON files:
- `progress/download_progress.json` - Downloaded variable/year combinations
- `progress/processing_progress.json` - Processed TSV files
- `progress/map_progress.json` - Created maps

### Resuming After Interruption

Simply **rerun the same command**:

```bash
# If download was interrupted
python scripts/03_download_source.py --source epa_aqs

# System automatically:
# 1. Loads progress from progress/download_progress.json
# 2. Skips completed years
# 3. Continues from where it left off
```

### Cache Validation

Cached files are validated before use:
- File exists and size > 0
- SHA-256 checksum (optional)
- Age check (re-download if expired)

### Retry Logic

All downloads use **exponential backoff**:
- 1st attempt: immediate
- 2nd attempt: 2 seconds
- 3rd attempt: 4 seconds
- 4th attempt: 8 seconds
- Max: 60 seconds between attempts

---

## 📈 Performance

### Parallel Processing

- **Downloads:** Sequential over variables, parallel over years (8 workers)
- **Processing:** Parallel over files (8 workers)
- **Mapping:** Parallel over maps (8 workers)

### Speed Optimizations

- **Polars DataFrames:** 10-100x faster than pandas
- **Caching:** Download once, reuse forever
- **Lazy evaluation:** Load only what's needed
- **Async HTTP:** Multiple concurrent downloads

### Resource Usage

- **CPU:** 8/10 cores used (leave 2 for system)
- **RAM:** ~4-8 GB typical, up to 16 GB for large rasters
- **Disk:** ~1-5 TB estimated for complete dataset
- **Network:** Depends on source rate limits

---

## 🧪 Testing

### Validate Installation

```bash
# Run setup script (includes validation)
python scripts/00_setup_environment.py
```

### Test with Small Dataset

```bash
# Download just one variable for one year
python scripts/03_download_source.py --source epa_aqs --variable PM25_Annual --years 2020

# Process to TSV
python scripts/04_process_cached_data.py

# Generate map
python scripts/05_generate_maps.py --category 01_AIR_ATMOSPHERE
```

---

## 📝 Logging

### Log Files

- `logs/main.log` - All operations (rotating, 10MB max, 10 backups)
- `logs/errors.log` - Errors only
- `logs/downloads/{source}_{timestamp}.log` - Per-source logs

### Log Levels

```bash
# Debug logging
python scripts/03_download_source.py --log-level DEBUG

# Info logging (default)
python scripts/03_download_source.py --log-level INFO

# Warnings only
python scripts/03_download_source.py --log-level WARNING
```

### Log Format

```
2025-11-21 14:30:15 - INFO - downloader.py:45 - Downloading PM25 for 2020
2025-11-21 14:30:18 - INFO - cache_manager.py:78 - Cached: 2020_data.csv (2.5 MB)
2025-11-21 14:30:20 - INFO - tsv_generator.py:102 - Created TSV: 2020_PM25_Annual.tsv
```

---

## 🤝 Contributing

### Adding a New Data Source

1. **Create downloader class**:
   ```python
   # src/downloaders/python/my_source_downloader.py
   from src.core.base_downloader import BaseDownloader

   class MySourceDownloader(BaseDownloader):
       def get_available_years(self, variable):
           return list(range(2000, 2025))

       def download_variable_year(self, variable, year, force_refresh=False):
           # Download logic here
           return cached_file_path

       def get_metadata(self, variable):
           return {"unit": "...", "description": "..."}
   ```

2. **Add to source registry**:
   Edit `config/sources_registry.json`

3. **Test**:
   ```bash
   python scripts/03_download_source.py --source my_source
   ```

---

## 📚 Documentation

- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Detailed implementation plan
- **[SocialEnvironmentalObservatoryDataList/](../SocialEnvironmentalObservatoryDataList/)** - Data source documentation
- **[src/](src/)** - Well-documented code with docstrings

---

## 🙏 Acknowledgments

### Data Sources

This system aggregates data from 200+ authoritative sources including:
- US Census Bureau
- EPA (Environmental Protection Agency)
- CDC (Centers for Disease Control)
- USGS (US Geological Survey)
- NOAA (National Oceanic and Atmospheric Administration)
- ECMWF (European Centre for Medium-Range Weather Forecasts)
- And 194+ more...

### Technologies

Built with modern, high-performance tools:
- **Polars** (Rust-based DataFrames)
- **Geopandas** (Geospatial operations)
- **Loguru** (Beautiful logging)
- **Tenacity** (Retry logic)

---

## 📄 License

[To be determined based on project requirements]

---

## 📧 Contact

[To be determined]

---

**Last Updated:** 2025-11-23
**Version:** 1.2.0
**Status:** Phase 1 Complete - EPA AQS + IPUMS NHGIS Fully Operational

**Current Implementation Status:**
- ✅ EPA AQS Downloader (6 pollutants, 1980-2024) - 243 TSVs + 243 maps (100%)
- ✅ IPUMS NHGIS Downloader (266 datasets, 1790-2023) - 58,243 TSVs + 51,464 maps (88.4%)
- ✅ Autonomous download/process/map pipeline
- ✅ Data completeness validated (see docs/DATA_COMPLETENESS_REPORT.md)
- ✅ All census variables verified with complete county coverage
- ⏳ Remaining: 6,779 IPUMS maps (11.6%) - completion in progress
- ⏳ Next priority: Add CDC WONDER, USGS NWIS, NOAA Climate data
