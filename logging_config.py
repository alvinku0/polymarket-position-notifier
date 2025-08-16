#!/usr/bin/env python3
"""
Centralized Logging Configuration
setup_file_logging() 
setup_console_logging() 
"""

import logging
import os
from datetime import datetime

def setup_file_logging(logger_name: str) -> logging.Logger:
    """
    Set up standardized logging configuration for all scripts
    
    Args:
        logger_name: Name for the logger
        
    Returns:
        Configured logger instance
    """
    # Configure logging
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, "log")
    
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    log_path = os.path.join(log_dir, f"{datetime.now():%Y-%m-%d}.log")
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Create and return logger
    logger = logging.getLogger(logger_name)
    
    return logger

def setup_console_logging(logger: logging.Logger) -> logging.Logger:
    """
    Add console output
    
    Args:
        logger: Logger to add console handler to
        
    Returns:
        Logger with console handler added
    """
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger 