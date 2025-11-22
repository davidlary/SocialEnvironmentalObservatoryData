#!/usr/bin/env python3
"""
Generate Choropleth Maps from TSV Files.

Creates publication-quality choropleth maps for each TSV file showing
spatial distribution of county-level data.

Each map includes:
- Quantile-based color classification
- Legend with value ranges
- Title with variable name, year, unit
- Statistics box with min/max/mean
- Missing data shown in gray

Usage:
    # Generate all maps
    python scripts/05_generate_maps.py --all

    # Generate maps for specific source
    python scripts/05_generate_maps.py --source epa_aqs

    # Generate maps for specific category
    python scripts/05_generate_maps.py --category 01_AIR_ATMOSPHERE

    # Generate maps for specific variable
    python scripts/05_generate_maps.py --variable PM25
"""

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import get_logger, setup_logging
from core.map_generator import MapGenerator
from utils.constants import PROCESSED_DIR, SYSTEM_NAME, SYSTEM_VERSION
from utils.file_utils import read_tsv


# ============================================================================
# MAP GENERATION LOGIC
# ============================================================================


def generate_map_for_tsv(tsv_path: Path, force_refresh: bool = False) -> bool:
    """
    Generate map for a single TSV file.

    Args:
        tsv_path: Path to TSV file
        force_refresh: Force regeneration even if map exists

    Returns:
        True if successful, False otherwise
    """
    logger = get_logger()

    # Check if map already exists
    map_path = tsv_path.with_suffix(".png")
    if map_path.exists() and not force_refresh:
        logger.debug(f"Map already exists: {map_path.name}")
        return True

    try:
        logger.info(f"Generating map: {tsv_path.name}")

        # Initialize map generator
        map_gen = MapGenerator()

        # Generate map
        map_gen.create_map(
            tsv_path=tsv_path,
            output_path=map_path,
        )

        logger.info(f"✅ Map created: {map_path.name}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to generate map for {tsv_path.name}: {e}")
        return False


def find_tsv_files(
    source: Optional[str] = None,
    category: Optional[str] = None,
    variable: Optional[str] = None,
) -> List[Path]:
    """
    Find TSV files to process.

    Args:
        source: Filter by source ID
        category: Filter by category
        variable: Filter by variable name

    Returns:
        List of TSV file paths
    """
    logger = get_logger()

    # Determine search path
    if category:
        search_path = PROCESSED_DIR / category
    else:
        search_path = PROCESSED_DIR

    if not search_path.exists():
        logger.warning(f"Processed directory does not exist: {search_path}")
        return []

    # Find all TSV files
    tsv_files = list(search_path.glob("**/*.tsv"))

    # Filter by variable if specified
    if variable:
        tsv_files = [
            f for f in tsv_files if variable in f.parent.name
        ]

    logger.info(f"Found {len(tsv_files)} TSV files")

    return sorted(tsv_files)


def generate_maps_parallel(
    tsv_files: List[Path],
    force_refresh: bool = False,
    max_workers: int = 8,
) -> dict:
    """
    Generate maps in parallel.

    Args:
        tsv_files: List of TSV file paths
        force_refresh: Force regeneration
        max_workers: Maximum parallel workers

    Returns:
        Dictionary with statistics
    """
    logger = get_logger()

    if len(tsv_files) == 0:
        logger.warning("No TSV files to process")
        return {"success": 0, "failed": 0, "skipped": 0}

    logger.info(f"Generating maps for {len(tsv_files)} TSV files...")
    logger.info(f"Using {max_workers} parallel workers")

    success_count = 0
    fail_count = 0
    skipped_count = 0

    # Filter out files that already have maps (if not force_refresh)
    files_to_process = []
    for tsv_path in tsv_files:
        map_path = tsv_path.with_suffix(".png")
        if map_path.exists() and not force_refresh:
            skipped_count += 1
        else:
            files_to_process.append(tsv_path)

    if skipped_count > 0:
        logger.info(f"Skipping {skipped_count} files (maps already exist)")

    if len(files_to_process) == 0:
        logger.info("All maps already exist (use --force-refresh to regenerate)")
        return {"success": 0, "failed": 0, "skipped": skipped_count}

    # Process in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(generate_map_for_tsv, tsv_path, force_refresh): tsv_path
            for tsv_path in files_to_process
        }

        # Process results as they complete
        for future in as_completed(futures):
            tsv_path = futures[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"Error processing {tsv_path.name}: {e}")
                fail_count += 1

            # Progress update
            total_processed = success_count + fail_count
            if total_processed % 10 == 0:
                logger.info(
                    f"Progress: {total_processed}/{len(files_to_process)} "
                    f"({success_count} succeeded, {fail_count} failed)"
                )

    return {
        "success": success_count,
        "failed": fail_count,
        "skipped": skipped_count,
    }


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Generate choropleth maps from TSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all maps
  python scripts/05_generate_maps.py --all

  # Generate maps for EPA AQS data
  python scripts/05_generate_maps.py --source epa_aqs

  # Generate maps for specific category
  python scripts/05_generate_maps.py --category 01_AIR_ATMOSPHERE

  # Generate maps for specific variable
  python scripts/05_generate_maps.py --variable PM25

  # Force regenerate all maps
  python scripts/05_generate_maps.py --all --force-refresh
""",
    )

    # Source/category/variable selection
    selection_group = parser.add_mutually_exclusive_group(required=True)
    selection_group.add_argument(
        "--all",
        action="store_true",
        help="Generate maps for all TSV files",
    )
    selection_group.add_argument(
        "--source",
        type=str,
        help="Generate maps for specific source (e.g., 'epa_aqs')",
    )
    selection_group.add_argument(
        "--category",
        type=str,
        help="Generate maps for specific category (e.g., '01_AIR_ATMOSPHERE')",
    )
    selection_group.add_argument(
        "--variable",
        type=str,
        help="Generate maps for specific variable (e.g., 'PM25')",
    )

    # Options
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force regeneration even if map exists",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum parallel workers (default: 8)",
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
    logger.info("MAP GENERATION: TSV → PNG")
    logger.info("=" * 70)

    try:
        # Find TSV files
        logger.info("Finding TSV files...")

        if args.all:
            tsv_files = find_tsv_files()
        elif args.source:
            # For source-based filtering, we need to map source to category
            # For now, use all files and filter by directory name
            tsv_files = find_tsv_files()
        elif args.category:
            tsv_files = find_tsv_files(category=args.category)
        elif args.variable:
            tsv_files = find_tsv_files(variable=args.variable)
        else:
            logger.error("No selection criteria specified")
            sys.exit(1)

        if len(tsv_files) == 0:
            logger.warning("No TSV files found to process")
            logger.info(
                "Run data processing first: "
                "python scripts/04_process_cached_data.py"
            )
            sys.exit(0)

        # Generate maps
        stats = generate_maps_parallel(
            tsv_files=tsv_files,
            force_refresh=args.force_refresh,
            max_workers=args.max_workers,
        )

        # Print summary
        logger.info("=" * 70)
        logger.info("MAP GENERATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Successfully generated: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Skipped (already exist): {stats['skipped']}")
        logger.info("=" * 70)

        if stats["success"] > 0:
            logger.info("")
            logger.info("Maps saved to: data/processed/{category}/{variable}/")
            logger.info("Each variable directory contains:")
            logger.info("  - {year}_{variable}.tsv (county-level data)")
            logger.info("  - {year}_{variable}.png (choropleth map)")
            logger.info("=" * 70)

        sys.exit(0 if stats["failed"] == 0 else 1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Map generation interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Map generation failed: {e}")
        logger.exception("Full error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
