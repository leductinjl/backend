"""
Exam Room model module.

This module defines the ExamRoom model for rooms within exam locations.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class ExamRoom(Base):
    """
    Model for exam rooms.
    
    Represents specific rooms within exam locations where
    exams are conducted, including capacity details.
    """
    __tablename__ = "exam_room"
    
    room_id = Column(String(60), primary_key=True)
    room_name = Column(String(50), nullable=False)
    location_id = Column(String(60), ForeignKey("exam_location.location_id"), nullable=False)
    capacity = Column(Integer)  # Maximum capacity
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    location = relationship("ExamLocation", back_populates="exam_rooms")
    
    @validates('room_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamRoom")
        return id_value
    
    def __repr__(self):
        return f"<ExamRoom(room_id='{self.room_id}', room_name='{self.room_name}', location_id='{self.location_id}')>"