"""
Recognition model module.

This module defines the Recognition model for formal acknowledgments 
of a candidate's participation or achievements.
"""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Recognition(Base):
    """
    Model for recognitions.
    
    Represents formal acknowledgments of a candidate's participation
    or achievements, such as completion certificates, appreciation letters,
    or participation acknowledgments.
    """
    __tablename__ = "recognition"
    
    recognition_id = Column(String(60), primary_key=True)
    title = Column(String(200), nullable=False)
    issuing_organization = Column(String(100), nullable=False)
    issue_date = Column(Date)
    recognition_type = Column(String(50))  # Completion, Participation, Appreciation
    candidate_exam_id = Column(String(50), ForeignKey("candidate_exam.candidate_exam_id"), nullable=False)
    recognition_image_url = Column(Text)
    description = Column(Text)
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate_exam = relationship("CandidateExam", back_populates="recognitions")
    
    @validates('recognition_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("Recognition")
        return id_value
    
    def __repr__(self):
        return f"<Recognition(recognition_id='{self.recognition_id}', title='{self.title}')>" 