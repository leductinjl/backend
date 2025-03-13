"""
Education History model module.

This module defines the EducationHistory model for recording a candidate's
educational background, particularly for primary, secondary, and high school levels.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class EducationHistory(Base):
    """
    Model for a candidate's educational history.
    
    Records a candidate's educational background, particularly for 
    primary, secondary, and high school levels, including the years attended
    and academic performance.
    """
    __tablename__ = "education_history"
    
    education_history_id = Column(String(50), primary_key=True)
    candidate_id = Column(String(20), ForeignKey("candidate.candidate_id"), nullable=False)
    school_id = Column(String(50), ForeignKey("school.school_id"), nullable=False)
    education_level = Column(String(50), nullable=False)  # Primary, Secondary, High School
    start_year = Column(Integer)
    end_year = Column(Integer)
    academic_performance = Column(String(20))  # Good, Excellent
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate = relationship("Candidate", back_populates="education_histories")
    school = relationship("School", back_populates="education_histories")
    
    @validates('education_history_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("EducationHistory")
        return id_value
    
    def __repr__(self):
        return f"<EducationHistory(education_history_id='{self.education_history_id}', candidate_id='{self.candidate_id}', education_level='{self.education_level}')>" 