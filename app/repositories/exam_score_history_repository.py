"""
Exam Score History repository module.

This module provides database operations for exam score history entries,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join, and_, or_
from sqlalchemy.sql import expression

from app.domain.models.exam_score_history import ExamScoreHistory
from app.domain.models.exam_score import ExamScore
from app.domain.models.candidate_exam import CandidateExam
from app.domain.models.exam_subject import ExamSubject
from app.domain.models.candidate import Candidate
from app.domain.models.exam import Exam
from app.domain.models.subject import Subject
from app.domain.models.user import User
from app.domain.models.score_review import ScoreReview

logger = logging.getLogger(__name__)

class ExamScoreHistoryRepository:
    """Repository for managing ExamScoreHistory entities in the database."""
    
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
        Get all score history entries with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of score history entries with details and total count
        """
        # Base query with all necessary joins
        query = (
            select(
                ExamScoreHistory,
                Candidate.full_name,
                Candidate.candidate_id,
                Exam.exam_name,
                Subject.subject_name
            )
            .join(ExamScore, ExamScoreHistory.score_id == ExamScore.exam_score_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .outerjoin(User, ExamScoreHistory.changed_by == User.user_id)
        )
        
        # Apply search filter
        if filters and "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Candidate.full_name.ilike(search_term),
                    Candidate.candidate_id.ilike(search_term),
                    Exam.exam_name.ilike(search_term),
                    Subject.subject_name.ilike(search_term),
                    Subject.subject_code.ilike(search_term),
                    ExamScoreHistory.change_reason.ilike(search_term)
                )
            )
        
        # Apply score_id filter
        if filters and "score_id" in filters and filters["score_id"]:
            query = query.filter(ExamScoreHistory.score_id == filters["score_id"])
        
        # Apply changed_by filter
        if filters and "changed_by" in filters and filters["changed_by"]:
            query = query.filter(ExamScoreHistory.changed_by == filters["changed_by"])
        
        # Apply candidate_id filter
        if filters and "candidate_id" in filters and filters["candidate_id"]:
            query = query.filter(CandidateExam.candidate_id == filters["candidate_id"])
        
        # Apply exam_id filter
        if filters and "exam_id" in filters and filters["exam_id"]:
            query = query.filter(ExamSubject.exam_id == filters["exam_id"])
        
        # Apply subject_id filter
        if filters and "subject_id" in filters and filters["subject_id"]:
            query = query.filter(ExamSubject.subject_id == filters["subject_id"])
        
        # Apply date range filters
        if filters and "created_after" in filters and filters["created_after"]:
            query = query.filter(ExamScoreHistory.created_at >= filters["created_after"])
        
        if filters and "created_before" in filters and filters["created_before"]:
            query = query.filter(ExamScoreHistory.created_at <= filters["created_before"])
        
        # Apply additional filters if any
        if filters:
            for field, value in filters.items():
                if field not in ["search", "score_id", "changed_by", "candidate_id", 
                              "exam_id", "subject_id", "created_after", "created_before"] and value is not None:
                    if hasattr(ExamScoreHistory, field):
                        query = query.filter(getattr(ExamScoreHistory, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Add ordering by created_at descending (most recent first)
        query = query.order_by(ExamScoreHistory.created_at.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include related entity names
        history_entries = []
        for history, full_name, candidate_id, exam_name, subject_name in result:
            # Get changed_by name if available
            changed_by_name = None
            
            if history.changed_by:
                user_query = select(User.name).filter(User.user_id == history.changed_by)
                user_result = await self.db.execute(user_query)
                changed_by_name = user_result.scalar_one_or_none()
            
            history_dict = {
                "history_id": history.history_id,
                "score_id": history.score_id,
                "previous_score": history.previous_score,
                "new_score": history.new_score,
                "change_date": history.change_date,
                "change_reason": history.change_reason,
                "changed_by": history.changed_by,
                "created_at": history.created_at,
                "updated_at": history.updated_at,
                "candidate_name": full_name,
                "candidate_code": candidate_id,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "changed_by_name": changed_by_name
            }
            history_entries.append(history_dict)
        
        return history_entries, total or 0
    
    async def get_by_id(self, history_id: str) -> Optional[Dict]:
        """
        Get a score history entry by its ID, including related entity details.
        
        Args:
            history_id: The unique identifier of the score history entry
            
        Returns:
            The score history entry with related entity details if found, None otherwise
        """
        query = (
            select(
                ExamScoreHistory,
                Candidate.full_name,
                Candidate.candidate_id,
                Exam.exam_name,
                Subject.subject_name
            )
            .join(ExamScore, ExamScoreHistory.score_id == ExamScore.exam_score_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(ExamScoreHistory.history_id == history_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        history, full_name, candidate_id, exam_name, subject_name = row
        
        # Get changed_by name if available
        changed_by_name = None
        
        if history.changed_by:
            user_query = select(User.name).filter(User.user_id == history.changed_by)
            user_result = await self.db.execute(user_query)
            changed_by_name = user_result.scalar_one_or_none()
        
        return {
            "history_id": history.history_id,
            "score_id": history.score_id,
            "previous_score": history.previous_score,
            "new_score": history.new_score,
            "change_date": history.change_date,
            "change_reason": history.change_reason,
            "changed_by": history.changed_by,
            "created_at": history.created_at,
            "updated_at": history.updated_at,
            "candidate_name": full_name,
            "candidate_code": candidate_id,
            "exam_name": exam_name,
            "subject_name": subject_name,
            "changed_by_name": changed_by_name
        }
    
    async def get_by_score_id(self, score_id: str) -> List[Dict]:
        """
        Get all history entries for a specific exam score.
        
        Args:
            score_id: The ID of the exam score
            
        Returns:
            List of history entries for the specified exam score
        """
        query = (
            select(
                ExamScoreHistory,
                Candidate.full_name,
                Candidate.candidate_id,
                Exam.exam_name,
                Subject.subject_name
            )
            .join(ExamScore, ExamScoreHistory.score_id == ExamScore.exam_score_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(ExamScoreHistory.score_id == score_id)
            .order_by(ExamScoreHistory.created_at.desc())
        )
        
        result = await self.db.execute(query)
        
        history_entries = []
        for history, full_name, candidate_id, exam_name, subject_name in result:
            # Get changed_by name if available
            changed_by_name = None
            
            if history.changed_by:
                user_query = select(User.name).filter(User.user_id == history.changed_by)
                user_result = await self.db.execute(user_query)
                changed_by_name = user_result.scalar_one_or_none()
            
            history_dict = {
                "history_id": history.history_id,
                "score_id": history.score_id,
                "previous_score": history.previous_score,
                "new_score": history.new_score,
                "change_date": history.change_date,
                "change_reason": history.change_reason,
                "changed_by": history.changed_by,
                "created_at": history.created_at,
                "updated_at": history.updated_at,
                "candidate_name": full_name,
                "candidate_code": candidate_id,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "changed_by_name": changed_by_name
            }
            history_entries.append(history_dict)
        
        return history_entries
    
    async def get_by_review_id(self, review_id: str) -> List[Dict]:
        """
        Get all history entries related to a specific score review.
        
        Args:
            review_id: The ID of the score review
            
        Returns:
            List of history entries related to the specified score review
        """
        query = (
            select(
                ExamScoreHistory,
                Candidate.full_name,
                Candidate.candidate_id,
                Exam.exam_name,
                Subject.subject_name
            )
            .join(ExamScore, ExamScoreHistory.score_id == ExamScore.exam_score_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(ExamScoreHistory.review_id == review_id)
            .order_by(ExamScoreHistory.created_at.desc())
        )
        
        result = await self.db.execute(query)
        
        history_entries = []
        for history, full_name, candidate_id, exam_name, subject_name in result:
            # Get changed_by name if available
            changed_by_name = None
            
            if history.changed_by:
                user_query = select(User.name).filter(User.user_id == history.changed_by)
                user_result = await self.db.execute(user_query)
                changed_by_name = user_result.scalar_one_or_none()
            
            history_dict = {
                "history_id": history.history_id,
                "score_id": history.score_id,
                "previous_score": history.previous_score,
                "new_score": history.new_score,
                "change_date": history.change_date,
                "change_reason": history.change_reason,
                "changed_by": history.changed_by,
                "created_at": history.created_at,
                "updated_at": history.updated_at,
                "candidate_name": full_name,
                "candidate_code": candidate_id,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "changed_by_name": changed_by_name
            }
            history_entries.append(history_dict)
        
        return history_entries
    
    async def get_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all score history entries for a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of score history entries for the specified candidate
        """
        query = (
            select(
                ExamScoreHistory,
                Candidate.full_name,
                Candidate.candidate_id,
                Exam.exam_name,
                Subject.subject_name
            )
            .join(ExamScore, ExamScoreHistory.score_id == ExamScore.exam_score_id)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(CandidateExam.candidate_id == candidate_id)
            .order_by(ExamScoreHistory.created_at.desc())
        )
        
        result = await self.db.execute(query)
        
        history_entries = []
        for history, full_name, candidate_id, exam_name, subject_name in result:
            # Get changed_by name if available
            changed_by_name = None
            
            if history.changed_by:
                user_query = select(User.name).filter(User.user_id == history.changed_by)
                user_result = await self.db.execute(user_query)
                changed_by_name = user_result.scalar_one_or_none()
            
            history_dict = {
                "history_id": history.history_id,
                "score_id": history.score_id,
                "previous_score": history.previous_score,
                "new_score": history.new_score,
                "change_date": history.change_date,
                "change_reason": history.change_reason,
                "changed_by": history.changed_by,
                "created_at": history.created_at,
                "updated_at": history.updated_at,
                "candidate_name": full_name,
                "candidate_code": candidate_id,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "changed_by_name": changed_by_name
            }
            history_entries.append(history_dict)
        
        return history_entries
    
    async def create(self, history_data: Dict[str, Any]) -> ExamScoreHistory:
        """
        Create a new score history entry.
        
        Args:
            history_data: Dictionary containing the score history data
            
        Returns:
            The created score history entry
        """
        # Create a new score history entry
        new_history = ExamScoreHistory(**history_data)
        
        # Add to session and commit
        self.db.add(new_history)
        await self.db.commit()
        await self.db.refresh(new_history)
        
        logger.info(f"Created score history entry with ID: {new_history.history_id}")
        return new_history
    
    async def create_from_score_change(
        self, 
        score_id: str, 
        previous_score: Optional[float], 
        new_score: Optional[float], 
        changed_by: Optional[str], 
        change_type: str, 
        reason: Optional[str] = None, 
        review_id: Optional[str] = None, 
        metadata: Optional[Dict] = None
    ) -> ExamScoreHistory:
        """
        Create a history entry from a score change.
        
        Args:
            score_id: ID of the exam score that was changed
            previous_score: Previous score value before the change
            new_score: New score value after the change
            changed_by: ID of the user who made the change
            change_type: Type of change that occurred
            reason: Reason for the change
            review_id: ID of the score review if the change was due to a review
            metadata: Additional metadata for the history entry
            
        Returns:
            The created history entry
        """
        history_data = {
            "score_id": score_id,
            "previous_score": previous_score,
            "new_score": new_score,
            "changed_by": changed_by,
            "change_reason": reason,
            "change_date": datetime.now()
        }
        
        return await self.create(history_data) 