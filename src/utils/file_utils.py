"""
File I/O utilities using Polars for maximum performance.

This module provides fast, reusable file operations with a consistent interface.
Uses Polars (Rust-based) for 10-100x speed improvement over pandas.

Design Patterns:
- Strategy Pattern: Different readers for different formats
- Factory Pattern: Auto-detect format and use appropriate reader
- Singleton Pattern: Cache file schemas for reuse
"""

import gzip
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import polars as pl
import yaml
from loguru import logger

from utils.constants import (
    EXT_CSV,
    EXT_GEOTIFF,
    EXT_GZIP,
    EXT_JSON,
    EXT_PARQUET,
    EXT_TSV,
    EXT_YAML,
    EXT_ZIP,
    TSV_DELIMITER,
    TSV_ENCODING,
    TSV_NA_VALUE,
)


# ============================================================================
# FILE READING (Polars-based for speed)
# ============================================================================


def read_tsv(
    file_path: Union[str, Path],
    schema: Optional[Dict[str, pl.DataType]] = None,
    lazy: bool = False,
) -> Union[pl.DataFrame, pl.LazyFrame]:
    """
    Read TSV file using Polars (10-100x faster than pandas).

    Args:
        file_path: Path to TSV file
        schema: Optional schema specification for type safety
        lazy: If True, return LazyFrame for query optimization

    Returns:
        Polars DataFrame or LazyFrame

    Example:
        >>> df = read_tsv("data.tsv")
        >>> df_lazy = read_tsv("data.tsv", lazy=True)
        >>> result = df_lazy.filter(pl.col("Value") > 100).collect()
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"TSV file not found: {file_path}")

    logger.debug(f"Reading TSV: {file_path}")

    try:
        if lazy:
            return pl.scan_csv(
                file_path,
                separator=TSV_DELIMITER,
                null_values=TSV_NA_VALUE,
                dtypes=schema,
            )
        else:
            return pl.read_csv(
                file_path,
                separator=TSV_DELIMITER,
                null_values=TSV_NA_VALUE,
                dtypes=schema,
            )
    except Exception as e:
        logger.error(f"Error reading TSV {file_path}: {e}")
        raise


def read_csv(
    file_path: Union[str, Path],
    schema: Optional[Dict[str, pl.DataType]] = None,
    lazy: bool = False,
) -> Union[pl.DataFrame, pl.LazyFrame]:
    """
    Read CSV file using Polars.

    Args:
        file_path: Path to CSV file
        schema: Optional schema specification
        lazy: If True, return LazyFrame

    Returns:
        Polars DataFrame or LazyFrame
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    logger.debug(f"Reading CSV: {file_path}")

    try:
        if lazy:
            return pl.scan_csv(file_path, dtypes=schema)
        else:
            return pl.read_csv(file_path, dtypes=schema)
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        raise


def read_parquet(
    file_path: Union[str, Path],
    lazy: bool = False,
) -> Union[pl.DataFrame, pl.LazyFrame]:
    """
    Read Parquet file using Polars (extremely fast, columnar format).

    Parquet is recommended for intermediate caching (much faster than CSV).

    Args:
        file_path: Path to Parquet file
        lazy: If True, return LazyFrame

    Returns:
        Polars DataFrame or LazyFrame
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")

    logger.debug(f"Reading Parquet: {file_path}")

    try:
        if lazy:
            return pl.scan_parquet(file_path)
        else:
            return pl.read_parquet(file_path)
    except Exception as e:
        logger.error(f"Error reading Parquet {file_path}: {e}")
        raise


def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary with JSON contents
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    logger.debug(f"Reading JSON: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON {file_path}: {e}")
        raise


def read_yaml_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        Dictionary with YAML contents
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    logger.debug(f"Reading YAML: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error reading YAML {file_path}: {e}")
        raise


# ============================================================================
# FILE WRITING
# ============================================================================


def write_tsv(
    df: Union[pl.DataFrame, pl.LazyFrame],
    file_path: Union[str, Path],
    create_dirs: bool = True,
) -> None:
    """
    Write DataFrame to TSV file using Polars (fast).

    Args:
        df: Polars DataFrame or LazyFrame
        file_path: Output TSV path
        create_dirs: If True, create parent directories
    """
    file_path = Path(file_path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Writing TSV: {file_path}")

    try:
        # Collect LazyFrame if needed
        if isinstance(df, pl.LazyFrame):
            df = df.collect()

        df.write_csv(
            file_path,
            separator=TSV_DELIMITER,
            null_value=TSV_NA_VALUE,
        )

        logger.info(f"Successfully wrote TSV: {file_path} ({len(df)} rows)")
    except Exception as e:
        logger.error(f"Error writing TSV {file_path}: {e}")
        raise


def write_parquet(
    df: Union[pl.DataFrame, pl.LazyFrame],
    file_path: Union[str, Path],
    compression: str = "zstd",
    create_dirs: bool = True,
) -> None:
    """
    Write DataFrame to Parquet file (recommended for caching).

    Parquet is columnar, compressed, and 10x smaller + faster than CSV.

    Args:
        df: Polars DataFrame or LazyFrame
        file_path: Output Parquet path
        compression: Compression algorithm (zstd, snappy, gzip, lz4)
        create_dirs: If True, create parent directories
    """
    file_path = Path(file_path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Writing Parquet: {file_path}")

    try:
        # Collect LazyFrame if needed
        if isinstance(df, pl.LazyFrame):
            df = df.collect()

        df.write_parquet(file_path, compression=compression)

        logger.info(f"Successfully wrote Parquet: {file_path} ({len(df)} rows)")
    except Exception as e:
        logger.error(f"Error writing Parquet {file_path}: {e}")
        raise


def write_json_file(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    indent: int = 2,
    create_dirs: bool = True,
) -> None:
    """
    Write dictionary to JSON file.

    Args:
        data: Dictionary to write
        file_path: Output JSON path
        indent: Indentation level (2 for readability)
        create_dirs: If True, create parent directories
    """
    file_path = Path(file_path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Writing JSON: {file_path}")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

        logger.info(f"Successfully wrote JSON: {file_path}")
    except Exception as e:
        logger.error(f"Error writing JSON {file_path}: {e}")
        raise


def write_yaml_file(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    create_dirs: bool = True,
) -> None:
    """
    Write dictionary to YAML file.

    Args:
        data: Dictionary to write
        file_path: Output YAML path
        create_dirs: If True, create parent directories
    """
    file_path = Path(file_path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Writing YAML: {file_path}")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Successfully wrote YAML: {file_path}")
    except Exception as e:
        logger.error(f"Error writing YAML {file_path}: {e}")
        raise


# ============================================================================
# COMPRESSED FILE HANDLING
# ============================================================================


def extract_zip(
    zip_path: Union[str, Path],
    extract_to: Union[str, Path],
    file_filter: Optional[str] = None,
) -> List[Path]:
    """
    Extract ZIP archive.

    Args:
        zip_path: Path to ZIP file
        extract_to: Directory to extract to
        file_filter: Optional glob pattern to filter files (e.g., "*.csv")

    Returns:
        List of extracted file paths
    """
    zip_path = Path(zip_path)
    extract_to = Path(extract_to)

    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    extract_to.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Extracting ZIP: {zip_path} to {extract_to}")

    extracted_files = []

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                # Apply file filter if specified
                if file_filter is None or Path(file_info.filename).match(file_filter):
                    zip_ref.extract(file_info, extract_to)
                    extracted_files.append(extract_to / file_info.filename)

        logger.info(f"Extracted {len(extracted_files)} files from {zip_path}")
        return extracted_files

    except Exception as e:
        logger.error(f"Error extracting ZIP {zip_path}: {e}")
        raise


def read_gzipped_file(file_path: Union[str, Path]) -> bytes:
    """
    Read gzipped file.

    Args:
        file_path: Path to .gz file

    Returns:
        Decompressed bytes
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Gzipped file not found: {file_path}")

    logger.debug(f"Reading gzipped file: {file_path}")

    try:
        with gzip.open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading gzipped file {file_path}: {e}")
        raise


