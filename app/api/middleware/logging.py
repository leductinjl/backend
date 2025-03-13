"""
Logging middleware module.

This module provides a logging middleware for FastAPI that logs request and response
information, including performance metrics, status codes, and error details.
It also adds request IDs for tracking requests through the system.
"""

import time
import uuid
from fastapi import Request
import logging as python_logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    This middleware adds request/response logging capabilities and
    attaches a unique request ID to each request for tracing.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the logging middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        self.logger = python_logging.getLogger("api.middleware")

    async def dispatch(self, request: Request, call_next):
        """
        Process an incoming request and log request/response details.
        
        This method:
        1. Generates a unique request ID
        2. Logs the incoming request details
        3. Processes the request through the application
        4. Logs the response details
        5. Returns the response
        
        Args:
            request: The incoming HTTP request
            call_next: Async function that processes the request
            
        Returns:
            starlette.responses.Response: The HTTP response
        """
        # Add unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer for performance tracking
        start_time = time.time()
        
        # Log request information
        await self._log_request(request, request_id)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Log response information (for successful responses)
            process_time = (time.time() - start_time) * 1000
            self._log_response(request, response, process_time, request_id)
            
            # Add request ID to response headers for client-side tracking
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # Log errors for exceptions during processing
            process_time = (time.time() - start_time) * 1000
            self._log_exception(request, exc, process_time, request_id)
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """
        Log details about the incoming request.
        
        Args:
            request: The incoming HTTP request
            request_id: Unique identifier for this request
        """
        # Get request body if needed (this consumes the stream, so use with caution)
        # body = await request.body()
        # body_str = body.decode() if body else None
        
        client_host = request.client.host if request.client else "unknown"
        self.logger.info(
            f"Request {request_id}: {request.method} {request.url.path} from {client_host}"
        )
        
        # Log headers if debug is enabled
        if self.logger.isEnabledFor(python_logging.DEBUG):
            headers = dict(request.headers.items())
            # Remove sensitive headers
            if "authorization" in headers:
                headers["authorization"] = "REDACTED"
            if "cookie" in headers:
                headers["cookie"] = "REDACTED"
            self.logger.debug(f"Request {request_id} headers: {json.dumps(headers)}")
    
    def _log_response(self, request: Request, response, process_time: float, request_id: str):
        """
        Log details about the outgoing response.
        
        Args:
            request: The original HTTP request
            response: The HTTP response
            process_time: Time taken to process the request in milliseconds
            request_id: Unique identifier for this request
        """
        status_phrase = "OK" if response.status_code < 400 else "Error"
        log_message = (
            f"Response {request_id}: {request.method} {request.url.path} "
            f"completed with {response.status_code} {status_phrase} in {process_time:.2f}ms"
        )
        
        # Use appropriate log level based on status code
        if response.status_code >= 500:
            self.logger.error(log_message)
        elif response.status_code >= 400:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _log_exception(self, request: Request, exc: Exception, process_time: float, request_id: str):
        """
        Log details about an exception that occurred during request processing.
        
        Args:
            request: The original HTTP request
            exc: The exception that was raised
            process_time: Time taken before the exception occurred in milliseconds
            request_id: Unique identifier for this request
        """
        self.logger.error(
            f"Exception {request_id}: {request.method} {request.url.path} "
            f"failed after {process_time:.2f}ms with {type(exc).__name__}: {str(exc)}"
        )
        self.logger.exception(exc) 