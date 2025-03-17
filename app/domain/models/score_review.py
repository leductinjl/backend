"""
Score Review model module.

This module defines the ScoreReview model for tracking requests to review
and potentially adjust candidate exam scores.
"""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DECIMAL, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from app.infrastructure.database.connection import Base
from app.services.id_service import generate_model_id

class ScoreReview(Base):
    """
    Model for exam score review requests.
    
    Represents a request to review a candidate's exam score,
    including the original score, the reviewed score, and the status
    of the review process.
    """
    __tablename__ = "score_review"
    
    score_review_id = Column(String(60), primary_key=True, index=True)
    score_id = Column(String(60), ForeignKey("exam_score.exam_score_id"), nullable=False)
    request_date = Column(Date, nullable=False)
    review_status = Column(String(50), nullable=False)  # Pending, Approved, Rejected
    original_score = Column(DECIMAL(5, 2))
    reviewed_score = Column(DECIMAL(5, 2))
    review_result = Column(Text)
    review_date = Column(Date)
    additional_info = Column(Text)
    score_review_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    score = relationship("ExamScore", back_populates="score_reviews")
    
    @validates('score_review_id')
    def validate_id(self, key, id_value):
        """Validate and generate ID if not provided."""
        if not id_value:
            return generate_model_id("ScoreReview")
        return id_value
    
    def __repr__(self):
        return f"<ScoreReview(score_review_id='{self.score_review_id}', score_id='{self.score_id}', review_status='{self.review_status}')>" 