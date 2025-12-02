"""
EPA Chemical Speciation Network (CSN) Downloader.

Downloads PM2.5 chemical composition data from pre-generated EPA AQS files:
- PM2.5 Mass (gravimetric)
- Elemental Carbon (EC)
- Organic Carbon (OC)
- Sulfate (SO4)
- Nitrate (NO3)
- Ammonium (NH4)
- Chloride, Sodium, and other major ions
- 33 trace elements measured by XRF

Data Source: https://aqs.epa.gov/aqsweb/airdata/
File Format: daily_SPEC_{year}.zip (pre-generated annual CSV files)

Data Coverage:
- Geographic: ~180 urban monitoring sites (county-assigned)
- Temporal: 2000-present (25-year record)
- Frequency: Daily measurements (1-in-3 or 1-in-6 days)
- Variables: ~40 chemical species

Design Patterns:
- Template Method: Inherits from BaseDownloader
- Strategy: Bulk CSV download (no API calls)
- Cache-First: Download entire year, cache, then filter parameters
"""

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import polars as pl
from loguru import logger

from core.base_downloader import BaseDownloader
from utils.constants import CACHE_DIR
from utils.file_utils import ensure_directory


# ============================================================================
# CSN PARAMETERS
# ============================================================================

# PM2.5 chemical species with AQS parameter codes
# NOTE: These codes are from actual CSN data files (daily_SPEC_YYYY.zip)
CSN_PARAMETERS = {
    # Priority 1: Core PM2.5 components
    "pm25": {
        "code": "88401",
        "name": "PM25_Reconstructed_Mass",
        "description": "PM2.5 reconstructed mass",
        "unit": "μg/m³",
    },
    "ec": {
        "code": "88380",
        "name": "Elemental_Carbon",
        "description": "Elemental carbon CSN_Rev (black carbon)",
        "unit": "μg/m³",
    },
    "oc": {
        "code": "88320",
        "name": "Organic_Carbon",
        "description": "Organic carbon TOR method",
        "unit": "μg/m³",
    },
    "sulfate": {
        "code": "88403",
        "name": "Sulfate",
        "description": "Sulfate PM2.5 LC",
        "unit": "μg/m³",
    },
    "nitrate": {
        "code": "88306",
        "name": "Nitrate",
        "description": "Total nitrate PM2.5 LC",
        "unit": "μg/m³",
    },
    "ammonium": {
        "code": "88301",
        "name": "Ammonium",
        "description": "Ammonium ion PM2.5 LC",
        "unit": "μg/m³",
    },
    # Priority 2: Major ions
    "chloride": {
        "code": "88203",
        "name": "Chloride",
        "description": "Chloride PM2.5 LC",
        "unit": "μg/m³",
    },
    "sodium": {
        "code": "88184",
        "name": "Sodium",
        "description": "Sodium PM2.5 LC",
        "unit": "μg/m³",
    },
    "calcium": {
        "code": "88111",
        "name": "Calcium",
        "description": "Calcium PM2.5 LC",
        "unit": "μg/m³",
    },
    "magnesium": {
        "code": "88140",
        "name": "Magnesium",
        "description": "Magnesium PM2.5 LC",
        "unit": "μg/m³",
    },
    "potassium": {
        "code": "88180",
        "name": "Potassium",
        "description": "Potassium PM2.5 LC",
        "unit": "μg/m³",
    },
    # Priority 3: Trace elements (toxic metals)
    "lead": {
        "code": "88128",
        "name": "Lead",
        "description": "Lead PM2.5 LC - toxic metal",
        "unit": "μg/m³",
    },
    "arsenic": {
        "code": "88103",
        "name": "Arsenic",
        "description": "Arsenic PM2.5 LC - carcinogen",
        "unit": "μg/m³",
    },
    "chromium": {
        "code": "88112",
        "name": "Chromium",
        "description": "Chromium PM2.5 LC - potential carcinogen",
        "unit": "μg/m³",
    },
    "nickel": {
        "code": "88136",
        "name": "Nickel",
        "description": "Nickel PM2.5 LC - respiratory irritant",
        "unit": "μg/m³",
    },
    # Source tracers
    "vanadium": {
        "code": "88164",
        "name": "Vanadium",
        "description": "Vanadium PM2.5 LC - oil combustion tracer",
        "unit": "μg/m³",
    },
    "zinc": {
        "code": "88167",
        "name": "Zinc",
        "description": "Zinc PM2.5 LC - industrial emissions",
        "unit": "μg/m³",
    },
    "copper": {
        "code": "88114",
        "name": "Copper",
        "description": "Copper PM2.5 LC - brake wear tracer",
        "unit": "μg/m³",
    },
    # Crustal elements
    "iron": {
        "code": "88126",
        "name": "Iron",
        "description": "Iron PM2.5 LC - crustal element",
        "unit": "μg/m³",
    },
    "silicon": {
        "code": "88165",
        "name": "Silicon",
        "description": "Silicon PM2.5 LC - crustal element",
        "unit": "μg/m³",
    },
    "aluminum": {
        "code": "88104",
        "name": "Aluminum",
        "description": "Aluminum PM2.5 LC - crustal element",
        "unit": "μg/m³",
    },
}

