"""
School model module.

This module defines the School model for storing information about
educational institutions including their location and management.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class School(Base):
    """
    Model for educational institutions.
    
    Represents schools, universities, or other educational institutions
    that can serve multiple education levels.
    """
    __tablename__ = "school"
    
    school_id = Column(String(50), primary_key=True, index=True)
    school_name = Column(String(150), nullable=False)
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    school_majors = relationship("SchoolMajor", back_populates="school")
    education_histories = relationship("EducationHistory", back_populates="school")
    
    @validates('school_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("School")
        return id_value
    
    def __repr__(self):
        return f"<School(school_id='{self.school_id}', school_name='{self.school_name}')>" 