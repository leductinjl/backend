"""
User model module.

This module defines the User model for the system. In this system, only admin users 
are stored in the database, as student/candidate information is accessed without authentication.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import validates, relationship
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class User(Base):
    """
    Model for admin users in the system.
    
    This model only represents administrative users, as candidate data
    is accessed without authentication.
    """
    __tablename__ = "users"
    
    user_id = Column(String(50), primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="admin")
    role_id = Column(String(50), ForeignKey("roles.role_id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 2FA fields
    require_2fa = Column(Boolean, default=False)
    two_factor_secret = Column(String(100), nullable=True)
    two_factor_enabled = Column(Boolean, default=False)
    backup_codes = Column(Text, nullable=True)  # JSON string of backup codes
    
    # Login history
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    role_relation = relationship("Role", back_populates="users")
    security_logs = relationship("SecurityLog", back_populates="user", cascade="all, delete-orphan")
    created_invitations = relationship("Invitation", foreign_keys="Invitation.created_by", back_populates="creator")
    
    @validates('user_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("User")
        return id_value
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}', role='{self.role}')>" 