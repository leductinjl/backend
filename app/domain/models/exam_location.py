"""
Exam Location model module.

This module defines the ExamLocation model for places where exams are held.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id
from sqlalchemy.dialects.postgresql import JSONB

class ExamLocation(Base):
    """
    Model for exam locations.
    
    Represents physical locations where exams are conducted,
    including details like address and capacity.
    """
    __tablename__ = "exam_location"
    
    location_id = Column(String(60), primary_key=True, index=True)
    location_name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100))
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20))
    capacity = Column(Integer)  # Maximum capacity
    contact_info = Column(JSONB)
    additional_info = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exam_location_mappings = relationship("ExamLocationMapping", back_populates="location")
    exam_rooms = relationship("ExamRoom", back_populates="location")
    
    def __init__(self, **kwargs):
        """Initialize a new ExamLocation instance with an auto-generated ID if not provided."""
        if 'location_id' not in kwargs:
            kwargs['location_id'] = generate_model_id("ExamLocation")
        super(ExamLocation, self).__init__(**kwargs)
    
    @validates('location_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamLocation")
        return id_value
    
    def __repr__(self):
        return f"<ExamLocation(location_id='{self.location_id}', location_name='{self.location_name}')>" 