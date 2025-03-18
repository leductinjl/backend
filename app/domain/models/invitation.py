"""
Invitation model module.

This module defines the Invitation model for controlling admin registration.
Only users with valid invitation codes can register as admin users.
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Invitation(Base):
    """
    Model for admin registration invitations.
    
    Controls who can register as admin by requiring valid invitation codes.
    """
    __tablename__ = "invitations"
    
    invitation_id = Column(String(50), primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True)  # Optional: restrict to specific email
    created_by = Column(String(50), nullable=False)  # User ID of admin who created invitation
    is_used = Column(Boolean, default=False)
    used_by = Column(String(50), nullable=True)  # User ID who used this invitation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    
    def __repr__(self):
        return f"<Invitation(invitation_id='{self.invitation_id}', code='{self.code}', is_used={self.is_used})>" 