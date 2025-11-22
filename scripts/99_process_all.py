#!/usr/bin/env python3
"""
Master Processing Script - Process All Data Sources.

This is the SINGLE SCRIPT that orchestrates all data processing:
1. Process cached data to TSV files
2. Generate choropleth maps for all TSV files

Run this script regularly to keep processed data up-to-date.
It's intelligent: skips already-processed files, only processes new data.

Usage:
    # Process everything (recommended)
    python scripts/99_process_all.py

    # Process specific sources only
    python scripts/99_process_all.py --sources epa_aqs ipums_nhgis

    # Force re-processing (regenerate all files)
    python scripts/99_process_all.py --force-refresh

    # Skip map generation (only create TSVs)
    python scripts/99_process_all.py --skip-maps
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import get_logger, setup_logging
from utils.constants import SYSTEM_NAME, SYSTEM_VERSION


# ============================================================================
# AVAILABLE SOURCES
# ============================================================================

AVAILABLE_SOURCES = [
    "epa_aqs",       # EPA Air Quality System (6 pollutants, 1980-2024)
    "ipums_nhgis",   # IPUMS NHGIS demographics (1970-2024)
]


# ============================================================================
# PROCESSING ORCHESTRATION
# ============================================================================


def run_command(cmd: list, description: str) -> bool:
    """
    Run subprocess command.

    Args:
        cmd: Command as list
        description: Human-readable description

    Returns:
        True if successful
    """
    logger = get_logger()
    logger.info(f"Running: {description}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        # Log output if verbose
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if 'INFO' in line or 'SUCCESS' in line or '✅' in line:
                    logger.info(line)

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {description}")
        if e.stderr:
            logger.error(e.stderr)
        return False


def process_source(
    source: str,
    force_refresh: bool,
    skip_maps: bool,
    log_level: str,
) -> bool:
    """
    Process single data source.

    Args:
        source: Source ID
        force_refresh: Force re-processing
        skip_maps: Skip map generation
        log_level: Logging level

    Returns:
        True if successful
    """
    logger = get_logger()

    # Step 1: Process cached data to TSV
    cmd_process = [
        "python",
        "scripts/04_process_cached_data.py",
        "--source", source,
        "--log-level", log_level,
    ]

    if force_refresh:
        cmd_process.append("--force-refresh")

    success = run_command(cmd_process, f"Process {source} → TSV")

    if not success:
        return False

    # Step 2: Generate maps (if not skipped)
    if not skip_maps:
        # Determine category from source
        category_map = {
            "epa_aqs": "01_AIR_ATMOSPHERE",
            "ipums_nhgis": "02_DEMOGRAPHICS_SOCIAL",
        }

        category = category_map.get(source)

        if category:
            cmd_maps = [
                "python",
                "scripts/05_generate_maps.py",
                "--category", category,
                "--log-level", log_level,
            ]

            if force_refresh:
                cmd_maps.append("--force-refresh")

            success = run_command(cmd_maps, f"Generate {source} maps")

            if not success:
                logger.warning(f"Map generation failed for {source}")
                return False

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Master processing script - process all data sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all sources (TSV + maps)
  python scripts/99_process_all.py

  # Process specific sources
  python scripts/99_process_all.py --sources epa_aqs

  # Force regenerate everything
  python scripts/99_process_all.py --force-refresh

  # Only create TSVs, skip maps
  python scripts/99_process_all.py --skip-maps
""",
    )

    # Source selection
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=AVAILABLE_SOURCES,
        help=f"Sources to process (default: all). Available: {AVAILABLE_SOURCES}",
    )

    # Options
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force re-processing even if files exist",
    )
    parser.add_argument(
        "--skip-maps",
        action="store_true",
        help="Skip map generation (only create TSV files)",
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

    logger.info("=" * 80)
    logger.info(f"{SYSTEM_NAME} v{SYSTEM_VERSION}")
    logger.info("MASTER PROCESSING: Cache → TSV → Maps")
    logger.info("=" * 80)

    # Determine sources to process
    sources = args.sources if args.sources else AVAILABLE_SOURCES

    logger.info(f"Sources to process: {sources}")
    logger.info(f"Force refresh: {args.force_refresh}")
    logger.info(f"Skip maps: {args.skip_maps}")
    logger.info("")

    # Process each source
    all_success = True
    results = {}

    for i, source in enumerate(sources, 1):
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"[{i}/{len(sources)}] PROCESSING: {source}")
        logger.info("=" * 80)

        success = process_source(
            source=source,
            force_refresh=args.force_refresh,
            skip_maps=args.skip_maps,
            log_level=args.log_level,
        )

        results[source] = "✅ SUCCESS" if success else "❌ FAILED"

        if not success:
            all_success = False

    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 80)

    for source, result in results.items():
        logger.info(f"  {source}: {result}")

    logger.info("=" * 80)

    if all_success:
        logger.info("✅ All processing completed successfully")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  • Processed TSV files: data/processed/{category}/{variable}/{year}_{variable}.tsv")
        logger.info("  • Maps: data/processed/{category}/{variable}/{year}_{variable}.png")
        logger.info("  • To update with new data: Just run this script again!")
    else:
        logger.warning("⚠️ Some processing failed (see errors above)")

    logger.info("=" * 80)

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
