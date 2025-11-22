"""
Core framework modules for the Observatory Data Download System.

This package provides the foundational components:
- logger: Comprehensive logging system
- cache_manager: Intelligent caching
- progress_tracker: Progress tracking and resumability
- metadata_manager: FIPS codes and county boundaries
- tsv_generator: TSV file creation with metadata
- map_generator: Choropleth map generation
- base_downloader: Abstract base class for downloaders
- retry_handler: Exponential backoff retry logic
"""

import core.logger as logger

__all__ = ["logger"]
