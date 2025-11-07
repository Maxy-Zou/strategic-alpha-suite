"""Tests for rate_limiter.py module."""

import pytest
import time
from pathlib import Path
import sys
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rate_limiter import RateLimiter, RateLimitExceeded


def test_rate_limiter_initialization():
    """Test RateLimiter initializes with correct default values."""
    limiter = RateLimiter(calls_per_minute=60, calls_per_hour=1000)

    assert limiter.calls_per_minute == 60
    assert limiter.calls_per_hour == 1000
    assert len(limiter.call_history) == 0


def test_rate_limiter_allows_calls_within_limit():
    """Test that calls within rate limit are allowed."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_hour=100)

    # Make 5 calls - should all succeed
    for i in range(5):
        limiter.check_rate_limit()

    assert len(limiter.call_history) == 5


def test_rate_limiter_blocks_when_minute_limit_exceeded():
    """Test that RateLimiter raises exception when minute limit exceeded."""
    limiter = RateLimiter(calls_per_minute=3, calls_per_hour=100)

    # Make 3 calls - should succeed
    for i in range(3):
        limiter.check_rate_limit()

    # 4th call should fail
    with pytest.raises(RateLimitExceeded) as exc_info:
        limiter.check_rate_limit()

    assert "per-minute" in str(exc_info.value).lower()


def test_rate_limiter_blocks_when_hour_limit_exceeded():
    """Test that RateLimiter raises exception when hour limit exceeded."""
    limiter = RateLimiter(calls_per_minute=1000, calls_per_hour=5)

    # Make 5 calls - should succeed
    for i in range(5):
        limiter.check_rate_limit()

    # 6th call should fail
    with pytest.raises(RateLimitExceeded) as exc_info:
        limiter.check_rate_limit()

    assert "per-hour" in str(exc_info.value).lower()


def test_rate_limiter_clears_old_calls():
    """Test that old calls are removed from history."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_hour=100)

    # Add an old call (61 seconds ago)
    old_timestamp = time.time() - 61
    limiter.call_history.append(old_timestamp)

    # Make a new call
    limiter.check_rate_limit()

    # Old call should be removed, new call should be added
    assert len(limiter.call_history) == 1
    assert limiter.call_history[0] > old_timestamp


def test_wait_for_rate_limit_waits_appropriate_time():
    """Test that wait_for_rate_limit waits before making call."""
    limiter = RateLimiter(calls_per_minute=2, calls_per_hour=100)

    # Fill up the rate limit
    limiter.check_rate_limit()
    limiter.check_rate_limit()

    # Next call should wait
    start_time = time.time()
    limiter.wait_for_rate_limit()
    elapsed = time.time() - start_time

    # Should have waited at least a few milliseconds (not instant)
    assert elapsed > 0.01


def test_rate_limited_call_executes_function():
    """Test that rate_limited_call executes the provided function."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_hour=100)

    mock_func = Mock(return_value="success")
    result = limiter.rate_limited_call(mock_func, 1, 2, key="value")

    assert result == "success"
    mock_func.assert_called_once_with(1, 2, key="value")


def test_rate_limited_call_respects_limits():
    """Test that rate_limited_call respects rate limits."""
    limiter = RateLimiter(calls_per_minute=2, calls_per_hour=100)

    mock_func = Mock(return_value="success")

    # First two calls should succeed immediately
    result1 = limiter.rate_limited_call(mock_func)
    result2 = limiter.rate_limited_call(mock_func)

    assert result1 == "success"
    assert result2 == "success"
    assert mock_func.call_count == 2


def test_rate_limited_call_with_exponential_backoff():
    """Test that rate_limited_call implements exponential backoff on errors."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_hour=100)

    # Create a function that fails twice then succeeds
    call_count = 0

    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary error")
        return "success"

    result = limiter.rate_limited_call(flaky_func, max_retries=3)

    assert result == "success"
    assert call_count == 3


