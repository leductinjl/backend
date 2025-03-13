"""
Candidate model module.

This module defines the Candidate model, which represents the basic information
about candidates in the system.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Candidate(Base):
    """
    Model cho thông tin cơ bản của thí sinh
    """
    __tablename__ = "candidate"
    
    candidate_id = Column(String(20), primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    personal_info = relationship("PersonalInfo", back_populates="candidate", uselist=False)
    education_histories = relationship("EducationHistory", back_populates="candidate")
    candidate_exams = relationship("CandidateExam", back_populates="candidate")
    
    @validates('candidate_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("Candidate")
        return id_value
    
    def __repr__(self):
        return f"<Candidate(candidate_id='{self.candidate_id}', full_name='{self.full_name}')>" 