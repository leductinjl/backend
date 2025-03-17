"""
Exam Schedule model module.

This module defines the ExamSchedule model for storing information about
exam schedules, including start and end times for specific exam subjects.
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id
import enum

class ScheduleStatus(str, enum.Enum):
    """Enum for exam schedule status."""
    SCHEDULED = "SCHEDULED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ExamSchedule(Base):
    """
    Model for exam schedules.
    
    Represents a scheduled time slot for a specific exam subject.
    """
    __tablename__ = "exam_schedule"
    
    exam_schedule_id = Column(String(50), primary_key=True, index=True)
    exam_subject_id = Column(String(50), ForeignKey("exam_subject.exam_subject_id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="SCHEDULED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exam_subject = relationship("ExamSubject", back_populates="exam_schedules")
    
    @validates('exam_schedule_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamSchedule")
        return id_value
    
    @validates('end_time')
    def validate_end_time(self, key, end_time):
        """Validate that end_time is after start_time."""
        if hasattr(self, 'start_time') and self.start_time and end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        return end_time
    
    def __repr__(self):
        return f"<ExamSchedule(exam_schedule_id='{self.exam_schedule_id}', exam_subject_id='{self.exam_subject_id}', start_time='{self.start_time}')>" 