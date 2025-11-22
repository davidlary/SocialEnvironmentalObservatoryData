"""
US County-Level Observatory Data Download System

This package provides automated download, processing, and visualization
of county-level data from 200+ authoritative sources.

Main modules:
- core: Core framework (logger, cache, progress tracking, etc.)
- downloaders: Source-specific downloaders
- processors: Data processing and aggregation
- utils: Utility functions and constants
"""

__version__ = "1.0.0"
__author__ = "David Lary"

# Make core modules easily accessible
import core
import utils

__all__ = ["core", "utils"]
