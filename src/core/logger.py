"""
Comprehensive logging system for the Observatory Data Download System.

Provides structured logging with:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Rotating file handlers (prevents disk fill-up)
- Separate error log
- Context-aware logging (source, variable, year)
- Performance tracking
- JSON structured logs (optional)

Design Patterns:
- Singleton: Single logger instance
- Decorator: Performance timing decorator
"""

import functools
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from loguru import logger as loguru_logger

from utils.constants import (
    DOWNLOAD_LOGS_DIR,
    LOG_BACKUP_COUNT,
    LOG_FORMAT,
    LOG_LEVEL_DEFAULT,
    LOG_MAX_BYTES,
    LOGS_DIR,
    PROCESSING_LOGS_DIR,
)


# ============================================================================
# LOGGER CONFIGURATION
# ============================================================================


class LoggerManager:
    """
    Singleton manager for application logging.

    Uses loguru for beautiful, structured logs with rotation.
    """

    _initialized = False

    @classmethod
    def setup(
        cls,
        log_level: str = LOG_LEVEL_DEFAULT,
        enable_json: bool = False,
        enable_console: bool = True,
    ) -> None:
        """
        Initialize logging system (call once at app startup).

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_json: If True, write JSON-structured logs
            enable_console: If True, log to console
        """
        if cls._initialized:
            loguru_logger.debug("Logger already initialized")
            return

        # Create log directories
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        DOWNLOAD_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSING_LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Remove default handler
        loguru_logger.remove()

        # Console handler (colorized, human-readable)
        if enable_console:
            loguru_logger.add(
                sys.stderr,
                level=log_level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                       "<level>{level: <8}</level> | "
                       "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                       "<level>{message}</level>",
                colorize=True,
            )

        # Main log file (rotating)
        main_log = LOGS_DIR / "main.log"
        loguru_logger.add(
            main_log,
            level=log_level,
            format=LOG_FORMAT,
            rotation=LOG_MAX_BYTES,  # Rotate when file reaches 10MB
            retention=LOG_BACKUP_COUNT,  # Keep last 10 files
            compression="zip",  # Compress old logs
            enqueue=True,  # Thread-safe
        )

        # Error-only log file (rotating)
        error_log = LOGS_DIR / "errors.log"
        loguru_logger.add(
            error_log,
            level="ERROR",
            format=LOG_FORMAT,
            rotation=LOG_MAX_BYTES,
            retention=LOG_BACKUP_COUNT,
            compression="zip",
            enqueue=True,
        )

        # JSON structured log (optional, for parsing)
        if enable_json:
            json_log = LOGS_DIR / "structured.json"
            loguru_logger.add(
                json_log,
                level=log_level,
                format="{message}",
                serialize=True,  # Output as JSON
                rotation=LOG_MAX_BYTES,
                retention=LOG_BACKUP_COUNT,
                compression="zip",
            )

        cls._initialized = True
        loguru_logger.info(
            f"Logger initialized (level={log_level}, "
            f"main={main_log}, errors={error_log})"
        )

    @classmethod
    def create_source_logger(
        cls,
        source_name: str,
        log_level: str = LOG_LEVEL_DEFAULT,
    ) -> loguru_logger:
        """
        Create a dedicated logger for a specific data source.

        Each source gets its own log file for easier debugging.

        Args:
            source_name: Name of data source (e.g., "epa_aqs", "nhgis")
            log_level: Logging level

        Returns:
            Configured logger instance

        Example:
            >>> logger = LoggerManager.create_source_logger("nhgis")
            >>> logger.info("Downloading extract 123")
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = DOWNLOAD_LOGS_DIR / f"{source_name}_{timestamp}.log"

        # Create source-specific logger
        source_logger = loguru_logger.bind(source=source_name)

        # Add source-specific file handler
        source_logger.add(
            log_file,
            level=log_level,
            format=LOG_FORMAT,
            rotation=LOG_MAX_BYTES,
            retention=5,  # Keep last 5 runs
            filter=lambda record: record["extra"].get("source") == source_name,
        )

        source_logger.info(f"Created source logger: {source_name} -> {log_file}")

        return source_logger


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def setup_logging(
    log_level: str = LOG_LEVEL_DEFAULT,
    enable_json: bool = False,
    enable_console: bool = True,
) -> None:
    """
    Setup logging system (convenience function).

    Call this once at the start of your script.

    Args:
        log_level: Logging level
        enable_json: Enable JSON structured logging
        enable_console: Enable console logging

    Example:
        >>> from src.core.logger import setup_logging
        >>> setup_logging(log_level="DEBUG")
    """
    LoggerManager.setup(
        log_level=log_level,
        enable_json=enable_json,
        enable_console=enable_console,
    )


def get_logger() -> loguru_logger:
    """
    Get the global logger instance.

    Returns:
        Configured logger

    Example:
        >>> from src.core.logger import get_logger
        >>> logger = get_logger()
        >>> logger.info("Starting download")
    """
    if not LoggerManager._initialized:
        LoggerManager.setup()

    return loguru_logger


# ============================================================================
# CONTEXT LOGGING
# ============================================================================


class LogContext:
    """
    Context manager for structured logging with automatic timing.

    Example:
        >>> with LogContext("Downloading PM2.5 data", year=2020):
        ...     download_data()
        # Logs: "Downloading PM2.5 data" (start)
        # Logs: "Downloading PM2.5 data completed in 5.2s" (end)
    """

    def __init__(
        self,
        operation: str,
        logger_instance: Optional[loguru_logger] = None,
        **kwargs,
    ):
        """
        Initialize log context.

        Args:
            operation: Description of operation
            logger_instance: Logger to use (default: global logger)
            **kwargs: Additional context to log
        """
        self.operation = operation
        self.logger = logger_instance if logger_instance else get_logger()
        self.context = kwargs
        self.start_time = None

    def __enter__(self):
        """Start operation and log."""
        self.start_time = time.time()

        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        msg = f"{self.operation}"
        if context_str:
            msg += f" ({context_str})"

        self.logger.info(f"START: {msg}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End operation and log duration."""
        duration = time.time() - self.start_time

        if exc_type is None:
            # Success
            self.logger.info(
                f"COMPLETED: {self.operation} in {duration:.2f}s"
            )
        else:
            # Error
            self.logger.error(
                f"FAILED: {self.operation} after {duration:.2f}s - {exc_val}"
            )

        return False  # Don't suppress exceptions


# ============================================================================
# PERFORMANCE TIMING DECORATOR
# ============================================================================


def log_performance(
    operation: Optional[str] = None,
    log_args: bool = False,
) -> Callable:
    """
    Decorator to log function execution time.

    Args:
        operation: Custom operation name (default: function name)
        log_args: If True, log function arguments

    Example:
        >>> @log_performance()
        ... def download_data(year):
        ...     time.sleep(2)
        ...     return "data"
        >>>
        >>> result = download_data(2020)
        # Logs: "download_data completed in 2.01s"

        >>> @log_performance(operation="Downloading EPA data", log_args=True)
        ... def fetch_epa(year, param):
        ...     pass
        # Logs: "Downloading EPA data (year=2020, param='PM25') completed in 1.5s"
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger_instance = get_logger()

            op_name = operation if operation else func.__name__

            # Log arguments if requested
            if log_args:
                args_str = ", ".join(str(arg) for arg in args)
                kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                all_args = ", ".join(filter(None, [args_str, kwargs_str]))
                logger_instance.debug(f"{op_name}({all_args})")

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger_instance.info(
                    f"{op_name} completed in {duration:.2f}s"
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger_instance.error(
                    f"{op_name} failed after {duration:.2f}s: {e}"
                )

                raise

        return wrapper

    return decorator


# ============================================================================
# STRUCTURED EVENT LOGGING
# ============================================================================


def log_download_event(
    source: str,
    variable: str,
    year: int,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log download event in structured format.

    Args:
        source: Data source name
        variable: Variable name
        year: Year
        status: "started", "completed", "failed"
        details: Additional details (error message, file size, etc.)

    Example:
        >>> log_download_event(
        ...     source="epa_aqs",
        ...     variable="PM25",
        ...     year=2020,
        ...     status="completed",
        ...     details={"file_size_mb": 5.2, "records": 15000}
        ... )
    """
    logger_instance = get_logger()

    event = {
        "event_type": "download",
        "source": source,
        "variable": variable,
        "year": year,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }

    if details:
        event.update(details)

    # Log as both human-readable and JSON
    msg = f"[{source}] {variable} ({year}): {status.upper()}"
    if details:
        msg += f" - {details}"

    if status == "failed":
        logger_instance.error(msg)
    else:
        logger_instance.info(msg)

    # Also log as structured data (if JSON logging enabled)
    logger_instance.bind(**event).debug(json.dumps(event))


def log_processing_event(
    variable: str,
    year: int,
    status: str,
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    records_processed: Optional[int] = None,
) -> None:
    """
    Log processing event.

    Args:
        variable: Variable name
        year: Year
        status: "started", "completed", "failed"
        input_path: Input file path
        output_path: Output file path
        records_processed: Number of records processed
    """
    logger_instance = get_logger()

    event = {
        "event_type": "processing",
        "variable": variable,
        "year": year,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }

    if input_path:
        event["input_path"] = str(input_path)
    if output_path:
        event["output_path"] = str(output_path)
    if records_processed is not None:
        event["records_processed"] = records_processed

    msg = f"[PROCESS] {variable} ({year}): {status.upper()}"
    if records_processed:
        msg += f" - {records_processed} records"

    if status == "failed":
        logger_instance.error(msg)
    else:
        logger_instance.info(msg)

    logger_instance.bind(**event).debug(json.dumps(event))


# ============================================================================
# EXPORTS
# ============================================================================

# Export main functions for convenience
__all__ = [
    "setup_logging",
    "get_logger",
    "LogContext",
    "log_performance",
    "log_download_event",
    "log_processing_event",
    "LoggerManager",
]


# Auto-initialize on import (with defaults)
if not LoggerManager._initialized:
    LoggerManager.setup()
