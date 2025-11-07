"""Tests for database.py module."""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import (
    init_database,
    log_valuation_run,
    log_api_call,
    log_user_interaction,
    log_error,
    get_valuation_history,
    get_recent_errors,
)


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    init_database(str(db_path))
    yield str(db_path)
    # Cleanup
    if db_path.exists():
        db_path.unlink()


def test_init_database_creates_tables(test_db):
    """Test that database initialization creates all required tables."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Check that all tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    assert 'valuation_runs' in tables
    assert 'api_calls' in tables
    assert 'user_interactions' in tables
    assert 'error_logs' in tables

    conn.close()


def test_init_database_creates_indexes(test_db):
    """Test that appropriate indexes are created."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cursor.fetchall()}

    # Check for expected indexes
    assert 'idx_valuation_ticker_time' in indexes
    assert 'idx_api_timestamp' in indexes
    assert 'idx_interaction_timestamp' in indexes

    conn.close()


def test_log_valuation_run(test_db):
    """Test logging a valuation run."""
    log_valuation_run(
        db_path=test_db,
        ticker='NVDA',
        start_date='2023-01-01',
        end_date='2024-01-01',
        peers=['AMD', 'INTC'],
        dcf_value=125_000_000_000,
        equity_value=132_000_000_000,
        equity_value_per_share=53.66,
        user_inputs={'revenue_growth': 0.25, 'terminal_growth': 0.03}
    )

    # Verify the record was inserted
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM valuation_runs WHERE ticker='NVDA'")
    row = cursor.fetchone()

    assert row is not None
    assert row[1] == 'NVDA'  # ticker
    assert row[2] == '2023-01-01'  # start_date
    assert row[5] == 125_000_000_000  # dcf_value

    conn.close()


def test_log_api_call_success(test_db):
    """Test logging a successful API call."""
    log_api_call(
        db_path=test_db,
        api_name='yfinance',
        endpoint='/ticker/NVDA',
        status_code=200,
        response_time_ms=250,
        success=True
    )

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_calls WHERE api_name='yfinance'")
    row = cursor.fetchone()

    assert row is not None
    assert row[2] == '/ticker/NVDA'  # endpoint
    assert row[3] == 200  # status_code
    assert row[5] == 1  # success (SQLite stores bool as int)
    assert row[6] is None  # error_message should be None

    conn.close()


def test_log_api_call_failure(test_db):
    """Test logging a failed API call."""
    log_api_call(
        db_path=test_db,
        api_name='yfinance',
        endpoint='/ticker/INVALID',
        status_code=404,
        response_time_ms=100,
        success=False,
        error_message='Ticker not found'
    )

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_calls WHERE success=0")
    row = cursor.fetchone()

    assert row is not None
    assert row[3] == 404  # status_code
    assert row[5] == 0  # success
    assert row[6] == 'Ticker not found'  # error_message

    conn.close()


def test_log_user_interaction(test_db):
    """Test logging user interactions."""
    log_user_interaction(
        db_path=test_db,
        session_id='test_session_123',
        action='run_dcf_analysis',
        ticker='NVDA',
        parameters={'revenue_growth': 0.25}
    )

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_interactions WHERE session_id='test_session_123'")
    row = cursor.fetchone()

    assert row is not None
    assert row[2] == 'run_dcf_analysis'  # action
    assert row[3] == 'NVDA'  # ticker
    assert '0.25' in row[4]  # parameters (stored as JSON string)

    conn.close()


def test_log_error(test_db):
    """Test logging errors."""
    log_error(
        db_path=test_db,
        error_type='ValueError',
        error_message='Invalid ticker format',
        stack_trace='Traceback...',
        context='User input validation',
        ticker='invalid123'
    )

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM error_logs WHERE error_type='ValueError'")
    row = cursor.fetchone()

    assert row is not None
    assert row[2] == 'Invalid ticker format'  # error_message
    assert row[5] == 'invalid123'  # ticker

    conn.close()


