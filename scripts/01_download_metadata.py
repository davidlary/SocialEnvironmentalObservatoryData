#!/usr/bin/env python3
"""
Download Essential Metadata

Downloads and validates:
1. Census Bureau FIPS codes (all 3,143 US counties)
2. TIGER/Line county boundaries (2020 vintage)
3. Validates metadata completeness

This must run BEFORE any data download scripts.

Usage:
    python scripts/01_download_metadata.py
    python scripts/01_download_metadata.py --year 2020 --force-refresh
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import setup_logging, get_logger
from core.metadata_manager import MetadataManager
from utils.constants import METADATA_DIR, TOTAL_US_COUNTIES


# ============================================================================
# METADATA DOWNLOAD FUNCTIONS
# ============================================================================


def download_fips_codes(force_refresh: bool = False):
    """
    Download FIPS codes from Census Bureau.

    Args:
        force_refresh: If True, re-download even if cached
    """
    logger.info("=" * 70)
    logger.info("Step 1: Downloading FIPS Codes")
    logger.info("=" * 70)

    manager = MetadataManager()

    try:
        fips_df = manager.download_fips_codes(force_refresh=force_refresh)

        logger.info(f"✅ Downloaded {len(fips_df)} FIPS codes")

        # Display sample
        logger.info("\nSample FIPS codes:")
        sample = fips_df.head(5).to_pandas()
        for idx, row in sample.iterrows():
            logger.info(
                f"  {row['FIPS']}: {row['County_Name']}, {row['State_Name']}"
            )

        # Validate count
        if len(fips_df) == TOTAL_US_COUNTIES:
            logger.info(f"✅ Count validation passed ({TOTAL_US_COUNTIES} counties)")
        else:
            logger.warning(
                f"⚠️ Expected {TOTAL_US_COUNTIES} counties, got {len(fips_df)}"
            )

        return fips_df

    except Exception as e:
        logger.error(f"❌ Failed to download FIPS codes: {e}")
        raise


def download_county_boundaries(year: int = 2020, force_refresh: bool = False):
    """
    Download county boundaries from Census TIGER/Line.

    Args:
        year: Census year
        force_refresh: If True, re-download even if cached
    """
    logger.info("=" * 70)
    logger.info(f"Step 2: Downloading County Boundaries ({year})")
    logger.info("=" * 70)

    manager = MetadataManager()

    try:
        boundaries = manager.download_county_boundaries(
            year=year, force_refresh=force_refresh
        )

        logger.info(f"✅ Downloaded {len(boundaries)} county boundaries")

        # Display sample
        logger.info("\nSample boundaries:")
        sample = boundaries.head(5)
        for idx, row in sample.iterrows():
            logger.info(
                f"  {row['GEOID']}: {row['NAME']} ({row['STATEFP']})"
            )

        # Validate count
        if len(boundaries) == TOTAL_US_COUNTIES:
            logger.info(f"✅ Count validation passed ({TOTAL_US_COUNTIES} counties)")
        else:
            logger.warning(
                f"⚠️ Expected {TOTAL_US_COUNTIES} counties, got {len(boundaries)}"
            )

        # Check CRS
        logger.info(f"CRS: {boundaries.crs}")

        return boundaries

    except Exception as e:
        logger.error(f"❌ Failed to download county boundaries: {e}")
        raise


def validate_metadata():
    """Validate metadata completeness and consistency."""
    logger.info("=" * 70)
    logger.info("Step 3: Validating Metadata")
    logger.info("=" * 70)

    manager = MetadataManager()

    try:
        results = manager.validate_metadata()

        logger.info(f"FIPS codes: {results['fips_count']}")
        logger.info(f"Boundaries: {results['boundaries_count']}")
        logger.info(f"Counts match: {results['fips_boundaries_match']}")

        if results.get("missing_in_boundaries"):
            logger.warning(
                f"FIPS codes missing in boundaries: "
                f"{len(results['missing_in_boundaries'])}"
            )

        if results.get("missing_in_fips"):
            logger.warning(
                f"Boundaries missing in FIPS: "
                f"{len(results['missing_in_fips'])}"
            )

        if results["all_valid"]:
            logger.info("✅ Metadata validation: PASSED")
        else:
            logger.warning("⚠️ Metadata validation: FAILED (see warnings above)")

        return results

    except Exception as e:
        logger.error(f"❌ Metadata validation failed: {e}")
        raise


def print_summary(fips_df, boundaries, validation_results):
    """Print summary of downloaded metadata."""
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)

    logger.info(f"\nFIPS Codes:")
    logger.info(f"  Count: {len(fips_df)}")
    logger.info(f"  Location: {METADATA_DIR / 'fips_codes_master.tsv'}")

    logger.info(f"\nCounty Boundaries:")
    logger.info(f"  Count: {len(boundaries)}")
    logger.info(f"  Location: {METADATA_DIR / 'county_boundaries_2020.gpkg'}")
    logger.info(f"  Format: GeoPackage")
    logger.info(f"  CRS: {boundaries.crs}")

    logger.info(f"\nValidation:")
    if validation_results["all_valid"]:
        logger.info("  Status: ✅ PASSED")
    else:
        logger.info("  Status: ⚠️ WARNING (see above)")

    logger.info("\nNext steps:")
    logger.info("  1. Run: python scripts/02_build_source_registry.py")
    logger.info("  2. Start downloading data with scripts/03_download_source.py")

    logger.info("=" * 70)


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main metadata download function."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Download essential metadata (FIPS codes, county boundaries)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2020,
        help="Census year for county boundaries (default: 2020)",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Re-download even if cached",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(log_level=args.log_level, enable_json=False, enable_console=True)

    global logger
    logger = get_logger()

    logger.info("=" * 70)
    logger.info("METADATA DOWNLOAD")
    logger.info("=" * 70)
    logger.info(f"Year: {args.year}")
    logger.info(f"Force refresh: {args.force_refresh}")
    logger.info("")

    try:
        # Step 1: Download FIPS codes
        fips_df = download_fips_codes(force_refresh=args.force_refresh)

        # Step 2: Download county boundaries
        boundaries = download_county_boundaries(
            year=args.year, force_refresh=args.force_refresh
        )

        # Step 3: Validate metadata
        validation_results = validate_metadata()

        # Print summary
        print_summary(fips_df, boundaries, validation_results)

        # Exit code based on validation
        if validation_results["all_valid"]:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Download interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Metadata download failed: {e}")
        logger.exception("Full error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
