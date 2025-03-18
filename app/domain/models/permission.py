"""
Permission model module.

This module defines the Permission model used for role-based access control (RBAC).
Permissions define specific actions that can be performed within the system.
"""

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.infrastructure.database.connection import Base

class Permission(Base):
    """
    Permission database model.
    
    A permission represents a specific action that can be performed in the system.
    Permissions are assigned to roles, which are then assigned to users.
    """
    __tablename__ = "permissions"
    
    permission_id = Column(String(50), primary_key=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text, nullable=True)
    resource = Column(String(100), nullable=True)  # e.g., "candidate", "exam", "admin"
    action = Column(String(100), nullable=True)    # e.g., "create", "read", "update", "delete"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions") 