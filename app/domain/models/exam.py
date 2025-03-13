"""
Exam model module.

This module defines the Exam model for examinations conducted at various levels.
"""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class Exam(Base):
    """
    Model for examinations.
    
    Represents exams conducted at various levels (school, provincial, national),
    including details about timing, scope, and organizing bodies.
    """
    __tablename__ = "exam"
    
    exam_id = Column(String(50), primary_key=True)
    exam_name = Column(String(200), nullable=False)
    type_id = Column(String(60), ForeignKey("exam_type.type_id"), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    scope = Column(String(50))  # School, Provincial, National, International
    education_level = Column(String(50))  # Secondary, High School, University
    organizing_unit_id = Column(String(50), ForeignKey("management_unit.unit_id"))
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exam_type = relationship("ExamType", back_populates="exams")
    organizing_unit = relationship("ManagementUnit", back_populates="exams")
    exam_location_mappings = relationship("ExamLocationMapping", back_populates="exam")
    exam_subjects = relationship("ExamSubject", back_populates="exam")
    candidate_exams = relationship("CandidateExam", back_populates="exam")
    
    @validates('exam_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("Exam")
        return id_value
    
    def __repr__(self):
        return f"<Exam(exam_id='{self.exam_id}', exam_name='{self.exam_name}', scope='{self.scope}')>" 