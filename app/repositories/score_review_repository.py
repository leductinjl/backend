"""
Score Review repository module.

This module provides database operations for score reviews,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join, and_, or_
from sqlalchemy.sql import expression

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
        # Base query with all necessary joins
        query = (
            select(
                ScoreReview,
                ExamScore.score,
                Candidate.candidate_name,
                Candidate.candidate_code,
                Exam.exam_name,
                Subject.subject_name,
                ExamSubject.max_score
            )
            .join(ExamScore, ScoreReview.score_id == ExamScore.score_id)
            .join(CandidateExam, ExamScore.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .outerjoin(User, ScoreReview.assigned_to == User.user_id)
        )
        
        # Apply search filter
        if filters and "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Candidate.candidate_name.ilike(search_term),
                    Candidate.candidate_code.ilike(search_term),
                    Exam.exam_name.ilike(search_term),
                    Subject.subject_name.ilike(search_term),
                    Subject.subject_code.ilike(search_term),
                    ScoreReview.reason.ilike(search_term)
                )
            )
        
        # Apply status filter
        if filters and "status" in filters and filters["status"]:
            query = query.filter(ScoreReview.status == filters["status"])
        
        # Apply priority filter
        if filters and "priority" in filters and filters["priority"]:
            query = query.filter(ScoreReview.priority == filters["priority"])
        
        # Apply score_id filter
        if filters and "score_id" in filters and filters["score_id"]:
            query = query.filter(ScoreReview.score_id == filters["score_id"])
        
        # Apply requested_by filter
        if filters and "requested_by" in filters and filters["requested_by"]:
            query = query.filter(ScoreReview.requested_by == filters["requested_by"])
        
        # Apply assigned_to filter
        if filters and "assigned_to" in filters and filters["assigned_to"]:
            query = query.filter(ScoreReview.assigned_to == filters["assigned_to"])
        
        # Apply candidate_id filter
        if filters and "candidate_id" in filters and filters["candidate_id"]:
            query = query.filter(CandidateExam.candidate_id == filters["candidate_id"])
        
        # Apply exam_id filter
        if filters and "exam_id" in filters and filters["exam_id"]:
            query = query.filter(ExamSubject.exam_id == filters["exam_id"])
        
        # Apply subject_id filter
        if filters and "subject_id" in filters and filters["subject_id"]:
            query = query.filter(ExamSubject.subject_id == filters["subject_id"])
        
        # Apply created_after filter
        if filters and "created_after" in filters and filters["created_after"]:
            query = query.filter(ScoreReview.created_at >= filters["created_after"])
        
        # Apply created_before filter
        if filters and "created_before" in filters and filters["created_before"]:
            query = query.filter(ScoreReview.created_at <= filters["created_before"])
        
        # Apply resolved_after filter
        if filters and "resolved_after" in filters and filters["resolved_after"]:
            query = query.filter(ScoreReview.resolved_at >= filters["resolved_after"])
        
        # Apply resolved_before filter
        if filters and "resolved_before" in filters and filters["resolved_before"]:
            query = query.filter(ScoreReview.resolved_at <= filters["resolved_before"])
        
        # Apply additional filters if any
        if filters:
            for field, value in filters.items():
                if field not in ["search", "status", "priority", "score_id", "requested_by", "assigned_to",
                                "candidate_id", "exam_id", "subject_id", "created_after", "created_before",
                                "resolved_after", "resolved_before"] and value is not None:
                    if hasattr(ScoreReview, field):
                        query = query.filter(getattr(ScoreReview, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include related entity names
        score_reviews = []
        for review, current_score, candidate_name, candidate_code, exam_name, subject_name, max_score in result:
            # Get requested_by and assigned_to names if available
            requested_by_name = None
            assigned_to_name = None
            
            if review.requested_by:
                requester_query = select(User.name).filter(User.user_id == review.requested_by)
                requester_result = await self.db.execute(requester_query)
                requested_by_name = requester_result.scalar_one_or_none()
            
            if review.assigned_to:
                assignee_query = select(User.name).filter(User.user_id == review.assigned_to)
                assignee_result = await self.db.execute(assignee_query)
                assigned_to_name = assignee_result.scalar_one_or_none()
            
            score_review_dict = {
                "review_id": review.review_id,
                "score_id": review.score_id,
                "requested_by": review.requested_by,
                "reason": review.reason,
                "expected_score": review.expected_score,
                "status": review.status,
                "priority": review.priority,
                "assigned_to": review.assigned_to,
                "resolution_notes": review.resolution_notes,
                "resolved_at": review.resolved_at,
                "metadata": review.metadata,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
                "candidate_name": candidate_name,
                "candidate_code": candidate_code,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "current_score": current_score,
                "max_score": max_score,
                "requested_by_name": requested_by_name,
                "assigned_to_name": assigned_to_name
            }
            score_reviews.append(score_review_dict)
        
        return score_reviews, total or 0
    
    async def get_by_id(self, review_id: str) -> Optional[Dict]:
        """
        Get a score review by its ID, including related entity details.
        
        Args:
            review_id: The unique identifier of the score review
            
        Returns:
            The score review with related entity details if found, None otherwise
        """
        query = (
            select(
                ScoreReview,
                ExamScore.score,
                Candidate.candidate_name,
                Candidate.candidate_code,
                Exam.exam_name,
                Subject.subject_name,
                ExamSubject.max_score
            )
            .join(ExamScore, ScoreReview.score_id == ExamScore.score_id)
            .join(CandidateExam, ExamScore.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .filter(ScoreReview.review_id == review_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        review, current_score, candidate_name, candidate_code, exam_name, subject_name, max_score = row
        
        # Get requested_by and assigned_to names if available
        requested_by_name = None
        assigned_to_name = None
        
        if review.requested_by:
            requester_query = select(User.name).filter(User.user_id == review.requested_by)
            requester_result = await self.db.execute(requester_query)
            requested_by_name = requester_result.scalar_one_or_none()
        
        if review.assigned_to:
            assignee_query = select(User.name).filter(User.user_id == review.assigned_to)
            assignee_result = await self.db.execute(assignee_query)
            assigned_to_name = assignee_result.scalar_one_or_none()
        
        return {
            "review_id": review.review_id,
            "score_id": review.score_id,
            "requested_by": review.requested_by,
            "reason": review.reason,
            "expected_score": review.expected_score,
            "status": review.status,
            "priority": review.priority,
            "assigned_to": review.assigned_to,
            "resolution_notes": review.resolution_notes,
            "resolved_at": review.resolved_at,
            "metadata": review.metadata,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "candidate_name": candidate_name,
            "candidate_code": candidate_code,
            "exam_name": exam_name,
            "subject_name": subject_name,
            "current_score": current_score,
            "max_score": max_score,
            "requested_by_name": requested_by_name,
            "assigned_to_name": assigned_to_name
        }
    
    async def get_by_score_id(self, score_id: str) -> List[Dict]:
        """
        Get all reviews for a specific exam score.
        
        Args:
            score_id: The ID of the exam score
            
        Returns:
            List of reviews for the specified exam score
        """
        query = (
            select(
                ScoreReview,
                ExamScore.score,
                Candidate.candidate_name,
                Candidate.candidate_code,
                Exam.exam_name,
                Subject.subject_name,
                ExamSubject.max_score
            )
            .join(ExamScore, ScoreReview.score_id == ExamScore.score_id)
            .join(CandidateExam, ExamScore.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .filter(ScoreReview.score_id == score_id)
        )
        
        result = await self.db.execute(query)
        
        score_reviews = []
        for review, current_score, candidate_name, candidate_code, exam_name, subject_name, max_score in result:
            # Get requested_by and assigned_to names if available
            requested_by_name = None
            assigned_to_name = None
            
            if review.requested_by:
                requester_query = select(User.name).filter(User.user_id == review.requested_by)
                requester_result = await self.db.execute(requester_query)
                requested_by_name = requester_result.scalar_one_or_none()
            
            if review.assigned_to:
                assignee_query = select(User.name).filter(User.user_id == review.assigned_to)
                assignee_result = await self.db.execute(assignee_query)
                assigned_to_name = assignee_result.scalar_one_or_none()
            
            score_review_dict = {
                "review_id": review.review_id,
                "score_id": review.score_id,
                "requested_by": review.requested_by,
                "reason": review.reason,
                "expected_score": review.expected_score,
                "status": review.status,
                "priority": review.priority,
                "assigned_to": review.assigned_to,
                "resolution_notes": review.resolution_notes,
                "resolved_at": review.resolved_at,
                "metadata": review.metadata,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
                "candidate_name": candidate_name,
                "candidate_code": candidate_code,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "current_score": current_score,
                "max_score": max_score,
                "requested_by_name": requested_by_name,
                "assigned_to_name": assigned_to_name
            }
            score_reviews.append(score_review_dict)
        
        return score_reviews
    
    async def get_by_requested_by(self, user_id: str) -> List[Dict]:
        """
        Get all reviews requested by a specific user.
        
        Args:
            user_id: The ID of the user who requested the reviews
            
        Returns:
            List of reviews requested by the specified user
        """
        query = (
            select(
                ScoreReview,
                ExamScore.score,
                Candidate.candidate_name,
                Candidate.candidate_code,
                Exam.exam_name,
                Subject.subject_name,
                ExamSubject.max_score
            )
            .join(ExamScore, ScoreReview.score_id == ExamScore.score_id)
            .join(CandidateExam, ExamScore.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .filter(ScoreReview.requested_by == user_id)
        )
        
        result = await self.db.execute(query)
        
        score_reviews = []
        for review, current_score, candidate_name, candidate_code, exam_name, subject_name, max_score in result:
            # Get assigned_to name if available
            assigned_to_name = None
            
            if review.assigned_to:
                assignee_query = select(User.name).filter(User.user_id == review.assigned_to)
                assignee_result = await self.db.execute(assignee_query)
                assigned_to_name = assignee_result.scalar_one_or_none()
            
            score_review_dict = {
                "review_id": review.review_id,
                "score_id": review.score_id,
                "requested_by": review.requested_by,
                "reason": review.reason,
                "expected_score": review.expected_score,
                "status": review.status,
                "priority": review.priority,
                "assigned_to": review.assigned_to,
                "resolution_notes": review.resolution_notes,
                "resolved_at": review.resolved_at,
                "metadata": review.metadata,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
                "candidate_name": candidate_name,
                "candidate_code": candidate_code,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "current_score": current_score,
                "max_score": max_score,
                "requested_by_name": user_id,  # We already know the requester
                "assigned_to_name": assigned_to_name
            }
            score_reviews.append(score_review_dict)
        
        return score_reviews
    
    async def get_by_assigned_to(self, user_id: str) -> List[Dict]:
        """
        Get all reviews assigned to a specific user.
        
        Args:
            user_id: The ID of the user who is assigned to the reviews
            
        Returns:
            List of reviews assigned to the specified user
        """
        query = (
            select(
                ScoreReview,
                ExamScore.score,
                Candidate.candidate_name,
                Candidate.candidate_code,
                Exam.exam_name,
                Subject.subject_name,
                ExamSubject.max_score
            )
            .join(ExamScore, ScoreReview.score_id == ExamScore.score_id)
            .join(CandidateExam, ExamScore.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .filter(ScoreReview.assigned_to == user_id)
        )
        
        result = await self.db.execute(query)
        
        score_reviews = []
        for review, current_score, candidate_name, candidate_code, exam_name, subject_name, max_score in result:
            # Get requested_by name if available
            requested_by_name = None
            
            if review.requested_by:
                requester_query = select(User.name).filter(User.user_id == review.requested_by)
                requester_result = await self.db.execute(requester_query)
                requested_by_name = requester_result.scalar_one_or_none()
            
            score_review_dict = {
                "review_id": review.review_id,
                "score_id": review.score_id,
                "requested_by": review.requested_by,
                "reason": review.reason,
                "expected_score": review.expected_score,
                "status": review.status,
                "priority": review.priority,
                "assigned_to": review.assigned_to,
                "resolution_notes": review.resolution_notes,
                "resolved_at": review.resolved_at,
                "metadata": review.metadata,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
                "candidate_name": candidate_name,
                "candidate_code": candidate_code,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "current_score": current_score,
                "max_score": max_score,
                "requested_by_name": requested_by_name,
                "assigned_to_name": user_id  # We already know the assignee
            }
            score_reviews.append(score_review_dict)
        
        return score_reviews
    
    async def get_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all reviews related to a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of reviews related to the specified candidate
        """
        query = (
            select(
                ScoreReview,
                ExamScore.score,
                Candidate.candidate_name,
                Candidate.candidate_code,
                Exam.exam_name,
                Subject.subject_name,
                ExamSubject.max_score
            )
            .join(ExamScore, ScoreReview.score_id == ExamScore.score_id)
            .join(CandidateExam, ExamScore.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .filter(CandidateExam.candidate_id == candidate_id)
        )
        
        result = await self.db.execute(query)
        
        score_reviews = []
        for review, current_score, candidate_name, candidate_code, exam_name, subject_name, max_score in result:
            # Get requested_by and assigned_to names if available
            requested_by_name = None
            assigned_to_name = None
            
            if review.requested_by:
                requester_query = select(User.name).filter(User.user_id == review.requested_by)
                requester_result = await self.db.execute(requester_query)
                requested_by_name = requester_result.scalar_one_or_none()
            
            if review.assigned_to:
                assignee_query = select(User.name).filter(User.user_id == review.assigned_to)
                assignee_result = await self.db.execute(assignee_query)
                assigned_to_name = assignee_result.scalar_one_or_none()
            
            score_review_dict = {
                "review_id": review.review_id,
                "score_id": review.score_id,
                "requested_by": review.requested_by,
                "reason": review.reason,
                "expected_score": review.expected_score,
                "status": review.status,
                "priority": review.priority,
                "assigned_to": review.assigned_to,
                "resolution_notes": review.resolution_notes,
                "resolved_at": review.resolved_at,
                "metadata": review.metadata,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
                "candidate_name": candidate_name,
                "candidate_code": candidate_code,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "current_score": current_score,
                "max_score": max_score,
                "requested_by_name": requested_by_name,
                "assigned_to_name": assigned_to_name
            }
            score_reviews.append(score_review_dict)
        
        return score_reviews
    
    async def create(self, review_data: Dict[str, Any]) -> ScoreReview:
        """
        Create a new score review.
        
        Args:
            review_data: Dictionary containing the score review data
            
        Returns:
            The created score review
        """
        # Create a new score review
        new_review = ScoreReview(**review_data)
        
        # Add to session and commit
        self.db.add(new_review)
        await self.db.commit()
        await self.db.refresh(new_review)
        
        logger.info(f"Created score review with ID: {new_review.review_id}")
        return new_review
    
    async def update(self, review_id: str, review_data: Dict[str, Any]) -> Optional[ScoreReview]:
        """
        Update a score review.
        
        Args:
            review_id: The unique identifier of the score review
            review_data: Dictionary containing the updated data
            
        Returns:
            The updated score review if found, None otherwise
        """
        # Get the raw ScoreReview object first
        query = select(ScoreReview).filter(ScoreReview.review_id == review_id)
        result = await self.db.execute(query)
        existing_review = result.scalar_one_or_none()
        
        if not existing_review:
            return None
        
        # Update the score review
        update_stmt = (
            update(ScoreReview)
            .where(ScoreReview.review_id == review_id)
            .values(**review_data)
            .returning(ScoreReview)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_review = result.scalar_one_or_none()
        if updated_review:
            logger.info(f"Updated score review with ID: {review_id}")
        
        return updated_review
    
    async def delete(self, review_id: str) -> bool:
        """
        Delete a score review.
        
        Args:
            review_id: The unique identifier of the score review
            
        Returns:
            True if the score review was deleted, False otherwise
        """
        # Check if the score review exists
        query = select(ScoreReview).filter(ScoreReview.review_id == review_id)
        result = await self.db.execute(query)
        existing_review = result.scalar_one_or_none()
        
        if not existing_review:
            return False
        
        # Delete the score review
        delete_stmt = delete(ScoreReview).where(ScoreReview.review_id == review_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted score review with ID: {review_id}")
        return True 