"""
Middleware registry module.

This module provides a centralized registry for all API middleware components,
allowing for consistent configuration and setup of the middleware pipeline.
It organizes middleware in the recommended order of execution.
"""

from fastapi import FastAPI
from typing import Optional
import logging as python_logging

from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.rate_limiter import RateLimiterMiddleware
from app.api.middleware.authentication import AdminAuthenticationMiddleware
from app.infrastructure.cache.redis_connection import RedisCache

logger = python_logging.getLogger("api")

def register_middleware(app: FastAPI, redis_cache: Optional[RedisCache] = None):
    """
    Register all middleware components with the FastAPI application.
    
    This function adds middleware to the application in the correct order.
    The registration order is important as it determines execution order:
    - First middleware registered is executed last (outermost)
    - Last middleware registered is executed first (innermost)
    
    Args:
        app: The FastAPI application instance
        redis_cache: Redis cache instance for rate limiting (optional)
        
    Note:
        Some middleware may require additional services like Redis.
        These are passed as parameters to this function.
    """
    # Register middleware in reverse order of execution
    # (FastAPI executes middleware in reverse order of registration)
    
    # 1. Admin Authentication middleware (executed third)
    # This validates admin tokens for admin-only routes
    logger.info("Registering Admin Authentication middleware")
    app.add_middleware(
        AdminAuthenticationMiddleware,
        admin_path_prefix="/api/v1/admin"
    )
    
    # 2. Rate limiter middleware (executed second)
    # This limits request rates to prevent abuse
    if redis_cache:
        logger.info("Registering Rate Limiter middleware")
        app.add_middleware(
            RateLimiterMiddleware,
            redis_cache=redis_cache,
            requests_limit=100,  # Adjust based on your requirements
            window_seconds=60    # 1 minute window
        )
    else:
        logger.warning("Redis connection not available. Rate Limiter middleware not registered.")
    
    # 3. Logging middleware (executed first)
    # This logs all incoming requests and outgoing responses
    logger.info("Registering Logging middleware")
    app.add_middleware(LoggingMiddleware)
    
    logger.info("All middleware registered successfully")
    
    return app 