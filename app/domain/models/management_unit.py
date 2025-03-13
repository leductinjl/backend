"""
Management Unit model module.

This module defines the ManagementUnit model for storing information about
organizations that manage schools, exams, and other educational entities.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.infrastructure.database.connection import Base

class ManagementUnit(Base):
    """
    Model for organizations that manage exams and other educational entities.
    
    This can represent departments, ministries, university groups, or other administrative units
    that organize and manage examinations.
    """
    __tablename__ = "management_unit"
    
    unit_id = Column(String(50), primary_key=True)
    unit_name = Column(String(100), nullable=False)
    unit_type = Column(String(50), nullable=False)  # Department, Ministry, University Group
    additional_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exams = relationship("Exam", back_populates="organizing_unit")
    
    def __init__(self, **kwargs):
        """Initialize a new ManagementUnit instance with an auto-generated ID if not provided."""
        if 'unit_id' not in kwargs:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            kwargs['unit_id'] = f"MNGUNT_{timestamp}"
        super(ManagementUnit, self).__init__(**kwargs)
    
    def __repr__(self):
        return f"<ManagementUnit(unit_id='{self.unit_id}', unit_name='{self.unit_name}', unit_type='{self.unit_type}')>" 