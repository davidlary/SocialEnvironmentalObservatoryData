"""
Progress Tracker for resumable downloads and processing.

This is CRITICAL for recovery - tracks every completed operation so we can
resume from any point after interruption or error.

Tracks three types of progress:
1. Downloads: Which variable/year combinations have been downloaded
2. Processing: Which cached files have been processed to TSV
3. Mapping: Which TSV files have had maps generated

Progress stored as JSON for easy inspection and manual editing if needed.

Design Patterns:
- Memento: Save/restore progress state
- Observer: Notify on progress updates (optional)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from loguru import logger

from utils.constants import (
    DOWNLOAD_PROGRESS_PATH,
    MAP_PROGRESS_PATH,
    PROCESSING_PROGRESS_PATH,
    PROGRESS_DIR,
)
from utils.file_utils import ensure_directory, write_json_file


# ============================================================================
# PROGRESS TRACKER
# ============================================================================


class ProgressTracker:
    """
    Track progress for downloads, processing, and mapping.

    Progress structure:
    {
        "last_updated": "2025-11-21T15:30:00",
        "sources": {
            "epa_aqs": {
                "status": "in_progress",
                "variables": {
                    "PM25_Annual": {
                        "completed_years": [2020, 2021, 2022],
                        "failed_years": [2023],
                        "pending_years": [2024]
                    }
                }
            }
        }
    }
    """

    def __init__(self, progress_file: Optional[Path] = None):
        """
        Initialize progress tracker.

        Args:
            progress_file: Path to progress JSON file
                          (default: download_progress.json)
        """
        self.progress_file = progress_file if progress_file else DOWNLOAD_PROGRESS_PATH
        ensure_directory(PROGRESS_DIR)

        self.progress = self._load_progress()

    def _load_progress(self) -> Dict:
        """
        Load progress from file.

        Returns:
            Progress dictionary
        """
        if not self.progress_file.exists():
            logger.info(f"Creating new progress file: {self.progress_file}")
            return {
                "last_updated": datetime.now().isoformat(),
                "sources": {},
            }

        try:
            with open(self.progress_file, "r") as f:
                progress = json.load(f)
                logger.info(f"Loaded progress from {self.progress_file}")
                return progress
        except Exception as e:
            logger.error(f"Error loading progress: {e}. Starting fresh.")
            return {
                "last_updated": datetime.now().isoformat(),
                "sources": {},
            }

    def _save_progress(self) -> None:
        """Save progress to file."""
        self.progress["last_updated"] = datetime.now().isoformat()

        try:
            write_json_file(self.progress, self.progress_file)
            logger.debug(f"Saved progress to {self.progress_file}")
        except Exception as e:
            logger.error(f"Error saving progress: {e}")

    # ========================================================================
    # DOWNLOAD PROGRESS
    # ========================================================================

    def mark_downloaded(
        self,
        source: str,
        variable: str,
        year: int,
        status: str = "completed",
    ) -> None:
        """
        Mark a download as completed or failed.

        Args:
            source: Data source name
            variable: Variable name
            year: Year
            status: "completed" or "failed"

        Example:
            >>> tracker = ProgressTracker()
            >>> tracker.mark_downloaded("epa_aqs", "PM25_Annual", 2020, "completed")
        """
        # Initialize source if needed
        if source not in self.progress["sources"]:
            self.progress["sources"][source] = {
                "status": "in_progress",
                "variables": {},
            }

        # Initialize variable if needed
        if variable not in self.progress["sources"][source]["variables"]:
            self.progress["sources"][source]["variables"][variable] = {
                "completed_years": [],
                "failed_years": [],
                "pending_years": [],
            }

        var_progress = self.progress["sources"][source]["variables"][variable]

        # Update progress
        if status == "completed":
            if year not in var_progress["completed_years"]:
                var_progress["completed_years"].append(year)
                var_progress["completed_years"].sort()

            # Remove from failed/pending if present
            if year in var_progress["failed_years"]:
                var_progress["failed_years"].remove(year)
            if year in var_progress["pending_years"]:
                var_progress["pending_years"].remove(year)

            logger.info(f"✅ Marked downloaded: {source}/{variable}/{year}")

        elif status == "failed":
            if year not in var_progress["failed_years"]:
                var_progress["failed_years"].append(year)
                var_progress["failed_years"].sort()

            # Remove from completed/pending if present
            if year in var_progress["completed_years"]:
                var_progress["completed_years"].remove(year)
            if year in var_progress["pending_years"]:
                var_progress["pending_years"].remove(year)

            logger.warning(f"❌ Marked failed: {source}/{variable}/{year}")

        self._save_progress()

    def is_downloaded(
        self,
        source: str,
        variable: str,
        year: int,
    ) -> bool:
        """
        Check if download is completed.

        Args:
            source: Data source name
            variable: Variable name
            year: Year

        Returns:
            True if completed, False otherwise
        """
        if source not in self.progress["sources"]:
            return False

        if variable not in self.progress["sources"][source]["variables"]:
            return False

        var_progress = self.progress["sources"][source]["variables"][variable]
        return year in var_progress["completed_years"]

    def get_pending_downloads(
        self,
        source: str,
        variable: str,
        all_years: List[int],
    ) -> List[int]:
        """
        Get list of years that still need to be downloaded.

        Args:
            source: Data source name
            variable: Variable name
            all_years: Complete list of years available

        Returns:
            List of years not yet completed

        Example:
            >>> tracker = ProgressTracker()
            >>> pending = tracker.get_pending_downloads(
            ...     "epa_aqs", "PM25_Annual", list(range(2015, 2025))
            ... )
            >>> print(pending)  # [2023, 2024] (if others are done)
        """
        if source not in self.progress["sources"]:
            return all_years

        if variable not in self.progress["sources"][source]["variables"]:
            return all_years

        var_progress = self.progress["sources"][source]["variables"][variable]
        completed = set(var_progress["completed_years"])

        pending = [year for year in all_years if year not in completed]
        return pending

    def get_failed_downloads(
        self,
        source: str,
        variable: str,
    ) -> List[int]:
        """
        Get list of years that failed to download.

        Args:
            source: Data source name
            variable: Variable name

        Returns:
            List of failed years
        """
        if source not in self.progress["sources"]:
            return []

        if variable not in self.progress["sources"][source]["variables"]:
            return []

        var_progress = self.progress["sources"][source]["variables"][variable]
        return var_progress["failed_years"]

    def mark_source_complete(self, source: str) -> None:
        """
        Mark entire source as complete.

        Args:
            source: Data source name
        """
        if source in self.progress["sources"]:
            self.progress["sources"][source]["status"] = "completed"
            self._save_progress()
            logger.info(f"✅ Source completed: {source}")

    # ========================================================================
    # PROGRESS STATISTICS
    # ========================================================================

    def get_progress_summary(self, source: Optional[str] = None) -> Dict:
        """
        Get progress summary statistics.

        Args:
            source: Optional source name (None = all sources)

        Returns:
            Dictionary with progress statistics

        Example:
            >>> tracker = ProgressTracker()
            >>> summary = tracker.get_progress_summary("epa_aqs")
            >>> print(summary["total_downloads"])
            >>> print(summary["completion_pct"])
        """
        if source:
            sources_to_check = [source] if source in self.progress["sources"] else []
        else:
            sources_to_check = list(self.progress["sources"].keys())

        total_completed = 0
        total_failed = 0
        total_pending = 0
        variable_count = 0

        for src in sources_to_check:
            for var, var_progress in self.progress["sources"][src]["variables"].items():
                variable_count += 1
                total_completed += len(var_progress["completed_years"])
                total_failed += len(var_progress["failed_years"])
                total_pending += len(var_progress["pending_years"])

        total_downloads = total_completed + total_failed + total_pending

        summary = {
            "source": source if source else "ALL",
            "variables": variable_count,
            "total_downloads": total_downloads,
            "completed": total_completed,
            "failed": total_failed,
            "pending": total_pending,
            "completion_pct": (
                round(total_completed / total_downloads * 100, 2)
                if total_downloads > 0
                else 0.0
            ),
        }

        logger.info(
            f"Progress for {summary['source']}: "
            f"{summary['completed']}/{summary['total_downloads']} "
            f"({summary['completion_pct']}%)"
        )

        return summary

    def get_all_completed_downloads(self, source: str) -> List[Dict]:
        """
        Get all completed downloads for a source.

        Args:
            source: Data source name

        Returns:
            List of dictionaries with variable/year info

        Example:
            >>> tracker = ProgressTracker()
            >>> completed = tracker.get_all_completed_downloads("epa_aqs")
            >>> for item in completed:
            ...     print(f"{item['variable']} - {item['year']}")
        """
        if source not in self.progress["sources"]:
            return []

        completed = []

        for variable, var_progress in self.progress["sources"][source]["variables"].items():
            for year in var_progress["completed_years"]:
                completed.append({"variable": variable, "year": year})

        return completed

    # ========================================================================
    # RESET AND MAINTENANCE
    # ========================================================================

    def reset_source(self, source: str, confirm: bool = False) -> None:
        """
        Reset progress for a source (use with caution).

        Args:
            source: Data source name
            confirm: Must be True to actually reset
        """
        if not confirm:
            logger.warning(f"Reset not confirmed for {source}")
            return

        if source in self.progress["sources"]:
            del self.progress["sources"][source]
            self._save_progress()
            logger.warning(f"⚠️ Reset progress for source: {source}")

    def reset_variable(
        self,
        source: str,
        variable: str,
        confirm: bool = False,
    ) -> None:
        """
        Reset progress for a specific variable.

        Args:
            source: Data source name
            variable: Variable name
            confirm: Must be True to actually reset
        """
        if not confirm:
            logger.warning(f"Reset not confirmed for {source}/{variable}")
            return

        if (
            source in self.progress["sources"]
            and variable in self.progress["sources"][source]["variables"]
        ):
            del self.progress["sources"][source]["variables"][variable]
            self._save_progress()
            logger.warning(f"⚠️ Reset progress for {source}/{variable}")

    def export_progress(self, output_path: Path) -> None:
        """
        Export progress to human-readable format.

        Args:
            output_path: Path to export file

        Example:
            >>> tracker = ProgressTracker()
            >>> tracker.export_progress(Path("progress_report.json"))
        """
        write_json_file(self.progress, output_path)
        logger.info(f"Exported progress to {output_path}")


# ============================================================================
# SPECIALIZED TRACKERS
# ============================================================================


class ProcessingProgressTracker(ProgressTracker):
    """
    Track processing progress (cache → TSV).

    Same interface as ProgressTracker but for processing operations.
    """

    def __init__(self):
        super().__init__(progress_file=PROCESSING_PROGRESS_PATH)


class MapProgressTracker(ProgressTracker):
    """
    Track map generation progress (TSV → PNG).

    Same interface as ProgressTracker but for mapping operations.
    """

    def __init__(self):
        super().__init__(progress_file=MAP_PROGRESS_PATH)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global tracker instances
_download_tracker = None
_processing_tracker = None
_map_tracker = None


def get_download_tracker() -> ProgressTracker:
    """Get download progress tracker (singleton)."""
    global _download_tracker
    if _download_tracker is None:
        _download_tracker = ProgressTracker()
    return _download_tracker


def get_processing_tracker() -> ProcessingProgressTracker:
    """Get processing progress tracker (singleton)."""
    global _processing_tracker
    if _processing_tracker is None:
        _processing_tracker = ProcessingProgressTracker()
    return _processing_tracker


def get_map_tracker() -> MapProgressTracker:
    """Get map progress tracker (singleton)."""
    global _map_tracker
    if _map_tracker is None:
        _map_tracker = MapProgressTracker()
    return _map_tracker


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ProgressTracker",
    "ProcessingProgressTracker",
    "MapProgressTracker",
    "get_download_tracker",
    "get_processing_tracker",
    "get_map_tracker",
]
