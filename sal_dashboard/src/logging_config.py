"""
Logging configuration for the Strategic Alpha Dashboard.

Provides structured logging with file rotation, error tracking,
and performance monitoring.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

from src.config import ROOT_DIR

# Create logs directory
LOGS_DIR = ROOT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        # Add module and function name
        record.module = record.name.split('.')[-1]
        record.function = record.funcName
        
        # Format exception info if present
        if record.exc_info:
            record.exception_text = self.formatException(record.exc_info)
        else:
            record.exception_text = ""
        
        # Build log message
        log_msg = (
            f"[{record.levelname:8s}] {record.asctime} | "
            f"{record.module}.{record.function} | {record.getMessage()}"
        )
        
        if record.exception_text:
            log_msg += f"\n{record.exception_text}"
        
        return log_msg


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = StructuredFormatter(
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        log_file = LOGS_DIR / "dashboard.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = StructuredFormatter(
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Separate error log file
        error_log_file = LOGS_DIR / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
    
    # Set levels for third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("fredapi").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    
    root_logger.info("Logging configured: level=%s, file=%s, console=%s", 
                     log_level, log_to_file, log_to_console)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class PerformanceLogger:
    """Context manager for logging function execution time."""
    
    def __init__(self, logger: logging.Logger, operation: str):
        """
        Initialize performance logger.
        
        Args:
            logger: Logger instance
            operation: Description of operation being timed
        """
        self.logger = logger
        self.operation = operation
        self.start_time: float | None = None
    
    def __enter__(self) -> PerformanceLogger:
        """Start timing."""
        import time
        self.start_time = time.time()
        self.logger.debug("Starting: %s", self.operation)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End timing and log duration."""
        import time
        if self.start_time:
            duration = time.time() - self.start_time
            if exc_type is None:
                self.logger.info(
                    "Completed: %s (duration: %.2f seconds)",
                    self.operation,
                    duration
                )
            else:
                self.logger.error(
                    "Failed: %s (duration: %.2f seconds, error: %s)",
                    self.operation,
                    duration,
                    exc_val
                )


__all__ = ["setup_logging", "get_logger", "PerformanceLogger", "LOGS_DIR"]

