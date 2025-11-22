#!/usr/bin/env python3
"""
Process Cached Data to TSV Files.

Converts cached downloaded files to standardized county-level TSV files.

Each TSV file contains:
- FIPS code with full county/state metadata
- Annual aggregated values
- Consistent column structure across all sources

Usage:
    # Process all cached files from all sources
    python scripts/04_process_cached_data.py --all

    # Process specific source
    python scripts/04_process_cached_data.py --source epa_aqs

    # Force re-processing (ignore existing TSV files)
    python scripts/04_process_cached_data.py --source epa_aqs --force-refresh
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import get_logger, setup_logging
from utils.constants import SYSTEM_NAME, SYSTEM_VERSION

# Import processors
from processors.epa_aqs_processor import EPAAQSProcessor


# ============================================================================
# PROCESSOR REGISTRY
# ============================================================================

PROCESSOR_REGISTRY = {
    "epa_aqs": EPAAQSProcessor,
    # Add more processors as implemented
}


# ============================================================================
# MAIN PROCESSING LOGIC
# ============================================================================


def process_source(
    source_id: str,
    force_refresh: bool = False,
) -> bool:
    """
    Process cached data for a specific source.

    Args:
        source_id: Source identifier (e.g., "epa_aqs")
        force_refresh: Force re-processing even if TSV exists

    Returns:
        True if successful, False otherwise
    """
    logger = get_logger()
    logger.info("=" * 70)
    logger.info(f"PROCESSING SOURCE: {source_id}")
    logger.info("=" * 70)

    # Check if processor exists
    if source_id not in PROCESSOR_REGISTRY:
        logger.error(
            f"Unknown source: {source_id}. "
            f"Available: {list(PROCESSOR_REGISTRY.keys())}"
        )
        return False

    try:
        # Initialize processor
        processor_class = PROCESSOR_REGISTRY[source_id]
        processor = processor_class()

        # Process all cached files
        stats = processor.process_all_cached(force_refresh=force_refresh)

        # Report results
        logger.info("")
        logger.info("Results:")
        logger.info(f"  Successfully processed: {stats['success']}")
        logger.info(f"  Failed: {stats['failed']}")

        return stats["failed"] == 0

    except Exception as e:
        logger.error(f"Error processing source {source_id}: {e}")
        logger.exception("Full error:")
        return False


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Process cached data to TSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all cached EPA AQS data
  python scripts/04_process_cached_data.py --source epa_aqs

  # Force re-processing (regenerate existing TSV files)
  python scripts/04_process_cached_data.py --source epa_aqs --force-refresh

  # Process all sources
  python scripts/04_process_cached_data.py --all
""",
    )

    # Source selection
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--source",
        type=str,
        help=f"Source ID to process. Available: {list(PROCESSOR_REGISTRY.keys())}",
    )
    source_group.add_argument(
        "--all",
        action="store_true",
        help="Process all sources",
    )

    # Options
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force re-processing even if TSV exists",
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
    logger.info("DATA PROCESSING: Cache → TSV")
    logger.info("=" * 70)

    try:
        # Determine which sources to process
        if args.source:
            sources = [args.source]
        elif args.all:
            sources = list(PROCESSOR_REGISTRY.keys())
        else:
            logger.error("No source or --all specified")
            sys.exit(1)

        logger.info(f"Sources to process: {sources}")
        logger.info("")

        # Process each source
        all_success = True
        for source in sources:
            success = process_source(
                source_id=source,
                force_refresh=args.force_refresh,
            )

            if not success:
                all_success = False

            logger.info("")

        # Print summary
        logger.info("=" * 70)
        if all_success:
            logger.info("✅ All processing completed successfully")
        else:
            logger.warning("⚠️ Some processing failed (see errors above)")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Run: python scripts/05_generate_maps.py")
        logger.info("     (Generate choropleth maps for all TSV files)")
        logger.info("=" * 70)

        sys.exit(0 if all_success else 1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Processing interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        logger.exception("Full error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
