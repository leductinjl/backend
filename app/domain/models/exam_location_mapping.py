"""
Exam-Location mapping model module.

This module defines the ExamLocationMapping model for the many-to-many
relationship between exams and their locations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id
from sqlalchemy.dialects.postgresql import JSONB

class ExamLocationMapping(Base):
    """
    Model for mapping exams to locations.
    
    This represents which locations are used for which exams,
    as one exam can take place across multiple locations.
    """
    __tablename__ = "exam_location_mapping"
    
    mapping_id = Column(String(50), primary_key=True, index=True)
    location_id = Column(String(60), ForeignKey("exam_location.location_id"), nullable=False)
    exam_id = Column(String(50), ForeignKey("exam.exam_id"), nullable=False)
    mapping_metadata = Column(JSONB) # Additional metadata for the mapping
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    location = relationship("ExamLocation", back_populates="exam_location_mappings")
    exam = relationship("Exam", back_populates="exam_location_mappings")
    
    # Ensure a location can only be mapped once to an exam
    __table_args__ = (UniqueConstraint('exam_id', 'location_id', name='unique_exam_location'),)
    
    def __init__(self, **kwargs):
        """Initialize a new ExamLocationMapping instance with an auto-generated ID if not provided."""
        if 'mapping_id' not in kwargs:
            kwargs['mapping_id'] = generate_model_id("ExamLocationMapping")
        # Handle metadata rename for backwards compatibility
        if 'metadata' in kwargs:
            kwargs['mapping_metadata'] = kwargs.pop('metadata')
        super(ExamLocationMapping, self).__init__(**kwargs)
    
    @validates('mapping_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamLocationMapping")
        return id_value
    
    def __repr__(self):
        return f"<ExamLocationMapping(mapping_id='{self.mapping_id}', location_id='{self.location_id}')>" 