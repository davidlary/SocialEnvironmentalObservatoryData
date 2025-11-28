#!/usr/bin/env python3
"""
Test script for CDC EPHT Radon downloader.

Tests basic functionality with a single state (Illinois) and year (2021).
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from downloaders.python.cdc_epht_radon_downloader import CDCEPHTRadonDownloader
from loguru import logger

def test_single_state():
    """Test download for Illinois, 2021."""
    logger.info("=" * 80)
    logger.info("Testing CDC EPHT Radon Downloader")
    logger.info("=" * 80)

    # Initialize downloader
    downloader = CDCEPHTRadonDownloader()

    # Check metadata
    metadata = downloader.get_metadata("radon_testing")
    logger.info(f"Metadata: {metadata}")

    # Check available years
    years = downloader.get_available_years("radon_testing")
    logger.info(f"Available years: {years}")

    # Test with single year (2021)
    logger.info("\nDownloading 2021 data...")
    try:
        result = downloader.download_variable_year("radon_testing", 2021)
        if result:
            logger.info(f"✅ Success! Data cached at: {result}")

            # Check file size
            if result.exists():
                size_mb = result.stat().st_size / 1024 / 1024
                logger.info(f"File size: {size_mb:.2f} MB")
        else:
            logger.warning("⚠️ No data returned")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_state()