# Years with available CSN data
CSN_YEARS = list(range(2000, 2025))  # 2000-2024


# ============================================================================
# CSN DOWNLOADER
# ============================================================================


class CSNDownloader(BaseDownloader):
    """
    Downloader for EPA Chemical Speciation Network data.

    Downloads PM2.5 composition data from pre-generated annual CSV files.
    Each file contains all CSN measurements for one year (~1.9 million rows).
    """

    def __init__(self):
        """
        Initialize CSN downloader.

        No API key required - uses pre-generated CSV files.
        """
        super().__init__(
            source_id="csn",
            source_name="EPA Chemical Speciation Network",
            category="01_AIR_ATMOSPHERE",
            rate_limit=1.0,  # 1 request/sec for politeness (no official limit)
        )

        # Base URL for pre-generated files
        self.base_url = "https://aqs.epa.gov/aqsweb/airdata"

        # Cache directory for this source
        self.cache_dir = CACHE_DIR / self.category / self.source_id
        ensure_directory(self.cache_dir)

        # Create subdirectories for raw files and processed data
        self.raw_dir = self.cache_dir / "raw"
        self.processed_dir = self.cache_dir / "processed"
        ensure_directory(self.raw_dir)
        ensure_directory(self.processed_dir)

        logger.info(f"CSN downloader initialized (cache={self.cache_dir})")

    # ========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS
    # ========================================================================

    def get_available_years(self, variable: str) -> List[int]:
        """
        Get available years for a variable.

        Args:
            variable: Parameter name (e.g., "pm25", "ec", "oc")

        Returns:
            List of years with data (2000-2024)

        Raises:
            ValueError: If variable is unknown
        """
        if variable not in CSN_PARAMETERS:
            raise ValueError(
                f"Unknown parameter: {variable}. "
                f"Available: {list(CSN_PARAMETERS.keys())}"
            )

        return CSN_YEARS

    def download_variable_year(
        self,
        variable: str,
        year: int,
        force_refresh: bool = False,
    ) -> Optional[Path]:
        """
        Download data for one variable and year.

        Strategy:
        1. Download full daily_SPEC_{year}.zip if not cached
        2. Extract CSV from ZIP
        3. Filter to requested parameter code
        4. Aggregate to county level (mean by county-year)
        5. Cache processed data

        Args:
            variable: Parameter name (e.g., "pm25")
            year: Year to download (2000-2024)
            force_refresh: Force re-download even if cached

        Returns:
            Path to cached CSV file (county-aggregated)

        Raises:
            ValueError: If variable or year is invalid
            RuntimeError: If download fails
        """
        # Validate inputs
        if variable not in CSN_PARAMETERS:
            raise ValueError(f"Unknown parameter: {variable}")

        if year not in CSN_YEARS:
            raise ValueError(f"Year {year} not in valid range: {CSN_YEARS[0]}-{CSN_YEARS[-1]}")

        # Check if processed file exists
        processed_file = self.processed_dir / f"{variable}_{year}.csv"
        if processed_file.exists() and not force_refresh:
            logger.debug(f"Using cached file: {processed_file}")
            return processed_file

        # Download raw SPEC file if needed
        try:
            raw_csv = self._download_spec_file(year, force_refresh)
        except Exception as e:
            logger.error(f"Failed to download SPEC file for {year}: {e}")
            return None

        # Process: filter parameter and aggregate to counties
        try:
            parameter_code = CSN_PARAMETERS[variable]["code"]
            processed_data = self._process_spec_file(raw_csv, parameter_code, variable, year)

            if processed_data is None or processed_data.height == 0:
                logger.warning(f"No data found for {variable} in {year}")
                return None

            # Save processed data
            processed_data.write_csv(processed_file)
            logger.info(f"✅ Cached {variable}/{year}: {processed_data.height} counties")

            return processed_file

        except Exception as e:
            logger.error(f"Failed to process {variable}/{year}: {e}")
            return None

    def get_metadata(self, variable: str) -> Dict[str, str]:
        """
        Get metadata for a variable.

        Args:
            variable: Parameter name (e.g., "pm25")

        Returns:
            Dictionary with metadata (unit, description, source_url)

        Raises:
            ValueError: If variable is unknown
        """
        if variable not in CSN_PARAMETERS:
            raise ValueError(f"Unknown parameter: {variable}")

        param_info = CSN_PARAMETERS[variable]

        return {
            "variable": variable,
            "parameter_code": param_info["code"],
            "name": param_info["name"],
            "description": param_info["description"],
            "unit": param_info["unit"],
            "source_url": f"{self.base_url}/download_files.html",
            "years": f"{CSN_YEARS[0]}-{CSN_YEARS[-1]}",
            "network": "Chemical Speciation Network (CSN)",
            "method": "Monitor-based measurements (urban sites)",
        }

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _download_spec_file(self, year: int, force_refresh: bool = False) -> Path:
        """
        Download raw daily_SPEC_{year}.zip file from EPA.

        Args:
            year: Year to download
            force_refresh: Force re-download

        Returns:
            Path to extracted CSV file

        Raises:
            RuntimeError: If download or extraction fails
        """
        # Check if CSV already extracted
        csv_file = self.raw_dir / f"daily_SPEC_{year}.csv"
        if csv_file.exists() and not force_refresh:
            logger.debug(f"Using cached raw file: {csv_file}")
            return csv_file

        # Download ZIP
        zip_file = self.raw_dir / f"daily_SPEC_{year}.zip"
        url = f"{self.base_url}/daily_SPEC_{year}.zip"

        logger.info(f"Downloading {url}...")

        try:
            # Use http_client from BaseDownloader (has retry logic)
            response = self.http_client.get(url)

            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to download {url}: HTTP {response.status_code}"
                )

            # Save ZIP
            with open(zip_file, "wb") as f:
                f.write(response.content)

            file_size_mb = zip_file.stat().st_size / 1024 / 1024
            logger.info(f"Downloaded {zip_file.name} ({file_size_mb:.1f} MB)")

        except Exception as e:
            raise RuntimeError(f"Failed to download {url}: {e}")

        # Extract CSV from ZIP
        try:
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                # ZIP should contain one CSV file: daily_SPEC_{year}.csv
                csv_name = f"daily_SPEC_{year}.csv"
                zip_ref.extract(csv_name, self.raw_dir)

            logger.info(f"Extracted {csv_name}")

            # Clean up ZIP file to save space
            zip_file.unlink()
            logger.debug(f"Removed {zip_file.name}")

            return csv_file

        except Exception as e:
            raise RuntimeError(f"Failed to extract {zip_file}: {e}")

    def _process_spec_file(
        self, csv_file: Path, parameter_code: str, variable: str, year: int
    ) -> Optional[pl.DataFrame]:
        """
        Process raw SPEC CSV file: filter parameter and aggregate to counties.

        Args:
            csv_file: Path to raw CSV file
            parameter_code: AQS parameter code to filter
            variable: Variable name (for logging)
            year: Year (for logging)

        Returns:
            Polars DataFrame with county-aggregated data

        Schema of output:
            FIPS (str): 5-digit county FIPS code
            State_FIPS (str): 2-digit state FIPS
            County_FIPS (str): 3-digit county FIPS
            State_Name (str): State name
            County_Name (str): County name
            Year (int): Year
            Value (float): Mean concentration
            Unit (str): Unit of measurement
            N_Sites (int): Number of sites in county
            N_Samples (int): Number of samples
        """
        logger.info(f"Processing {csv_file.name} for parameter {parameter_code}...")

        try:
            # Read CSV with Polars (fast)
            df = pl.read_csv(csv_file)

            logger.debug(f"Loaded {df.height:,} rows from {csv_file.name}")

            # Filter to requested parameter
            df_param = df.filter(pl.col("Parameter Code") == int(parameter_code))

            if df_param.height == 0:
                logger.warning(f"No data for parameter {parameter_code} in {year}")
                return None

            logger.debug(f"Filtered to {df_param.height:,} rows for parameter {parameter_code}")

            # Construct 5-digit FIPS code
            df_param = df_param.with_columns(
                FIPS=(
                    pl.col("State Code").cast(pl.Utf8).str.zfill(2) +
                    pl.col("County Code").cast(pl.Utf8).str.zfill(3)
                )
            )

            # Aggregate to county level (mean concentration)
            df_county = (
                df_param
                .group_by("FIPS", "State Code", "County Code", "State Name", "County Name")
                .agg([
                    pl.col("Arithmetic Mean").mean().alias("Value"),
                    pl.col("Units of Measure").first().alias("Unit"),
                    pl.col("Site Num").n_unique().alias("N_Sites"),
                    pl.col("Arithmetic Mean").count().alias("N_Samples"),
                ])
                .with_columns([
                    pl.col("State Code").cast(pl.Utf8).str.zfill(2).alias("State_FIPS"),
                    pl.col("County Code").cast(pl.Utf8).str.zfill(3).alias("County_FIPS"),
                    pl.col("State Name").alias("State_Name"),
                    pl.col("County Name").alias("County_Name"),
                    pl.lit(year).alias("Year"),
                ])
                .select([
                    "FIPS",
                    "State_FIPS",
                    "County_FIPS",
                    "State_Name",
                    "County_Name",
                    "Year",
                    "Value",
                    "Unit",
                    "N_Sites",
                    "N_Samples",
                ])
                .sort("FIPS")
            )

            logger.info(
                f"✅ Aggregated to {df_county.height} counties "
                f"({df_county['N_Samples'].sum()} samples total)"
            )

            return df_county

        except Exception as e:
            logger.error(f"Failed to process {csv_file}: {e}")
            return None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ["CSNDownloader", "CSN_PARAMETERS"]
