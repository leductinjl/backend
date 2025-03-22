"""
Exam-Subject relationship model module.

This module defines the ExamSubject model which represents the many-to-many
relationship between exams and subjects tested in those exams.
"""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, JSON, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class ExamSubject(Base):
    """
    Model for the relationship between exams and subjects.
    
    This represents which subjects are tested in which exams,
    including details like exam date, duration, and room.
    """
    __tablename__ = "exam_subject"
    
    exam_subject_id = Column(String(60), primary_key=True, index=True)
    exam_id = Column(String(60), ForeignKey("exam.exam_id"), nullable=False)
    subject_id = Column(String(60), ForeignKey("subject.subject_id"), nullable=False)
    weight = Column(Float, default=1.0)
    passing_score = Column(Float, nullable=True)
    max_score = Column(Float, default=100.0)
    is_required = Column(Boolean, default=True)
    exam_date = Column(Date)
    duration_minutes = Column(Integer)
    additional_info = Column(Text)
    subject_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exam = relationship("Exam", back_populates="exam_subjects")
    subject = relationship("Subject", back_populates="exam_subjects")
    exam_scores = relationship("ExamScore", back_populates="exam_subject")
    exam_schedules = relationship("ExamSchedule", back_populates="exam_subject")
    candidate_exam_subjects = relationship("CandidateExamSubject", back_populates="exam_subject")
    
    @validates('exam_subject_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamSubject")
        return id_value
    
    def __repr__(self):
        return f"<ExamSubject(exam_subject_id='{self.exam_subject_id}', exam_id='{self.exam_id}', subject_id='{self.subject_id}')>" 