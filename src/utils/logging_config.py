"""
Logging configuration for the trading bot.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Check if logging is already configured
    if hasattr(setup_logging, '_configured'):
        # Don't setup again, just return
        return
    
    # Clear any existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Set level
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('binance').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Mark as configured to prevent re-configuration
    setup_logging._configured = True
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {level}")
    if log_file:
        logger.info(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
