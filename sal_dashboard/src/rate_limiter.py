"""
Rate limiting and API throttling utilities.

Provides decorators and context managers for rate limiting API calls
with exponential backoff and request queuing.
"""

from __future__ import annotations

import functools
import time
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class RateLimiter:
    """
    Rate limiter with per-API throttling and exponential backoff.
    
    Features:
    - Per-API key rate limiting
    - Exponential backoff on rate limit errors
    - Request queuing with max wait time
    - Thread-safe operations
    """

    def __init__(
        self,
        max_calls_per_minute: int = 60,
        max_calls_per_hour: int = 1000,
        backoff_factor: float = 2.0,
        max_backoff_seconds: int = 300,
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_calls_per_minute: Maximum API calls per minute per key
            max_calls_per_hour: Maximum API calls per hour per key
            backoff_factor: Multiplier for exponential backoff
            max_backoff_seconds: Maximum backoff time in seconds
        """
        self.max_calls_per_minute = max_calls_per_minute
        self.max_calls_per_hour = max_calls_per_hour
        self.backoff_factor = backoff_factor
        self.max_backoff_seconds = max_backoff_seconds
        
        # Track calls per API key
        self.minute_calls: dict[str, list[datetime]] = defaultdict(list)
        self.hour_calls: dict[str, list[datetime]] = defaultdict(list)
        self.backoff_until: dict[str, datetime] = {}
        self.lock = Lock()

    def _cleanup_old_calls(self, api_key: str) -> None:
        """Remove calls older than 1 hour."""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean minute window
        self.minute_calls[api_key] = [
            call_time for call_time in self.minute_calls[api_key]
            if call_time > one_minute_ago
        ]
        
        # Clean hour window
        self.hour_calls[api_key] = [
            call_time for call_time in self.hour_calls[api_key]
            if call_time > one_hour_ago
        ]

    def _wait_if_needed(self, api_key: str) -> None:
        """Wait if rate limit is exceeded or backoff is active."""
        now = datetime.utcnow()
        
        # Check if we're in backoff period
        if api_key in self.backoff_until:
            if now < self.backoff_until[api_key]:
                wait_seconds = (self.backoff_until[api_key] - now).total_seconds()
                time.sleep(min(wait_seconds, self.max_backoff_seconds))
            else:
                # Backoff period expired
                del self.backoff_until[api_key]
        
        # Clean old calls
        self._cleanup_old_calls(api_key)
        
        # Check minute limit
        if len(self.minute_calls[api_key]) >= self.max_calls_per_minute:
            oldest_call = min(self.minute_calls[api_key])
            wait_until = oldest_call + timedelta(minutes=1)
            wait_seconds = (wait_until - now).total_seconds()
            if wait_seconds > 0:
                time.sleep(min(wait_seconds, 60))
            self._cleanup_old_calls(api_key)
        
        # Check hour limit
        if len(self.hour_calls[api_key]) >= self.max_calls_per_hour:
            oldest_call = min(self.hour_calls[api_key])
            wait_until = oldest_call + timedelta(hours=1)
            wait_seconds = (wait_until - now).total_seconds()
            if wait_seconds > 0:
                raise RateLimitError(
                    f"Hourly rate limit exceeded for {api_key}. "
                    f"Please wait {wait_seconds:.0f} seconds."
                )

    def _record_call(self, api_key: str) -> None:
        """Record an API call."""
        now = datetime.utcnow()
        self.minute_calls[api_key].append(now)
        self.hour_calls[api_key].append(now)

    def _handle_rate_limit_error(self, api_key: str, retry_count: int) -> None:
        """Handle rate limit error with exponential backoff."""
        backoff_seconds = min(
            self.backoff_factor ** retry_count,
            self.max_backoff_seconds
        )
        self.backoff_until[api_key] = datetime.utcnow() + timedelta(seconds=backoff_seconds)
        time.sleep(backoff_seconds)

    def call(
        self,
        api_key: str,
        func: Callable[[], T],
        max_retries: int = 3,
    ) -> T:
        """
        Execute a function with rate limiting.
        
        Args:
            api_key: Identifier for the API being called
            func: Function to execute
            max_retries: Maximum number of retries on rate limit errors
            
        Returns:
            Result of function execution
            
        Raises:
            RateLimitError: If rate limit cannot be satisfied
        """
        with self.lock:
            self._wait_if_needed(api_key)
            self._record_call(api_key)
        
        retry_count = 0
        while retry_count <= max_retries:
            try:
                return func()
            except RateLimitException as e:
                retry_count += 1
                if retry_count > max_retries:
                    raise RateLimitError(
                        f"Rate limit exceeded after {max_retries} retries: {e}"
                    )
                with self.lock:
                    self._handle_rate_limit_error(api_key, retry_count)
            except Exception as e:
                # Check if error is rate limit related
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ["rate limit", "429", "too many requests"]):
                    retry_count += 1
                    if retry_count > max_retries:
                        raise RateLimitError(
                            f"Rate limit exceeded after {max_retries} retries: {e}"
                        )
                    with self.lock:
                        self._handle_rate_limit_error(api_key, retry_count)
                else:
                    raise

    def limit(self, api_key: str, max_retries: int = 3):
        """
        Decorator for rate limiting function calls.
        
        Usage:
            @rate_limiter.limit("yfinance")
            def fetch_data():
                ...
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                return self.call(api_key, lambda: func(*args, **kwargs), max_retries)
            return wrapper
        return decorator


class RateLimitError(Exception):
    """Raised when rate limit cannot be satisfied."""
    pass


class RateLimitException(Exception):
    """Raised by API when rate limit is exceeded."""
    pass


# Global rate limiter instance
_global_rate_limiter: RateLimiter | None = None


def get_rate_limiter(
    max_calls_per_minute: int = 60,
    max_calls_per_hour: int = 1000,
) -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(
            max_calls_per_minute=max_calls_per_minute,
            max_calls_per_hour=max_calls_per_hour,
        )
    return _global_rate_limiter


__all__ = ["RateLimiter", "RateLimitError", "RateLimitException", "get_rate_limiter"]

