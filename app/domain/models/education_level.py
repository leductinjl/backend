"""
Education Level model module.

This module defines the EducationLevel model for standardizing 
educational levels across the system.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id
from datetime import datetime

class EducationLevel(Base):
    """
    Model for standardized education levels.
    
    Represents different levels of education such as Primary, 
    Secondary, High School, University, etc.
    """
    __tablename__ = "education_level"
    
    education_level_id = Column(String(50), primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    display_order = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __init__(self, **kwargs):
        """Initialize a new EducationLevel instance with an auto-generated ID if not provided."""
        if 'education_level_id' not in kwargs:
            kwargs['education_level_id'] = generate_model_id("EducationLevel")
        super(EducationLevel, self).__init__(**kwargs)
    
    @validates('education_level_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("EducationLevel")
        return id_value
    
    def __repr__(self):
        return f"<EducationLevel(education_level_id='{self.education_level_id}', name='{self.name}', code='{self.code}')>" 