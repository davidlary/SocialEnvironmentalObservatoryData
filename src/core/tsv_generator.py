"""
TSV Generator with FIPS metadata integration.

Creates standardized TSV files with required columns:
- FIPS (5-digit)
- State_FIPS (2-digit)
- County_FIPS (3-digit)
- State_Name
- County_Name
- State_Abbrev
- Year
- Value
- Unit

Every TSV file has identical structure for easy joining and analysis.

Design Patterns:
- Template Method: Standard TSV creation workflow
- Builder: Construct TSV step-by-step with validation
"""

from pathlib import Path
from typing import Optional, Union

import polars as pl
from loguru import logger

from core.metadata_manager import get_fips_codes
from utils.constants import (
    PROCESSED_DIR,
    TSV_DELIMITER,
    TSV_ENCODING,
    TSV_NA_VALUE,
    TSV_REQUIRED_COLUMNS,
)
from utils.file_utils import (
    ensure_directory,
    get_tsv_schema,
    validate_tsv_schema,
    write_tsv,
)


# ============================================================================
# TSV GENERATOR
# ============================================================================


class TSVGenerator:
    """
    Generate standardized TSV files with FIPS metadata.

    Workflow:
    1. Load raw data (from cache or processor)
    2. Ensure FIPS column exists
    3. Join with FIPS metadata
    4. Add year and unit columns
    5. Validate structure
    6. Write to standardized location
    """

    def __init__(self):
        """Initialize TSV generator."""
        self.fips_metadata = None
        logger.debug("TSV generator initialized")

    def _load_fips_metadata(self) -> pl.DataFrame:
        """
        Load FIPS metadata (cached).

        Returns:
            Polars DataFrame with FIPS codes and metadata
        """
        if self.fips_metadata is None:
            logger.info("Loading FIPS metadata for TSV generation")
            self.fips_metadata = get_fips_codes()

        return self.fips_metadata

    def create_tsv(
        self,
        data: pl.DataFrame,
        category: str,
        variable: str,
        year: int,
        unit: str,
        value_column: str = "value",
        fips_column: str = "FIPS",
    ) -> Path:
        """
        Create standardized TSV file.

        Args:
            data: Polars DataFrame with county-level data
            category: Data category (e.g., "01_AIR_ATMOSPHERE")
            variable: Variable name (e.g., "PM25_Annual_Mean")
            year: Year
            unit: Unit of measurement (e.g., "μg/m³")
            value_column: Name of value column in input data
            fips_column: Name of FIPS column in input data

        Returns:
            Path to created TSV file

        Example:
            >>> generator = TSVGenerator()
            >>> data = pl.DataFrame({
            ...     "FIPS": ["48453", "06037"],
            ...     "value": [8.5, 12.3]
            ... })
            >>> tsv_path = generator.create_tsv(
            ...     data,
            ...     "01_AIR_ATMOSPHERE",
            ...     "PM25_Annual_Mean",
            ...     2020,
            ...     "μg/m³"
            ... )
        """
        logger.info(f"Creating TSV: {category}/{variable}/{year}")

        # Validate input data
        if fips_column not in data.columns:
            raise ValueError(f"Input data missing FIPS column: {fips_column}")

        if value_column not in data.columns:
            raise ValueError(f"Input data missing value column: {value_column}")

        # Ensure FIPS is string with proper padding
        data = data.with_columns(
            pl.col(fips_column).cast(pl.Utf8).str.zfill(5).alias("FIPS")
        )

        # Rename value column if needed
        if value_column != "Value":
            data = data.rename({value_column: "Value"})

        # Join with FIPS metadata
        fips_metadata = self._load_fips_metadata()

        tsv_data = data.join(
            fips_metadata,
            on="FIPS",
            how="left",
        )

        # Add year and unit columns
        tsv_data = tsv_data.with_columns([
            pl.lit(year).alias("Year"),
            pl.lit(unit).alias("Unit"),
        ])

        # Select required columns in correct order
        tsv_data = tsv_data.select(TSV_REQUIRED_COLUMNS)

        # Validate schema
        try:
            validate_tsv_schema(tsv_data)
        except ValueError as e:
            logger.error(f"TSV schema validation failed: {e}")
            raise

        # Check for missing FIPS metadata
        null_fips = tsv_data.filter(pl.col("State_Name").is_null())
        if len(null_fips) > 0:
            logger.warning(
                f"Found {len(null_fips)} counties with missing FIPS metadata"
            )
            logger.debug(f"Missing FIPS: {null_fips['FIPS'].to_list()}")

        # Determine output path
        output_dir = PROCESSED_DIR / category / variable
        ensure_directory(output_dir)
        output_path = output_dir / f"{year}_{variable}.tsv"

        # Write TSV
        write_tsv(tsv_data, output_path)

        logger.info(
            f"✅ Created TSV: {output_path.name} "
            f"({len(tsv_data)} counties)"
        )

        return output_path

    def create_tsv_from_csv(
        self,
        csv_path: Union[str, Path],
        category: str,
        variable: str,
        year: int,
        unit: str,
        value_column: str = "value",
        fips_column: str = "FIPS",
    ) -> Path:
        """
        Create TSV from cached CSV file.

        Convenience method that loads CSV and creates TSV.

        Args:
            csv_path: Path to CSV file
            category: Data category
            variable: Variable name
            year: Year
            unit: Unit
            value_column: Name of value column
            fips_column: Name of FIPS column

        Returns:
            Path to created TSV file

        Example:
            >>> generator = TSVGenerator()
            >>> tsv_path = generator.create_tsv_from_csv(
            ...     "data/cache/epa_aqs/2020_data.csv",
            ...     "01_AIR_ATMOSPHERE",
            ...     "PM25_Annual_Mean",
            ...     2020,
            ...     "μg/m³"
            ... )
        """
        csv_path = Path(csv_path)

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        logger.info(f"Loading data from {csv_path}")

        # Load CSV with Polars (fast!)
        data = pl.read_csv(csv_path)

        logger.debug(f"Loaded {len(data)} rows from CSV")

        # Create TSV
        return self.create_tsv(
            data,
            category,
            variable,
            year,
            unit,
            value_column,
            fips_column,
        )

    def create_multi_year_tsvs(
        self,
        data: pl.DataFrame,
        category: str,
        variable: str,
        unit: str,
        year_column: str = "Year",
        value_column: str = "value",
        fips_column: str = "FIPS",
    ) -> list[Path]:
        """
        Create TSV files for multiple years from single DataFrame.

        Useful when cached data contains multiple years.

        Args:
            data: Polars DataFrame with multi-year data
            category: Data category
            variable: Variable name
            unit: Unit
            year_column: Name of year column
            value_column: Name of value column
            fips_column: Name of FIPS column

        Returns:
            List of paths to created TSV files

        Example:
            >>> # Data with years 2015-2020
            >>> data = pl.DataFrame({
            ...     "FIPS": ["48453"] * 6,
            ...     "Year": list(range(2015, 2021)),
            ...     "value": [8.5, 8.3, 8.1, 7.9, 7.7, 7.5]
            ... })
            >>> generator = TSVGenerator()
            >>> tsv_paths = generator.create_multi_year_tsvs(
            ...     data,
            ...     "01_AIR_ATMOSPHERE",
            ...     "PM25_Annual_Mean",
            ...     "μg/m³"
            ... )
            >>> print(len(tsv_paths))  # 6 (one per year)
        """
        if year_column not in data.columns:
            raise ValueError(f"Data missing year column: {year_column}")

        years = sorted(data[year_column].unique().to_list())
        logger.info(
            f"Creating TSV files for {len(years)} years: {years[0]}-{years[-1]}"
        )

        tsv_paths = []

        for year in years:
            # Filter data for this year
            year_data = data.filter(pl.col(year_column) == year)

            # Drop year column (will be added by create_tsv)
            year_data = year_data.drop(year_column)

            try:
                tsv_path = self.create_tsv(
                    year_data,
                    category,
                    variable,
                    year,
                    unit,
                    value_column,
                    fips_column,
                )
                tsv_paths.append(tsv_path)

            except Exception as e:
                logger.error(f"Error creating TSV for year {year}: {e}")
                # Continue with other years

        logger.info(f"✅ Created {len(tsv_paths)}/{len(years)} TSV files")

        return tsv_paths

    def validate_existing_tsv(self, tsv_path: Union[str, Path]) -> bool:
        """
        Validate an existing TSV file.

        Args:
            tsv_path: Path to TSV file

        Returns:
            True if valid, False otherwise

        Example:
            >>> generator = TSVGenerator()
            >>> is_valid = generator.validate_existing_tsv(
            ...     "data/processed/.../2020_PM25_Annual_Mean.tsv"
            ... )
            >>> if not is_valid:
            ...     regenerate_tsv()
        """
        tsv_path = Path(tsv_path)

        if not tsv_path.exists():
            logger.error(f"TSV file not found: {tsv_path}")
            return False

        try:
            # Load TSV
            df = pl.read_csv(
                tsv_path,
                separator=TSV_DELIMITER,
                null_values=TSV_NA_VALUE,
            )

            # Validate schema
            validate_tsv_schema(df)

            # Check for data
            if len(df) == 0:
                logger.error(f"TSV file is empty: {tsv_path}")
                return False

            # Check for null FIPS
            null_fips = df.filter(pl.col("FIPS").is_null())
            if len(null_fips) > 0:
                logger.warning(
                    f"TSV has {len(null_fips)} rows with null FIPS: {tsv_path}"
                )

            logger.debug(f"✅ TSV validation passed: {tsv_path}")
            return True

        except Exception as e:
            logger.error(f"TSV validation failed: {e}")
            return False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_tsv_generator = None


def get_tsv_generator() -> TSVGenerator:
    """Get TSV generator (singleton)."""
    global _tsv_generator
    if _tsv_generator is None:
        _tsv_generator = TSVGenerator()
    return _tsv_generator


def create_tsv(
    data: pl.DataFrame,
    category: str,
    variable: str,
    year: int,
    unit: str,
    **kwargs,
) -> Path:
    """Create TSV (convenience function)."""
    generator = get_tsv_generator()
    return generator.create_tsv(data, category, variable, year, unit, **kwargs)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "TSVGenerator",
    "get_tsv_generator",
    "create_tsv",
]
