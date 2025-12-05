#!/usr/bin/env python3
"""
Convert CSN processed CSV files to standard TSV format.

Input: data/cache/01_AIR_ATMOSPHERE/csn/processed/*.csv
Output: data/processed/01_AIR_ATMOSPHERE/CSN/CSN_{VARIABLE}_{YEAR}.tsv
"""

from pathlib import Path
import sys

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import polars as pl
from core.logger import setup_logging
from loguru import logger

# Setup logging
setup_logging()

def convert_csn_files():
    """Convert all CSN processed CSV files to TSV format."""

    # Paths
    input_dir = project_root / "data/cache/01_AIR_ATMOSPHERE/csn/processed"
    output_dir = project_root / "data/processed/01_AIR_ATMOSPHERE/CSN"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all CSV files
    csv_files = list(input_dir.glob("*.csv"))

    logger.info(f"Found {len(csv_files)} CSV files to convert")

    success_count = 0
    fail_count = 0

    for csv_file in sorted(csv_files):
        try:
            # Parse filename: variable_year.csv
            parts = csv_file.stem.split("_")
            variable = parts[0].upper()
            year = parts[1]

            # Read CSV
            df = pl.read_csv(csv_file)

            # Output filename: CSN_VARIABLE_YEAR.tsv
            output_file = output_dir / f"CSN_{variable}_{year}.tsv"

            # Write TSV
            df.write_csv(output_file, separator="\t")

            logger.info(f"✅ {csv_file.name} → {output_file.name}")
            success_count += 1

        except Exception as e:
            logger.error(f"❌ Failed to convert {csv_file.name}: {e}")
            fail_count += 1

    logger.info("=" * 70)
    logger.info(f"Conversion complete: {success_count} succeeded, {fail_count} failed")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 70)

if __name__ == "__main__":
    convert_csn_files()
