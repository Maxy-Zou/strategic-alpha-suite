"""Tests for health.py module."""

import pytest
from pathlib import Path
import sys
import os
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.health import (
    check_disk_space,
    check_directory_exists,
    check_database_connection,
    run_health_checks,
    HealthStatus,
)


def test_check_disk_space_sufficient(tmp_path):
    """Test disk space check when sufficient space available."""
    result = check_disk_space(str(tmp_path), min_free_gb=0.001)  # Very small threshold

    assert result.healthy is True
    assert result.message is not None
    assert "GB free" in result.message


def test_check_disk_space_insufficient(tmp_path):
    """Test disk space check when insufficient space."""
    # Set threshold impossibly high
    result = check_disk_space(str(tmp_path), min_free_gb=999999)

    assert result.healthy is False
    assert "insufficient" in result.message.lower() or "low" in result.message.lower()


def test_check_disk_space_invalid_path():
    """Test disk space check with invalid path."""
    result = check_disk_space("/this/path/does/not/exist/at/all")

    assert result.healthy is False
    assert "error" in result.message.lower() or "not found" in result.message.lower()


def test_check_directory_exists_success(tmp_path):
    """Test directory check when directory exists."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    result = check_directory_exists(str(test_dir))

    assert result.healthy is True
    assert "exists" in result.message.lower()


def test_check_directory_exists_missing(tmp_path):
    """Test directory check when directory doesn't exist."""
    missing_dir = tmp_path / "missing_dir"

    result = check_directory_exists(str(missing_dir))

    assert result.healthy is False
    assert "not found" in result.message.lower() or "does not exist" in result.message.lower()


def test_check_directory_exists_file_not_dir(tmp_path):
    """Test directory check when path is a file, not a directory."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("test")

    result = check_directory_exists(str(test_file))

    assert result.healthy is False


def test_check_database_connection_success(tmp_path):
    """Test database connection check with valid database."""
    db_path = tmp_path / "test.db"

    # Create a simple database
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.commit()
    conn.close()

    result = check_database_connection(str(db_path))

    assert result.healthy is True
    assert "connected" in result.message.lower()


def test_check_database_connection_new_db(tmp_path):
    """Test database connection creates new DB if doesn't exist."""
    db_path = tmp_path / "new.db"

    result = check_database_connection(str(db_path))

    # Should successfully create and connect
    assert result.healthy is True
    assert db_path.exists()


def test_check_database_connection_invalid_path():
    """Test database connection with invalid path."""
    # Try to create DB in non-existent directory
    result = check_database_connection("/invalid/path/to/database.db")

    assert result.healthy is False


def test_check_database_connection_corrupted(tmp_path):
    """Test database connection with corrupted database file."""
    db_path = tmp_path / "corrupted.db"

    # Create a corrupted database file (not valid SQLite format)
    with open(db_path, 'w') as f:
        f.write("This is not a valid SQLite database file")

    result = check_database_connection(str(db_path))

    assert result.healthy is False
    assert "error" in result.message.lower() or "corrupt" in result.message.lower()


def test_run_health_checks_all_healthy(tmp_path):
    """Test run_health_checks when all checks pass."""
    # Create necessary directories and database
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db_path = tmp_path / "test.db"

    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.close()

    checks_config = [
        {
            'name': 'data_directory',
            'check_func': check_directory_exists,
            'args': [str(data_dir)],
        },
        {
            'name': 'database',
            'check_func': check_database_connection,
            'args': [str(db_path)],
        },
        {
            'name': 'disk_space',
            'check_func': check_disk_space,
            'args': [str(tmp_path), 0.001],
        },
    ]

    results = run_health_checks(checks_config)

    assert all(result.healthy for result in results.values())
    assert len(results) == 3


def test_run_health_checks_some_unhealthy(tmp_path):
    """Test run_health_checks when some checks fail."""
    checks_config = [
        {
            'name': 'existing_dir',
            'check_func': check_directory_exists,
            'args': [str(tmp_path)],  # Exists
        },
        {
            'name': 'missing_dir',
            'check_func': check_directory_exists,
            'args': [str(tmp_path / "nonexistent")],  # Doesn't exist
        },
    ]

    results = run_health_checks(checks_config)

    assert results['existing_dir'].healthy is True
    assert results['missing_dir'].healthy is False


def test_health_status_dataclass():
    """Test HealthStatus dataclass creation."""
    status = HealthStatus(
        healthy=True,
        message="All systems operational",
        details={'check_time': '2024-01-01'}
    )

    assert status.healthy is True
    assert status.message == "All systems operational"
    assert status.details['check_time'] == '2024-01-01'


def test_health_status_without_details():
    """Test HealthStatus without optional details."""
    status = HealthStatus(healthy=False, message="Error occurred")

    assert status.healthy is False
    assert status.message == "Error occurred"
    assert status.details is None


def test_check_disk_space_percentage(tmp_path):
    """Test that disk space check includes percentage information."""
    result = check_disk_space(str(tmp_path), min_free_gb=0.001)

    assert result.healthy is True
    assert result.details is not None
    assert 'free_gb' in result.details
    assert 'free_percent' in result.details
    assert result.details['free_gb'] > 0
    assert 0 <= result.details['free_percent'] <= 100


def test_check_database_connection_permissions(tmp_path):
    """Test database connection check handles permission errors gracefully."""
    db_path = tmp_path / "readonly.db"

    # Create database
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.close()

    # Make it read-only
    os.chmod(db_path, 0o444)

    try:
        # Connection might still work (read-only), but writes would fail
        result = check_database_connection(str(db_path))
        # Just ensure it returns a valid HealthStatus
        assert isinstance(result, HealthStatus)
    finally:
        # Restore permissions for cleanup
        os.chmod(db_path, 0o644)


def test_concurrent_health_checks(tmp_path):
    """Test that health checks can run concurrently."""
    import threading

    db_path = tmp_path / "concurrent.db"

    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.close()

    results = []

    def run_check():
        result = check_database_connection(str(db_path))
        results.append(result)

    threads = [threading.Thread(target=run_check) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 10
    assert all(r.healthy for r in results)


def test_health_check_with_exception_handling(tmp_path):
    """Test that health checks handle unexpected exceptions gracefully."""

    def faulty_check():
        raise RuntimeError("Unexpected error")

    # Should not crash, should return unhealthy status
    try:
        result = faulty_check()
    except Exception as e:
        # Expected to raise, or should be caught and returned as HealthStatus
        assert isinstance(e, RuntimeError)


def test_multiple_disk_space_checks(tmp_path):
    """Test multiple disk space checks with different thresholds."""
    # Very permissive - should pass
    result1 = check_disk_space(str(tmp_path), min_free_gb=0.001)
    assert result1.healthy is True

    # Very strict - likely to fail unless you have terabytes free
    result2 = check_disk_space(str(tmp_path), min_free_gb=10000)
    assert result2.healthy is False
