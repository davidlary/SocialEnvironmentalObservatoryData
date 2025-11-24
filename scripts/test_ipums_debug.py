#!/usr/bin/env python3
"""
Test IPUMS NHGIS fix with DEBUG logging
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import setup_logger
from downloaders.python.ipums_nhgis_downloader import IPUMSNHGISDownloader

# Set DEBUG level to see full API responses
setup_logger(level="DEBUG")
logger = setup_logger()

logger.info("=" * 80)
logger.info("TESTING IPUMS NHGIS FIX (DEBUG MODE)")
logger.info("=" * 80)

downloader = IPUMSNHGISDownloader()

# Test with 2023_ACS1
logger.info("Testing with 2023_ACS1...")
result = downloader.download_variable_year("2023_ACS1", 2023, force_refresh=True)

if result:
    logger.info(f"✅ SUCCESS: {result}")
else:
    logger.error("❌ FAILED")

logger.info("=" * 80)
