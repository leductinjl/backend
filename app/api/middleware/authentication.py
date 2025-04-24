"""
Authentication middleware module for admin access.

This module provides a JWT-based authentication middleware for FastAPI that validates
admin user tokens. It implements Role-Based Access Control (RBAC) to enforce
permissions across different user roles.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.config import settings
from typing import List, Optional, Dict, Any, Tuple

from app.infrastructure.database.connection import get_db
from app.domain.models.role import Role
from app.domain.models.permission import Permission
from app.domain.models.user import User
from app.domain.models.security_log import SecurityLog
from app.services.id_service import generate_model_id
from app.infrastructure.cache.redis_connection import get_redis
from sqlalchemy import select, text

class AdminAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT-based authentication with RBAC.
    
    Validates JWT tokens from Authorization headers for protected routes
    and enforces role-based access control.
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
        
        # Public endpoints that don't require authentication
        self.public_endpoints = [
            f"{admin_path_prefix}/login",
            f"{admin_path_prefix}/register"
        ]

    async def dispatch(self, request: Request, call_next):
        """
        Process the request, authenticate admin users, and enforce permissions.
        
        This method:
        1. Checks if the path is an admin path requiring authentication
        2. If not admin path, allows the request without authentication
        3. For admin paths, validates the JWT token
        4. Attaches admin data to the request state for protected routes
        5. Enforces role-based access control
        
        Args:
            request: The HTTP request
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
        request.state.is_super_admin = False
        request.state.permissions = []
        
        # Check if path is an admin path (requires authentication)
        path = request.url.path
        
        # Allow access to public endpoints without authentication
        if path in self.public_endpoints:
            self.logger.debug(f"Allowing access to public endpoint: {path}")
            return await call_next(request)
            
        if not path.startswith(self.admin_path_prefix):
            # Not an admin path, allow without authentication
            return await call_next(request)
            
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
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
        
        # Check if token is blacklisted
        try:
            redis_client = await get_redis()
            if await redis_client.exists(f"blacklist:{token}"):
                self.logger.warning(f"Attempted use of blacklisted token for path: {path}")
                raise HTTPException(
                    status_code=401, 
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except Exception as e:
            self.logger.error(f"Error checking token blacklist: {str(e)}")
        
        try:
            # Decode and validate JWT token
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            
            user_id = payload.get("sub")
            role = payload.get("role")
            
            # Get database connection
            db = None
            try:
                db_gen = get_db()
                db = await anext(db_gen)
                
                # Get user from database to ensure account is still active and has correct role
                user_query = select(User).where(User.user_id == user_id)
                user_result = await db.execute(user_query)
                user = user_result.scalar_one_or_none()
                
                if not user:
                    self.logger.warning(f"Token references non-existent user: {user_id}")
                    raise HTTPException(status_code=401, detail="Invalid user")
                
                if not user.is_active:
                    self.logger.warning(f"Deactivated user attempted access: {user_id}")
                    raise HTTPException(status_code=401, detail="Account is inactive")
                
                # Verify role is either admin or super_admin
                if user.role not in ["admin", "super_admin"]:
                    self.logger.warning(f"Non-admin user attempted to access admin path: {path}")
                    raise HTTPException(
                        status_code=403, 
                        detail="Admin access required"
                    )
                
                # Fetch permissions from database for the role
                permissions = []
                if user.role_id:
                    permissions_result = await db.execute(text("""
                        SELECT p.name 
                        FROM permissions p
                        JOIN role_permissions rp ON p.permission_id = rp.permission_id
                        WHERE rp.role_id = :role_id
                    """), {"role_id": user.role_id})
                    
                    permissions = [row[0] for row in permissions_result]
                
                # Log successful authentication
                log_entry = SecurityLog(
                    log_id=generate_model_id("SecurityLog"),
                    user_id=user_id,
                    action="auth_success",
                    ip_address=request.client.host,
                    user_agent=request.headers.get("User-Agent", ""),
                    description=f"User authenticated successfully for {path}",
                    request_id=request.scope.get("aws.request_id", ""),
                    success=True
                )
                db.add(log_entry)
                await db.commit()
                
                # Update user last login
                user.last_login = datetime.utcnow()
                user.last_login_ip = request.client.host
                await db.commit()
            except Exception as db_error:
                self.logger.error(f"Database error during authentication: {str(db_error)}")
                # Continue with token data if DB error
                permissions = payload.get("permissions", [])
            finally:
                if db:
                    await db.close()
            
            # Extract admin user information from token payload
            user_data = {
                "sub": user_id,  # Use "sub" to match token structure
                "email": payload.get("email"),
                "role": role,
                "name": payload.get("name"),
                "permissions": permissions,
            }
            
            # Store admin data in request state for access in route handlers
            request.state.user = user_data
            request.state.is_authenticated = True
            request.state.is_admin = role in ["admin", "super_admin"]
            request.state.is_super_admin = role == "super_admin"
            request.state.permissions = permissions
            
            # Log successful admin authentication
            self.logger.debug(f"Authenticated user {user_id} ({role}) for path: {path}")
            
        except jwt.ExpiredSignatureError:
            self.logger.warning(f"Expired JWT token for admin path: {path}")
            raise HTTPException(
                status_code=401, 
                detail="Authentication token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            self.logger.warning(f"Invalid JWT token for admin path: {path}")
            raise HTTPException(
                status_code=401, 
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Call the next middleware or route handler
        return await call_next(request)

# Helper function to use in API endpoints for permission checks
def has_permission(request: Request, permission: str) -> bool:
    """
    Check if the authenticated user has a specific permission.
    
    Args:
        request: The HTTP request with user state information
        permission: The permission to check
        
    Returns:
        bool: True if user has the permission, False otherwise
    """
    if not request.state.is_authenticated:
        return False
        
    # Super admin has all permissions
    if request.state.is_super_admin:
        return True
        
    # Check specific permission
    return permission in request.state.permissions

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