"""
IPUMS NHGIS Data Processor.

Converts IPUMS NHGIS cached ZIP files to standardized county-level TSV files.

IPUMS NHGIS provides hundreds of variables per dataset, organized in wide-format CSV files.
This processor:
1. Extracts ZIP files
2. Reads CSV data
3. Converts GISJOIN to FIPS codes
4. Transforms wide format to long format (one variable per TSV)
5. Creates standardized TSV files with FIPS metadata

Design Patterns:
- Strategy: Different extraction strategies for different dataset formats
- Template Method: Standard processing workflow
"""

import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import polars as pl
from loguru import logger

from core.metadata_manager import MetadataManager
from core.tsv_generator import TSVGenerator
from utils.constants import CACHE_DIR, PROCESSED_DIR
from utils.file_utils import ensure_directory, read_tsv, write_tsv


# ============================================================================
# IPUMS NHGIS PROCESSOR
# ============================================================================


class IPUMSNHGISProcessor:
    """
    Processor for IPUMS NHGIS data.

    Converts raw IPUMS NHGIS ZIP extracts to standardized county-level TSV files.
    """

    def __init__(self):
        """Initialize IPUMS NHGIS processor."""
        self.source_id = "ipums_nhgis"
        self.category = "02_DEMOGRAPHICS_SOCIAL"
        self.cache_dir = CACHE_DIR / self.category / self.source_id
        self.processed_dir = PROCESSED_DIR / self.category

        # Initialize components
        self.metadata_manager = MetadataManager()
        self.tsv_generator = TSVGenerator()

        # Load FIPS codes
        self.fips_lookup = self.metadata_manager.get_fips_codes()

        logger.info(f"IPUMS NHGIS processor initialized")

    def _gisjoin_to_fips(self, gisjoin: str) -> Optional[str]:
        """
        Convert GISJOIN to FIPS code.

        GISJOIN format: G[STATE][COUNTY]
        Example: G0100010 -> 01001

        Args:
            gisjoin: GISJOIN code

        Returns:
            5-digit FIPS code or None
        """
        if not gisjoin or len(gisjoin) < 8:
            return None

        try:
            # Remove 'G' prefix and extract state/county
            state = gisjoin[1:3]  # Characters 1-2
            county = gisjoin[4:7]  # Characters 4-6
            fips = state + county
            return fips
        except Exception:
            return None

    def process_zip_file(
        self,
        zip_path: Path,
        force_refresh: bool = False,
    ) -> Dict[str, int]:
        """
        Process single IPUMS NHGIS ZIP file.

        Args:
            zip_path: Path to ZIP file
            force_refresh: Force re-processing

        Returns:
            Dictionary with statistics
        """
        logger.info(f"Processing: {zip_path.name}")

        success_count = 0
        fail_count = 0

        try:
            # Extract ZIP to temporary location
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Find CSV file(s) inside
                csv_files = [f for f in zf.namelist() if f.endswith('.csv')]

                if not csv_files:
                    logger.warning(f"No CSV files found in {zip_path.name}")
                    return {"success": 0, "failed": 1}

                for csv_file in csv_files:
                    logger.debug(f"Extracting {csv_file}")

                    # Read CSV directly from ZIP
                    # IPUMS CSV has 2-row header:
                    # Row 1: Column names (GISJOIN, YEAR, etc.)
                    # Row 2: Descriptions ("GIS Join Match Code", "Data File Year", etc.)
                    # Row 3+: Actual data
                    # IPUMS uses multiple null markers: ".", "##", "####", "N", etc.
                    # Strategy: Read all columns as strings first, then handle nulls flexibly
                    with zf.open(csv_file) as f:
                        df = pl.read_csv(
                            f,
                            skip_rows_after_header=1,
                            null_values=[".", "##", "####", "######", "N", "NA", "null", "NULL", ""],
                            infer_schema_length=10000,  # Scan more rows for type inference
                            try_parse_dates=False  # Don't auto-parse dates to avoid errors
                        )

                    # Convert GISJOIN to FIPS
                    if "GISJOIN" not in df.columns:
                        logger.error(f"No GISJOIN column in {csv_file}")
                        fail_count += 1
                        continue

                    # Add FIPS column
                    df = df.with_columns(
                        pl.col("GISJOIN").map_elements(
                            self._gisjoin_to_fips,
                            return_dtype=pl.Utf8
                        ).alias("FIPS")
                    )

                    # Filter to county level only
                    df = df.filter(pl.col("FIPS").is_not_null())

                    if len(df) == 0:
                        logger.warning(f"No county-level data in {csv_file}")
                        fail_count += 1
                        continue

                    # Get year from YEAR column or filename
                    year = self._extract_year(df, zip_path.name)

                    # Process each variable column
                    variable_cols = self._identify_variable_columns(df)

                    logger.info(f"Found {len(variable_cols)} variables in {csv_file}")

                    for var_col in variable_cols:  # Process ALL variables
                        try:
                            var_df = self._create_variable_tsv(
                                df, var_col, year, force_refresh
                            )
                            if var_df is not None:
                                success_count += 1
                        except Exception as e:
                            logger.error(f"Error processing variable {var_col}: {e}")
                            fail_count += 1

        except Exception as e:
            logger.error(f"Error processing {zip_path.name}: {e}")
            fail_count += 1

        return {"success": success_count, "failed": fail_count}

    def _extract_year(self, df: pl.DataFrame, filename: str) -> int:
        """Extract year from data or filename."""
        # Try YEAR column first
        if "YEAR" in df.columns:
            return int(df["YEAR"][0])

        # Try filename: e.g., "2023_ACS1_2023_extract.zip"
        parts = filename.split("_")
        if parts and parts[0].isdigit() and len(parts[0]) == 4:
            return int(parts[0])

        return 0

    def _identify_variable_columns(self, df: pl.DataFrame) -> List[str]:
        """
        Identify data variable columns (exclude metadata columns).

        Returns list of column names that contain actual data variables.
        """
        # Metadata columns to exclude
        metadata_cols = {
            "GISJOIN", "YEAR", "STUSAB", "REGIONA", "DIVISIONA", "STATE",
            "STATEA", "COUNTY", "COUNTYA", "FIPS", "GEO_ID", "TL_GEO_ID",
            "NAME_E", "NAME_M"
        }

        variable_cols = [
            col for col in df.columns
            if col not in metadata_cols and not col.endswith("_M")  # Exclude margin of error columns
        ]

        return variable_cols

    def _create_variable_tsv(
        self,
        df: pl.DataFrame,
        variable: str,
        year: int,
        force_refresh: bool,
    ) -> Optional[pl.DataFrame]:
        """Create TSV file for single variable."""
        # Check if output already exists
        dataset_name = "NHGIS"  # Simplified for now
        variable_dir = self.processed_dir / dataset_name / variable
        ensure_directory(variable_dir)
        output_file = variable_dir / f"{year}_{variable}.tsv"

        if output_file.exists() and not force_refresh:
            logger.debug(f"Output exists: {output_file.name}")
            return None

        # Select relevant columns
        var_df = df.select(["FIPS", variable])

        # Rename variable column to "Value"
        var_df = var_df.rename({variable: "Value"})

        # Add State_FIPS and County_FIPS
        var_df = var_df.with_columns([
            pl.col("FIPS").str.slice(0, 2).alias("State_FIPS"),
            pl.col("FIPS").str.slice(2, 3).alias("County_FIPS"),
        ])

        # Join with FIPS metadata
        fips_metadata = self.fips_lookup.select(
            ["FIPS", "State_Name", "County_Name", "State_Abbrev"]
        ).with_columns(pl.col("FIPS").cast(pl.Utf8))

        var_df = var_df.join(fips_metadata, on="FIPS", how="left")

        # Add year and unit
        var_df = var_df.with_columns([
            pl.lit(year).alias("Year"),
            pl.lit("count").alias("Unit"),  # Most NHGIS variables are counts
        ])

        # Select final columns in correct order
        var_df = var_df.select([
            "FIPS", "State_FIPS", "County_FIPS",
            "State_Name", "County_Name", "State_Abbrev",
            "Year", "Value", "Unit"
        ])

        # Remove nulls
        var_df = var_df.filter(pl.col("State_Name").is_not_null())

        # Write TSV
        write_tsv(var_df, output_file)
        logger.info(f"✅ Created: {output_file.name} ({len(var_df)} counties)")

        return var_df

    def process_all_cached(
        self,
        force_refresh: bool = False,
        limit: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        Process all cached IPUMS NHGIS files.

        Args:
            force_refresh: Force re-processing
            limit: Limit number of ZIP files to process

        Returns:
            Dictionary with statistics
        """
        logger.info("=" * 70)
        logger.info("PROCESSING ALL CACHED IPUMS NHGIS FILES")
        logger.info("=" * 70)

        # Find all cached ZIP files
        if not self.cache_dir.exists():
            logger.warning(f"Cache directory does not exist: {self.cache_dir}")
            return {"success": 0, "failed": 0}

        cached_files = sorted(list(self.cache_dir.glob("*.zip")))

        if limit:
            cached_files = cached_files[:limit]

        logger.info(f"Found {len(cached_files)} cached ZIP files")

        if len(cached_files) == 0:
            logger.warning("No cached files found")
            return {"success": 0, "failed": 0}

        # Process each ZIP file
        total_success = 0
        total_failed = 0

        for i, zip_file in enumerate(cached_files, 1):
            logger.info(f"[{i}/{len(cached_files)}] {zip_file.name}")

            stats = self.process_zip_file(zip_file, force_refresh)

            total_success += stats["success"]
            total_failed += stats["failed"]

        logger.info("=" * 70)
        logger.info(f"PROCESSING COMPLETE: {total_success} variables, {total_failed} failed")
        logger.info("=" * 70)

        return {"success": total_success, "failed": total_failed}


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "IPUMSNHGISProcessor",
]
