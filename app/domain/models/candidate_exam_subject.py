"""
Candidate-Exam-Subject relationship model module.

This module defines the CandidateExamSubject model which represents the relationship
between candidates and specific subjects within exams they participate in.
"""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id
import enum

class RegistrationStatus(str, enum.Enum):
    """Enum for registration status."""
    REGISTERED = "REGISTERED"
    CONFIRMED = "CONFIRMED"  
    WITHDRAWN = "WITHDRAWN"
    ABSENT = "ABSENT"
    COMPLETED = "COMPLETED"

class CandidateExamSubject(Base):
    """
    Model for the relationship between candidates and exam subjects.
    
    This represents which specific subjects a candidate is registered for
    within an exam, allowing for precise tracking of a candidate's exam schedule.
    """
    __tablename__ = "candidate_exam_subject"
    
    candidate_exam_subject_id = Column(String(60), primary_key=True, index=True)
    candidate_exam_id = Column(String(50), ForeignKey("candidate_exam.candidate_exam_id"), nullable=False)
    exam_subject_id = Column(String(60), ForeignKey("exam_subject.exam_subject_id"), nullable=False)
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default=RegistrationStatus.REGISTERED)
    is_required = Column(Boolean, default=True)  # Whether this subject is mandatory for the candidate
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    candidate_exam = relationship("CandidateExam", back_populates="candidate_exam_subjects")
    exam_subject = relationship("ExamSubject", back_populates="candidate_exam_subjects")
    # Relationship with exam scores will be defined in ExamScore model using backref
    
    @validates('candidate_exam_subject_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("CandidateExamSubject")
        return id_value
    
    def __repr__(self):
        return f"<CandidateExamSubject(candidate_exam_subject_id='{self.candidate_exam_subject_id}', candidate_exam_id='{self.candidate_exam_id}', exam_subject_id='{self.exam_subject_id}')>"
