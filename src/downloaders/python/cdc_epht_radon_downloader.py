"""
CDC Environmental Public Health Tracking Network (EPHT) - Radon Testing Downloader.

Downloads radon testing data from the CDC Environmental Public Health Tracking Network API:
- Radon test counts by county
- Mean and median radon concentrations
- Percentages exceeding EPA (4 pCi/L) and WHO (2.7 pCi/L) guidelines
- Test characteristics (type, location)

API Documentation: https://ephtracking.cdc.gov/apihelp
Contact: trackingsupport@cdc.gov

Data Coverage:
- Geographic: County-level (46 states + DC, 21 contributing states)
- Temporal: 2013-2022 (annual updates, 1-2 year lag)
- Frequency: Annual summaries
- Sample Size: 11.9M tests (1988-2022) from 21 states + 6 national labs

Data Quality:
- Strengths: Actual test results, large sample, standardized, recent
- Limitations: Selection bias (voluntary testing), privacy suppression (<10 tests)

Design Patterns:
- Template Method: Inherits from BaseDownloader
- Strategy: State-by-state download pattern
- Caching: County-year level caching with validation
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import polars as pl
from loguru import logger

from core.base_downloader import BaseDownloader
from utils.constants import CACHE_DIR, DATA_DIR, TSV_DELIMITER
from utils.file_utils import ensure_directory, read_json_file, write_json_file, write_tsv


# ============================================================================
# CDC EPHT RADON PARAMETERS
# ============================================================================

# Radon measure configuration
CDC_EPHT_RADON_CONFIG = {
    "measure_id": 479,
    "content_area_id": 479,
    "measure_name": "Radon_Testing",
    "description": "County-level radon testing results from CDC EPHT",
    "years": list(range(2013, 2023)),  # 2013-2022 confirmed availability
    "contributing_states": [
        "02", "08", "09", "12", "17", "20", "22", "27", "29",  # AK, CO, CT, FL, IL, KS, LA, MN, MO
        "31", "34", "36", "37", "41", "42", "44", "47", "49",  # NE, NJ, NY, NC, OR, PA, RI, TN, UT
        "50", "53", "55"  # VT, WA, WI
    ]
}

# Radon variables with metadata
RADON_VARIABLES = {
    "num_tests": {
        "description": "Total radon tests conducted in county",
        "unit": "count",
        "priority": "high"
    },
    "mean_radon_pci_l": {
        "description": "Average radon concentration",
        "unit": "pCi/L",
        "priority": "high"
    },
    "median_radon_pci_l": {
        "description": "Median radon concentration",
        "unit": "pCi/L",
        "priority": "high"
    },
    "pct_above_4_pci_l": {
        "description": "Percent exceeding EPA action level (4 pCi/L)",
        "unit": "percent",
        "priority": "high"
    },
    "pct_above_2_7_pci_l": {
        "description": "Percent exceeding WHO guideline (2.7 pCi/L)",
        "unit": "percent",
        "priority": "medium"
    },
    "test_type": {
        "description": "Short-term (<90 days) vs long-term (≥90 days)",
        "unit": "categorical",
        "priority": "medium"
    },
    "test_location": {
        "description": "Basement, first floor, living area",
        "unit": "categorical",
        "priority": "low"
    },
    "test_year": {
        "description": "Year of testing",
        "unit": "year",
        "priority": "high"
    }
}

# All US state FIPS codes (51 states including DC)
US_STATE_FIPS = [f"{i:02d}" for i in range(1, 57)]  # 01-56


# ============================================================================
# CDC EPHT RADON DOWNLOADER
# ============================================================================


class CDCEPHTRadonDownloader(BaseDownloader):
    """
    Downloader for CDC Environmental Public Health Tracking Network radon data.

    Downloads county-level radon testing statistics including test counts,
    mean/median concentrations, and exceedance percentages.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CDC EPHT Radon downloader.

        Args:
            api_key: CDC EPHT API key (or set CDC_EPHT_API_KEY env var)

        API Key:
            Request from: trackingsupport@cdc.gov
            Or set environment variable CDC_EPHT_API_KEY
        """
        super().__init__(
            source_id="cdc_epht_radon",
            source_name="CDC Environmental Public Health Tracking - Radon",
            category="05_RADIATION",
            rate_limit=2.0,  # Conservative rate limit (unknown official limit)
        )

        # Get API credentials
        self.api_key = api_key or os.getenv("CDC_EPHT_API_KEY")

        if not self.api_key:
            logger.warning(
                "CDC_EPHT_API_KEY not set. API requests will fail. "
                "Request key from: trackingsupport@cdc.gov"
            )

        # API configuration
        self.base_url = "https://ephtracking.cdc.gov/apigateway/api/v1"
        self.measure_id = CDC_EPHT_RADON_CONFIG["measure_id"]
        self.content_area_id = CDC_EPHT_RADON_CONFIG["content_area_id"]

        # Cache directory for this source
        self.cache_dir = CACHE_DIR / self.category / self.source_id
        ensure_directory(self.cache_dir)

        logger.info(f"CDC EPHT Radon downloader initialized (cache={self.cache_dir})")
        logger.info(f"Radon Measure ID: {self.measure_id}")

    # ========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS
    # ========================================================================

    def get_available_years(self, variable: str) -> List[int]:
        """
        Get available years for radon testing data.

        Args:
            variable: Variable name (e.g., "radon_testing")

        Returns:
            List of years with data (2013-2022)
        """
        # CDC EPHT has radon data for 2013-2022
        return CDC_EPHT_RADON_CONFIG["years"]

    def download_variable_year(
        self,
        variable: str,
        year: int,
        force_refresh: bool = False,
    ) -> Optional[Path]:
        """
        Download radon data for one year (all states and counties).

        Args:
            variable: Variable name (should be "radon_testing")
            year: Year to download
            force_refresh: Force re-download even if cached

        Returns:
            Path to cached CSV file with radon data

        Raises:
            ValueError: If year is invalid
            RuntimeError: If download fails
        """
        # Validate year
        available_years = self.get_available_years(variable)
        if year not in available_years:
            raise ValueError(
                f"Year {year} not available. Available: {min(available_years)}-{max(available_years)}"
            )

        # Check cache
        cache_file = self.cache_dir / f"radon_testing_{year}.csv"
        if cache_file.exists() and not force_refresh:
            logger.info(f"Using cached data: {cache_file}")
            return cache_file

        logger.info(f"Downloading radon data for {year}...")

        # Download data for all states
        all_data = []
        states_with_data = 0
        counties_with_data = 0

        for state_fips in US_STATE_FIPS:
            try:
                state_data = self._download_state_year(state_fips, year)
                if state_data is not None and len(state_data) > 0:
                    all_data.append(state_data)
                    states_with_data += 1
                    counties_with_data += len(state_data)
                    logger.debug(
                        f"State {state_fips}: {len(state_data)} counties with data"
                    )
            except Exception as e:
                logger.debug(f"State {state_fips}: No data or error - {e}")
                continue

        if not all_data:
            logger.warning(f"No radon data found for {year}")
            return None

        # Combine all state data
        combined_df = pl.concat(all_data, how="vertical")

        logger.info(
            f"✅ Downloaded {year}: {states_with_data} states, {counties_with_data} counties"
        )

        # Save to cache
        combined_df.write_csv(cache_file)
        logger.info(f"Cached to: {cache_file}")

        return cache_file

    def get_metadata(self, variable: str) -> Dict[str, str]:
        """
        Get metadata for radon testing data.

        Args:
            variable: Variable name

        Returns:
            Dictionary with metadata
        """
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "measure_id": str(self.measure_id),
            "description": CDC_EPHT_RADON_CONFIG["description"],
            "unit": "various (see variable catalog)",
            "temporal_coverage": f"{min(CDC_EPHT_RADON_CONFIG['years'])}-{max(CDC_EPHT_RADON_CONFIG['years'])}",
            "geographic_coverage": "County-level (46 states + DC)",
            "source_url": "https://ephtracking.cdc.gov/",
            "data_sources": "CDC Tracking Program states (21 states) + 6 national radon labs",
            "sample_size": "11.9M tests (1988-2022)",
            "update_frequency": "Annual (1-2 year lag)",
            "variables": ", ".join(RADON_VARIABLES.keys()),
            "data_quality_notes": "Actual test results; voluntary testing (selection bias); privacy suppression <10 tests/county"
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _download_state_year(self, state_fips: str, year: int) -> Optional[pl.DataFrame]:
        """
        Download radon data for one state and year.

        Args:
            state_fips: 2-digit state FIPS code
            year: Year to download

        Returns:
            Polars DataFrame with county-level data, or None if no data
        """
        # Build API URL
        # Endpoint: getCoreHolder/{contentAreaId}/{stateId}/{countyId}
        # countyId=0 means all counties in the state
        url = (
            f"{self.base_url}/getCoreHolder/"
            f"{self.content_area_id}/{state_fips}/0"
        )

        params = {
            "apiToken": self.api_key,
            "measureId": self.measure_id,
            "stratificationLevelId": 1,  # County level
            "isSmoothed": "false",
            "year": year
        }

        # Make request with retry logic
        try:
            response = self.http_client.get(url, params=params)
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Check for API errors
            if isinstance(data, dict) and data.get("code") == 400:
                logger.debug(f"State {state_fips}, {year}: {data.get('message', 'No data')}")
                return None

            # Check if data is a list
            if not isinstance(data, list) or len(data) == 0:
                return None

            # Convert to DataFrame
            df = pl.DataFrame(data)

            # Return DataFrame (will be processed later)
            return df

        except Exception as e:
            logger.debug(f"Error downloading state {state_fips}, year {year}: {e}")
            return None

    def get_variable_list(self) -> List[str]:
        """
        Get list of available variables.

        Returns:
            List of variable names
        """
        return list(RADON_VARIABLES.keys())

    def get_contributing_states(self) -> List[str]:
        """
        Get list of states contributing radon data.

        Returns:
            List of 2-digit state FIPS codes
        """
        return CDC_EPHT_RADON_CONFIG["contributing_states"]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ["CDCEPHTRadonDownloader", "RADON_VARIABLES", "CDC_EPHT_RADON_CONFIG"]
