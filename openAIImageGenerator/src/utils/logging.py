"""Logging configuration for the application."""

import logging
from logging.handlers import RotatingFileHandler
import sys
from .config import Config

def setup_logging():
    """Configure application logging.
    
    Sets up logging to both file and console with different formats and levels.
    File logging includes more detailed information for debugging.
    Console logging is more concise for general use.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler (rotating log file)
    file_handler = RotatingFileHandler(
        Config.LOG_PATH,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Initial log message
    logger.info("Logging system initialized") 
