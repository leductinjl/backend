"""
Security Log model module.

This module defines the SecurityLog model used to track security-related actions
such as login attempts, password changes, and permission changes.
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.infrastructure.database.connection import Base

class SecurityLog(Base):
    """
    Security Log database model.
    
    This model logs all security-related actions in the system, providing an audit
    trail for security monitoring and compliance purposes.
    """
    __tablename__ = "security_logs"
    
    log_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), index=True)  # login, logout, register, password_reset, etc.
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    description = Column(Text)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    success = Column(Boolean, default=True)
    
    # Metadata
    request_id = Column(String(50), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="security_logs") 