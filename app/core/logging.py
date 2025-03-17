"""
Core logging configuration module.

This module provides centralized logging configuration for the application,
setting up file and console handlers with appropriate formatting.
"""

import logging
import os
from app.config import settings

def setup_logging():
    """
    Configure logging for the application.
    
    This function:
    1. Creates log directory if it doesn't exist
    2. Sets up basic logging configuration including:
       - Log level from settings
       - Formatter for timestamps and log levels
       - File handler for persistent logs
       - Console handler for real-time monitoring
    """
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(settings.LOG_FILE_PATH), exist_ok=True)
    
    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(settings.LOG_FILE_PATH),
            logging.StreamHandler()
        ]
    )
    
    # Log successful logging setup
    logging.info(f"Logging initialized at level {settings.LOG_LEVEL}") 