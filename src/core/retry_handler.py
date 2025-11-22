"""
Retry Handler with exponential backoff for robust downloads.

Handles transient failures gracefully:
- Network timeouts
- API rate limits (429 errors)
- Server errors (5xx)
- Temporary unavailability

Uses exponential backoff: 1s, 2s, 4s, 8s, ...

Design Patterns:
- Decorator: @retry_on_failure decorator for functions
- Strategy: Different retry strategies for different error types
"""

import functools
import time
from typing import Any, Callable, Optional, Tuple, Type

import requests
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from utils.constants import (
    BACKOFF_FACTOR,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
)


# ============================================================================
# RETRY DECORATORS
# ============================================================================


def retry_on_failure(
    max_attempts: int = MAX_RETRIES,
    backoff_factor: float = BACKOFF_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_level: str = "WARNING",
) -> Callable:
    """
    Decorator to retry function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        exceptions: Tuple of exception types to catch
        log_level: Log level for retry messages

    Example:
        >>> @retry_on_failure(max_attempts=3)
        ... def download_data(url):
        ...     response = requests.get(url)
        ...     response.raise_for_status()
        ...     return response.json()
        >>>
        >>> data = download_data("https://api.example.com/data")
        # Retries up to 3 times with exponential backoff on any exception
    """

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=backoff_factor, min=1, max=60),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, getattr(logger, log_level.lower())),
            reraise=True,
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def retry_on_http_error(
    max_attempts: int = MAX_RETRIES,
    backoff_factor: float = BACKOFF_FACTOR,
    retry_on_status: Tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Callable:
    """
    Decorator to retry HTTP requests on specific status codes.

    Args:
        max_attempts: Maximum retry attempts
        backoff_factor: Exponential backoff multiplier
        retry_on_status: HTTP status codes to retry on

    Example:
        >>> @retry_on_http_error(retry_on_status=(429, 500, 503))
        ... def fetch_api_data(url):
        ...     response = requests.get(url)
        ...     response.raise_for_status()
        ...     return response.json()
        >>>
        >>> data = fetch_api_data("https://api.example.com/endpoint")
        # Retries on rate limit (429) and server errors (500, 503)
    """

    def should_retry(exception):
        """Check if exception warrants a retry."""
        if isinstance(exception, requests.exceptions.HTTPError):
            return exception.response.status_code in retry_on_status
        elif isinstance(exception, requests.exceptions.Timeout):
            return True
        elif isinstance(exception, requests.exceptions.ConnectionError):
            return True
        return False

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=backoff_factor, min=1, max=60),
            retry=retry_if_exception_type(
                (
                    requests.exceptions.HTTPError,
                    requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                )
            ),
            before_sleep=before_sleep_log(logger, logger.level("WARNING").no),
            reraise=True,
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                if should_retry(e):
                    logger.warning(
                        f"HTTP error {e.response.status_code}: {e}. Retrying..."
                    )
                    raise
                else:
                    logger.error(f"HTTP error (no retry): {e}")
                    raise
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
            ) as e:
                logger.warning(f"Network error: {e}. Retrying...")
                raise

        return wrapper

    return decorator


# ============================================================================
# RATE LIMITER
# ============================================================================


class RateLimiter:
    """
    Simple rate limiter for API calls.

    Ensures we don't exceed rate limits.

    Example:
        >>> limiter = RateLimiter(requests_per_second=5)
        >>> for item in items:
        ...     limiter.wait()
        ...     result = api_call(item)
    """

    def __init__(self, requests_per_second: float = 5.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def __call__(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with rate limiting.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        self.wait()
        return func(*args, **kwargs)


# ============================================================================
# ROBUST HTTP CLIENT
# ============================================================================


class RobustHTTPClient:
    """
    HTTP client with automatic retries and rate limiting.

    Combines retry logic, rate limiting, and timeout handling.

    Example:
        >>> client = RobustHTTPClient(rate_limit=5.0)
        >>> response = client.get("https://api.example.com/data")
        >>> data = response.json()
    """

    def __init__(
        self,
        rate_limit: Optional[float] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Initialize HTTP client.

        Args:
            rate_limit: Requests per second (None = no limit)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries

        # Setup rate limiter if specified
        if rate_limit:
            self.rate_limiter = RateLimiter(rate_limit)
        else:
            self.rate_limiter = None

        # Setup requests session with retry adapter
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            max_retries=max_retries,
            pool_connections=10,
            pool_maxsize=10,
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.debug(
            f"Initialized HTTP client (rate_limit={rate_limit}, "
            f"timeout={timeout}, max_retries={max_retries})"
        )

    @retry_on_http_error()
    def get(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> requests.Response:
        """
        Perform GET request with retries and rate limiting.

        Args:
            url: URL to request
            params: Query parameters
            headers: HTTP headers
            **kwargs: Additional arguments for requests.get()

        Returns:
            Response object

        Raises:
            requests.exceptions.HTTPError: On non-retryable HTTP errors
            requests.exceptions.Timeout: On timeout after retries
            requests.exceptions.ConnectionError: On connection errors after retries
        """
        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.wait()

        logger.debug(f"GET {url}")

        response = self.session.get(
            url,
            params=params,
            headers=headers,
            timeout=self.timeout,
            **kwargs,
        )

        response.raise_for_status()
        return response

    @retry_on_http_error()
    def post(
        self,
        url: str,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> requests.Response:
        """
        Perform POST request with retries and rate limiting.

        Args:
            url: URL to request
            data: Form data
            json: JSON data
            headers: HTTP headers
            **kwargs: Additional arguments for requests.post()

        Returns:
            Response object
        """
        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.wait()

        logger.debug(f"POST {url}")

        response = self.session.post(
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=self.timeout,
            **kwargs,
        )

        response.raise_for_status()
        return response

    def download_file(
        self,
        url: str,
        output_path: str,
        chunk_size: int = 8192,
    ) -> None:
        """
        Download file with progress and retries.

        Args:
            url: URL to download
            output_path: Path to save file
            chunk_size: Download chunk size in bytes

        Example:
            >>> client = RobustHTTPClient()
            >>> client.download_file(
            ...     "https://example.com/data.zip",
            ...     "/tmp/data.zip"
            ... )
        """
        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.wait()

        logger.info(f"Downloading {url} → {output_path}")

        @retry_on_http_error()
        def _download():
            response = self.session.get(
                url,
                stream=True,
                timeout=self.timeout,
            )
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Log progress every 10MB
                        if downloaded % (10 * 1024 * 1024) < chunk_size:
                            if total_size > 0:
                                pct = (downloaded / total_size) * 100
                                logger.debug(
                                    f"Download progress: {pct:.1f}% "
                                    f"({downloaded / 1024 / 1024:.1f} MB)"
                                )

            logger.info(
                f"Downloaded {downloaded / 1024 / 1024:.1f} MB to {output_path}"
            )

        _download()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "retry_on_failure",
    "retry_on_http_error",
    "RateLimiter",
    "RobustHTTPClient",
]
