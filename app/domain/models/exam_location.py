"""
Exam Location model module.

This module defines the ExamLocation model for places where exams are held.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class ExamLocation(Base):
    """
    Model for exam locations.
    
    Represents physical locations where exams are conducted,
    including details like address and capacity.
    """
    __tablename__ = "exam_location"
    
    location_id = Column(String(60), primary_key=True)
    location_name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    capacity = Column(Integer)  # Maximum capacity
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exam_location_mappings = relationship("ExamLocationMapping", back_populates="location")
    exam_rooms = relationship("ExamRoom", back_populates="location")
    
    @validates('location_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamLocation")
        return id_value
    
    def __repr__(self):
        return f"<ExamLocation(location_id='{self.location_id}', location_name='{self.location_name}')>" 