"""
Award model module.

This module defines the Award model for honors or prizes
received by candidates in competitions or exams.
"""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Award(Base):
    """
    Model for awards.
    
    Represents honors or prizes received by candidates in competitions
    or exams, such as gold medals, first place, or other distinctions.
    """
    __tablename__ = "award"
    
    award_id = Column(String(60), primary_key=True)
    candidate_exam_id = Column(String(50), ForeignKey("candidate_exam.candidate_exam_id"), nullable=False)
    award_type = Column(String(50))  # First, Second, Third, Gold Medal, Silver Medal
    achievement = Column(String(100))  # Specific achievement if any
    certificate_image_url = Column(Text)
    education_level = Column(String(50))  # Education level when the award was earned
    award_date = Column(Date)
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate_exam = relationship("CandidateExam", back_populates="awards")
    
    @validates('award_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("Award")
        return id_value
    
    def __repr__(self):
        return f"<Award(award_id='{self.award_id}', award_type='{self.award_type}')>" 