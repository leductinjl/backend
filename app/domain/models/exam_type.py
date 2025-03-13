"""
Exam Type model module.

This module defines the ExamType model for categorizing different types of exams.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class ExamType(Base):
    """
    Model for exam types.
    
    Categorizes exams into different types such as Semester, Certificate, Competition, etc.
    """
    __tablename__ = "exam_type"
    
    type_id = Column(String(60), primary_key=True)
    type_name = Column(String(100), nullable=False)  # Semester, Certificate, Competition
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exams = relationship("Exam", back_populates="exam_type")
    
    @validates('type_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamType")
        return id_value
    
    def __repr__(self):
        return f"<ExamType(type_id='{self.type_id}', type_name='{self.type_name}')>" 