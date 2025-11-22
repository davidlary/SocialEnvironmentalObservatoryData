"""
Abstract Base Downloader class.

Defines the interface for all source-specific downloaders.

All downloaders must implement:
- get_available_years(): Return list of years with data
- download_variable_year(): Download data for one variable/year
- get_metadata(): Return variable metadata

Base class provides:
- Progress tracking integration
- Cache management integration
- Logging integration
- Retry logic
- Common utilities

Design Patterns:
- Template Method: Define workflow, subclasses fill in details
- Strategy: Different download strategies for different sources
- Facade: Simplify complex download operations
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from core.cache_manager import CacheManager
from core.progress_tracker import ProgressTracker
from core.retry_handler import RobustHTTPClient
from utils.constants import DEFAULT_RATE_LIMIT


# ============================================================================
# BASE DOWNLOADER (Abstract)
# ============================================================================


class BaseDownloader(ABC):
    """
    Abstract base class for data downloaders.

    Subclasses must implement:
    - get_available_years()
    - download_variable_year()
    - get_metadata()

    Example subclass:
        class EPAAQSDownloader(BaseDownloader):
            def get_available_years(self, variable):
                return list(range(1980, 2025))

            def download_variable_year(self, variable, year):
                # Download logic here
                return cached_file_path

            def get_metadata(self, variable):
                return {"unit": "μg/m³", "description": "..."}
    """

    def __init__(
        self,
        source_id: str,
        source_name: str,
        category: str,
        rate_limit: Optional[float] = DEFAULT_RATE_LIMIT,
    ):
        """
        Initialize base downloader.

        Args:
            source_id: Unique source identifier (e.g., "epa_aqs")
            source_name: Human-readable source name (e.g., "EPA Air Quality System")
            category: Data category (e.g., "01_AIR_ATMOSPHERE")
            rate_limit: Requests per second (None = no limit)
        """
        self.source_id = source_id
        self.source_name = source_name
        self.category = category

        # Initialize core components
        self.cache_manager = CacheManager()
        self.progress_tracker = ProgressTracker()
        self.http_client = RobustHTTPClient(rate_limit=rate_limit)

        # Setup source-specific logger
        self.logger = logger.bind(source=source_id)

        self.logger.info(
            f"Initialized {source_name} downloader (category={category})"
        )

    # ========================================================================
    # ABSTRACT METHODS (must be implemented by subclasses)
    # ========================================================================

    @abstractmethod
    def get_available_years(self, variable: str) -> List[int]:
        """
        Get list of available years for a variable.

        Args:
            variable: Variable identifier

        Returns:
            List of years with available data

        Example:
            def get_available_years(self, variable):
                # EPA AQS has data from 1980-2024
                return list(range(1980, 2025))
        """
        pass

    @abstractmethod
    def download_variable_year(
        self,
        variable: str,
        year: int,
        force_refresh: bool = False,
    ) -> Optional[Path]:
        """
        Download data for one variable/year.

        Should:
        1. Check cache (unless force_refresh)
        2. Download if not cached
        3. Save to cache
        4. Return path to cached file

        Args:
            variable: Variable identifier
            year: Year
            force_refresh: If True, re-download even if cached

        Returns:
            Path to cached file, or None if failed

        Example:
            def download_variable_year(self, variable, year, force_refresh=False):
                # Check cache
                cached = self.cache_manager.get_from_cache(
                    self.category, self.source_id, variable, year
                )
                if cached and not force_refresh:
                    return cached

                # Download
                data = self._fetch_from_api(variable, year)

                # Save to temp file
                temp_file = Path(f"/tmp/{variable}_{year}.csv")
                data.write_csv(temp_file)

                # Cache
                cached_path = self.cache_manager.save_to_cache(
                    temp_file, self.category, self.source_id, variable, year
                )

                return cached_path
        """
        pass

    @abstractmethod
    def get_metadata(self, variable: str) -> Dict[str, str]:
        """
        Get metadata for a variable.

        Should return at minimum:
        - unit: Unit of measurement
        - description: Variable description
        - source_url: URL to data source

        Args:
            variable: Variable identifier

        Returns:
            Dictionary with metadata

        Example:
            def get_metadata(self, variable):
                return {
                    "unit": "μg/m³",
                    "description": "PM2.5 annual mean concentration",
                    "source_url": "https://aqs.epa.gov/...",
                    "method": "Monitor-based measurements"
                }
        """
        pass

    # ========================================================================
    # TEMPLATE METHOD (common workflow)
    # ========================================================================

    def download_variable(
        self,
        variable: str,
        years: Optional[List[int]] = None,
        force_refresh: bool = False,
    ) -> Dict[int, Optional[Path]]:
        """
        Download all years for a variable (template method).

        This implements the common workflow:
        1. Get available years
        2. Filter by requested years
        3. Check progress tracker
        4. Download pending years
        5. Update progress

        Args:
            variable: Variable identifier
            years: Optional list of specific years (None = all available)
            force_refresh: If True, re-download cached data

        Returns:
            Dictionary mapping year to cached file path

        Example:
            >>> downloader = EPAAQSDownloader()
            >>> results = downloader.download_variable(
            ...     "PM25_Annual",
            ...     years=[2020, 2021, 2022]
            ... )
            >>> for year, path in results.items():
            ...     print(f"{year}: {path}")
        """
        self.logger.info(f"Downloading variable: {variable}")

        # Get available years
        available_years = self.get_available_years(variable)
        self.logger.debug(f"Available years: {len(available_years)}")

        # Filter by requested years
        if years:
            download_years = [y for y in years if y in available_years]
        else:
            download_years = available_years

        # Check progress tracker for completed downloads
        if not force_refresh:
            pending_years = self.progress_tracker.get_pending_downloads(
                self.source_id, variable, download_years
            )
            self.logger.info(
                f"Pending years: {len(pending_years)}/{len(download_years)}"
            )
        else:
            pending_years = download_years

        # Download each year
        results = {}

        for year in download_years:
            # Skip if already completed (unless force_refresh)
            if not force_refresh and year not in pending_years:
                cached_path = self.cache_manager.get_from_cache(
                    self.category, self.source_id, variable, year
                )
                if cached_path:
                    results[year] = cached_path
                    continue

            try:
                self.logger.info(f"Downloading {variable} - {year}")

                cached_path = self.download_variable_year(
                    variable, year, force_refresh
                )

                if cached_path:
                    results[year] = cached_path
                    self.progress_tracker.mark_downloaded(
                        self.source_id, variable, year, "completed"
                    )
                else:
                    results[year] = None
                    self.progress_tracker.mark_downloaded(
                        self.source_id, variable, year, "failed"
                    )

            except Exception as e:
                self.logger.error(f"Error downloading {variable}/{year}: {e}")
                results[year] = None
                self.progress_tracker.mark_downloaded(
                    self.source_id, variable, year, "failed"
                )

        # Summary
        successful = sum(1 for path in results.values() if path is not None)
        self.logger.info(
            f"✅ Downloaded {successful}/{len(download_years)} years for {variable}"
        )

        return results

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_cache_path(self, variable: str, year: int, extension: str = "csv") -> Path:
        """
        Get cache path for a variable/year.

        Args:
            variable: Variable identifier
            year: Year
            extension: File extension

        Returns:
            Path to cache file
        """
        return self.cache_manager.get_cache_path(
            self.category, self.source_id, variable, year, extension
        )

    def is_cached(self, variable: str, year: int, extension: str = "csv") -> bool:
        """
        Check if variable/year is cached.

        Args:
            variable: Variable identifier
            year: Year
            extension: File extension

        Returns:
            True if cached and valid
        """
        return self.cache_manager.is_cached(
            self.category, self.source_id, variable, year, extension
        )

    def get_progress_summary(self) -> Dict:
        """
        Get progress summary for this source.

        Returns:
            Dictionary with progress statistics
        """
        return self.progress_tracker.get_progress_summary(self.source_id)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ["BaseDownloader"]
