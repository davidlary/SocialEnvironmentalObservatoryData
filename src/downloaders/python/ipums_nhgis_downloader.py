"""
IPUMS NHGIS Downloader

Downloads census and demographic data from IPUMS NHGIS via API.

IPUMS NHGIS provides:
- 266 datasets spanning 1790-2023
- 10,000+ variables
- Census data, ACS, decennial censuses, historical data
- County-level aggregation available

API Documentation: https://developer.ipums.org/
Rate Limit: 100 requests/minute

Design Pattern: Template Method + Strategy
- Template Method: Standard extract workflow (create → monitor → download)
- Strategy: Different data selection strategies for different time periods
"""

import json
import os
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import polars as pl
import requests
from loguru import logger

from core.base_downloader import BaseDownloader
from core.retry_handler import RobustHTTPClient
from utils.constants import CACHE_DIR
from utils.file_utils import ensure_directory


# ============================================================================
# IPUMS NHGIS API CONFIGURATION
# ============================================================================

IPUMS_API_BASE = "https://api.ipums.org"
IPUMS_API_VERSION = "2"
NHGIS_COLLECTION = "nhgis"

# Geographic levels for county-level data
COUNTY_GEO_LEVELS = ["county"]

# Data format preferences
DATA_FORMAT = "csv_header"  # CSV with headers


# ============================================================================
# IPUMS NHGIS DOWNLOADER
# ============================================================================


