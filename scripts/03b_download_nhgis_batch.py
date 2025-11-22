#!/usr/bin/env python3
"""
Download IPUMS NHGIS data in batches.

This script handles the special workflow for IPUMS NHGIS:
1. Create extract request
2. Wait for IPUMS to prepare extract (can take 5-60 minutes)
3. Download prepared extract
4. Move to next dataset

Usage:
    # Download batch 1 (recent ACS 2019-2023)
    python scripts/03b_download_nhgis_batch.py --batch 1

    # Download specific datasets
    python scripts/03b_download_nhgis_batch.py --datasets 2023_ACS1 2022_ACS1

    # Download all 266 datasets (will take DAYS!)
    python scripts/03b_download_nhgis_batch.py --all
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import get_logger, setup_logging
from downloaders.python.ipums_nhgis_downloader import IPUMSNHGISDownloader
from utils.constants import SYSTEM_NAME, SYSTEM_VERSION


def load_batches() -> dict:
    """Load download batches from metadata."""
    batch_file = Path("data/metadata/nhgis_download_batches.json")
    if batch_file.exists():
        with open(batch_file) as f:
            return json.load(f)
    return {}


def download_datasets(datasets: List[str], downloader: IPUMSNHGISDownloader) -> tuple:
    """
    Download list of datasets.

    Args:
        datasets: List of dataset names
        downloader: IPUMS NHGIS downloader instance

    Returns:
        Tuple of (success_count, fail_count)
    """
    logger = get_logger()
    success_count = 0
    fail_count = 0

    for i, dataset in enumerate(datasets, 1):
        logger.info(f"[{i}/{len(datasets)}] Processing dataset: {dataset}")

        try:
            # For NHGIS, use the dataset name as variable and extract year from name
            # If dataset has year in name (e.g., "2023_ACS1"), extract it
            # Otherwise use 0 as placeholder
            year = 0
            parts = dataset.split("_")
            if parts and parts[0].isdigit():
                year = int(parts[0])

            result = downloader.download_variable_year(
                variable=dataset,
                year=year,
                force_refresh=False
            )

            if result:
                logger.info(f"✅ {dataset} downloaded successfully")
                success_count += 1
            else:
                logger.error(f"❌ {dataset} download failed")
                fail_count += 1

        except Exception as e:
            logger.error(f"❌ {dataset} error: {e}")
            fail_count += 1

        # Small delay between datasets to respect rate limits
        if i < len(datasets):
            time.sleep(1)

    return success_count, fail_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download IPUMS NHGIS data in batches",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Dataset selection (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--batch",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Download predefined batch (1=recent ACS, 2=2020 census, etc.)"
    )
    group.add_argument(
        "--datasets",
        nargs="+",
        help="Download specific datasets by name"
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Download ALL 266 datasets (WARNING: takes days!)"
    )

    # Options
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(log_level=args.log_level)
    logger = get_logger()

    logger.info("=" * 80)
    logger.info(f"{SYSTEM_NAME} v{SYSTEM_VERSION}")
    logger.info("IPUMS NHGIS BATCH DOWNLOAD")
    logger.info("=" * 80)

    try:
        # Initialize downloader
        downloader = IPUMSNHGISDownloader()

        # Determine which datasets to download
        if args.batch:
            batches = load_batches()
            batch_name = f"batch_0{args.batch}_"
            batch_key = [k for k in batches.keys() if k.startswith(batch_name)]
            if not batch_key:
                logger.error(f"Batch {args.batch} not found")
                sys.exit(1)

            datasets = batches[batch_key[0]]
            logger.info(f"Batch {args.batch}: {len(datasets)} datasets")

        elif args.datasets:
            datasets = args.datasets
            logger.info(f"Custom selection: {len(datasets)} datasets")

        elif args.all:
            all_datasets = downloader.get_all_datasets()
            datasets = [d.get('name', d.get('id')) for d in all_datasets]
            logger.info(f"ALL datasets: {len(datasets)} datasets")
            logger.warning("This will take MANY HOURS or DAYS to complete!")
            logger.warning("Each extract can take 5-60 minutes to prepare")
            response = input("Continue? (yes/no): ")
            if response.lower() != "yes":
                logger.info("Cancelled by user")
                sys.exit(0)

        else:
            logger.error("No datasets specified")
            sys.exit(1)

        # Download datasets
        logger.info("-" * 80)
        logger.info(f"Starting download of {len(datasets)} datasets...")
        logger.info("-" * 80)

        success_count, fail_count = download_datasets(datasets, downloader)

        # Summary
        logger.info("=" * 80)
        logger.info("DOWNLOAD COMPLETE")
        logger.info("=" * 80)
        logger.info(f"✅ Success: {success_count}")
        logger.info(f"❌ Failed: {fail_count}")
        logger.info(f"Total: {len(datasets)}")
        logger.info("=" * 80)

        sys.exit(0 if fail_count == 0 else 1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Download interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        logger.exception("Full error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
