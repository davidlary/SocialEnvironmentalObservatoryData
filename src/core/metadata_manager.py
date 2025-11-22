"""
Metadata Manager for FIPS codes and county boundaries.

Handles downloading, caching, and providing access to essential metadata:
- Official Census FIPS codes (3,143 counties)
- County boundaries (TIGER/Line shapefiles)
- State-level metadata
- Geographic crosswalks

This is the FOUNDATION - all other modules depend on this metadata.

Design Patterns:
- Singleton: Single instance managing metadata
- Lazy Loading: Download only when needed
- Caching: Store locally to avoid repeated downloads
"""

import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import geopandas as gpd
import polars as pl
from loguru import logger

from utils.constants import (
    CRS_WGS84,
    METADATA_DIR,
    TOTAL_US_COUNTIES,
    TSV_DELIMITER,
    URL_CENSUS_FIPS,
    URL_TIGER_LINE_BASE,
)
from utils.file_utils import (
    ensure_directory,
    extract_zip,
    read_tsv,
    validate_file_exists,
    write_tsv,
)


# ============================================================================
# METADATA MANAGER (Singleton)
# ============================================================================


class MetadataManager:
    """
    Singleton manager for geographic metadata.

    Responsibilities:
    - Download official Census FIPS codes
    - Download TIGER/Line county boundaries
    - Provide lookup functions
    - Cache metadata locally
    """

    _instance = None
    _fips_data = None
    _county_boundaries = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize metadata manager."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            ensure_directory(METADATA_DIR)
            logger.info("Metadata manager initialized")

    # ========================================================================
    # FIPS CODES
    # ========================================================================

    def download_fips_codes(
        self,
        force_refresh: bool = False,
    ) -> pl.DataFrame:
        """
        Download official Census FIPS codes.

        Args:
            force_refresh: If True, re-download even if cached

        Returns:
            Polars DataFrame with FIPS codes and metadata

        Columns:
            - FIPS: 5-digit FIPS code (string)
            - State_FIPS: 2-digit state code (string)
            - County_FIPS: 3-digit county code (string)
            - State_Name: Full state name
            - County_Name: Full county name (with "County", "Parish", etc.)
            - State_Abbrev: 2-letter state abbreviation
        """
        fips_file = METADATA_DIR / "fips_codes_master.tsv"

        # Check cache
        if fips_file.exists() and not force_refresh:
            logger.info(f"Loading cached FIPS codes: {fips_file}")
            try:
                self._fips_data = read_tsv(fips_file)
                logger.info(f"Loaded {len(self._fips_data)} FIPS codes from cache")
                return self._fips_data
            except Exception as e:
                logger.warning(f"Error loading cached FIPS: {e}. Re-downloading.")

        # Download from Census Bureau
        logger.info(f"Downloading FIPS codes from Census Bureau: {URL_CENSUS_FIPS}")

        try:
            response = requests.get(URL_CENSUS_FIPS, timeout=30)
            response.raise_for_status()

            # Parse CSV (Census format: STATE,STATEFP,COUNTYFP,COUNTYNAME,CLASSFP)
            lines = response.text.strip().split("\n")
            header = lines[0].split(",")
            data = [line.split(",") for line in lines[1:]]

            # Convert to Polars DataFrame
            df = pl.DataFrame(
                {
                    "State_Abbrev": [row[0] for row in data],
                    "State_FIPS": [row[1] for row in data],
                    "County_FIPS": [row[2] for row in data],
                    "County_Name": [row[3] for row in data],
                }
            )

            # Create 5-digit FIPS
            df = df.with_columns(
                (pl.col("State_FIPS") + pl.col("County_FIPS")).alias("FIPS")
            )

            # Add full state names
            state_names_map = self._get_state_names_map()
            df = df.with_columns(
                pl.col("State_Abbrev").replace(state_names_map, default=None).alias("State_Name")
            )

            # Reorder columns
            df = df.select([
                "FIPS",
                "State_FIPS",
                "County_FIPS",
                "State_Name",
                "County_Name",
                "State_Abbrev",
            ])

            # Validate
            if len(df) != TOTAL_US_COUNTIES:
                logger.warning(
                    f"Expected {TOTAL_US_COUNTIES} counties, "
                    f"downloaded {len(df)}"
                )

            # Save to cache
            write_tsv(df, fips_file)
            logger.info(f"Saved {len(df)} FIPS codes to {fips_file}")

            self._fips_data = df
            return df

        except Exception as e:
            logger.error(f"Error downloading FIPS codes: {e}")
            raise

    def get_fips_codes(self) -> pl.DataFrame:
        """
        Get FIPS codes (download if not cached).

        Returns:
            Polars DataFrame with FIPS codes
        """
        if self._fips_data is None:
            self._fips_data = self.download_fips_codes()

        return self._fips_data

    def lookup_county(self, fips: str) -> Optional[Dict[str, str]]:
        """
        Lookup county metadata by FIPS code.

        Args:
            fips: 5-digit FIPS code

        Returns:
            Dictionary with county metadata, or None if not found

        Example:
            >>> manager = MetadataManager()
            >>> info = manager.lookup_county("48453")
            >>> print(info)
            {'FIPS': '48453', 'State_Name': 'Texas', 'County_Name': 'Travis County', ...}
        """
        fips_df = self.get_fips_codes()

        county = fips_df.filter(pl.col("FIPS") == fips)

        if len(county) == 0:
            logger.warning(f"FIPS code not found: {fips}")
            return None

        return county.to_dicts()[0]

    def get_counties_by_state(self, state_fips: str) -> pl.DataFrame:
        """
        Get all counties for a state.

        Args:
            state_fips: 2-digit state FIPS code

        Returns:
            Polars DataFrame with counties for that state

        Example:
            >>> manager = MetadataManager()
            >>> tx_counties = manager.get_counties_by_state("48")
            >>> print(len(tx_counties))  # 254 counties in Texas
        """
        fips_df = self.get_fips_codes()

        return fips_df.filter(pl.col("State_FIPS") == state_fips)

    # ========================================================================
    # COUNTY BOUNDARIES
    # ========================================================================

    def download_county_boundaries(
        self,
        year: int = 2020,
        force_refresh: bool = False,
    ) -> gpd.GeoDataFrame:
        """
        Download TIGER/Line county boundaries shapefile.

        Args:
            year: Census year (2010, 2020, etc.)
            force_refresh: If True, re-download even if cached

        Returns:
            GeoDataFrame with county boundaries

        Columns:
            - GEOID: 5-digit FIPS code
            - NAME: County name
            - STATEFP: State FIPS
            - COUNTYFP: County FIPS
            - geometry: Polygon geometry
        """
        boundaries_file = METADATA_DIR / f"county_boundaries_{year}.gpkg"

        # Check cache
        if boundaries_file.exists() and not force_refresh:
            logger.info(f"Loading cached county boundaries: {boundaries_file}")
            try:
                self._county_boundaries = gpd.read_file(boundaries_file)
                logger.info(
                    f"Loaded {len(self._county_boundaries)} county boundaries from cache"
                )
                return self._county_boundaries
            except Exception as e:
                logger.warning(f"Error loading cached boundaries: {e}. Re-downloading.")

        # Download from Census TIGER/Line
        # URL format: https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/tl_{year}_us_county.zip
        tiger_url = URL_TIGER_LINE_BASE.format(year=year)
        zip_filename = f"tl_{year}_us_county.zip"
        zip_url = urljoin(tiger_url, zip_filename)

        logger.info(f"Downloading county boundaries from Census: {zip_url}")

        try:
            # Download ZIP file
            zip_path = METADATA_DIR / zip_filename
            response = requests.get(zip_url, timeout=60, stream=True)
            response.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded {zip_path.stat().st_size / 1024 / 1024:.1f} MB")

            # Extract shapefile
            extract_dir = METADATA_DIR / f"tiger_{year}_county"
            extracted_files = extract_zip(zip_path, extract_dir)
            logger.info(f"Extracted {len(extracted_files)} files")

            # Find .shp file
            shp_file = next(
                (f for f in extracted_files if f.suffix == ".shp"),
                None
            )

            if shp_file is None:
                raise FileNotFoundError("Shapefile (.shp) not found in ZIP")

            # Read shapefile
            gdf = gpd.read_file(shp_file)

            # Validate
            if "GEOID" not in gdf.columns:
                raise ValueError("Shapefile missing GEOID column")

            if len(gdf) != TOTAL_US_COUNTIES:
                logger.warning(
                    f"Expected {TOTAL_US_COUNTIES} counties, "
                    f"downloaded {len(gdf)}"
                )

            # Ensure WGS84 CRS
            if gdf.crs != CRS_WGS84:
                logger.info(f"Reprojecting from {gdf.crs} to {CRS_WGS84}")
                gdf = gdf.to_crs(CRS_WGS84)

            # Save to GeoPackage (more efficient than shapefile)
            gdf.to_file(boundaries_file, driver="GPKG")
            logger.info(f"Saved {len(gdf)} boundaries to {boundaries_file}")

            # Clean up temporary files
            zip_path.unlink()
            logger.debug("Cleaned up ZIP file")

            self._county_boundaries = gdf
            return gdf

        except Exception as e:
            logger.error(f"Error downloading county boundaries: {e}")
            raise

    def get_county_boundaries(
        self,
        year: int = 2020,
    ) -> gpd.GeoDataFrame:
        """
        Get county boundaries (download if not cached).

        Args:
            year: Census year

        Returns:
            GeoDataFrame with county boundaries
        """
        if self._county_boundaries is None:
            self._county_boundaries = self.download_county_boundaries(year)

        return self._county_boundaries

    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================

    @staticmethod
    def _get_state_names_map() -> Dict[str, str]:
        """
        Get mapping of state abbreviations to full names.

        Returns:
            Dictionary mapping state abbreviation to full name
        """
        return {
            "AL": "Alabama",
            "AK": "Alaska",
            "AZ": "Arizona",
            "AR": "Arkansas",
            "CA": "California",
            "CO": "Colorado",
            "CT": "Connecticut",
            "DE": "Delaware",
            "DC": "District of Columbia",
            "FL": "Florida",
            "GA": "Georgia",
            "HI": "Hawaii",
            "ID": "Idaho",
            "IL": "Illinois",
            "IN": "Indiana",
            "IA": "Iowa",
            "KS": "Kansas",
            "KY": "Kentucky",
            "LA": "Louisiana",
            "ME": "Maine",
            "MD": "Maryland",
            "MA": "Massachusetts",
            "MI": "Michigan",
            "MN": "Minnesota",
            "MS": "Mississippi",
            "MO": "Missouri",
            "MT": "Montana",
            "NE": "Nebraska",
            "NV": "Nevada",
            "NH": "New Hampshire",
            "NJ": "New Jersey",
            "NM": "New Mexico",
            "NY": "New York",
            "NC": "North Carolina",
            "ND": "North Dakota",
            "OH": "Ohio",
            "OK": "Oklahoma",
            "OR": "Oregon",
            "PA": "Pennsylvania",
            "RI": "Rhode Island",
            "SC": "South Carolina",
            "SD": "South Dakota",
            "TN": "Tennessee",
            "TX": "Texas",
            "UT": "Utah",
            "VT": "Vermont",
            "VA": "Virginia",
            "WA": "Washington",
            "WV": "West Virginia",
            "WI": "Wisconsin",
            "WY": "Wyoming",
            # Territories
            "AS": "American Samoa",
            "GU": "Guam",
            "MP": "Northern Mariana Islands",
            "PR": "Puerto Rico",
            "VI": "U.S. Virgin Islands",
        }

    def validate_metadata(self) -> Dict[str, any]:
        """
        Validate metadata completeness and consistency.

        Returns:
            Dictionary with validation results

        Example:
            >>> manager = MetadataManager()
            >>> results = manager.validate_metadata()
            >>> print(results["fips_count"])  # 3143
            >>> print(results["all_valid"])   # True
        """
        results = {
            "fips_count": 0,
            "boundaries_count": 0,
            "fips_boundaries_match": False,
            "all_valid": False,
        }

        try:
            # Check FIPS codes
            fips_df = self.get_fips_codes()
            results["fips_count"] = len(fips_df)

            # Check boundaries
            boundaries = self.get_county_boundaries()
            results["boundaries_count"] = len(boundaries)

            # Check if counts match
            results["fips_boundaries_match"] = (
                results["fips_count"] == results["boundaries_count"]
            )

            # Check if all FIPS in boundaries
            fips_set = set(fips_df["FIPS"].to_list())
            boundaries_set = set(boundaries["GEOID"].to_list())

            missing_in_boundaries = fips_set - boundaries_set
            missing_in_fips = boundaries_set - fips_set

            results["missing_in_boundaries"] = list(missing_in_boundaries)
            results["missing_in_fips"] = list(missing_in_fips)

            results["all_valid"] = (
                results["fips_count"] == TOTAL_US_COUNTIES
                and results["boundaries_count"] == TOTAL_US_COUNTIES
                and len(missing_in_boundaries) == 0
                and len(missing_in_fips) == 0
            )

            if results["all_valid"]:
                logger.info("✅ Metadata validation: PASSED")
            else:
                logger.warning(f"⚠️ Metadata validation issues: {results}")

        except Exception as e:
            logger.error(f"Metadata validation failed: {e}")
            results["error"] = str(e)

        return results


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Singleton instance
_metadata_manager = MetadataManager()


def get_fips_codes() -> pl.DataFrame:
    """
    Get FIPS codes (convenience function).

    Returns:
        Polars DataFrame with FIPS codes
    """
    return _metadata_manager.get_fips_codes()


def get_county_boundaries(year: int = 2020) -> gpd.GeoDataFrame:
    """
    Get county boundaries (convenience function).

    Args:
        year: Census year

    Returns:
        GeoDataFrame with county boundaries
    """
    return _metadata_manager.get_county_boundaries(year)


def lookup_county(fips: str) -> Optional[Dict[str, str]]:
    """
    Lookup county by FIPS code (convenience function).

    Args:
        fips: 5-digit FIPS code

    Returns:
        Dictionary with county metadata
    """
    return _metadata_manager.lookup_county(fips)


def validate_metadata() -> Dict[str, any]:
    """
    Validate metadata (convenience function).

    Returns:
        Validation results
    """
    return _metadata_manager.validate_metadata()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "MetadataManager",
    "get_fips_codes",
    "get_county_boundaries",
    "lookup_county",
    "validate_metadata",
]
