"""
Exam Score History model module.

This module defines the ExamScoreHistory model for tracking changes
to candidates' exam scores over time.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, TIMESTAMP, func, DateTime
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class ExamScoreHistory(Base):
    """
    Model for tracking changes to exam scores.
    
    Records the history of changes to a candidate's scores,
    including the previous and new scores, when the change occurred,
    and the reason for the change.
    """
    __tablename__ = "exam_score_history"
    
    history_id = Column(String(50), primary_key=True, index=True)
    score_id = Column(String(60), ForeignKey("exam_score.exam_score_id"), nullable=False)
    previous_score = Column(DECIMAL(5, 2))
    new_score = Column(DECIMAL(5, 2))
    change_date = Column(TIMESTAMP, nullable=False, server_default=func.now())
    change_reason = Column(String(200))
    changed_by = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    score = relationship("ExamScore", back_populates="score_histories")
    
    def __init__(self, **kwargs):
        """Initialize a new ExamScoreHistory instance with an auto-generated ID if not provided."""
        if 'history_id' not in kwargs:
            kwargs['history_id'] = generate_model_id("ExamScoreHistory")
        super(ExamScoreHistory, self).__init__(**kwargs)
    
    @validates('history_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ExamScoreHistory")
        return id_value
    
    def __repr__(self):
        return f"<ExamScoreHistory(history_id='{self.history_id}', score_id='{self.score_id}', previous_score={self.previous_score}, new_score={self.new_score})>" 