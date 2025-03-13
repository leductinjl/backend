"""
User model module.

This module defines the User model for the system. In this system, only admin users 
are stored in the database, as student/candidate information is accessed without authentication.
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.infrastructure.database.connection import Base
from sqlalchemy.orm import validates
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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    @validates('user_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("User")
        return id_value
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}', role='{self.role}')>" 