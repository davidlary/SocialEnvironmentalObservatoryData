"""
Global constants for the Observatory Data Download System.

This module centralizes all constants to ensure consistency and easy maintenance.
"""

from pathlib import Path
from typing import Final

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Root directory (project root)
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.parent.resolve()

# Configuration directories
CONFIG_DIR: Final[Path] = PROJECT_ROOT / "config"
SOURCES_REGISTRY_PATH: Final[Path] = CONFIG_DIR / "sources_registry.json"
PRIORITY_ORDER_PATH: Final[Path] = CONFIG_DIR / "priority_order.json"
PROCESSING_CONFIG_PATH: Final[Path] = CONFIG_DIR / "processing_config.yaml"
API_CREDENTIALS_PATH: Final[Path] = CONFIG_DIR / "api_credentials.json"

# Data directories
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
CACHE_DIR: Final[Path] = DATA_DIR / "cache"
PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
METADATA_DIR: Final[Path] = DATA_DIR / "metadata"

# Logging directories
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
DOWNLOAD_LOGS_DIR: Final[Path] = LOGS_DIR / "downloads"
PROCESSING_LOGS_DIR: Final[Path] = LOGS_DIR / "processing"

# Progress tracking
PROGRESS_DIR: Final[Path] = PROJECT_ROOT / "progress"
DOWNLOAD_PROGRESS_PATH: Final[Path] = PROGRESS_DIR / "download_progress.json"
PROCESSING_PROGRESS_PATH: Final[Path] = PROGRESS_DIR / "processing_progress.json"
MAP_PROGRESS_PATH: Final[Path] = PROGRESS_DIR / "map_progress.json"

# Reference data list repository
DATA_LIST_REPO: Final[Path] = (
    PROJECT_ROOT.parent / "SocialEnvironmentalObservatoryDataList"
)

# ============================================================================
# GEOGRAPHIC CONSTANTS
# ============================================================================

# US County Information
TOTAL_US_COUNTIES: Final[int] = 3143
US_STATE_FIPS_RANGE: Final[tuple[int, int]] = (1, 56)
US_TERRITORY_FIPS: Final[list[int]] = [60, 66, 69, 72, 78]

# Coordinate Reference Systems
CRS_WGS84: Final[str] = "EPSG:4326"  # Standard lat/lon
CRS_US_ALBERS: Final[str] = "EPSG:5070"  # US National Atlas Equal Area

# ============================================================================
# DATA CATEGORIES
# ============================================================================

DATA_CATEGORIES: Final[list[str]] = [
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
    "23_INTERNATIONAL_SOURCES",
]

SKIP_CATEGORIES: Final[list[str]] = ["25_PAID_RESTRICTED_DATA"]

# ============================================================================
# TSV FILE STANDARDS
# ============================================================================

# Required columns in every TSV file (in order)
TSV_REQUIRED_COLUMNS: Final[list[str]] = [
    "FIPS",
    "State_FIPS",
    "County_FIPS",
    "State_Name",
    "County_Name",
    "State_Abbrev",
    "Year",
    "Value",
    "Unit",
]

# TSV Format specifications
TSV_DELIMITER: Final[str] = "\t"
TSV_ENCODING: Final[str] = "utf-8"
TSV_NA_VALUE: Final[str] = "NA"
TSV_DATE_FORMAT: Final[str] = "%Y-%m-%d"

# ============================================================================
# MAP GENERATION STANDARDS
# ============================================================================

# Map output format
MAP_FORMAT: Final[str] = "png"
MAP_DPI: Final[int] = 300
MAP_FIGSIZE: Final[tuple[int, int]] = (12, 8)

# Colormaps by data type
COLORMAPS: Final[dict[str, str]] = {
    "sequential": "YlOrRd",  # Default for continuous positive data
    "diverging": "RdBu_r",   # For data with positive and negative
    "qualitative": "Set3",    # For categorical data
}

# Color bins
DEFAULT_QUANTILES: Final[int] = 5
MAP_MISSING_COLOR: Final[str] = "#CCCCCC"  # Gray for missing data

# ============================================================================
# API AND DOWNLOAD SETTINGS
# ============================================================================

# HTTP Request settings
DEFAULT_TIMEOUT: Final[int] = 30  # seconds
MAX_RETRIES: Final[int] = 3
BACKOFF_FACTOR: Final[float] = 2.0  # Exponential backoff multiplier

# Rate limiting (requests per second)
DEFAULT_RATE_LIMIT: Final[float] = 5.0

# Chunk sizes for large downloads
DOWNLOAD_CHUNK_SIZE: Final[int] = 8192  # 8 KB
LARGE_FILE_THRESHOLD: Final[int] = 100 * 1024 * 1024  # 100 MB

