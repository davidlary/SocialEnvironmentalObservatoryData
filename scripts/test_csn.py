#!/usr/bin/env python3
"""
Test script for CSN (Chemical Speciation Network) downloader.

Tests:
1. Initialize CSNDownloader
2. Get available years
3. Download single year (2023)
4. Verify cache file exists
5. Validate data structure
6. Check county FIPS codes

Usage:
    python scripts/test_csn.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import setup_logging
from downloaders.python.csn_downloader import CSNDownloader, CSN_PARAMETERS
from utils.file_utils import read_csv

# Setup logging
setup_logging()

print("=" * 80)
print("CSN DOWNLOADER TEST")
print("=" * 80)

# Test 1: Initialize downloader
print("\n[TEST 1] Initializing CSNDownloader...")
try:
    downloader = CSNDownloader()
    print("✅ CSNDownloader initialized successfully")
    print(f"   Source ID: {downloader.source_id}")
    print(f"   Source Name: {downloader.source_name}")
    print(f"   Category: {downloader.category}")
    print(f"   Cache Dir: {downloader.cache_dir}")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

# Test 2: Get available years
print("\n[TEST 2] Getting available years for PM2.5...")
try:
    years = downloader.get_available_years("pm25")
    print(f"✅ Available years: {years[0]}-{years[-1]} ({len(years)} years)")

    # Verify expected range
    assert years[0] == 2000, f"Expected start year 2000, got {years[0]}"
    assert years[-1] == 2024, f"Expected end year 2024, got {years[-1]}"
    assert len(years) == 25, f"Expected 25 years, got {len(years)}"
    print("   Range verification passed")
except Exception as e:
    print(f"❌ Failed to get available years: {e}")
    sys.exit(1)

# Test 3: Get metadata
print("\n[TEST 3] Getting metadata for key variables...")
try:
    test_vars = ["pm25", "ec", "oc", "sulfate", "nitrate", "ammonium"]
    for var in test_vars:
        metadata = downloader.get_metadata(var)
        print(f"✅ {var}:")
        print(f"   Name: {metadata['name']}")
        print(f"   Code: {metadata['parameter_code']}")
        print(f"   Unit: {metadata['unit']}")
        print(f"   Description: {metadata['description']}")
except Exception as e:
    print(f"❌ Failed to get metadata: {e}")
    sys.exit(1)

# Test 4: Download single year (2023)
print("\n[TEST 4] Downloading PM2.5 for 2023 (test year)...")
print("   This may take 1-2 minutes to download and process...")
try:
    cached_file = downloader.download_variable_year("pm25", 2023, force_refresh=False)

    if cached_file is None:
        print("❌ Download returned None")
        sys.exit(1)

    if not cached_file.exists():
        print(f"❌ Cached file not found: {cached_file}")
        sys.exit(1)

    print(f"✅ Download successful: {cached_file}")
    print(f"   File size: {cached_file.stat().st_size / 1024:.1f} KB")
except Exception as e:
    print(f"❌ Failed to download: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Validate data structure
print("\n[TEST 5] Validating data structure...")
try:
    df = read_csv(cached_file)

    print(f"✅ Loaded data successfully")
    print(f"   Rows: {df.height:,}")
    print(f"   Columns: {df.width}")

    # Check required columns
    required_cols = [
        "FIPS", "State_FIPS", "County_FIPS", "State_Name", "County_Name",
        "Year", "Value", "Unit", "N_Sites", "N_Samples"
    ]

    for col in required_cols:
        if col not in df.columns:
            print(f"❌ Missing required column: {col}")
            sys.exit(1)

    print(f"   ✅ All required columns present")

    # Display sample data
    print("\n   Sample data (first 5 rows):")
    print(df.head(5))

    # Check statistics
    print(f"\n   Statistics:")
    print(f"   - Counties: {df['FIPS'].n_unique()}")
    print(f"   - Sites: {df['N_Sites'].sum()}")
    print(f"   - Samples: {df['N_Samples'].sum():,}")
    print(f"   - Mean PM2.5: {df['Value'].mean():.2f} μg/m³")
    print(f"   - Min PM2.5: {df['Value'].min():.2f} μg/m³")
    print(f"   - Max PM2.5: {df['Value'].max():.2f} μg/m³")

except Exception as e:
    print(f"❌ Failed to validate data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Verify FIPS codes
print("\n[TEST 6] Verifying FIPS codes...")
try:
    # Check FIPS format (should be 5-digit strings)
    fips_codes = df["FIPS"].unique().to_list()

    invalid_fips = [fips for fips in fips_codes if len(fips) != 5 or not fips.isdigit()]

    if invalid_fips:
        print(f"❌ Found {len(invalid_fips)} invalid FIPS codes:")
        for fips in invalid_fips[:10]:  # Show first 10
            print(f"   - {fips}")
        sys.exit(1)

    print(f"✅ All {len(fips_codes)} FIPS codes are valid (5-digit format)")

    # Check State_FIPS + County_FIPS = FIPS
    fips_check = (df["State_FIPS"] + df["County_FIPS"]) == df["FIPS"]

    if not fips_check.all():
        print(f"❌ FIPS code construction error detected")
        sys.exit(1)

    print("✅ FIPS code construction verified (State_FIPS + County_FIPS = FIPS)")

except Exception as e:
    print(f"❌ Failed FIPS verification: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Check cache structure
print("\n[TEST 7] Checking cache directory structure...")
try:
    raw_dir = downloader.raw_dir
    processed_dir = downloader.processed_dir

    print(f"✅ Cache directories exist:")
    print(f"   Raw: {raw_dir}")
    print(f"   Processed: {processed_dir}")

    # List files
    raw_files = list(raw_dir.glob("*.csv"))
    processed_files = list(processed_dir.glob("*.csv"))

    print(f"\n   Files in cache:")
    print(f"   - Raw SPEC files: {len(raw_files)}")
    print(f"   - Processed files: {len(processed_files)}")

    if raw_files:
        print(f"\n   Raw files:")
        for f in raw_files:
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"   - {f.name} ({size_mb:.1f} MB)")

    if processed_files:
        print(f"\n   Processed files:")
        for f in processed_files:
            size_kb = f.stat().st_size / 1024
            print(f"   - {f.name} ({size_kb:.1f} KB)")

except Exception as e:
    print(f"❌ Failed cache check: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("ALL TESTS PASSED ✅")
print("=" * 80)
print("\nCSN Downloader is ready for full dataset download.")
print("\nNext steps:")
print("1. Download all years: python scripts/03_download_source.py --source csn --variable pm25,ec,oc,sulfate,nitrate,ammonium --years 2000-2024")
print("2. Process to TSV: python scripts/04_process_cached_data.py --source csn")
print("3. Generate maps: python scripts/05_generate_maps.py --category 01_AIR_ATMOSPHERE --source CSN")
print()
