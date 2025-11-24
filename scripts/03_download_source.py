#!/usr/bin/env python3
"""
Download Data from a Specific Source.

This is the MAIN DOWNLOADER script that orchestrates data acquisition.

PHASE 3 ENHANCEMENTS (2025-11-24):
- Registry integration: Loads sources from config/sources_registry.json
- Category-based downloads: Download all sources in a category
- All-source downloads: Download all sources in priority order
- Dynamic downloader instantiation from registry
- Backward compatible: Still accepts short names (epa_aqs) or full registry IDs

Usage:
    # Download specific source (short name or registry ID)
    python scripts/03_download_source.py --source epa_aqs
    python scripts/03_download_source.py --source 01_EPA_AQS_AIR_QUALITY_SYSTEM_AMB

    # Download all sources in category
    python scripts/03_download_source.py --category 01_AIR_ATMOSPHERE

    # Download all sources (WARNING: takes days/weeks!)
    python scripts/03_download_source.py --all

    # Download specific variable/year
    python scripts/03_download_source.py --source epa_aqs --variable PM25 --years 2020 2021

    # Force refresh (re-download even if cached)
    python scripts/03_download_source.py --source epa_aqs --force-refresh

Registry Integration:
    The script now loads source metadata from config/sources_registry.json:
    - 104 sources across 8 categories
    - Priority-based ordering (1=highest, 5=lowest)
    - Automatic filtering of blocked/restricted/unimplemented sources
    - Dynamic downloader class instantiation via SOURCE_ID_MAPPINGS

Categories Available:
    01_AIR_ATMOSPHERE, 02_WATER, 04_TOXIC_CHEMICALS, 05_RADIATION,
    07_BUILT_ENVIRONMENT, 09_OCCUPATIONAL, 11_INFECTIOUS_DISEASE,
    19_ECONOMIC_INDICATORS
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
from downloaders.python.ipums_nhgis_downloader import IPUMSNHGISDownloader


# ============================================================================
# DOWNLOADER REGISTRY (Manual mapping: short_name → class)
# ============================================================================

DOWNLOADER_REGISTRY = {
    "epa_aqs": EPAAQSDownloader,
    "ipums_nhgis": IPUMSNHGISDownloader,
    # Add more downloaders here as implemented
}

# Source ID mappings: registry source_id → short_name used in DOWNLOADER_REGISTRY
SOURCE_ID_MAPPINGS = {
    "01_EPA_AQS_AIR_QUALITY_SYSTEM_AMB": "epa_aqs",
    "ipums_nhgis": "ipums_nhgis",  # Not yet in registry (from different source), backward compat
    # NOTE: ipums_nhgis has 58,243 variables operational but not in sources_registry.json
    # because it came from IPUMS directly, not from the companion repo used by Script 02
}


# ============================================================================
# REGISTRY LOADING FUNCTIONS
# ============================================================================


def load_sources_registry() -> dict:
    """
    Load sources from the registry JSON file.

    Returns:
        Dictionary with 'sources' key containing list of source records
    """
    logger = get_logger()
    registry_path = CONFIG_DIR / "sources_registry.json"

    if not registry_path.exists():
        logger.error(f"Registry not found: {registry_path}")
        return {"sources": []}

    try:
        registry = read_json_file(registry_path)
        logger.debug(f"Loaded {len(registry['sources'])} sources from registry")
        return registry
    except Exception as e:
        logger.error(f"Failed to load registry: {e}")
        return {"sources": []}


def get_sources_by_category(category: str) -> List[dict]:
    """
    Get all sources in a specific category.

    Args:
        category: Category ID (e.g., "01_AIR_ATMOSPHERE")

    Returns:
        List of source records matching the category
    """
    logger = get_logger()
    registry = load_sources_registry()
    sources = [s for s in registry["sources"] if s["category"] == category]
    logger.info(f"Found {len(sources)} sources in category {category}")
    return sources


def get_all_sources_by_priority() -> List[dict]:
    """
    Get all sources sorted by priority (1 = highest priority).

    Returns:
        List of source records sorted by priority
    """
    logger = get_logger()
    registry = load_sources_registry()
    sources = sorted(registry["sources"], key=lambda s: s.get("priority", 99))
    logger.info(f"Loaded {len(sources)} sources sorted by priority")
    return sources


def filter_downloadable_sources(sources: List[dict]) -> List[dict]:
    """
    Filter sources to only those that are downloadable.

    Excludes:
    - Sources with status == "blocked" or "restricted"
    - Sources with no downloader class mapping

    Args:
        sources: List of source records

    Returns:
        Filtered list of downloadable sources
    """
    logger = get_logger()
    downloadable = []

    for source in sources:
        source_id = source["source_id"]
        status = source.get("status", "unknown")

        # Skip blocked/restricted sources
        if status in ["blocked", "restricted"]:
            logger.debug(f"Skipping {source_id}: status={status}")
            continue

        # Check if we have a downloader for this source
        short_name = SOURCE_ID_MAPPINGS.get(source_id)
        if not short_name or short_name not in DOWNLOADER_REGISTRY:
            logger.debug(
                f"Skipping {source_id}: no downloader class "
                f"(short_name={short_name})"
            )
            continue

        downloadable.append(source)

    logger.info(
        f"Filtered to {len(downloadable)} downloadable sources "
        f"(from {len(sources)} total)"
    )
    return downloadable


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
        source_id: Source identifier - can be:
                   - Short name (e.g., "epa_aqs") for backward compatibility
                   - Full registry ID (e.g., "01_EPA_AQS_AIR_QUALITY_SYSTEM_AMB")
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

    # Convert registry source_id to short name if needed
    short_name = SOURCE_ID_MAPPINGS.get(source_id, source_id)

    # Check if downloader exists
    if short_name not in DOWNLOADER_REGISTRY:
        logger.error(
            f"Unknown source: {source_id} (short_name: {short_name}). "
            f"Available: {list(DOWNLOADER_REGISTRY.keys())}"
        )
        return False

    try:
        # Initialize downloader
        downloader_class = DOWNLOADER_REGISTRY[short_name]
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
    setup_logging(log_level=args.log_level)
    logger = get_logger()

    logger.info("=" * 70)
    logger.info(f"{SYSTEM_NAME} v{SYSTEM_VERSION}")
    logger.info("DATA DOWNLOAD")
    logger.info("=" * 70)

    try:
        # Determine which sources to download
        if args.source:
            # Single source (backward compatible: accepts short names or registry IDs)
            sources = [args.source]
            logger.info(f"Downloading single source: {args.source}")

        elif args.category:
            # All sources in category
            logger.info(f"Loading sources from category: {args.category}")
            category_sources = get_sources_by_category(args.category)

            if not category_sources:
                logger.error(f"No sources found in category: {args.category}")
                logger.info("Available categories:")
                registry = load_sources_registry()
                categories = sorted(set(s["category"] for s in registry["sources"]))
                for cat in categories:
                    logger.info(f"  - {cat}")
                sys.exit(1)

            # Filter to downloadable sources
            downloadable = filter_downloadable_sources(category_sources)

            if not downloadable:
                logger.warning(
                    f"No downloadable sources in category {args.category} "
                    f"({len(category_sources)} total, but no downloaders implemented)"
                )
                sys.exit(0)

            # Extract source IDs
            sources = [s["source_id"] for s in downloadable]
            logger.info(
                f"Will download {len(sources)} sources from category {args.category}:"
            )
            for s in downloadable:
                logger.info(
                    f"  - {s['source_id']} (priority {s.get('priority', '?')})"
                )

        elif args.all:
            # All sources in priority order
            logger.info("Loading ALL sources from registry...")
            all_sources = get_all_sources_by_priority()

            # Filter to downloadable sources
            downloadable = filter_downloadable_sources(all_sources)

            if not downloadable:
                logger.warning(
                    f"No downloadable sources found "
                    f"({len(all_sources)} total, but no downloaders implemented)"
                )
                sys.exit(0)

            # Extract source IDs
            sources = [s["source_id"] for s in downloadable]
            logger.info(f"Will download {len(sources)} sources (priority order):")
            for s in downloadable:
                logger.info(
                    f"  - {s['source_id']} "
                    f"(priority {s.get('priority', '?')}, category {s['category']})"
                )

            logger.warning("")
            logger.warning("⚠️  WARNING: Downloading ALL sources may take days/weeks!")
            logger.warning("⚠️  Consider using --category instead for targeted downloads")
            logger.warning("")

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
