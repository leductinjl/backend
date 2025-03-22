"""
Candidate-Exam relationship model module.

This module defines the CandidateExam model which represents the relationship
between candidates and exams they participate in.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class CandidateExam(Base):
    """
    Model for a candidate's participation in an exam.
    
    This represents a candidate's registration and participation in an exam,
    including details like registration number, status, and room assignment.
    """
    __tablename__ = "candidate_exam"
    
    candidate_exam_id = Column(String(50), primary_key=True, index=True)
    candidate_id = Column(String(20), ForeignKey("candidate.candidate_id"), nullable=False)
    exam_id = Column(String(50), ForeignKey("exam.exam_id"), nullable=False)
    registration_number = Column(String(20))
    registration_date = Column(Date)
    status = Column(String(50))  # Registered, Attended, Absent
    attempt_number = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate = relationship("Candidate", back_populates="candidate_exams")
    exam = relationship("Exam", back_populates="candidate_exams")
    exam_attempt_histories = relationship("ExamAttemptHistory", back_populates="candidate_exam")
    certificates = relationship("Certificate", back_populates="candidate_exam")
    recognitions = relationship("Recognition", back_populates="candidate_exam")
    awards = relationship("Award", back_populates="candidate_exam")
    achievements = relationship("Achievement", back_populates="candidate_exam")
    candidate_exam_subjects = relationship("CandidateExamSubject", back_populates="candidate_exam")
    
    def __init__(self, **kwargs):
        """Initialize a new CandidateExam instance with an auto-generated ID if not provided."""
        if 'candidate_exam_id' not in kwargs:
            kwargs['candidate_exam_id'] = generate_model_id("CandidateExam")
        super(CandidateExam, self).__init__(**kwargs)
    
    @validates('candidate_exam_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("CandidateExam")
        return id_value
    
    def __repr__(self):
        return f"<CandidateExam(candidate_exam_id='{self.candidate_exam_id}', candidate_id='{self.candidate_id}', exam_id='{self.exam_id}')>" 