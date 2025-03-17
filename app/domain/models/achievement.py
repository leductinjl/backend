"""
Achievement model module.

This module defines the Achievement model for various accomplishments
by candidates outside of formal exams.
"""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Achievement(Base):
    """
    Model for achievements.
    
    Represents accomplishments by candidates outside of formal exams,
    such as research, community service, sports, or arts achievements.
    """
    __tablename__ = "achievement"
    
    achievement_id = Column(String(60), primary_key=True, index=True)
    candidate_exam_id = Column(String(50), ForeignKey("candidate_exam.candidate_exam_id"), nullable=False)
    achievement_name = Column(String(200), nullable=False)
    achievement_type = Column(String(50))  # Research, Community Service, Sports, Arts
    description = Column(Text)
    achievement_date = Column(Date)
    organization = Column(String(100))  # Organization recognizing the achievement
    proof_url = Column(Text)  # URL to proof of achievement
    education_level = Column(String(50))  # Education level when achieved
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate_exam = relationship("CandidateExam", back_populates="achievements")
    
    @validates('achievement_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("Achievement")
        return id_value
    
    def __repr__(self):
        return f"<Achievement(achievement_id='{self.achievement_id}', achievement_name='{self.achievement_name}')>" 