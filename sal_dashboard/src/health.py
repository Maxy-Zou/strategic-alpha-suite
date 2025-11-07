"""
Health check and monitoring utilities for the dashboard.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.config import ROOT_DIR
from src.database import get_db
from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class HealthStatus:
    """Health check result."""
    healthy: bool
    message: str
    details: Optional[Dict[str, Any]] = None


def check_health() -> Dict[str, Any]:
    """
    Perform comprehensive health check of the dashboard.
    
    Returns:
        Dictionary with health status and details
    """
    health_status = {
        "status": "healthy",
        "checks": {},
        "timestamp": None,
    }
    
    import datetime
    health_status["timestamp"] = datetime.datetime.utcnow().isoformat()
    
    # Check database connectivity
    try:
        db = get_db()
        # Try a simple query
        db.get_api_call_stats(hours=1)
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}",
        }
        health_status["status"] = "degraded"
        logger.error("Database health check failed: %s", e)
    
    # Check required directories
    required_dirs = [
        ROOT_DIR / "data",
        ROOT_DIR / "logs",
        ROOT_DIR / "artifacts",
        ROOT_DIR / "reports",
    ]
    
    dir_checks = {}
    for dir_path in required_dirs:
        exists = dir_path.exists()
        writable = False
        if exists:
            try:
                # Try to create a test file
                test_file = dir_path / ".write_test"
                test_file.touch()
                writable = test_file.exists()
                test_file.unlink()
            except Exception:
                writable = False
        else:
            # Try to create the directory
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                exists = True
                writable = True
            except Exception:
                exists = False
                writable = False
        
        dir_checks[dir_path.name] = {
            "exists": exists,
            "writable": writable,
        }
        
        if not exists or not writable:
            health_status["status"] = "degraded"
    
    health_status["checks"]["directories"] = dir_checks
    
    # Check Python version
    python_version = sys.version_info
    health_status["checks"]["python"] = {
        "version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
        "status": "healthy" if python_version.major == 3 and python_version.minor >= 10 else "warning",
    }
    
    # Check disk space (basic check)
    try:
        import shutil
        total, used, free = shutil.disk_usage(ROOT_DIR)
        free_gb = free / (1024 ** 3)
        health_status["checks"]["disk"] = {
            "free_gb": round(free_gb, 2),
            "status": "healthy" if free_gb > 1.0 else "warning",
        }
        if free_gb < 1.0:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "unknown",
            "message": f"Could not check disk space: {str(e)}",
        }
    
    return health_status


def get_metrics() -> Dict[str, Any]:
    """
    Get application metrics.
    
    Returns:
        Dictionary with application metrics
    """
    db = get_db()
    
    # Get API call statistics
    api_stats = db.get_api_call_stats(hours=24)
    
    # Get recent valuation runs count
    try:
        recent_runs = db.get_valuation_history(limit=1000)
        total_runs = len(recent_runs)
    except Exception:
        total_runs = 0
    
    return {
        "api_calls_24h": api_stats.get("total_calls", 0),
        "api_success_rate": (
            api_stats.get("successful_calls", 0) / max(api_stats.get("total_calls", 1), 1) * 100
        ),
        "avg_api_response_time_ms": api_stats.get("avg_response_time_ms", 0),
        "total_valuation_runs": total_runs,
        "health": check_health(),
    }


# Test compatibility functions
def check_disk_space(path: str, min_free_gb: float = 1.0) -> HealthStatus:
    """Check if sufficient disk space is available."""
    try:
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024 ** 3)
        free_percent = (free / total) * 100

        healthy = free_gb >= min_free_gb
        message = f"{free_gb:.2f} GB free ({free_percent:.1f}%)"
        if not healthy:
            message = f"Low disk space: {message} (minimum {min_free_gb} GB required)"

        return HealthStatus(
            healthy=healthy,
            message=message,
            details={'free_gb': free_gb, 'free_percent': free_percent}
        )
    except Exception as e:
        return HealthStatus(
            healthy=False,
            message=f"Error checking disk space: {str(e)}",
            details=None
        )


def check_directory_exists(path: str) -> HealthStatus:
    """Check if directory exists and is accessible."""
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return HealthStatus(
                healthy=False,
                message=f"Directory not found: {path}",
                details=None
            )
        if not dir_path.is_dir():
            return HealthStatus(
                healthy=False,
                message=f"Path exists but is not a directory: {path}",
                details=None
            )
        return HealthStatus(
            healthy=True,
            message=f"Directory exists: {path}",
            details={'path': path}
        )
    except Exception as e:
        return HealthStatus(
            healthy=False,
            message=f"Error checking directory: {str(e)}",
            details=None
        )


def check_database_connection(db_path: str) -> HealthStatus:
    """Check database connection and validity."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        # Try a simple query to verify database is valid
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        # Verify this is a valid SQLite database by checking schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        cursor.fetchall()

        return HealthStatus(
            healthy=True,
            message=f"Database connected successfully: {db_path}",
            details={'db_path': db_path}
        )
    except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
        return HealthStatus(
            healthy=False,
            message=f"Database error or corrupt: {str(e)}",
            details={'db_path': db_path, 'error': str(e)}
        )
    except Exception as e:
        return HealthStatus(
            healthy=False,
            message=f"Error connecting to database: {str(e)}",
            details={'db_path': db_path, 'error': str(e)}
        )
    finally:
        if conn:
            conn.close()


def run_health_checks(checks_config: List[Dict[str, Any]]) -> Dict[str, HealthStatus]:
    """
    Run multiple health checks.

    Args:
        checks_config: List of dicts with 'name', 'check_func', and 'args' keys

    Returns:
        Dictionary mapping check names to HealthStatus results
    """
    results = {}
    for check in checks_config:
        name = check['name']
        check_func = check['check_func']
        args = check.get('args', [])

        try:
            result = check_func(*args)
            results[name] = result
        except Exception as e:
            results[name] = HealthStatus(
                healthy=False,
                message=f"Check failed with exception: {str(e)}",
                details={'error': str(e)}
            )

    return results


__all__ = [
    "check_health", "get_metrics",
    # Test compatibility functions
    "HealthStatus", "check_disk_space", "check_directory_exists",
    "check_database_connection", "run_health_checks"
]

