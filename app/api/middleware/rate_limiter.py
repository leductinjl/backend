"""
Rate limiting middleware module.

This module provides a configurable rate limiting middleware for FastAPI that
restricts the number of requests a client can make within a specific time window.
It helps protect the API from abuse, DoS attacks, and ensures fair resource usage.
"""

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from app.infrastructure.cache.redis_connection import RedisCache

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware for implementing rate limiting based on client IP address.
    
    Uses Redis to track and limit the number of requests from each client
    within a configurable time window. When limits are exceeded, returns
    a 429 Too Many Requests response.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        redis_cache: RedisCache,
        requests_limit: int = 100,
        window_seconds: int = 60
    ):
        """
        Initialize the rate limiting middleware.
        
        Args:
            app: The ASGI application
            redis_cache: Redis cache instance for storing rate limit data
            requests_limit: Maximum number of requests allowed in the time window
            window_seconds: Time window in seconds for rate limiting
        """
        super().__init__(app)
        self.redis_cache = redis_cache
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.logger = logging.getLogger("api")

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and apply rate limiting.
        
        This method:
        1. Extracts the client IP address
        2. Increments the request counter for that IP in Redis
        3. Checks if the client has exceeded their rate limit
        4. Either blocks the request or forwards it to the next middleware
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint in the chain
            
        Returns:
            Response: The HTTP response or a 429 Too Many Requests error
            
        Raises:
            HTTPException: When rate limit is exceeded
        """
        # Skip rate limiting for specific endpoints if needed
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
            
        # Get client IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Create Redis key for this client
        redis_key = f"rate_limit:{client_ip}"
        
        # Get current count for this client
        current_count = await self.redis_cache.get(redis_key)
        
        if current_count is None:
            # First request from this client in this window
            await self.redis_cache.set(redis_key, 1, expires=self.window_seconds)
            current_count = 1
        else:
            # Increment the request counter
            current_count = int(current_count) + 1
            await self.redis_cache.set(redis_key, current_count, expires=self.window_seconds)
        
        # Check if rate limit is exceeded
        if current_count > self.requests_limit:
            # Calculate time until reset
            ttl = await self.redis_cache.ttl(redis_key)
            
            # Log rate limit exceeded
            self.logger.warning(
                f"Rate limit exceeded for {client_ip}: {current_count} requests. "
                f"Limit: {self.requests_limit} per {self.window_seconds} seconds."
            )
            
            # Return rate limit exceeded response
            response = Response(
                content={"detail": "Rate limit exceeded. Try again later."},
                status_code=429
            )
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(self.requests_limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(ttl)
            response.headers["Retry-After"] = str(ttl)
            
            return response
        
        # Process the request normally if within limits
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(self.requests_limit)
        response.headers["X-RateLimit-Remaining"] = str(self.requests_limit - current_count)
        
        return response 