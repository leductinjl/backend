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
        allow_origins=["*"],  # For production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all custom middleware
    register_middleware(app, redis_cache)
    
    return app 