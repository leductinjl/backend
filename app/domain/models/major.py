"""
Major model module.

This module defines the Major model for storing information about
fields of study offered at educational institutions.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Major(Base):
    """
    Model for fields of study or academic majors.
    
    Represents areas of specialization that students can pursue
    at various education levels.
    """
    __tablename__ = "major"
    
    major_id = Column(String(50), primary_key=True, index=True)
    major_name = Column(String(150), nullable=False)
    ministry_code = Column(String(20))  # Ministry's major code (if any)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    school_majors = relationship("SchoolMajor", back_populates="major")
    degrees = relationship("Degree", back_populates="major")
    
    @validates('major_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("Major")
        return id_value
    
    def __repr__(self):
        return f"<Major(major_id='{self.major_id}', major_name='{self.major_name}')>" 