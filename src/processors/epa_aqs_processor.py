"""
EPA AQS Data Processor.

Converts EPA AQS cached files to standardized county-level TSV files.

Input: Raw EPA AQS API responses (CSV format)
Output: Standardized TSV files with FIPS metadata

Processing Steps:
1. Read cached CSV file
2. Extract county-level data (arithmetic_mean)
3. Create FIPS code from state_code + county_code
4. Join with FIPS metadata (state name, county name)
5. Create standardized TSV with required columns
6. Save to processed directory

Output Format:
    FIPS, State_FIPS, County_FIPS, State_Name, County_Name, State_Abbrev, Year, Value, Unit

Design Patterns:
- Strategy: Different aggregation strategies for different metrics
- Template Method: Standard processing workflow
"""

from pathlib import Path
from typing import Dict, Optional

import polars as pl
from loguru import logger

from core.metadata_manager import MetadataManager
from core.tsv_generator import TSVGenerator
from utils.constants import CACHE_DIR, PROCESSED_DIR
from utils.file_utils import ensure_directory, read_tsv, write_tsv


# ============================================================================
# EPA AQS PROCESSOR
# ============================================================================


class EPAAQSProcessor:
    """
    Processor for EPA AQS data.

    Converts raw EPA AQS API responses to standardized county-level TSV files.
    """

    def __init__(self):
        """Initialize EPA AQS processor."""
        self.source_id = "epa_aqs"
        self.category = "01_AIR_ATMOSPHERE"
        self.cache_dir = CACHE_DIR / self.category / self.source_id
        self.processed_dir = PROCESSED_DIR / self.category

        # Initialize components
        self.metadata_manager = MetadataManager()
        self.tsv_generator = TSVGenerator()

        # Load FIPS codes
        self.fips_lookup = self.metadata_manager.get_fips_codes()

        logger.info(f"EPA AQS processor initialized")

    def process_variable_year(
        self,
        variable: str,
        year: int,
        force_refresh: bool = False,
    ) -> Optional[Path]:
        """
        Process one variable for one year.

        Args:
            variable: Parameter name (e.g., "PM25")
            year: Year
            force_refresh: Force re-processing even if output exists

        Returns:
            Path to output TSV file, or None if processing failed
        """
        # Check input file
        cache_file = self.cache_dir / f"{variable}_{year}_raw.csv"
        if not cache_file.exists():
            logger.warning(
                f"Cache file not found: {cache_file}. "
                f"Download data first with: "
                f"python scripts/03_download_source.py --source epa_aqs --variable {variable} --years {year}"
            )
            return None

        # Check output file
        variable_dir = self.processed_dir / variable
        ensure_directory(variable_dir)
        output_file = variable_dir / f"{year}_{variable}.tsv"

        if output_file.exists() and not force_refresh:
            logger.info(f"Output file already exists: {output_file}")
            return output_file

        logger.info(f"Processing {variable} {year}...")

        try:
            # Read cached data
            df = read_tsv(cache_file)
            logger.debug(f"Read {len(df)} records from cache")

            # Check if data is empty
            if len(df) == 0:
                logger.warning(f"No data in cache file: {cache_file}")
                return None

            # Extract and transform data
            df = self._transform_to_county_level(df, variable, year)

            if df is None or len(df) == 0:
                logger.warning(f"No data after transformation")
                return None

            # Save to TSV (data is already in correct format)
            write_tsv(df, output_file)

            logger.info(
                f"✅ Processed {variable} {year}: {len(df)} counties → {output_file.name}"
            )

            return output_file

        except Exception as e:
            logger.error(f"Error processing {variable} {year}: {e}")
            logger.exception("Full error:")
            return None

    def _transform_to_county_level(
        self,
        df: pl.DataFrame,
        variable: str,
        year: int,
    ) -> Optional[pl.DataFrame]:
        """
        Transform EPA AQS data to county level.

        Args:
            df: Raw EPA AQS data
            variable: Parameter name
            year: Year

        Returns:
            Transformed DataFrame with county-level data
        """
        try:
            # Check required columns
            required_cols = ["state_code", "county_code", "arithmetic_mean"]
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                logger.debug(f"Available columns: {df.columns}")
                return None

            # Create FIPS code (zero-padded 5 digits)
            df = df.with_columns(
                [
                    # Ensure state and county codes are zero-padded
                    pl.col("state_code").cast(pl.Utf8).str.zfill(2).alias("State_FIPS"),
                    pl.col("county_code").cast(pl.Utf8).str.zfill(3).alias("County_FIPS"),
                ]
            )

            # Combine to create FIPS
            df = df.with_columns(
                (pl.col("State_FIPS") + pl.col("County_FIPS")).alias("FIPS")
            )

            # If multiple monitors in county, take mean
            df = df.group_by(["FIPS", "State_FIPS", "County_FIPS"]).agg(
                pl.col("arithmetic_mean").mean().alias("Value")
            )

            # Get unit from EPA AQS parameter definitions
            unit = self._get_unit(variable)

            # Add year and unit
            df = df.with_columns(
                [
                    pl.lit(year).alias("Year"),
                    pl.lit(unit).alias("Unit"),
                ]
            )

            # Join with FIPS metadata to get state/county names
            # Ensure FIPS types match (both should be strings)
            fips_metadata = self.fips_lookup.select(
                ["FIPS", "State_Name", "County_Name", "State_Abbrev"]
            ).with_columns(
                pl.col("FIPS").cast(pl.Utf8)
            )

            df = df.join(
                fips_metadata,
                on="FIPS",
                how="left",
            )

            # Select and order columns
            df = df.select(
                [
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
            )

            # Remove rows with missing state/county names (invalid FIPS)
            df = df.filter(pl.col("State_Name").is_not_null())

            logger.debug(f"Transformed to {len(df)} county records")

            return df

        except Exception as e:
            logger.error(f"Error in transformation: {e}")
            raise

    def _get_unit(self, variable: str) -> str:
        """
        Get unit for a variable.

        Args:
            variable: Parameter name

        Returns:
            Unit string
        """
        units = {
            "PM25": "μg/m³",
            "PM10": "μg/m³",
            "O3": "ppm",
            "NO2": "ppb",
            "SO2": "ppb",
            "CO": "ppm",
        }
        return units.get(variable, "unknown")

    def process_all_cached(
        self,
        force_refresh: bool = False,
    ) -> Dict[str, int]:
        """
        Process all cached EPA AQS files.

        Args:
            force_refresh: Force re-processing

        Returns:
            Dictionary with statistics (success_count, fail_count)
        """
        logger.info("=" * 70)
        logger.info("PROCESSING ALL CACHED EPA AQS FILES")
        logger.info("=" * 70)

        # Find all cached files
        if not self.cache_dir.exists():
            logger.warning(f"Cache directory does not exist: {self.cache_dir}")
            return {"success": 0, "failed": 0}

        cached_files = list(self.cache_dir.glob("*_raw.csv"))
        logger.info(f"Found {len(cached_files)} cached files")

        if len(cached_files) == 0:
            logger.warning(
                "No cached files found. Download data first with: "
                "python scripts/03_download_source.py --source epa_aqs"
            )
            return {"success": 0, "failed": 0}

        # Process each file
        success_count = 0
        fail_count = 0

        for cache_file in sorted(cached_files):
            # Parse filename: {variable}_{year}_raw.csv
            filename = cache_file.stem  # Remove .csv
            parts = filename.rsplit("_", 2)  # Split from right

            if len(parts) != 3:
                logger.warning(f"Cannot parse filename: {cache_file.name}")
                fail_count += 1
                continue

            variable = parts[0]
            year = int(parts[1])

            try:
                output_file = self.process_variable_year(
                    variable=variable,
                    year=year,
                    force_refresh=force_refresh,
                )

                if output_file is not None:
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                logger.error(f"Error processing {cache_file.name}: {e}")
                fail_count += 1
                continue

        logger.info("=" * 70)
        logger.info(f"PROCESSING COMPLETE: {success_count} succeeded, {fail_count} failed")
        logger.info("=" * 70)

        return {"success": success_count, "failed": fail_count}
