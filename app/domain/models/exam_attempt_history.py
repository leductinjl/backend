"""
Exam Attempt History model module.

This module defines the ExamAttemptHistory model for tracking
a candidate's multiple attempts at the same exam.
"""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class ExamAttemptHistory(Base):
    """
    Model for a candidate's exam attempt history.
    
    Records the history of a candidate's attempts at an exam,
    including the date, result, and notes for each attempt.
    """
    __tablename__ = "exam_attempt_history"
    
    attempt_history_id = Column(String(50), primary_key=True, index=True, default=lambda: generate_model_id("ExamAttemptHistory"))
    candidate_exam_id = Column(String(50), ForeignKey("candidate_exam.candidate_exam_id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    attempt_date = Column(Date, nullable=False)
    result = Column(String(50))  # Pass, Fail
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate_exam = relationship("CandidateExam", back_populates="exam_attempt_histories")
    
    @validates('attempt_history_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamAttemptHistory")
        return id_value
    
    def __repr__(self):
        return f"<ExamAttemptHistory(attempt_history_id='{self.attempt_history_id}', candidate_exam_id='{self.candidate_exam_id}', attempt_number={self.attempt_number})>" 