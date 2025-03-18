"""
Role model module.

This module defines the Role model used for role-based access control (RBAC).
Roles define sets of permissions that can be assigned to users.
"""

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.infrastructure.database.connection import Base

class Role(Base):
    """
    Role database model.
    
    A role represents a set of permissions that can be assigned to users.
    Common roles include 'super_admin', 'admin', etc.
    """
    __tablename__ = "roles"
    
    role_id = Column(String(50), primary_key=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="role_relation")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles") 