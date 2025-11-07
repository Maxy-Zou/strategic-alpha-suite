"""
Database utilities for historical data tracking and audit trail.

Uses SQLite for lightweight, file-based storage of:
- Historical valuation runs
- API call logs
- User interactions
- Error tracking
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from src.config import ROOT_DIR
from src.logging_config import get_logger

logger = get_logger(__name__)

DB_DIR = ROOT_DIR / "data" / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "dashboard.db"


class DashboardDB:
    """Database interface for dashboard data persistence."""
    
    def __init__(self, db_path: Path = DB_PATH):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_schema()
    
    def _initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Valuation runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS valuation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    peers TEXT NOT NULL,
                    dcf_value REAL,
                    equity_value REAL,
                    equity_value_per_share REAL,
                    timestamp TEXT NOT NULL,
                    user_inputs TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # API call logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT NOT NULL,
                    endpoint TEXT,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    success BOOLEAN,
                    error_message TEXT,
                    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User interactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    action TEXT NOT NULL,
                    ticker TEXT,
                    parameters TEXT,
                    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Error logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    context TEXT,
                    ticker TEXT,
                    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_valuation_ticker_time
                ON valuation_runs(ticker, timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_timestamp
                ON api_calls(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interaction_timestamp
                ON user_interactions(timestamp)
            """)
            
            conn.commit()
            logger.info("Database schema initialized: %s", self.db_path)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_valuation_run(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        peers: Iterable[str],
        dcf_value: float,
        equity_value: float,
        equity_value_per_share: float,
        user_inputs: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Save a valuation run to the database.
        
        Returns:
            ID of the inserted record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO valuation_runs (
                    ticker, start_date, end_date, peers, dcf_value,
                    equity_value, equity_value_per_share, timestamp, user_inputs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker,
                start_date,
                end_date,
                json.dumps(list(peers)),
                dcf_value,
                equity_value,
                equity_value_per_share,
                datetime.utcnow().isoformat(),
                json.dumps(user_inputs) if user_inputs else None,
            ))
            conn.commit()
            run_id = cursor.lastrowid
            logger.debug("Saved valuation run: id=%d, ticker=%s", run_id, ticker)
            return run_id
    
    def log_api_call(
        self,
        api_name: str,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> int:
        """
        Log an API call.
        
        Returns:
            ID of the inserted record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO api_calls (
                    api_name, endpoint, status_code, response_time_ms,
                    success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                api_name,
                endpoint,
                status_code,
                response_time_ms,
                success,
                error_message,
            ))
            conn.commit()
            call_id = cursor.lastrowid
            logger.debug("Logged API call: id=%d, api=%s, success=%s", 
                        call_id, api_name, success)
            return call_id
    
    def log_user_interaction(
        self,
        action: str,
        session_id: Optional[str] = None,
        ticker: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Log a user interaction.
        
        Returns:
            ID of the inserted record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_interactions (
                    session_id, action, ticker, parameters
                ) VALUES (?, ?, ?, ?)
            """, (
                session_id,
                action,
                ticker,
                json.dumps(parameters) if parameters else None,
            ))
            conn.commit()
            interaction_id = cursor.lastrowid
            logger.debug("Logged user interaction: id=%d, action=%s", 
                        interaction_id, action)
            return interaction_id
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        ticker: Optional[str] = None,
    ) -> int:
        """
        Log an error.
        
        Returns:
            ID of the inserted record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO error_logs (
                    error_type, error_message, stack_trace, context, ticker
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                error_type,
                error_message,
                stack_trace,
                json.dumps(context) if context else None,
                ticker,
            ))
            conn.commit()
            error_id = cursor.lastrowid
            logger.error("Logged error: id=%d, type=%s, message=%s", 
                        error_id, error_type, error_message)
            return error_id
    
    def get_valuation_history(
        self,
        ticker: Optional[str] = None,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        """
        Get valuation run history.
        
        Args:
            ticker: Filter by ticker (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of valuation run records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if ticker:
                cursor.execute("""
                    SELECT * FROM valuation_runs
                    WHERE ticker = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (ticker, limit))
            else:
                cursor.execute("""
                    SELECT * FROM valuation_runs
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_api_call_stats(
        self,
        api_name: Optional[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get API call statistics.
        
        Args:
            api_name: Filter by API name (optional)
            hours: Number of hours to look back
            
        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            since = (datetime.utcnow().timestamp() - hours * 3600)
            
            query = """
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                    AVG(response_time_ms) as avg_response_time_ms,
                    MAX(response_time_ms) as max_response_time_ms
                FROM api_calls
                WHERE timestamp >= datetime(?, 'unixepoch')
            """
            params = [since]
            
            if api_name:
                query += " AND api_name = ?"
                params.append(api_name)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else {}


# Global database instance
_global_db: Optional[DashboardDB] = None


def get_db() -> DashboardDB:
    """Get or create global database instance."""
    global _global_db
    if _global_db is None:
        _global_db = DashboardDB()
    return _global_db


# Wrapper functions for backward compatibility with tests
def init_database(db_path: str = None) -> None:
    """Initialize database (test compatibility wrapper)."""
    if db_path:
        DashboardDB(Path(db_path))
    else:
        get_db()


def log_valuation_run(
    db_path: str,
    ticker: str,
    start_date: str,
    end_date: str,
    peers: Iterable[str],
    dcf_value: float,
    equity_value: float,
    equity_value_per_share: float,
    user_inputs: Optional[Dict[str, Any]] = None,
) -> int:
    """Log valuation run (test compatibility wrapper)."""
    db = DashboardDB(Path(db_path))
    return db.save_valuation_run(
        ticker, start_date, end_date, peers, dcf_value,
        equity_value, equity_value_per_share, user_inputs
    )


def log_api_call(
    db_path: str,
    api_name: str,
    endpoint: Optional[str] = None,
    status_code: Optional[int] = None,
    response_time_ms: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None,
) -> int:
    """Log API call (test compatibility wrapper)."""
    db = DashboardDB(Path(db_path))
    return db.log_api_call(
        api_name, endpoint, status_code, response_time_ms, success, error_message
    )


def log_user_interaction(
    db_path: str,
    session_id: Optional[str] = None,
    action: str = "",
    ticker: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> int:
    """Log user interaction (test compatibility wrapper)."""
    db = DashboardDB(Path(db_path))
    return db.log_user_interaction(action, session_id, ticker, parameters)


def log_error(
    db_path: str,
    error_type: str,
    error_message: str,
    stack_trace: Optional[str] = None,
    context: Optional[str] = None,
    ticker: Optional[str] = None,
) -> int:
    """Log error (test compatibility wrapper)."""
    db = DashboardDB(Path(db_path))
    context_dict = {"context": context} if context and isinstance(context, str) else None
    return db.log_error(error_type, error_message, stack_trace, context_dict, ticker)


def get_valuation_history(
    db_path: str,
    ticker: Optional[str] = None,
    limit: int = 100,
) -> list:
    """Get valuation history (test compatibility wrapper)."""
    db = DashboardDB(Path(db_path))
    results = db.get_valuation_history(ticker, limit)
    # Convert dict results to tuple format expected by tests
    return [
        (
            r['id'], r['ticker'], r['start_date'], r['end_date'],
            r['peers'], r['dcf_value'], r['equity_value'],
            r['equity_value_per_share'], r['user_inputs']
        )
        for r in results
    ]


def get_recent_errors(db_path: str, limit: int = 100) -> list:
    """Get recent errors (test compatibility wrapper)."""
    db = DashboardDB(Path(db_path))
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM error_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()


__all__ = [
    "DashboardDB", "get_db", "DB_PATH",
    # Test compatibility wrappers
    "init_database", "log_valuation_run", "log_api_call",
    "log_user_interaction", "log_error", "get_valuation_history",
    "get_recent_errors"
]

