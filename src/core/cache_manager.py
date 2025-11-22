"""
Cache Manager for downloaded data files.

Intelligent caching system that:
- Stores original downloaded files
- Validates cache integrity (checksums, age, corruption)
- Supports cache expiration (TTL)
- Provides cache statistics
- Enables efficient recovery

Design Patterns:
- Strategy: Different caching strategies for different data types
- Command: Cache operations as commands for undo/redo
"""

import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

import polars as pl
from loguru import logger

from utils.constants import (
    CACHE_DIR,
    DEFAULT_CACHE_TTL_DAYS,
    VALIDATE_CHECKSUMS,
)
from utils.file_utils import (
    ensure_directory,
    get_file_size_mb,
    validate_file_exists,
)


# ============================================================================
# CACHE MANAGER
# ============================================================================


class CacheManager:
    """
    Manager for caching downloaded data files.

    Cache hierarchy:
        data/cache/{category}/{source}/{variable}/{year}_data.{ext}

    Example:
        data/cache/01_AIR_ATMOSPHERE/epa_aqs/PM25/2020_data.csv
    """

    def __init__(self, cache_root: Optional[Path] = None):
        """
        Initialize cache manager.

        Args:
            cache_root: Root cache directory (default: from constants)
        """
        self.cache_root = cache_root if cache_root else CACHE_DIR
        ensure_directory(self.cache_root)
        logger.debug(f"Cache manager initialized: {self.cache_root}")

    # ========================================================================
    # CACHE PATH MANAGEMENT
    # ========================================================================

    def get_cache_path(
        self,
        category: str,
        source: str,
        variable: str,
        year: int,
        extension: str = "csv",
    ) -> Path:
        """
        Get cache file path for a specific data file.

        Args:
            category: Data category (e.g., "01_AIR_ATMOSPHERE")
            source: Data source (e.g., "epa_aqs")
            variable: Variable name (e.g., "PM25")
            year: Year
            extension: File extension (csv, nc, tif, etc.)

        Returns:
            Path object for cache file

        Example:
            >>> manager = CacheManager()
            >>> path = manager.get_cache_path(
            ...     "01_AIR_ATMOSPHERE", "epa_aqs", "PM25", 2020
            ... )
            >>> print(path)
            data/cache/01_AIR_ATMOSPHERE/epa_aqs/PM25/2020_data.csv
        """
        cache_dir = self.cache_root / category / source / variable
        ensure_directory(cache_dir)

        filename = f"{year}_data.{extension}"
        return cache_dir / filename

    def get_cache_dir(
        self,
        category: str,
        source: str,
        variable: Optional[str] = None,
    ) -> Path:
        """
        Get cache directory for a source or variable.

        Args:
            category: Data category
            source: Data source
            variable: Optional variable name

        Returns:
            Path to cache directory
        """
        if variable:
            cache_dir = self.cache_root / category / source / variable
        else:
            cache_dir = self.cache_root / category / source

        ensure_directory(cache_dir)
        return cache_dir

    # ========================================================================
    # CACHE OPERATIONS
    # ========================================================================

    def is_cached(
        self,
        category: str,
        source: str,
        variable: str,
        year: int,
        extension: str = "csv",
        max_age_days: Optional[int] = None,
    ) -> bool:
        """
        Check if data is cached and valid.

        Args:
            category: Data category
            source: Data source
            variable: Variable name
            year: Year
            extension: File extension
            max_age_days: Maximum cache age in days (None = no limit)

        Returns:
            True if cached and valid, False otherwise

        Example:
            >>> manager = CacheManager()
            >>> if not manager.is_cached("01_AIR_ATMOSPHERE", "epa_aqs", "PM25", 2020):
            ...     download_data()  # Only download if not cached
        """
        cache_path = self.get_cache_path(category, source, variable, year, extension)

        if not cache_path.exists():
            logger.debug(f"Cache miss: {cache_path}")
            return False

        # Check file size (must be > 0 bytes)
        if cache_path.stat().st_size == 0:
            logger.warning(f"Cached file is empty: {cache_path}")
            return False

        # Check age if max_age_days specified
        if max_age_days is not None:
            file_age = datetime.now() - datetime.fromtimestamp(
                cache_path.stat().st_mtime
            )
            if file_age > timedelta(days=max_age_days):
                logger.info(
                    f"Cached file expired (age={file_age.days} days): {cache_path}"
                )
                return False

        logger.debug(f"Cache hit: {cache_path}")
        return True

    def save_to_cache(
        self,
        source_file: Union[str, Path],
        category: str,
        source: str,
        variable: str,
        year: int,
        compute_checksum: bool = VALIDATE_CHECKSUMS,
    ) -> Path:
        """
        Save downloaded file to cache.

        Args:
            source_file: Path to source file to cache
            category: Data category
            source: Data source
            variable: Variable name
            year: Year
            compute_checksum: If True, compute and save checksum

        Returns:
            Path to cached file

        Example:
            >>> manager = CacheManager()
            >>> # After downloading
            >>> cached_path = manager.save_to_cache(
            ...     "/tmp/download.csv",
            ...     "01_AIR_ATMOSPHERE",
            ...     "epa_aqs",
            ...     "PM25",
            ...     2020
            ... )
        """
        source_file = Path(source_file)
        validate_file_exists(source_file)

        # Determine extension from source file
        extension = source_file.suffix.lstrip(".")

        cache_path = self.get_cache_path(category, source, variable, year, extension)

        # Copy file to cache
        logger.info(
            f"Caching {get_file_size_mb(source_file):.2f} MB: {cache_path.name}"
        )

        shutil.copy2(source_file, cache_path)

        # Compute checksum if requested
        if compute_checksum:
            checksum = self._compute_checksum(cache_path)
            checksum_path = cache_path.with_suffix(cache_path.suffix + ".sha256")
            checksum_path.write_text(checksum)
            logger.debug(f"Saved checksum: {checksum_path}")

        logger.info(f"Cached: {cache_path}")
        return cache_path

    def get_from_cache(
        self,
        category: str,
        source: str,
        variable: str,
        year: int,
        extension: str = "csv",
        validate_checksum: bool = VALIDATE_CHECKSUMS,
    ) -> Optional[Path]:
        """
        Get file from cache if available and valid.

        Args:
            category: Data category
            source: Data source
            variable: Variable name
            year: Year
            extension: File extension
            validate_checksum: If True, validate checksum

        Returns:
            Path to cached file if valid, None if not cached or invalid

        Example:
            >>> manager = CacheManager()
            >>> cached_file = manager.get_from_cache(
            ...     "01_AIR_ATMOSPHERE", "epa_aqs", "PM25", 2020
            ... )
            >>> if cached_file:
            ...     data = pl.read_csv(cached_file)
            ... else:
            ...     download_data()
        """
        if not self.is_cached(category, source, variable, year, extension):
            return None

        cache_path = self.get_cache_path(category, source, variable, year, extension)

        # Validate checksum if requested
        if validate_checksum:
            if not self._validate_checksum(cache_path):
                logger.error(f"Checksum validation failed: {cache_path}")
                return None

        return cache_path

    def remove_from_cache(
        self,
        category: str,
        source: str,
        variable: str,
        year: int,
        extension: str = "csv",
    ) -> bool:
        """
        Remove file from cache.

        Args:
            category: Data category
            source: Data source
            variable: Variable name
            year: Year
            extension: File extension

        Returns:
            True if removed, False if not found
        """
        cache_path = self.get_cache_path(category, source, variable, year, extension)

        if not cache_path.exists():
            return False

        logger.info(f"Removing from cache: {cache_path}")

        # Remove data file
        cache_path.unlink()

        # Remove checksum if exists
        checksum_path = cache_path.with_suffix(cache_path.suffix + ".sha256")
        if checksum_path.exists():
            checksum_path.unlink()

        return True

    # ========================================================================
    # CACHE STATISTICS AND MAINTENANCE
    # ========================================================================

    def get_cache_stats(self) -> Dict[str, any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics

        Example:
            >>> manager = CacheManager()
            >>> stats = manager.get_cache_stats()
            >>> print(f"Total size: {stats['total_size_gb']:.2f} GB")
            >>> print(f"File count: {stats['file_count']}")
        """
        stats = {
            "total_size_bytes": 0,
            "total_size_gb": 0.0,
            "file_count": 0,
            "by_category": {},
        }

        if not self.cache_root.exists():
            return stats

        # Walk cache directory
        for category_dir in self.cache_root.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            category_stats = {
                "size_bytes": 0,
                "file_count": 0,
            }

            for file_path in category_dir.rglob("*"):
                if file_path.is_file() and not file_path.suffix == ".sha256":
                    file_size = file_path.stat().st_size
                    category_stats["size_bytes"] += file_size
                    category_stats["file_count"] += 1
                    stats["total_size_bytes"] += file_size
                    stats["file_count"] += 1

            category_stats["size_gb"] = category_stats["size_bytes"] / (1024**3)
            stats["by_category"][category_name] = category_stats

        stats["total_size_gb"] = stats["total_size_bytes"] / (1024**3)

        logger.info(
            f"Cache stats: {stats['file_count']} files, "
            f"{stats['total_size_gb']:.2f} GB"
        )

        return stats

    def clean_old_cache(
        self,
        max_age_days: int = DEFAULT_CACHE_TTL_DAYS,
        dry_run: bool = False,
    ) -> List[Path]:
        """
        Remove cached files older than specified age.

        Args:
            max_age_days: Maximum age in days
            dry_run: If True, don't actually delete (just report)

        Returns:
            List of removed file paths

        Example:
            >>> manager = CacheManager()
            >>> # Remove files older than 1 year
            >>> removed = manager.clean_old_cache(max_age_days=365)
            >>> print(f"Removed {len(removed)} old files")
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        removed_files = []

        logger.info(
            f"Cleaning cache: removing files older than {max_age_days} days "
            f"(before {cutoff_date.date()})"
        )

        for file_path in self.cache_root.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.suffix == ".sha256":
                continue  # Handle checksums with data files

            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

            if file_mtime < cutoff_date:
                removed_files.append(file_path)

                if not dry_run:
                    logger.debug(f"Removing old cache file: {file_path}")
                    file_path.unlink()

                    # Remove checksum if exists
                    checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
                    if checksum_path.exists():
                        checksum_path.unlink()

        if dry_run:
            logger.info(f"[DRY RUN] Would remove {len(removed_files)} files")
        else:
            logger.info(f"Removed {len(removed_files)} old cache files")

        return removed_files

    def clear_cache(
        self,
        category: Optional[str] = None,
        source: Optional[str] = None,
        confirm: bool = False,
    ) -> int:
        """
        Clear cache (use with caution!).

        Args:
            category: Optional category to clear (None = all)
            source: Optional source to clear (requires category)
            confirm: Must be True to actually clear

        Returns:
            Number of files removed

        Example:
            >>> manager = CacheManager()
            >>> # Clear specific source
            >>> count = manager.clear_cache(
            ...     category="01_AIR_ATMOSPHERE",
            ...     source="epa_aqs",
            ...     confirm=True
            ... )
        """
        if not confirm:
            logger.warning("Cache clear not confirmed (set confirm=True)")
            return 0

        if category and source:
            target_dir = self.cache_root / category / source
        elif category:
            target_dir = self.cache_root / category
        else:
            target_dir = self.cache_root

        if not target_dir.exists():
            logger.info(f"Cache directory doesn't exist: {target_dir}")
            return 0

        logger.warning(f"⚠️ Clearing cache: {target_dir}")

        file_count = 0
        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                file_path.unlink()
                file_count += 1

        logger.info(f"Cleared {file_count} files from cache")
        return file_count

    # ========================================================================
    # CHECKSUM VALIDATION
    # ========================================================================

    @staticmethod
    def _compute_checksum(file_path: Path) -> str:
        """
        Compute SHA-256 checksum of file.

        Args:
            file_path: Path to file

        Returns:
            Hex string of SHA-256 checksum
        """
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _validate_checksum(self, file_path: Path) -> bool:
        """
        Validate file checksum.

        Args:
            file_path: Path to file to validate

        Returns:
            True if valid, False otherwise
        """
        checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")

        if not checksum_path.exists():
            logger.debug(f"No checksum file found: {checksum_path}")
            return True  # No checksum = assume valid

        try:
            stored_checksum = checksum_path.read_text().strip()
            computed_checksum = self._compute_checksum(file_path)

            if stored_checksum == computed_checksum:
                logger.debug(f"Checksum valid: {file_path.name}")
                return True
            else:
                logger.error(
                    f"Checksum mismatch: {file_path.name}\n"
                    f"  Stored:   {stored_checksum}\n"
                    f"  Computed: {computed_checksum}"
                )
                return False

        except Exception as e:
            logger.error(f"Error validating checksum: {e}")
            return False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Default cache manager instance
_cache_manager = CacheManager()


def is_cached(
    category: str,
    source: str,
    variable: str,
    year: int,
    extension: str = "csv",
) -> bool:
    """Check if data is cached (convenience function)."""
    return _cache_manager.is_cached(category, source, variable, year, extension)


def get_from_cache(
    category: str,
    source: str,
    variable: str,
    year: int,
    extension: str = "csv",
) -> Optional[Path]:
    """Get from cache (convenience function)."""
    return _cache_manager.get_from_cache(category, source, variable, year, extension)


def save_to_cache(
    source_file: Union[str, Path],
    category: str,
    source: str,
    variable: str,
    year: int,
) -> Path:
    """Save to cache (convenience function)."""
    return _cache_manager.save_to_cache(source_file, category, source, variable, year)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "CacheManager",
    "is_cached",
    "get_from_cache",
    "save_to_cache",
]
