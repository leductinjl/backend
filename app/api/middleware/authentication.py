"""
Authentication middleware module for admin access.

This module provides a JWT-based authentication middleware for FastAPI that validates
admin user tokens. It's designed to allow public access to candidate information endpoints
while restricting admin functionality to authenticated administrators.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import jwt
from app.config import settings
from typing import List, Optional, Dict, Any

class AdminAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT-based authentication for admin routes.
    
    Validates JWT tokens from Authorization headers only for admin routes,
    leaving candidate information endpoints publicly accessible.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        admin_path_prefix: str = "/api/v1/admin",
        token_prefix: str = "Bearer"
    ):
        """
        Initialize the admin authentication middleware.
        
        Args:
            app: The ASGI application
            admin_path_prefix: Prefix for admin paths that require authentication
            token_prefix: Prefix used in the Authorization header (default: "Bearer")
        """
        super().__init__(app)
        self.admin_path_prefix = admin_path_prefix
        self.token_prefix = token_prefix
        self.logger = logging.getLogger("api")

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and authenticate admin users.
        
        This method:
        1. Checks if the path is an admin path requiring authentication
        2. If not admin path, allows the request without authentication
        3. For admin paths, validates the JWT token
        4. Attaches admin data to the request state for protected routes
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint in the chain
            
        Returns:
            Response: The HTTP response
            
        Raises:
            HTTPException: When authentication fails for admin routes
        """
        # Initialize user information in request state
        request.state.user = None
        request.state.is_authenticated = False
        request.state.is_admin = False
        
        # Check if path is an admin path (requires authentication)
        path = request.url.path
        if not path.startswith(self.admin_path_prefix):
            # Not an admin path, allow without authentication
            return await call_next(request)
        
        # Admin path - require authentication
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            self.logger.warning(f"Missing Authorization header for admin path: {path}")
            raise HTTPException(
                status_code=401, 
                detail="Admin authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check token prefix format
        if not auth_header.startswith(f"{self.token_prefix} "):
            self.logger.warning(f"Invalid token format in Authorization header: {auth_header}")
            raise HTTPException(
                status_code=401, 
                detail=f"Invalid token format. Expected: {self.token_prefix} <token>",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract token from header
        token = auth_header.replace(f"{self.token_prefix} ", "")
        
        try:
            # Decode and validate JWT token
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            
            # Verify this is an admin user
            role = payload.get("role")
            if role != "admin":
                self.logger.warning(f"Non-admin user attempted to access admin path: {path}")
                raise HTTPException(
                    status_code=403, 
                    detail="Admin access required"
                )
            
            # Extract admin user information from token payload
            user_data = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "role": role,
                "name": payload.get("name"),
                "permissions": payload.get("permissions", []),
            }
            
            # Store admin data in request state for access in route handlers
            request.state.user = user_data
            request.state.is_authenticated = True
            request.state.is_admin = True
            
            # Log successful admin authentication
            self.logger.debug(f"Authenticated admin {user_data['id']} for path: {path}")
            
        except jwt.ExpiredSignatureError:
            self.logger.warning(f"Expired JWT token for admin path: {path}")
            raise HTTPException(
                status_code=401, 
                detail="Admin token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            self.logger.warning(f"Invalid JWT token for admin path: {path}")
            raise HTTPException(
                status_code=401, 
                detail="Invalid admin authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Call the next middleware or route handler
        return await call_next(request)

# Example of using admin authentication in route handlers:
#
# @router.get("/admin/dashboard")
# async def admin_dashboard(request: Request):
#     # The middleware already verified this is an admin
#     admin = request.state.user
#     return {"message": f"Welcome to admin dashboard, {admin['name']}!"}
#
# @router.get("/candidates/{candidate_id}")
# async def get_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
#     # This is public, no authentication needed
#     candidate = await candidate_service.get_candidate_by_id(db, candidate_id)
#     return candidate 