"""
Subject model module.

This module defines the Subject model for academic subjects 
taught at different educational levels.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id
from datetime import datetime

class Subject(Base):
    """
    Model for academic subjects.
    
    Represents the specific subjects/courses taught at various education levels,
    which can be part of exams, majors, and curriculum.
    """
    __tablename__ = "subject"
    
    subject_id = Column(String(50), primary_key=True, index=True)
    subject_name = Column(String(100), nullable=False)
    subject_code = Column(String(20), nullable=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exam_subjects = relationship("ExamSubject", back_populates="subject")
    
    def __init__(self, **kwargs):
        """Initialize a new Subject instance with an auto-generated ID if not provided."""
        if 'subject_id' not in kwargs:
            kwargs['subject_id'] = generate_model_id("Subject")
        super(Subject, self).__init__(**kwargs)
    
    @validates('subject_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("Subject")
        return id_value
    
    def __repr__(self):
        return f"<Subject(subject_id='{self.subject_id}', subject_name='{self.subject_name}')>" 