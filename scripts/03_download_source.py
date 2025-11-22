#!/usr/bin/env python3
"""
Download Data from a Specific Source.

This is the MAIN DOWNLOADER script that orchestrates data acquisition.

Usage:
    # Download specific source
    python scripts/03_download_source.py --source epa_aqs

    # Download specific category
    python scripts/03_download_source.py --category 01_AIR_ATMOSPHERE

    # Download all sources (WARNING: takes days/weeks!)
    python scripts/03_download_source.py --all

    # Download specific variable/year
    python scripts/03_download_source.py --source epa_aqs --variable PM25 --years 2020 2021

    # Force refresh (re-download even if cached)
    python scripts/03_download_source.py --source epa_aqs --force-refresh
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import get_logger, setup_logging
from core.progress_tracker import ProgressTracker
from utils.constants import CONFIG_DIR, SYSTEM_NAME, SYSTEM_VERSION
from utils.file_utils import read_json_file

# Import downloaders
from downloaders.python.epa_aqs_downloader import EPAAQSDownloader


# ============================================================================
# DOWNLOADER REGISTRY
# ============================================================================

DOWNLOADER_REGISTRY = {
    "epa_aqs": EPAAQSDownloader,
    # Add more downloaders here as implemented
}


# ============================================================================
# MAIN DOWNLOAD LOGIC
# ============================================================================


def download_source(
    source_id: str,
    variables: Optional[List[str]] = None,
    years: Optional[List[int]] = None,
    force_refresh: bool = False,
) -> bool:
    """
    Download data from a specific source.

    Args:
        source_id: Source identifier (e.g., "epa_aqs")
        variables: Specific variables to download (None = all)
        years: Specific years to download (None = all)
        force_refresh: Force re-download even if cached

    Returns:
        True if successful, False otherwise
    """
    logger = get_logger()
    logger.info("=" * 70)
    logger.info(f"DOWNLOADING SOURCE: {source_id}")
    logger.info("=" * 70)

    # Check if downloader exists
    if source_id not in DOWNLOADER_REGISTRY:
        logger.error(
            f"Unknown source: {source_id}. "
            f"Available: {list(DOWNLOADER_REGISTRY.keys())}"
        )
        return False

    try:
        # Initialize downloader
        downloader_class = DOWNLOADER_REGISTRY[source_id]
        downloader = downloader_class()

        # Get variables to download
        if variables is None:
            if hasattr(downloader, "get_all_parameters"):
                variables = downloader.get_all_parameters()
            else:
                logger.error(
                    f"No variables specified and downloader doesn't support "
                    f"get_all_parameters()"
                )
                return False

        logger.info(f"Variables to download: {variables}")

        # Download each variable
        for variable in variables:
            logger.info("-" * 70)
            logger.info(f"Downloading variable: {variable}")
            logger.info("-" * 70)

            try:
                # Get available years
                if years is None:
                    available_years = downloader.get_available_years(variable)
                else:
                    available_years = years

                logger.info(
                    f"Years: {available_years[0]}-{available_years[-1]} "
                    f"({len(available_years)} total)"
                )

                # Download each year
                success_count = 0
                fail_count = 0

                for year in available_years:
                    try:
                        logger.info(f"  Downloading {variable} {year}...")
                        cached_file = downloader.download_variable_year(
                            variable=variable,
                            year=year,
                            force_refresh=force_refresh,
                        )
                        logger.info(f"  ✅ {variable} {year} → {cached_file.name}")
                        success_count += 1

                    except Exception as e:
                        logger.error(f"  ❌ {variable} {year} failed: {e}")
                        fail_count += 1
                        continue

                logger.info(
                    f"Variable {variable} complete: "
                    f"{success_count} succeeded, {fail_count} failed"
                )

            except Exception as e:
                logger.error(f"Error downloading variable {variable}: {e}")
                continue

        logger.info("=" * 70)
        logger.info(f"Source {source_id} download complete")
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.error(f"Error downloading source {source_id}: {e}")
        logger.exception("Full error:")
        return False


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Download data from observatory sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download EPA AQS data (all parameters, all years)
  python scripts/03_download_source.py --source epa_aqs

  # Download specific parameter and years
  python scripts/03_download_source.py --source epa_aqs --variable PM25 --years 2020 2021 2022

  # Force re-download (ignore cache)
  python scripts/03_download_source.py --source epa_aqs --force-refresh

  # Download all sources in category
  python scripts/03_download_source.py --category 01_AIR_ATMOSPHERE

  # Download ALL sources (WARNING: takes very long!)
  python scripts/03_download_source.py --all
""",
    )

    # Source selection
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--source",
        type=str,
        help=f"Source ID to download (e.g., 'epa_aqs'). Available: {list(DOWNLOADER_REGISTRY.keys())}",
    )
    source_group.add_argument(
        "--category",
        type=str,
        help="Download all sources in category (e.g., '01_AIR_ATMOSPHERE')",
    )
    source_group.add_argument(
        "--all",
        action="store_true",
        help="Download ALL sources (WARNING: takes days/weeks!)",
    )

    # Variable/year filtering
    parser.add_argument(
        "--variable",
        "--variables",
        type=str,
        nargs="+",
        help="Specific variables to download (default: all)",
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        help="Specific years to download (default: all)",
    )

    # Options
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force re-download even if cached",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level)
    logger = get_logger()

    logger.info("=" * 70)
    logger.info(f"{SYSTEM_NAME} v{SYSTEM_VERSION}")
    logger.info("DATA DOWNLOAD")
    logger.info("=" * 70)

    try:
        # Determine which sources to download
        if args.source:
            sources = [args.source]
        elif args.category:
            # TODO: Implement category-based source lookup
            logger.error("Category-based download not yet implemented")
            logger.info("Please use --source instead")
            sys.exit(1)
        elif args.all:
            # TODO: Implement all-sources download
            logger.error("All-sources download not yet implemented")
            logger.info("Please use --source instead")
            sys.exit(1)
        else:
            logger.error("No source, category, or --all specified")
            sys.exit(1)

        # Download each source
        all_success = True
        for source in sources:
            success = download_source(
                source_id=source,
                variables=args.variable,
                years=args.years,
                force_refresh=args.force_refresh,
            )

            if not success:
                all_success = False

        # Print summary
        logger.info("=" * 70)
        if all_success:
            logger.info("✅ All downloads completed successfully")
        else:
            logger.warning("⚠️ Some downloads failed (see errors above)")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Run: python scripts/04_process_cached_data.py")
        logger.info("     (Process downloaded files to TSV format)")
        logger.info("  2. Run: python scripts/05_generate_maps.py")
        logger.info("     (Generate choropleth maps)")
        logger.info("=" * 70)

        sys.exit(0 if all_success else 1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Download interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        logger.exception("Full error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
