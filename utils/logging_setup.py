"""Centralized logging configuration for the noise cancellation application."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logging(
    log_dir: Optional[Path] = None,
    log_level: int = logging.INFO,
    app_name: str = "noise_cancellation"
) -> logging.Logger:
    """
    Set up application logging with both file and console handlers.
    
    Args:
        log_dir: Directory for log files. Defaults to ./logs/
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        app_name: Name of the application for log formatting
        
    Returns:
        Configured logger instance
    """
    if log_dir is None:
        log_dir = Path("logs")
    
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s"
    )
    
    # File handler with rotation
    log_file = log_dir / f"{app_name}-{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger with the specified name."""
    return logging.getLogger(f"noise_cancellation.{name}")