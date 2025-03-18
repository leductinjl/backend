"""
Two Factor Authentication Backup Codes model module.

This module defines the TwoFactorBackup model for storing backup codes that users
can use to log in when they don't have access to their 2FA device.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.infrastructure.database.connection import Base

class TwoFactorBackup(Base):
    """
    Two Factor Authentication Backup Codes database model.
    
    Stores hashed backup codes that users can use when they don't have
    access to their primary 2FA device. Each code can only be used once.
    """
    __tablename__ = "two_factor_backups"
    
    backup_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(100), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    used_ip = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User") 