# ============================================================================
# FILE VALIDATION AND UTILITIES
# ============================================================================


def validate_file_exists(file_path: Union[str, Path]) -> Path:
    """
    Validate that file exists and return Path object.

    Args:
        file_path: Path to validate

    Returns:
        Validated Path object

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return file_path


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to file

    Returns:
        File size in MB
    """
    file_path = validate_file_exists(file_path)
    size_bytes = file_path.stat().st_size
    return size_bytes / (1024 * 1024)


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """
    Ensure directory exists (create if not).

    Args:
        dir_path: Directory path

    Returns:
        Path object for directory
    """
    dir_path = Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def list_files_by_pattern(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False,
) -> List[Path]:
    """
    List files matching pattern.

    Args:
        directory: Directory to search
        pattern: Glob pattern (e.g., "*.csv", "**/*.tsv")
        recursive: If True, search recursively

    Returns:
        List of matching file paths
    """
    directory = Path(directory)

    if not directory.exists():
        logger.warning(f"Directory not found: {directory}")
        return []

    if recursive:
        files = list(directory.rglob(pattern))
    else:
        files = list(directory.glob(pattern))

    logger.debug(f"Found {len(files)} files matching '{pattern}' in {directory}")
    return files


# ============================================================================
# FORMAT AUTO-DETECTION (Factory Pattern)
# ============================================================================


def read_dataframe_auto(
    file_path: Union[str, Path],
    lazy: bool = False,
) -> Union[pl.DataFrame, pl.LazyFrame]:
    """
    Automatically detect format and read file (Factory Pattern).

    Supports: TSV, CSV, Parquet

    Args:
        file_path: Path to data file
        lazy: If True, return LazyFrame where possible

    Returns:
        Polars DataFrame or LazyFrame
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == EXT_TSV:
        return read_tsv(file_path, lazy=lazy)
    elif suffix == EXT_CSV:
        return read_csv(file_path, lazy=lazy)
    elif suffix == EXT_PARQUET:
        return read_parquet(file_path, lazy=lazy)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


# ============================================================================
# SCHEMA UTILITIES
# ============================================================================


def get_tsv_schema() -> Dict[str, pl.DataType]:
    """
    Get standard TSV schema for county-level data.

    Returns:
        Dictionary mapping column names to Polars data types
    """
    return {
        "FIPS": pl.Utf8,  # String to preserve leading zeros
        "State_FIPS": pl.Utf8,
        "County_FIPS": pl.Utf8,
        "State_Name": pl.Utf8,
        "County_Name": pl.Utf8,
        "State_Abbrev": pl.Utf8,
        "Year": pl.Int32,
        "Value": pl.Float64,
        "Unit": pl.Utf8,
    }


def validate_tsv_schema(df: pl.DataFrame) -> bool:
    """
    Validate DataFrame has required TSV columns.

    Args:
        df: Polars DataFrame to validate

    Returns:
        True if valid, raises ValueError if not
    """
    required_columns = list(get_tsv_schema().keys())
    actual_columns = df.columns

    missing_columns = set(required_columns) - set(actual_columns)

    if missing_columns:
        raise ValueError(
            f"TSV missing required columns: {missing_columns}. "
            f"Expected: {required_columns}"
        )

    return True
