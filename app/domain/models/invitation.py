"""
Invitation model module.

This module defines the Invitation model for controlling admin registration.
Only users with valid invitation codes can register as admin users.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Invitation(Base):
    """
    Model for admin registration invitations.
    
    Controls who can register as admin by requiring valid invitation codes.
    Invitations can be restricted to specific emails and have expiration dates.
    """
    __tablename__ = "invitations"
    
    invitation_id = Column(String(50), primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True)  # Optional: restrict to specific email
    role_id = Column(String(50), ForeignKey("roles.role_id", ondelete="SET NULL"), nullable=True)
    created_by = Column(String(50), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=False)  # User ID of admin who created invitation
    is_used = Column(Boolean, default=False)
    used_by = Column(String(50), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)  # User ID who used this invitation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(String(50), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    revocation_reason = Column(String(200), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_invitations")
    used_by_user = relationship("User", foreign_keys=[used_by])
    revoked_by_user = relationship("User", foreign_keys=[revoked_by])
    role = relationship("Role")
    
    def __repr__(self):
        return f"<Invitation(invitation_id='{self.invitation_id}', code='{self.code}', is_used={self.is_used})>" 