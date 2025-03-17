"""
Score Review repository module.

This module provides database operations for score reviews,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join, and_, or_
from sqlalchemy.sql import expression
from sqlalchemy.orm import joinedload

from app.domain.models.score_review import ScoreReview
from app.domain.models.exam_score import ExamScore
from app.domain.models.candidate_exam import CandidateExam
from app.domain.models.exam_subject import ExamSubject
from app.domain.models.candidate import Candidate
from app.domain.models.exam import Exam
from app.domain.models.subject import Subject
from app.domain.models.user import User

logger = logging.getLogger(__name__)

class ScoreReviewRepository:
    """Repository for managing ScoreReview entities in the database."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            db: An async SQLAlchemy session
        """
        self.db = db
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all score reviews with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of score reviews with details and total count
        """
        # Base query with eager loading of relationships
        query = select(ScoreReview).options(
            joinedload(ScoreReview.score)
        )
        
        # Apply filters
        if filters:
            if "search" in filters and filters["search"]:
                search_term = f"%{filters['search']}%"
                # Join all needed tables explicitly for searching
                query = query.join(
                    ExamScore, ScoreReview.score_id == ExamScore.score_id
                ).join(
                    ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id
                ).join(
                    Exam, ExamSubject.exam_id == Exam.exam_id
                ).join(
                    Subject, ExamSubject.subject_id == Subject.subject_id
                ).join(
                    CandidateExam, Exam.exam_id == CandidateExam.exam_id
                ).join(
                    Candidate, CandidateExam.candidate_id == Candidate.candidate_id
                ).filter(
                    or_(
                        Candidate.full_name.ilike(search_term),
                    Exam.exam_name.ilike(search_term),
                        Subject.name.ilike(search_term),
                        Subject.subject_code.ilike(search_term)
                    )
                )
            
            if "review_status" in filters and filters["review_status"]:
                query = query.filter(ScoreReview.review_status == filters["review_status"])
            
            if "score_id" in filters and filters["score_id"]:
                query = query.filter(ScoreReview.score_id == filters["score_id"])
        
            if "request_date_from" in filters and filters["request_date_from"]:
                date_from = date.fromisoformat(filters["request_date_from"])
                query = query.filter(ScoreReview.request_date >= date_from)
            
            if "request_date_to" in filters and filters["request_date_to"]:
                date_to = date.fromisoformat(filters["request_date_to"])
                query = query.filter(ScoreReview.request_date <= date_to)
            
            if "review_date_from" in filters and filters["review_date_from"]:
                date_from = date.fromisoformat(filters["review_date_from"])
                query = query.filter(ScoreReview.review_date >= date_from)
            
            if "review_date_to" in filters and filters["review_date_to"]:
                date_to = date.fromisoformat(filters["review_date_to"])
                query = query.filter(ScoreReview.review_date <= date_to)
            
            if "created_after" in filters and filters["created_after"]:
                created_after = datetime.fromisoformat(filters["created_after"])
                query = query.filter(ScoreReview.created_at >= created_after)
            
            if "created_before" in filters and filters["created_before"]:
                created_before = datetime.fromisoformat(filters["created_before"])
                query = query.filter(ScoreReview.created_at <= created_before)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(ScoreReview.created_at.desc())
        
        result = await self.db.execute(query)
        reviews = result.scalars().unique().all()
        
        # Convert ORM objects to dictionaries
        reviews_dict = [self._entity_to_dict(review) for review in reviews]
        
        return reviews_dict, total or 0
    
    async def get_by_id(self, score_review_id: str) -> Optional[Dict]:
        """
        Get a score review by its ID, including related entity details.
        
        Args:
            score_review_id: The unique identifier of the score review
            
        Returns:
            The score review with related entity details if found, None otherwise
        """
        # Query with the score review and eager load the exam score
        query = select(ScoreReview).options(
            joinedload(ScoreReview.score)
        ).filter(
            ScoreReview.score_review_id == score_review_id
        )
        
        result = await self.db.execute(query)
        review = result.scalar_one_or_none()
        
        if not review:
            return None
        
        # Additional query to get related data
        if review.score:
            # Get exam information
            exam_query = select(Exam).join(
                ExamSubject, Exam.exam_id == ExamSubject.exam_id
            ).join(
                ExamScore, ExamSubject.exam_subject_id == ExamScore.exam_subject_id
            ).filter(
                ExamScore.score_id == review.score_id
            )
            exam_result = await self.db.execute(exam_query)
            exam = exam_result.scalar_one_or_none()
            
            # Get subject information
            subject_query = select(Subject).join(
                ExamSubject, Subject.subject_id == ExamSubject.subject_id
            ).join(
                ExamScore, ExamSubject.exam_subject_id == ExamScore.exam_subject_id
            ).filter(
                ExamScore.score_id == review.score_id
            )
            subject_result = await self.db.execute(subject_query)
            subject = subject_result.scalar_one_or_none()
            
            # Get candidate information
            candidate_query = select(Candidate).join(
                CandidateExam, Candidate.candidate_id == CandidateExam.candidate_id
            ).join(
                Exam, CandidateExam.exam_id == Exam.exam_id
            ).join(
                ExamSubject, Exam.exam_id == ExamSubject.exam_id
            ).join(
                ExamScore, ExamSubject.exam_subject_id == ExamScore.exam_subject_id
            ).filter(
                ExamScore.score_id == review.score_id
            )
            candidate_result = await self.db.execute(candidate_query)
            candidate = candidate_result.scalar_one_or_none()
            
            # Add related entities to the score for use in _entity_to_dict
            review.score._exam = exam
            review.score._subject = subject
            review.score._candidate = candidate
        
        return self._entity_to_dict(review)
    
    async def get_by_score_id(self, score_id: str) -> List[Dict]:
        """
        Get all reviews for a specific exam score.
        
        Args:
            score_id: The ID of the exam score
            
        Returns:
            List of reviews for the specified exam score
        """
        # Base query to get all reviews for the specified score
        query = select(ScoreReview).options(
            joinedload(ScoreReview.score)
        ).filter(
            ScoreReview.score_id == score_id
        ).order_by(ScoreReview.created_at.desc())
        
        result = await self.db.execute(query)
        reviews = result.scalars().all()
        
        # If there are no reviews, return an empty list
        if not reviews:
            return []
            
        # Get exam, subject, and candidate information once for all reviews
        # since they all relate to the same exam score
        
        # Get exam information
        exam_query = select(Exam).join(
            ExamSubject, Exam.exam_id == ExamSubject.exam_id
        ).join(
            ExamScore, ExamSubject.exam_subject_id == ExamScore.exam_subject_id
        ).filter(
            ExamScore.score_id == score_id
        )
        exam_result = await self.db.execute(exam_query)
        exam = exam_result.scalar_one_or_none()
        
        # Get subject information
        subject_query = select(Subject).join(
            ExamSubject, Subject.subject_id == ExamSubject.subject_id
        ).join(
            ExamScore, ExamSubject.exam_subject_id == ExamScore.exam_subject_id
        ).filter(
            ExamScore.score_id == score_id
        )
        subject_result = await self.db.execute(subject_query)
        subject = subject_result.scalar_one_or_none()
        
        # Get candidate information
        candidate_query = select(Candidate).join(
            CandidateExam, Candidate.candidate_id == CandidateExam.candidate_id
        ).join(
            Exam, CandidateExam.exam_id == Exam.exam_id
        ).join(
            ExamSubject, Exam.exam_id == ExamSubject.exam_id
        ).join(
            ExamScore, ExamSubject.exam_subject_id == ExamScore.exam_subject_id
        ).filter(
            ExamScore.score_id == score_id
        )
        candidate_result = await self.db.execute(candidate_query)
        candidate = candidate_result.scalar_one_or_none()
        
        # Add related entities to each review's score object
        for review in reviews:
            if review.score:
                review.score._exam = exam
                review.score._subject = subject
                review.score._candidate = candidate
        
        # Convert ORM objects to dictionaries
        return [self._entity_to_dict(review) for review in reviews]
    
    async def get_by_requested_by(self, user_id: str) -> List[Dict]:
        """
        Get all reviews requested by a specific user.
        
        Args:
            user_id: The ID of the user who requested the reviews
            
        Returns:
            List of reviews requested by the specified user
        """
        # For now, let's return an empty list as the model doesn't have requested_by field
        # This will need to be updated when the field is added to the model
        logger.warning("get_by_requested_by not fully implemented - model changes required")
        return []
    
    async def get_by_assigned_to(self, user_id: str) -> List[Dict]:
        """
        Get all reviews assigned to a specific user.
        
        Args:
            user_id: The ID of the user who is assigned to the reviews
            
        Returns:
            List of reviews assigned to the specified user
        """
        # For now, let's return an empty list as the model doesn't have assigned_to field
        # This will need to be updated when the field is added to the model
        logger.warning("get_by_assigned_to not fully implemented - model changes required")
        return []
    
    async def get_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all reviews related to a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of reviews related to the specified candidate
        """
        # First, get all the score IDs related to this candidate
        score_ids_query = (
            select(ExamScore.score_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(Candidate.candidate_id == candidate_id)
        )
        
        score_ids_result = await self.db.execute(score_ids_query)
        score_ids = [row[0] for row in score_ids_result.all()]
        
        if not score_ids:
            return []
        
        # Then get all reviews for these scores
        reviews_query = (
            select(ScoreReview)
            .options(joinedload(ScoreReview.score))
            .filter(ScoreReview.score_id.in_(score_ids))
            .order_by(ScoreReview.created_at.desc())
        )
        
        reviews_result = await self.db.execute(reviews_query)
        reviews = reviews_result.scalars().all()
        
        # Process each review to add the related data
        processed_reviews = []
        for review in reviews:
            # Get the exam, subject, and candidate data for this review
            if review.score:
                # Get exam information
                exam_query = select(Exam).join(
                    ExamSubject, Exam.exam_id == ExamSubject.exam_id
                ).join(
                    ExamScore, ExamSubject.exam_subject_id == ExamScore.exam_subject_id
                ).filter(
                    ExamScore.score_id == review.score_id
                )
                exam_result = await self.db.execute(exam_query)
                exam = exam_result.scalar_one_or_none()
                
                # Get subject information
                subject_query = select(Subject).join(
                    ExamSubject, Subject.subject_id == ExamSubject.subject_id
                ).join(
                    ExamScore, ExamSubject.exam_subject_id == ExamScore.exam_subject_id
                ).filter(
                    ExamScore.score_id == review.score_id
                )
                subject_result = await self.db.execute(subject_query)
                subject = subject_result.scalar_one_or_none()
                
                # Get candidate information (we already know the candidate_id)
                candidate_query = select(Candidate).filter(Candidate.candidate_id == candidate_id)
                candidate_result = await self.db.execute(candidate_query)
                candidate = candidate_result.scalar_one_or_none()
                
                # Attach the related entities to the score
                review.score._exam = exam
                review.score._subject = subject
                review.score._candidate = candidate
            
            processed_reviews.append(self._entity_to_dict(review))
        
        return processed_reviews
    
    async def create(self, review_data: Dict[str, Any]) -> ScoreReview:
        """
        Create a new score review.
        
        Args:
            review_data: Dictionary containing the score review data
            
        Returns:
            The created score review
        """
        # Ensure score_review_id is set before creating the object
        if "score_review_id" not in review_data or not review_data["score_review_id"]:
            from app.services.id_service import generate_model_id
            review_data["score_review_id"] = generate_model_id("ScoreReview")
        
        # Create a new score review
        new_review = ScoreReview(**review_data)
        
        # Add to session and commit
        self.db.add(new_review)
        await self.db.commit()
        await self.db.refresh(new_review)
        
        logger.info(f"Created score review with ID: {new_review.score_review_id}")
        return new_review
    
    async def update(self, score_review_id: str, review_data: Dict[str, Any]) -> Optional[ScoreReview]:
        """
        Update a score review.
        
        Args:
            score_review_id: The unique identifier of the score review
            review_data: Dictionary containing the updated data
            
        Returns:
            The updated score review if found, None otherwise
        """
        # Get the raw ScoreReview object first
        query = select(ScoreReview).filter(ScoreReview.score_review_id == score_review_id)
        result = await self.db.execute(query)
        existing_review = result.scalar_one_or_none()
        
        if not existing_review:
            return None
        
        # Update the score review
        update_stmt = (
            update(ScoreReview)
            .where(ScoreReview.score_review_id == score_review_id)
            .values(**review_data)
            .returning(ScoreReview)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_review = result.scalar_one_or_none()
        if updated_review:
            logger.info(f"Updated score review with ID: {score_review_id}")
        
        return updated_review
    
    async def delete(self, score_review_id: str) -> bool:
        """
        Delete a score review.
        
        Args:
            score_review_id: The unique identifier of the score review
            
        Returns:
            True if the score review was deleted, False otherwise
        """
        # Check if the score review exists
        query = select(ScoreReview).filter(ScoreReview.score_review_id == score_review_id)
        result = await self.db.execute(query)
        existing_review = result.scalar_one_or_none()
        
        if not existing_review:
            return False
        
        # Delete the score review
        delete_stmt = delete(ScoreReview).where(ScoreReview.score_review_id == score_review_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted score review with ID: {score_review_id}")
        return True 
    
    def _entity_to_dict(self, review: ScoreReview) -> Dict:
        """
        Convert ScoreReview entity to dictionary with full relationship details.
        
        Args:
            review: ScoreReview entity
            
        Returns:
            Dictionary with ScoreReview data
        """
        review_dict = {
            "score_review_id": review.score_review_id,
            "score_id": review.score_id,
            "request_date": review.request_date.isoformat() if review.request_date else None,
            "review_status": review.review_status,
            "original_score": float(review.original_score) if review.original_score is not None else None,
            "reviewed_score": float(review.reviewed_score) if review.reviewed_score is not None else None,
            "review_result": review.review_result,
            "review_date": review.review_date.isoformat() if review.review_date else None,
            "additional_info": review.additional_info,
            "score_review_metadata": review.score_review_metadata,
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "updated_at": review.updated_at.isoformat() if review.updated_at else None
        }
        
        # Add exam score details if loaded
        if review.score:
            score = review.score
            review_dict["exam_score"] = {
                "score_id": getattr(score, 'exam_score_id', None),
                "candidate_id": getattr(getattr(score, '_candidate', None), 'candidate_id', None),
                "exam_id": getattr(getattr(score, '_exam', None), 'exam_id', None),
                "subject_id": getattr(getattr(score, '_subject', None), 'subject_id', None),
                "score": float(score.score) if hasattr(score, 'score') and score.score is not None else None,
                "scoring_date": score.scoring_date.isoformat() if hasattr(score, 'scoring_date') and score.scoring_date else None,
                "status": score.status if hasattr(score, 'status') else None
            }
            
            # Add candidate details if loaded
            if hasattr(score, '_candidate') and score._candidate:
                candidate = score._candidate
                review_dict["candidate"] = {
                    "candidate_id": candidate.candidate_id,
                    "name": candidate.full_name
                }
            
            # Add exam details if loaded
            if hasattr(score, '_exam') and score._exam:
                exam = score._exam
                review_dict["exam"] = {
                    "exam_id": exam.exam_id,
                    "name": exam.exam_name
                }
            
            # Add subject details if loaded
            if hasattr(score, '_subject') and score._subject:
                subject = score._subject
                review_dict["subject"] = {
                    "subject_id": subject.subject_id,
                    "subject_code": subject.subject_code,
                    "name": subject.name
                }
        
        return review_dict 