def test_get_valuation_history(test_db):
    """Test retrieving valuation history."""
    # Insert multiple valuation runs
    for i in range(5):
        log_valuation_run(
            db_path=test_db,
            ticker='NVDA',
            start_date='2023-01-01',
            end_date='2024-01-01',
            peers=['AMD'],
            dcf_value=125_000_000_000 + i * 1_000_000_000,
            equity_value=132_000_000_000 + i * 1_000_000_000,
            equity_value_per_share=53.66 + i * 0.4,
            user_inputs={}
        )

    history = get_valuation_history(test_db, 'NVDA', limit=3)

    assert len(history) == 3
    assert all(row[1] == 'NVDA' for row in history)
    # Should be in reverse chronological order (most recent first)
    assert history[0][5] > history[1][5]  # dcf_value increasing


def test_get_valuation_history_no_results(test_db):
    """Test getting history for ticker with no valuations."""
    history = get_valuation_history(test_db, 'AAPL', limit=10)
    assert len(history) == 0


def test_get_recent_errors(test_db):
    """Test retrieving recent errors."""
    # Insert multiple errors
    for i in range(5):
        log_error(
            db_path=test_db,
            error_type=f'Error{i}',
            error_message=f'Test error {i}',
            stack_trace='',
            context='test'
        )

    errors = get_recent_errors(test_db, limit=3)

    assert len(errors) == 3
    # Should be in reverse chronological order
    assert 'Error4' in errors[0][1]  # Most recent error type


def test_concurrent_writes(test_db):
    """Test that database handles concurrent writes without corruption."""
    import threading

    def write_valuation(ticker_suffix):
        log_valuation_run(
            db_path=test_db,
            ticker=f'TST{ticker_suffix}',
            start_date='2023-01-01',
            end_date='2024-01-01',
            peers=['AMD'],
            dcf_value=100_000_000_000,
            equity_value=105_000_000_000,
            equity_value_per_share=42.50,
            user_inputs={}
        )

    threads = [threading.Thread(target=write_valuation, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify all records were written
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM valuation_runs")
    count = cursor.fetchone()[0]
    assert count == 10
    conn.close()


def test_database_persists_after_close(test_db):
    """Test that data persists after closing connection."""
    log_valuation_run(
        db_path=test_db,
        ticker='PERSIST',
        start_date='2023-01-01',
        end_date='2024-01-01',
        peers=[],
        dcf_value=1_000_000,
        equity_value=1_000_000,
        equity_value_per_share=1.0,
        user_inputs={}
    )

    # Open new connection
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM valuation_runs WHERE ticker='PERSIST'")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 'PERSIST'
    conn.close()


def test_empty_peers_list(test_db):
    """Test logging valuation with empty peers list."""
    log_valuation_run(
        db_path=test_db,
        ticker='SOLO',
        start_date='2023-01-01',
        end_date='2024-01-01',
        peers=[],  # Empty list
        dcf_value=50_000_000_000,
        equity_value=52_000_000_000,
        equity_value_per_share=21.00,
        user_inputs={}
    )

    history = get_valuation_history(test_db, 'SOLO')
    assert len(history) == 1
    assert history[0][4] == '[]'  # Empty JSON array


def test_large_user_inputs(test_db):
    """Test storing large user_inputs dictionary."""
    large_inputs = {f'param_{i}': i * 0.1 for i in range(100)}

    log_valuation_run(
        db_path=test_db,
        ticker='BIG',
        start_date='2023-01-01',
        end_date='2024-01-01',
        peers=['AMD'],
        dcf_value=100_000_000_000,
        equity_value=105_000_000_000,
        equity_value_per_share=42.50,
        user_inputs=large_inputs
    )

    history = get_valuation_history(test_db, 'BIG')
    assert len(history) == 1
    # Verify the JSON was stored correctly
    assert 'param_99' in history[0][8]
