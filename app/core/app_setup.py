"""
Application setup module.

This module handles the creation and configuration of the FastAPI application,
including middleware setup, CORS policy, and API documentation settings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.middleware import register_middleware
from app.infrastructure.cache.redis_connection import redis_cache
import os

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
        debug=settings.DEBUG,
        # Add security scheme for Swagger UI Authorization button
        openapi_tags=[
            {"name": "Admin", "description": "Operations requiring admin privileges"}
        ],
        swagger_ui_parameters={"persistAuthorization": True}
    )
    
    # Configure security scheme for OpenAPI documentation
    app.swagger_ui_init_oauth = {
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": ""
    }
    
    # Add security scheme to OpenAPI
    security_scheme = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter the token with the `Bearer: ` prefix, e.g. 'Bearer abcdefghijklmnopqrstuvwxyz'"
        }
    }
    
    # Add security scheme to OpenAPI components
    if not hasattr(app, "openapi_schema"):
        app.openapi_schema = None
    
    # Store the original openapi method
    original_openapi = app.openapi
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = original_openapi()
        if not "components" in openapi_schema:
            openapi_schema["components"] = {}
            
        if not "securitySchemes" in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}
            
        openapi_schema["components"]["securitySchemes"] = security_scheme
        
        # Add global security requirement
        openapi_schema["security"] = [{"bearerAuth": []}]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Frontend URL
            "http://localhost:8000",  # Local API
            "http://127.0.0.1:8000",  # Local API alternative
            "http://10.0.2.2:8000",   # Android emulator
            "http://192.168.1.*:8000", # Local network
            "http://*:8000"           # Any IP on port 8000
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

    # Register all custom middleware
    register_middleware(app, redis_cache)
    
    # Mount static file directory for uploads
    uploads_dir = os.getenv("UPLOAD_DIR", "uploads")
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
    
    return app 