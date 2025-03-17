"""
Application setup module.

This module handles the creation and configuration of the FastAPI application,
including middleware setup, CORS policy, and API documentation settings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.middleware import register_middleware
from app.infrastructure.cache.redis_connection import redis_cache

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    This function:
    1. Creates the FastAPI instance with appropriate metadata
    2. Configures documentation endpoints
    3. Sets up CORS middleware
    4. Registers custom middleware components
    
    Returns:
        FastAPI: The configured application instance
    """
    # Initialize FastAPI with app metadata and documentation URLs
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="API for candidate information retrieval system",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        debug=settings.DEBUG
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all custom middleware
    register_middleware(app, redis_cache)
    
    return app 