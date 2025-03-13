"""
Exam Score model module.

This module defines the ExamScore model for storing scores achieved by 
candidates in specific subjects within an exam.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DECIMAL, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class ExamScore(Base):
    """
    Model for exam scores.
    
    Represents the scores achieved by candidates in specific subjects
    within an exam, along with additional information.
    """
    __tablename__ = "exam_score"
    
    exam_score_id = Column(String(60), primary_key=True)
    exam_subject_id = Column(String(60), ForeignKey("exam_subject.exam_subject_id"), nullable=False)
    score = Column(DECIMAL(5, 2))
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exam_subject = relationship("ExamSubject", back_populates="exam_scores")
    score_histories = relationship("ExamScoreHistory", back_populates="score")
    score_reviews = relationship("ScoreReview", back_populates="score")
    
    @validates('exam_score_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamScore")
        return id_value
    
    def __repr__(self):
        return f"<ExamScore(exam_score_id='{self.exam_score_id}', exam_subject_id='{self.exam_subject_id}', score={self.score})>" 