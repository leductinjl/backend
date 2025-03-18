"""
Role-Permission mapping model module.

This module defines the RolePermission model that maps roles to permissions 
in a many-to-many relationship for RBAC.
"""

from sqlalchemy import Column, String, ForeignKey, DateTime
from datetime import datetime

from app.infrastructure.database.connection import Base

class RolePermission(Base):
    """
    Role-Permission mapping database model.
    
    This model represents the many-to-many relationship between roles and permissions,
    allowing each role to have multiple permissions and each permission to be assigned
    to multiple roles.
    """
    __tablename__ = "role_permissions"
    
    role_id = Column(String(50), ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(String(50), ForeignKey("permissions.permission_id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow) 