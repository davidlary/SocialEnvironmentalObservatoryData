"""
Test EPA AQS Pipeline (Processor + Map Generator).

Creates synthetic EPA AQS data to test the processing and mapping pipeline.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import polars as pl
from loguru import logger

from core.metadata_manager import MetadataManager
from processors.epa_aqs_processor import EPAAQSProcessor
from core.map_generator import MapGenerator
from utils.constants import CACHE_DIR, PROCESSED_DIR
from utils.file_utils import ensure_directory, write_tsv


def create_synthetic_epa_aqs_data(
    variable: str = "PM25",
    year: int = 2020,
    num_counties: int = 100,
) -> Path:
    """
    Create synthetic EPA AQS data for testing.

    Args:
        variable: Parameter name
        year: Year
        num_counties: Number of counties to include

    Returns:
        Path to synthetic cache file
    """
    logger.info(f"Creating synthetic {variable} data for {year}...")

    # Get FIPS codes
    metadata_mgr = MetadataManager()
    fips_df = metadata_mgr.get_fips_codes()

    # Sample random counties
    sampled = fips_df.sample(n=min(num_counties, len(fips_df)), seed=42)

    # Create synthetic EPA AQS format data
    synthetic_data = []

    for row in sampled.iter_rows(named=True):
        state_fips = row["State_FIPS"]
        county_fips = row["County_FIPS"]

        # Generate realistic values based on parameter
        if variable == "PM25":
            # PM2.5 typically ranges 3-15 μg/m³
            import random
            random.seed(int(state_fips) * 1000 + int(county_fips) + year)
            value = random.uniform(3.0, 15.0)
        else:
            value = 10.0

        synthetic_data.append({
            "state_code": state_fips,
            "county_code": county_fips,
            "arithmetic_mean": value,
            "arithmetic_standard_dev": value * 0.1,
            "observation_count": 365,
            "observation_percent": 100.0,
            "completeness_indicator": "Y",
            "parameter_code": "88101" if variable == "PM25" else "81102",
            "parameter": variable,
            "units_of_measure": "Micrograms/cubic meter (LC)",
            "year": year,
        })

    # Create DataFrame
    df = pl.DataFrame(synthetic_data)

    # Save to cache directory
    cache_dir = CACHE_DIR / "01_AIR_ATMOSPHERE" / "epa_aqs"
    ensure_directory(cache_dir)
    cache_file = cache_dir / f"{variable}_{year}_raw.csv"

    write_tsv(df, cache_file)
    logger.info(f"Created synthetic data: {cache_file} ({len(df)} counties)")

    return cache_file


def test_epa_aqs_pipeline():
    """Test complete EPA AQS pipeline with synthetic data."""
    logger.info("=" * 70)
    logger.info("TESTING EPA AQS PIPELINE")
    logger.info("=" * 70)

    # Test parameters
    variables = ["PM25"]
    years = [2020, 2021, 2022]

    # Step 1: Create synthetic cached data
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1: Creating Synthetic Cached Data")
    logger.info("=" * 70)

    for variable in variables:
        for year in years:
            create_synthetic_epa_aqs_data(
                variable=variable,
                year=year,
                num_counties=100,  # Sample of counties
            )

    # Step 2: Process cached data to TSV
    logger.info("\n" + "=" * 70)
    logger.info("STEP 2: Processing Cached Data to TSV")
    logger.info("=" * 70)

    processor = EPAAQSProcessor()
    stats = processor.process_all_cached(force_refresh=True)

    logger.info(f"\nProcessing Results:")
    logger.info(f"  Success: {stats['success']}")
    logger.info(f"  Failed: {stats['failed']}")

    if stats['failed'] > 0:
        logger.error("Processing failed!")
        return False

    # Step 3: Generate maps
    logger.info("\n" + "=" * 70)
    logger.info("STEP 3: Generating Maps")
    logger.info("=" * 70)

    # Find TSV files
    processed_dir = PROCESSED_DIR / "01_AIR_ATMOSPHERE"
    tsv_files = list(processed_dir.glob("**/*.tsv"))

    logger.info(f"Found {len(tsv_files)} TSV files")

    if len(tsv_files) == 0:
        logger.error("No TSV files found!")
        return False

    # Generate maps
    map_gen = MapGenerator()
    success_count = 0
    fail_count = 0

    for tsv_path in tsv_files:
        try:
            map_path = tsv_path.with_suffix(".png")
            logger.info(f"Generating map: {tsv_path.name}")

            map_gen.create_map(
                tsv_path=tsv_path,
                output_path=map_path,
            )

            logger.info(f"  ✅ Created: {map_path.name}")
            success_count += 1

        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            fail_count += 1

    # Step 4: Verify outputs
    logger.info("\n" + "=" * 70)
    logger.info("STEP 4: Verification")
    logger.info("=" * 70)

    expected_files = len(variables) * len(years)
    logger.info(f"Expected TSV files: {expected_files}")
    logger.info(f"Found TSV files: {len(tsv_files)}")
    logger.info(f"Expected maps: {expected_files}")
    logger.info(f"Generated maps: {success_count}")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)

    all_success = (
        stats['failed'] == 0
        and len(tsv_files) == expected_files
        and success_count == expected_files
        and fail_count == 0
    )

    if all_success:
        logger.info("✅ ALL TESTS PASSED")
        logger.info("")
        logger.info("Output files:")
        for tsv_path in sorted(tsv_files):
            logger.info(f"  TSV: {tsv_path.relative_to(PROCESSED_DIR)}")
            map_path = tsv_path.with_suffix(".png")
            if map_path.exists():
                logger.info(f"  MAP: {map_path.relative_to(PROCESSED_DIR)}")
    else:
        logger.error("❌ SOME TESTS FAILED")

    logger.info("=" * 70)

    return all_success


if __name__ == "__main__":
    from core.logger import setup_logging

    setup_logging(log_level="INFO")
    success = test_epa_aqs_pipeline()
    sys.exit(0 if success else 1)