class IPUMSNHGISDownloader(BaseDownloader):
    """
    Download data from IPUMS NHGIS via API.

    NHGIS provides comprehensive US census and demographic data from
    1790 to present.
    """

    def __init__(self):
        """Initialize IPUMS NHGIS downloader."""
        super().__init__(
            source_id="ipums_nhgis",
            source_name="IPUMS NHGIS",
            category="02_DEMOGRAPHICS_SOCIAL"
        )

        # Load API credentials
        self.api_key = os.environ.get("IPUMS_NHGIS_API_KEY")
        self.email = os.environ.get("IPUMS_NHGIS_EMAIL")

        if not self.api_key:
            config_file = Path("config/api_credentials.json")
            if config_file.exists():
                with open(config_file) as f:
                    creds = json.load(f).get("nhgis", {})
                    self.api_key = creds.get("api_key")
                    self.email = creds.get("email")

        if not self.api_key:
            logger.warning(
                "IPUMS_NHGIS_API_KEY not set. Sign up at: "
                "https://account.ipums.org/api_keys"
            )

        # API configuration
        self.api_base = IPUMS_API_BASE
        self.extract_endpoint = f"{self.api_base}/extracts/?collection={NHGIS_COLLECTION}&version={IPUMS_API_VERSION}"
        self.metadata_endpoint = f"{self.api_base}/metadata/{NHGIS_COLLECTION}"

        # HTTP client with auth header
        self.http_client = RobustHTTPClient(
            max_retries=3,
            timeout=30
        )
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

        # Cache directory
        self.cache_dir = CACHE_DIR / self.category / self.source_id
        ensure_directory(self.cache_dir)

        logger.info(f"IPUMS NHGIS downloader initialized (cache={self.cache_dir})")

    # ========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS
    # ========================================================================

    def get_available_years(self, variable: str) -> List[int]:
        """
        Get available years for a dataset.

        For NHGIS, this depends on the dataset. Most modern datasets
        have annual or 5-year estimates.

        Args:
            variable: Dataset name (e.g., "2019_2023_ACS5a")

        Returns:
            List of available years
        """
        # NHGIS datasets are named with years
        # Extract years from dataset name
        if "_ACS" in variable:
            # ACS datasets: extract start and end years
            parts = variable.split("_")
            if len(parts) >= 2:
                year_part = parts[0]
                if len(year_part) == 4 and year_part.isdigit():
                    return [int(year_part)]
                # 5-year ACS: e.g., "2019_2023"
                years = [p for p in parts if len(p) == 4 and p.isdigit()]
                if years:
                    start_year = int(years[0])
                    end_year = int(years[-1]) if len(years) > 1 else start_year
                    return list(range(start_year, end_year + 1))

        # Decennial census: single year
        if variable[0].isdigit() and len(variable.split("_")[0]) == 4:
            year = int(variable.split("_")[0])
            return [year]

        # Default: return empty list
        return []

    def download_variable_year(
        self,
        variable: str,
        year: int,
        force_refresh: bool = False
    ) -> Optional[Path]:
        """
        Download data for a dataset and year.

        For NHGIS, we create an extract request, wait for it to complete,
        and download the resulting files.

        Args:
            variable: Dataset name
            year: Year (used for caching/tracking)
            force_refresh: If True, re-download even if cached

        Returns:
            Path to cached extract file or None if failed
        """
        cache_file = self.cache_dir / f"{variable}_{year}_extract.zip"

        if cache_file.exists() and not force_refresh:
            logger.debug(f"Using cached: {cache_file.name}")
            return cache_file

        logger.info(f"Creating extract for {variable} ({year})...")

        try:
            # Step 1: Create extract request
            extract_number = self._create_extract(variable, year)
            if not extract_number:
                return None

            # Step 2: Monitor extract status
            download_link = self._monitor_extract(extract_number)
            if not download_link:
                return None

            # Step 3: Download extract file
            success = self._download_extract(download_link, cache_file)
            if not success:
                return None

            logger.info(f"✅ Downloaded: {cache_file.name}")
            return cache_file

        except Exception as e:
            logger.error(f"Error downloading {variable} {year}: {e}")
            return None

    def get_metadata(self, variable: str) -> Dict:
        """
        Get metadata for a dataset.

        Args:
            variable: Dataset name

        Returns:
            Dictionary with metadata
        """
        return {
            "variable_name": variable,
            "description": f"IPUMS NHGIS dataset {variable}",
            "source": "IPUMS NHGIS",
            "geographic_level": "county",
            "url": "https://www.nhgis.org"
        }

    # ========================================================================
    # NHGIS-SPECIFIC METHODS
    # ========================================================================

    def _get_dataset_tables(self, dataset: str) -> List[str]:
        """
        Get available data tables for a dataset.

        Args:
            dataset: Dataset name

        Returns:
            List of data table names
        """
        try:
            url = f"{self.metadata_endpoint}/datasets/{dataset}?version={IPUMS_API_VERSION}"
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Get all data tables from the dataset
                data_tables = data.get("dataTables", [])
                table_names = [t.get("name") for t in data_tables if t.get("name")]
                logger.debug(f"Dataset {dataset}: found {len(table_names)} data tables")
                return table_names
            else:
                logger.warning(f"Could not get tables for {dataset}: {response.status_code}")
                return []

        except Exception as e:
            logger.warning(f"Error getting tables for {dataset}: {e}")
            return []

    def _create_extract(self, dataset: str, year: int) -> Optional[str]:
        """
        Create an extract request for a dataset.

        Args:
            dataset: Dataset name
            year: Year (for description)

        Returns:
            Extract number or None if failed
        """
        # Get available data tables for this dataset
        data_tables = self._get_dataset_tables(dataset)

        if not data_tables:
            logger.error(f"No data tables found for {dataset}")
            return None

        # CRITICAL FIX: Limit number of tables to prevent server overload
        # NHGIS extracts fail when too many tables are requested at once
        MAX_TABLES_PER_EXTRACT = 50  # Conservative limit based on NHGIS feedback

        if len(data_tables) > MAX_TABLES_PER_EXTRACT:
            logger.warning(
                f"Dataset {dataset} has {len(data_tables)} tables, "
                f"limiting to first {MAX_TABLES_PER_EXTRACT} tables to prevent server overload"
            )
            # Select first N tables - these are typically the most important/frequently used
            data_tables = data_tables[:MAX_TABLES_PER_EXTRACT]

        logger.info(f"Using {len(data_tables)} data tables from {dataset}")

        # Build extract request with correct API v2 format
        extract_request = {
            "description": f"{dataset} county-level extract",
            "datasets": {
                dataset: {
                    "dataTables": data_tables,  # REQUIRED
                    "geogLevels": COUNTY_GEO_LEVELS
                }
            },
            "dataFormat": DATA_FORMAT,  # At top level, not inside dataset
            "breakdownAndDataTypeLayout": "single_file"  # Required for datasets with multiple file types
        }

        try:
            response = requests.post(
                self.extract_endpoint,
                headers=self.headers,
                json=extract_request,
                timeout=30
            )

            if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                data = response.json()
                extract_number = data.get("number")
                logger.info(f"✅ Extract created: #{extract_number}")
                return str(extract_number)
            else:
                logger.error(f"Failed to create extract: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating extract: {e}")
            return None

    def _monitor_extract(self, extract_number: str, max_wait_minutes: int = 60) -> Optional[str]:
        """
        Monitor extract status until complete.

        Args:
            extract_number: Extract ID to monitor
            max_wait_minutes: Maximum time to wait

        Returns:
            Download link or None if failed/timed out
        """
        status_url = f"{self.extract_endpoint.split('?')[0]}/{extract_number}?collection={NHGIS_COLLECTION}&version={IPUMS_API_VERSION}"

        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60

        logger.info(f"Monitoring extract #{extract_number}...")

        while True:
            try:
                response = requests.get(
                    status_url,
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code != 200:
                    logger.error(f"Status check failed: {response.status_code}")
                    return None

                data = response.json()
                status = data.get("status")

                logger.debug(f"Extract #{extract_number} status: {status}")

                if status == "completed":
                    download_links = data.get("downloadLinks", {})
                    logger.debug(f"Download links: {download_links}")

                    # Try different possible keys for download link
                    # IPUMS API may use different keys depending on format
                    data_link_info = (
                        download_links.get("data") or
                        download_links.get("tableData") or
                        download_links.get("gisData")
                    )

                    if data_link_info:
                        # CRITICAL FIX: Download link is a dict with 'url', 'bytes', 'sha256'
                        # Extract the actual URL string from the dict
                        if isinstance(data_link_info, dict):
                            data_url = data_link_info.get("url")
                            if data_url:
                                logger.info(f"Extract #{extract_number} complete! ({data_link_info.get('bytes', 0) / 1024 / 1024:.1f} MB)")
                                return data_url
                            else:
                                logger.error(f"Download link dict missing 'url' field: {data_link_info}")
                                return None
                        else:
                            # Fallback: if it's already a string URL
                            logger.info(f"Extract #{extract_number} complete!")
                            return data_link_info
                    else:
                        logger.error(f"No download link in completed extract. Available keys: {list(download_links.keys())}")
                        logger.debug(f"Full response: {json.dumps(data, indent=2)}")
                        return None

                elif status in ["failed", "canceled"]:
                    logger.error(f"Extract #{extract_number} {status}")
                    return None

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > max_wait_seconds:
                    logger.error(f"Extract #{extract_number} timed out after {max_wait_minutes} minutes")
                    return None

                # Wait before next check (start with 10s, increase to 30s)
                wait_time = min(10 + elapsed / 60, 30)
                time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Error checking status: {e}")
                return None

    def _download_extract(self, download_url: str, output_file: Path) -> bool:
        """
        Download extract file.

        Args:
            download_url: URL to download from
            output_file: Where to save the file

        Returns:
            True if successful
        """
        try:
            logger.info(f"Downloading extract to {output_file.name}...")

            response = requests.get(
                download_url,
                headers=self.headers,
                stream=True,
                timeout=300
            )

            if response.status_code != 200:
                logger.error(f"Download failed: {response.status_code}")
                return False

            # Download in chunks
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Verify it's a valid ZIP
            if zipfile.is_zipfile(output_file):
                logger.info(f"Downloaded {output_file.stat().st_size / (1024**2):.1f} MB")
                return True
            else:
                logger.error("Downloaded file is not a valid ZIP")
                output_file.unlink()
                return False

        except Exception as e:
            logger.error(f"Error downloading extract: {e}")
            return False

    def get_all_datasets(self) -> List[Dict]:
        """
        Get list of all available NHGIS datasets.

        Returns:
            List of dataset metadata dictionaries
        """
        try:
            url = f"{self.metadata_endpoint}/datasets?version={IPUMS_API_VERSION}"
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                datasets = data.get("data", [])
                logger.info(f"Found {len(datasets)} NHGIS datasets")
                return datasets
            else:
                logger.error(f"Failed to get datasets: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error getting datasets: {e}")
            return []


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "IPUMSNHGISDownloader",
]
