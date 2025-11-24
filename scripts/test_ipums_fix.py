#!/usr/bin/env python3
"""Test IPUMS fix with single dataset."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))

from downloaders.python.ipums_nhgis_downloader import IPUMSNHGISDownloader
from loguru import logger

logger.info("=" * 80)
logger.info("TESTING IPUMS NHGIS FIX")
logger.info("=" * 80)

# Test with single dataset
dl = IPUMSNHGISDownloader()
logger.info("Testing with 2023_ACS1...")

result = dl.download_variable_year('2023_ACS1', 2023, force_refresh=False)

if result:
    logger.info(f"✅ SUCCESS: {result}")
else:
    logger.error("❌ FAILED")

logger.info("=" * 80)