# ============================================================================
# CACHE SETTINGS
# ============================================================================

# Cache validity
DEFAULT_CACHE_TTL_DAYS: Final[int] = 365
METADATA_CACHE_TTL_DAYS: Final[int] = 90  # Metadata expires sooner

# Cache validation
VALIDATE_CHECKSUMS: Final[bool] = True

# ============================================================================
# PROCESSING SETTINGS
# ============================================================================

# Parallel processing
MAX_WORKERS: Final[int] = 8  # Leave 2 cores free for system
TIMEOUT_SECONDS: Final[int] = 3600  # 1 hour per year download

# GIS Processing
RASTER_CHUNK_SIZE: Final[int] = 1024  # Pixels per chunk for large rasters
ZONAL_STATS_DEFAULT: Final[str] = "mean"  # Default aggregation statistic

# ============================================================================
# DATA VALIDATION
# ============================================================================

# Acceptable data ranges (for validation)
REASONABLE_POPULATION_MAX: Final[int] = 10_000_000  # Max county population
REASONABLE_TEMPERATURE_RANGE: Final[tuple[int, int]] = (-100, 150)  # Fahrenheit
REASONABLE_PRECIPITATION_MAX: Final[float] = 200.0  # Inches per year

# Missing data thresholds
MAX_ACCEPTABLE_MISSING_PCT: Final[float] = 20.0  # 20% missing data is warning threshold

# ============================================================================
# LOGGING SETTINGS
# ============================================================================

# Log levels
LOG_LEVEL_DEFAULT: Final[str] = "INFO"
LOG_LEVEL_DEBUG: Final[str] = "DEBUG"

# Log file settings
LOG_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT: Final[int] = 10

# Log format
LOG_FORMAT: Final[str] = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(filename)s:%(lineno)d - %(message)s"
)

# ============================================================================
# FILE EXTENSIONS
# ============================================================================

# Data formats
EXT_TSV: Final[str] = ".tsv"
EXT_CSV: Final[str] = ".csv"
EXT_JSON: Final[str] = ".json"
EXT_YAML: Final[str] = ".yaml"
EXT_PARQUET: Final[str] = ".parquet"

# Geospatial formats
EXT_GEOTIFF: Final[str] = ".tif"
EXT_NETCDF: Final[str] = ".nc"
EXT_HDF5: Final[str] = ".h5"
EXT_SHAPEFILE: Final[str] = ".shp"
EXT_GEOPACKAGE: Final[str] = ".gpkg"

# Compressed formats
EXT_ZIP: Final[str] = ".zip"
EXT_GZIP: Final[str] = ".gz"
EXT_TAR: Final[str] = ".tar"

# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_FIPS_INVALID: Final[str] = "Invalid FIPS code: {fips}. Must be 5-digit string."
ERROR_FILE_NOT_FOUND: Final[str] = "Required file not found: {path}"
ERROR_API_FAILURE: Final[str] = "API request failed after {attempts} attempts: {error}"
ERROR_CACHE_CORRUPTED: Final[str] = "Cache file corrupted: {path}. Re-downloading."
ERROR_MISSING_METADATA: Final[str] = "Missing required metadata: {field}"

# ============================================================================
# SUCCESS MESSAGES
# ============================================================================

SUCCESS_DOWNLOAD: Final[str] = "Successfully downloaded: {source} - {variable} - {year}"
SUCCESS_PROCESS: Final[str] = "Successfully processed: {variable} - {year}"
SUCCESS_MAP: Final[str] = "Successfully created map: {variable} - {year}"

# ============================================================================
# EXTERNAL URLS
# ============================================================================

# Census Bureau
URL_CENSUS_FIPS: Final[str] = (
    "https://www2.census.gov/geo/docs/reference/codes/files/national_county.txt"
)
URL_TIGER_LINE_BASE: Final[str] = (
    "https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/"
)

# EPA
URL_EPA_AQS_BASE: Final[str] = "https://aqs.epa.gov/data/api/"
URL_EPA_NEI_BASE: Final[str] = "https://www.epa.gov/air-emissions-inventories/"

# CDC
URL_CDC_WONDER_BASE: Final[str] = "https://wonder.cdc.gov/controller/"

# USGS
URL_USGS_NWIS_BASE: Final[str] = "https://nwis.waterdata.usgs.gov/"

# NHGIS
URL_NHGIS_BASE: Final[str] = "https://data2.nhgis.org/"

# ============================================================================
# VERSION INFO
# ============================================================================

SYSTEM_VERSION: Final[str] = "1.0.0"
SYSTEM_NAME: Final[str] = "US County-Level Observatory Data Download System"
CREATED_DATE: Final[str] = "2025-11-21"