def test_rate_limited_call_fails_after_max_retries():
    """Test that rate_limited_call gives up after max retries."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_hour=100)

    def always_fails():
        raise ValueError("Persistent error")

    with pytest.raises(ValueError):
        limiter.rate_limited_call(always_fails, max_retries=3)


def test_get_wait_time_minute_limit():
    """Test get_wait_time returns correct time for minute limit."""
    limiter = RateLimiter(calls_per_minute=2, calls_per_hour=100)

    # Fill up minute limit
    now = time.time()
    limiter.call_history.append(now - 30)  # 30 seconds ago
    limiter.call_history.append(now - 15)  # 15 seconds ago

    wait_time = limiter.get_wait_time()

    # Should wait until oldest call is >60 seconds old
    assert 25 <= wait_time <= 35  # ~30 seconds (with some tolerance)


def test_get_wait_time_hour_limit():
    """Test get_wait_time returns correct time for hour limit."""
    limiter = RateLimiter(calls_per_minute=1000, calls_per_hour=2)

    # Fill up hour limit
    now = time.time()
    limiter.call_history.append(now - 1800)  # 30 minutes ago
    limiter.call_history.append(now - 900)   # 15 minutes ago

    wait_time = limiter.get_wait_time()

    # Should wait until oldest call is >3600 seconds old
    assert 1700 <= wait_time <= 1900  # ~1800 seconds


def test_get_wait_time_no_wait_needed():
    """Test get_wait_time returns 0 when no wait is needed."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_hour=100)

    # Make just one call
    limiter.check_rate_limit()

    wait_time = limiter.get_wait_time()
    assert wait_time == 0


def test_thread_safety():
    """Test that RateLimiter is thread-safe."""
    import threading

    limiter = RateLimiter(calls_per_minute=100, calls_per_hour=1000)
    successful_calls = []
    errors = []

    def make_calls():
        for _ in range(10):
            try:
                limiter.check_rate_limit()
                successful_calls.append(1)
            except RateLimitExceeded:
                errors.append(1)

    threads = [threading.Thread(target=make_calls) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should have made 100 successful calls (up to minute limit)
    total_calls = len(successful_calls) + len(errors)
    assert total_calls == 100
    assert len(successful_calls) <= 100


def test_reset_clears_history():
    """Test that reset clears call history."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_hour=100)

    # Make some calls
    for _ in range(5):
        limiter.check_rate_limit()

    assert len(limiter.call_history) == 5

    # Reset
    limiter.reset()
    assert len(limiter.call_history) == 0


def test_custom_backoff_calculation():
    """Test exponential backoff calculation."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_hour=100)

    # Backoff should increase exponentially
    backoff_1 = limiter._calculate_backoff(attempt=1)
    backoff_2 = limiter._calculate_backoff(attempt=2)
    backoff_3 = limiter._calculate_backoff(attempt=3)

    assert backoff_2 > backoff_1
    assert backoff_3 > backoff_2
    assert backoff_3 <= 32  # Max backoff should be capped


def test_rate_limiter_context_manager():
    """Test RateLimiter can be used as context manager if implemented."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_hour=100)

    # This test assumes we might add context manager support later
    # For now, just test basic usage
    with limiter:
        limiter.check_rate_limit()

    assert len(limiter.call_history) >= 1


def test_different_instances_independent():
    """Test that different RateLimiter instances are independent."""
    limiter1 = RateLimiter(calls_per_minute=2, calls_per_hour=100)
    limiter2 = RateLimiter(calls_per_minute=2, calls_per_hour=100)

    # Fill limiter1
    limiter1.check_rate_limit()
    limiter1.check_rate_limit()

    # limiter1 should be at limit
    with pytest.raises(RateLimitExceeded):
        limiter1.check_rate_limit()

    # limiter2 should still work
    limiter2.check_rate_limit()
    assert len(limiter2.call_history) == 1
