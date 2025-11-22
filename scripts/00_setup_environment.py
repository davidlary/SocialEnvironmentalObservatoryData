#!/usr/bin/env python3
"""
Setup Script - Initialize Project Environment

This script:
1. Verifies Python version (>=3.9)
2. Installs required dependencies
3. Creates directory structure
4. Initializes progress tracking files
5. Validates installation

Run this FIRST before any other scripts.

Usage:
    python scripts/00_setup_environment.py
"""

import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logger import setup_logging, get_logger
from utils.constants import (
    CACHE_DIR,
    CONFIG_DIR,
    DATA_DIR,
    DOWNLOAD_LOGS_DIR,
    LOGS_DIR,
    METADATA_DIR,
    PROCESSED_DIR,
    PROCESSING_LOGS_DIR,
    PROGRESS_DIR,
    PROJECT_ROOT,
    SYSTEM_NAME,
    SYSTEM_VERSION,
)
from utils.file_utils import ensure_directory


# ============================================================================
# SETUP FUNCTIONS
# ============================================================================


def check_python_version():
    """Check Python version is >= 3.9."""
    logger.info("Checking Python version...")

    version = sys.version_info

    if version.major < 3 or (version.major == 3 and version.minor < 9):
        logger.error(
            f"Python 3.9+ required. Current version: "
            f"{version.major}.{version.minor}.{version.micro}"
        )
        sys.exit(1)

    logger.info(
        f"✅ Python version: {version.major}.{version.minor}.{version.micro}"
    )


def install_dependencies():
    """Install required Python packages."""
    logger.info("Installing Python dependencies...")

    requirements_file = PROJECT_ROOT / "requirements.txt"

    if not requirements_file.exists():
        logger.error(f"requirements.txt not found: {requirements_file}")
        sys.exit(1)

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            capture_output=True,
            text=True,
        )

        logger.info("✅ Dependencies installed successfully")

    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e.stderr}")
        sys.exit(1)


def create_directory_structure():
    """Create all required directories."""
    logger.info("Creating directory structure...")

    directories = [
        # Config
        CONFIG_DIR,
        # Data
        DATA_DIR,
        CACHE_DIR,
        PROCESSED_DIR,
        METADATA_DIR,
        # Logs
        LOGS_DIR,
        DOWNLOAD_LOGS_DIR,
        PROCESSING_LOGS_DIR,
        # Progress
        PROGRESS_DIR,
    ]

    # Create category subdirectories in cache and processed
    from utils.constants import DATA_CATEGORIES

    for category in DATA_CATEGORIES:
        directories.append(CACHE_DIR / category)
        directories.append(PROCESSED_DIR / category)

    for directory in directories:
        try:
            ensure_directory(directory)
            logger.debug(f"Created: {directory}")
        except Exception as e:
            logger.error(f"Error creating {directory}: {e}")
            sys.exit(1)

    logger.info(f"✅ Created {len(directories)} directories")


def initialize_progress_files():
    """Initialize progress tracking JSON files."""
    logger.info("Initializing progress tracking files...")

    from utils.file_utils import write_json_file

    progress_files = [
        PROGRESS_DIR / "download_progress.json",
        PROGRESS_DIR / "processing_progress.json",
        PROGRESS_DIR / "map_progress.json",
    ]

    initial_progress = {
        "last_updated": None,
        "sources": {},
    }

    for progress_file in progress_files:
        if not progress_file.exists():
            write_json_file(initial_progress, progress_file)
            logger.debug(f"Created: {progress_file}")

    logger.info("✅ Progress tracking initialized")


def create_gitkeep_files():
    """Create .gitkeep files in empty directories."""
    logger.info("Creating .gitkeep files...")

    directories = [
        CACHE_DIR,
        PROCESSED_DIR,
        LOGS_DIR,
        PROGRESS_DIR,
    ]

    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    logger.info("✅ .gitkeep files created")


def verify_installation():
    """Verify installation by importing key modules."""
    logger.info("Verifying installation...")

    try:
        # Test core imports
        import polars as pl
        import geopandas as gpd
        import matplotlib.pyplot as plt
        import rasterio
        import xarray as xr

        logger.debug("✅ Core dependencies import successfully")

        # Test our modules
        from core.metadata_manager import MetadataManager
        from core.cache_manager import CacheManager
        from core.progress_tracker import ProgressTracker
        from core.tsv_generator import TSVGenerator
        from core.map_generator import MapGenerator

        logger.debug("✅ Core modules import successfully")

        logger.info("✅ Installation verified")

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Some dependencies may not have installed correctly")
        sys.exit(1)


def print_summary():
    """Print setup summary."""
    logger.info("=" * 70)
    logger.info(f"{SYSTEM_NAME} v{SYSTEM_VERSION}")
    logger.info("Setup Complete!")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Run: python scripts/01_download_metadata.py")
    logger.info("     (Downloads FIPS codes and county boundaries)")
    logger.info("")
    logger.info("  2. Run: python scripts/02_build_source_registry.py")
    logger.info("     (Parses data list documentation)")
    logger.info("")
    logger.info("  3. Start downloading data!")
    logger.info("")
    logger.info("Directories created:")
    logger.info(f"  - Config:    {CONFIG_DIR}")
    logger.info(f"  - Data:      {DATA_DIR}")
    logger.info(f"  - Cache:     {CACHE_DIR}")
    logger.info(f"  - Processed: {PROCESSED_DIR}")
    logger.info(f"  - Logs:      {LOGS_DIR}")
    logger.info(f"  - Progress:  {PROGRESS_DIR}")
    logger.info("=" * 70)


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main setup function."""
    # Setup logging (console only for setup)
    setup_logging(enable_json=False, enable_console=True)

    global logger
    logger = get_logger()

    logger.info("=" * 70)
    logger.info(f"{SYSTEM_NAME} v{SYSTEM_VERSION}")
    logger.info("Environment Setup")
    logger.info("=" * 70)

    try:
        # Step 1: Check Python version
        check_python_version()

        # Step 2: Install dependencies
        install_dependencies()

        # Step 3: Create directory structure
        create_directory_structure()

        # Step 4: Initialize progress files
        initialize_progress_files()

        # Step 5: Create .gitkeep files
        create_gitkeep_files()

        # Step 6: Verify installation
        verify_installation()

        # Step 7: Print summary
        print_summary()

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Setup interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        logger.exception("Full error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
