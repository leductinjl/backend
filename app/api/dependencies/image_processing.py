"""
Image Processing Dependencies module.

This module provides FastAPI dependencies for image processing services.
"""

from app.services.image_processing_service import ImageProcessingService

def get_image_processor():
    """Dependency to get image processing service instance."""
    return ImageProcessingService() 