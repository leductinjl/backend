"""
Database dependencies module.

This module provides FastAPI dependencies for database operations.
"""

from app.infrastructure.database.connection import get_db

__all__ = ['get_db'] 