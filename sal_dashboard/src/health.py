"""
Health check and monitoring utilities for the dashboard.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any

from src.config import ROOT_DIR
from src.database import get_db
from src.logging_config import get_logger

logger = get_logger(__name__)


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


__all__ = ["check_health", "get_metrics"]

