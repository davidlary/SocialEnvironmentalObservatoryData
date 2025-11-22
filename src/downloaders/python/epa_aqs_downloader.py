"""
EPA Air Quality System (AQS) Downloader.

Downloads criteria pollutant data from the EPA AQS API:
- PM2.5 (Fine particulate matter)
- PM10 (Coarse particulate matter)
- O3 (Ozone)
- NO2 (Nitrogen dioxide)
- SO2 (Sulfur dioxide)
- CO (Carbon monoxide)

API Documentation: https://aqs.epa.gov/aqsweb/documents/data_api.html
API Signup: https://aqs.epa.gov/data/api/signup

Data Coverage:
- Geographic: County-level (US only)
- Temporal: 1980-present (varies by parameter)
- Frequency: Annual summaries

Design Patterns:
- Template Method: Inherits from BaseDownloader
- Strategy: Different endpoints for different data types
- Rate Limiting: Respects EPA's 10 requests/second, 500/hour limits
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import polars as pl
from loguru import logger

from core.base_downloader import BaseDownloader
from utils.constants import CACHE_DIR, DATA_DIR, TSV_DELIMITER
from utils.file_utils import ensure_directory, read_json_file, write_json_file, write_tsv


# ============================================================================
# EPA AQS PARAMETERS
# ============================================================================

# Criteria pollutants with parameter codes
EPA_AQS_PARAMETERS = {
    "PM25": {
        "code": "88101",
        "name": "PM25_Annual_Mean",
        "description": "Fine particulate matter (PM2.5) annual arithmetic mean",
        "unit": "μg/m³",
        "years": list(range(1999, 2025)),  # PM2.5 monitoring started 1999
    },
    "PM10": {
        "code": "81102",
        "name": "PM10_Annual_Mean",
        "description": "Coarse particulate matter (PM10) annual arithmetic mean",
        "unit": "μg/m³",
        "years": list(range(1988, 2025)),  # PM10 monitoring started 1988
    },
    "O3": {
        "code": "44201",
        "name": "Ozone_8hr_4th_Max",
        "description": "Ozone 8-hour 4th highest daily maximum",
        "unit": "ppm",
        "years": list(range(1980, 2025)),
    },
    "NO2": {
        "code": "42602",
        "name": "NO2_Annual_Mean",
        "description": "Nitrogen dioxide annual arithmetic mean",
        "unit": "ppb",
        "years": list(range(1980, 2025)),
    },
    "SO2": {
        "code": "42401",
        "name": "SO2_Annual_Mean",
        "description": "Sulfur dioxide annual arithmetic mean",
        "unit": "ppb",
        "years": list(range(1980, 2025)),
    },
    "CO": {
        "code": "42101",
        "name": "CO_8hr_2nd_Max",
        "description": "Carbon monoxide 8-hour 2nd highest daily maximum",
        "unit": "ppm",
        "years": list(range(1980, 2025)),
    },
}

# All US state FIPS codes (including territories)
US_STATE_FIPS = [
    f"{i:02d}" for i in range(1, 57)  # 01-56
] + ["60", "66", "69", "72", "78"]  # Territories


# ============================================================================
# EPA AQS DOWNLOADER
# ============================================================================


class EPAAQSDownloader(BaseDownloader):
    """
    Downloader for EPA Air Quality System data.

    Downloads annual summary statistics for criteria pollutants
    at the county level for all US states and territories.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        email: Optional[str] = None,
    ):
        """
        Initialize EPA AQS downloader.

        Args:
            api_key: EPA AQS API key (or set EPA_AQS_API_KEY env var)
            email: Email for API requests (or set EPA_AQS_EMAIL env var)

        API Key:
            Sign up at: https://aqs.epa.gov/data/api/signup
            Or set environment variable EPA_AQS_API_KEY
        """
        super().__init__(
            source_id="epa_aqs",
            source_name="EPA Air Quality System",
            category="01_AIR_ATMOSPHERE",
            rate_limit=5.0,  # EPA allows 10/sec, use 5 to be safe
        )

        # Get API credentials
        self.api_key = api_key or os.getenv("EPA_AQS_API_KEY")
        self.email = email or os.getenv("EPA_AQS_EMAIL")

        if not self.api_key:
            logger.warning(
                "EPA_AQS_API_KEY not set. Some operations may fail. "
                "Sign up at: https://aqs.epa.gov/data/api/signup"
            )

        if not self.email:
            logger.warning(
                "EPA_AQS_EMAIL not set. API requests require an email address."
            )

        # API configuration
        self.base_url = "https://aqs.epa.gov/data/api"
        self.endpoints = {
            "annual_summary": f"{self.base_url}/annualData/byCounty",
            "monitors": f"{self.base_url}/monitors/byCounty",
        }

        # Cache directory for this source
        self.cache_dir = CACHE_DIR / self.category / self.source_id
        ensure_directory(self.cache_dir)

        logger.info(f"EPA AQS downloader initialized (cache={self.cache_dir})")

    # ========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS
    # ========================================================================

    def get_available_years(self, variable: str) -> List[int]:
        """
        Get available years for a variable.

        Args:
            variable: Parameter name (e.g., "PM25")

        Returns:
            List of years with data
        """
        if variable not in EPA_AQS_PARAMETERS:
            raise ValueError(
                f"Unknown parameter: {variable}. "
                f"Available: {list(EPA_AQS_PARAMETERS.keys())}"
            )

        return EPA_AQS_PARAMETERS[variable]["years"]

    def download_variable_year(
        self,
        variable: str,
        year: int,
        force_refresh: bool = False,
    ) -> Path:
        """
        Download data for one variable and year.

        Args:
            variable: Parameter name (e.g., "PM25")
            year: Year to download
            force_refresh: Force re-download even if cached

        Returns:
            Path to cached CSV file

        Raises:
            ValueError: If variable or year is invalid
            RuntimeError: If download fails
        """
        # Validate inputs
        if variable not in EPA_AQS_PARAMETERS:
            raise ValueError(f"Unknown parameter: {variable}")

        param_info = EPA_AQS_PARAMETERS[variable]
        if year not in param_info["years"]:
            raise ValueError(
                f"Year {year} not available for {variable}. "
                f"Available: {param_info['years'][0]}-{param_info['years'][-1]}"
            )

        # Check cache
        cache_file = self.cache_dir / f"{variable}_{year}_raw.csv"
        if cache_file.exists() and not force_refresh:
            logger.info(f"Using cached file: {cache_file}")
            return cache_file

        # Check API credentials
        if not self.api_key or not self.email:
            raise RuntimeError(
                "EPA_AQS_API_KEY and EPA_AQS_EMAIL must be set. "
                "Sign up at: https://aqs.epa.gov/data/api/signup"
            )

        logger.info(
            f"Downloading {variable} data for {year} from EPA AQS API..."
        )

        # Download data for all states
        all_data = []
        param_code = param_info["code"]

        for state_fips in US_STATE_FIPS:
            try:
                state_data = self._download_state_year(
                    param_code, year, state_fips
                )
                if state_data is not None and len(state_data) > 0:
                    all_data.append(state_data)
                    logger.debug(
                        f"Downloaded {len(state_data)} records for state {state_fips}"
                    )
            except Exception as e:
                logger.warning(
                    f"Error downloading state {state_fips} for {year}: {e}"
                )
                continue

        if not all_data:
            raise RuntimeError(
                f"No data downloaded for {variable} {year} from any state"
            )

        # Combine all state data
        df = pl.concat(all_data, how="vertical_relaxed")
        logger.info(
            f"Downloaded {len(df)} records for {variable} {year} "
            f"from {len(all_data)} states"
        )

        # Save to cache
        write_tsv(df, cache_file)
        logger.info(f"Cached to: {cache_file}")

        return cache_file

    def get_metadata(self, variable: str) -> Dict:
        """
        Get metadata for a variable.

        Args:
            variable: Parameter name

        Returns:
            Dictionary with metadata
        """
        if variable not in EPA_AQS_PARAMETERS:
            raise ValueError(f"Unknown parameter: {variable}")

        param_info = EPA_AQS_PARAMETERS[variable]
        return {
            "variable_name": param_info["name"],
            "description": param_info["description"],
            "unit": param_info["unit"],
            "source": "EPA Air Quality System",
            "temporal_coverage": {
                "start": param_info["years"][0],
                "end": param_info["years"][-1],
                "frequency": "annual",
            },
            "geographic_level": "county",
            "url": "https://aqs.epa.gov",
        }

    # ========================================================================
    # EPA AQS-SPECIFIC METHODS
    # ========================================================================

    def _download_state_year(
        self,
        param_code: str,
        year: int,
        state_fips: str,
    ) -> Optional[pl.DataFrame]:
        """
        Download data for one state, one year.

        Args:
            param_code: EPA parameter code (e.g., "88101" for PM2.5)
            year: Year
            state_fips: 2-digit state FIPS code

        Returns:
            Polars DataFrame or None if no data
        """
        url = self.endpoints["annual_summary"]

        # API parameters
        params = {
            "email": self.email,
            "key": self.api_key,
            "param": param_code,
            "bdate": f"{year}0101",
            "edate": f"{year}1231",
            "state": state_fips,
        }

        try:
            # Make API request with retry logic
            response = self.http_client.get(url, params=params)

            # Parse response
            data = response.json()

            # Check for API errors
            if "error" in data:
                logger.warning(
                    f"API error for state {state_fips}: {data['error']}"
                )
                return None

            # Extract data records
            if "Data" not in data or not data["Data"]:
                logger.debug(f"No data for state {state_fips} year {year}")
                return None

            records = data["Data"]

            # Convert to Polars DataFrame
            df = pl.DataFrame(records)

            # Keep only essential columns
            essential_cols = [
                "state_code",
                "county_code",
                "arithmetic_mean",
                "arithmetic_standard_dev",
                "observation_count",
                "observation_percent",
                "completeness_indicator",
                "parameter_code",
                "parameter",
                "units_of_measure",
                "year",
            ]

            # Select available columns
            available_cols = [c for c in essential_cols if c in df.columns]
            df = df.select(available_cols)

            return df

        except Exception as e:
            logger.error(
                f"Error downloading state {state_fips} year {year}: {e}"
            )
            raise

    def get_all_parameters(self) -> List[str]:
        """
        Get list of all available parameters.

        Returns:
            List of parameter names
        """
        return list(EPA_AQS_PARAMETERS.keys())

    def download_all_years(
        self,
        variable: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        force_refresh: bool = False,
    ) -> List[Path]:
        """
        Download all years for a variable.

        Args:
            variable: Parameter name
            start_year: Start year (default: earliest available)
            end_year: End year (default: latest available)
            force_refresh: Force re-download

        Returns:
            List of paths to cached files
        """
        available_years = self.get_available_years(variable)

        if start_year is None:
            start_year = available_years[0]
        if end_year is None:
            end_year = available_years[-1]

        years = [y for y in available_years if start_year <= y <= end_year]

        logger.info(
            f"Downloading {variable} for {len(years)} years ({start_year}-{end_year})"
        )

        cached_files = []
        for year in years:
            try:
                cached_file = self.download_variable_year(
                    variable, year, force_refresh=force_refresh
                )
                cached_files.append(cached_file)
                logger.info(f"✅ {variable} {year} complete")
            except Exception as e:
                logger.error(f"❌ {variable} {year} failed: {e}")
                continue

        logger.info(
            f"Downloaded {len(cached_files)}/{len(years)} years for {variable}"
        )

        return cached_files
