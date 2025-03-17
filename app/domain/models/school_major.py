"""
School-Major relationship model module.

This module defines the SchoolMajor model which represents the many-to-many
relationship between schools and majors (programs offered by schools).
"""

from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint, DateTime, Integer, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class SchoolMajor(Base):
    """
    Model for the relationship between schools and majors.
    
    This represents which majors/programs are offered by which schools,
    including when they started offering the program.
    """
    __tablename__ = "school_major"
    
    school_major_id = Column(String(60), primary_key=True, index=True)
    school_id = Column(String(60), ForeignKey("school.school_id"), nullable=False)
    major_id = Column(String(60), ForeignKey("major.major_id"), nullable=False)
    start_year = Column(Integer)  # When the school started offering this major
    is_active = Column(Boolean, default=True, nullable=False)  # Whether the major is still offered by the school
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    school = relationship("School", back_populates="school_majors")
    major = relationship("Major", back_populates="school_majors")
    
    # Ensure a major can only be linked once to a school
    __table_args__ = (UniqueConstraint('school_id', 'major_id', name='unique_school_major'),)
    
    @validates('school_major_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("SchoolMajor")
        return id_value
    
    def __repr__(self):
        return f"<SchoolMajor(school_major_id='{self.school_major_id}', school_id='{self.school_id}', major_id='{self.major_id}', start_year={self.start_year})>" 