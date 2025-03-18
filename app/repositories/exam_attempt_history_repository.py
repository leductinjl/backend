"""
Exam Attempt History repository module.

This module provides database operations for exam attempt history entries,
including CRUD operations and queries to track candidates' exam attempts.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.orm import joinedload

from app.domain.models.exam_attempt_history import ExamAttemptHistory
from app.domain.models.candidate import Candidate
from app.domain.models.exam import Exam
from app.domain.models.exam_type import ExamType
from app.domain.models.user import User
from app.domain.models.exam_score import ExamScore
from app.domain.models.candidate_exam import CandidateExam
from app.domain.models.exam_subject import ExamSubject
from app.domain.models.subject import Subject

logger = logging.getLogger(__name__)

class ExamAttemptHistoryRepository:
    """Repository for managing ExamAttemptHistory entities in the database."""
    
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
        Get all exam attempt history entries with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of attempt history entries with details and total count
        """
        # Base query with all necessary joins
        query = (
            select(
                ExamAttemptHistory,
                Candidate.full_name,
                Exam.exam_name,
                ExamType.type_name.label("exam_type")
            )
            .join(CandidateExam, ExamAttemptHistory.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
            .outerjoin(ExamType, Exam.type_id == ExamType.type_id)
            .outerjoin(User, ExamAttemptHistory.attendance_verified_by == User.user_id)
        )
        
        # Apply search filter
        if filters and "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Candidate.full_name.ilike(search_term),
                    Exam.exam_name.ilike(search_term),
                    ExamAttemptHistory.notes.ilike(search_term)
                )
            )
        
        # Apply candidate_id filter
        if filters and "candidate_id" in filters and filters["candidate_id"]:
            query = query.filter(CandidateExam.candidate_id == filters["candidate_id"])
        
        # Apply exam_id filter
        if filters and "exam_id" in filters and filters["exam_id"]:
            query = query.filter(CandidateExam.exam_id == filters["exam_id"])
        
        # Apply attempt_number filter
        if filters and "attempt_number" in filters and filters["attempt_number"]:
            query = query.filter(ExamAttemptHistory.attempt_number == filters["attempt_number"])
        
        # Apply status filter
        if filters and "status" in filters and filters["status"]:
            query = query.filter(ExamAttemptHistory.status == filters["status"])
        
        # Apply result filter
        if filters and "result" in filters and filters["result"]:
            query = query.filter(ExamAttemptHistory.result == filters["result"])
        
        # Apply attempt_date range filters
        if filters and "attempt_date_from" in filters and filters["attempt_date_from"]:
            query = query.filter(ExamAttemptHistory.attempt_date >= filters["attempt_date_from"])
        
        if filters and "attempt_date_to" in filters and filters["attempt_date_to"]:
            query = query.filter(ExamAttemptHistory.attempt_date <= filters["attempt_date_to"])
        
        # Apply attendance_verified_by filter
        if filters and "attendance_verified_by" in filters and filters["attendance_verified_by"]:
            query = query.filter(ExamAttemptHistory.attendance_verified_by == filters["attendance_verified_by"])
        
        # Apply min_score and max_score filters
        if filters and "min_score" in filters and filters["min_score"] is not None:
            query = query.filter(ExamAttemptHistory.total_score >= filters["min_score"])
        
        if filters and "max_score" in filters and filters["max_score"] is not None:
            query = query.filter(ExamAttemptHistory.total_score <= filters["max_score"])
        
        # Apply sorting
        sort_field = filters.get("sort_field", "attempt_date") if filters else "attempt_date"
        sort_dir = filters.get("sort_dir", "desc") if filters else "desc"
        
        if hasattr(ExamAttemptHistory, sort_field):
            sort_attr = getattr(ExamAttemptHistory, sort_field)
            if sort_dir.lower() == "asc":
                query = query.order_by(asc(sort_attr))
            else:
                query = query.order_by(desc(sort_attr))
        else:
            # Default sort by attempt_date desc
            query = query.order_by(desc(ExamAttemptHistory.attempt_date))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include related entity details
        attempts = []
        for attempt, candidate_name, exam_name, exam_type in result:
            # Get attendance_verified_by name if available
            verified_by_name = None
            
            if hasattr(attempt, 'attendance_verified_by') and attempt.attendance_verified_by:
                user_query = select(User.name).filter(User.user_id == attempt.attendance_verified_by)
                user_result = await self.db.execute(user_query)
                verified_by_name = user_result.scalar_one_or_none()
            
            # Get subject scores if available
            subject_scores = await self._get_subject_scores(
                attempt.candidate_exam_id, 
                attempt.attempt_number
            )
            
            # Get candidate_id and exam_id from candidate_exam
            candidate_exam_query = (
                select(CandidateExam.candidate_id, CandidateExam.exam_id)
                .filter(CandidateExam.candidate_exam_id == attempt.candidate_exam_id)
            )
            
            candidate_exam_result = await self.db.execute(candidate_exam_query)
            candidate_exam_row = candidate_exam_result.first()
            
            candidate_id = None
            exam_id = None
            if candidate_exam_row:
                candidate_id, exam_id = candidate_exam_row
            
            # Prepare base response dict with attributes we know exist
            attempt_dict = {
                "attempt_history_id": attempt.attempt_history_id,
                "candidate_exam_id": attempt.candidate_exam_id,
                "candidate_id": candidate_id,
                "exam_id": exam_id,
                "attempt_number": attempt.attempt_number,
                "attempt_date": attempt.attempt_date,
                "result": attempt.result,
                "notes": attempt.notes,
                "created_at": attempt.created_at,
                "updated_at": attempt.updated_at,
                "candidate_name": candidate_name,
                "exam_name": exam_name,
                "exam_type": exam_type,
                "attendance_verified_by_name": verified_by_name,
                "subject_scores": subject_scores
            }
            
            # Add optional attributes if they exist
            optional_attributes = [
                "status", "check_in_time", "start_time", "end_time", "total_score", 
                "attendance_verified_by", "disqualification_reason", "cancellation_reason", 
                "metadata"
            ]
            
            for attr in optional_attributes:
                if hasattr(attempt, attr):
                    attempt_dict[attr] = getattr(attempt, attr)
            
            attempts.append(attempt_dict)
        
        return attempts, total
    
    async def get_by_id(self, attempt_history_id: str) -> Optional[Dict]:
        """
        Get an attempt history entry by its ID, including related entity details.
        
        Args:
            attempt_history_id: The unique identifier of the attempt history entry
            
        Returns:
            The attempt history entry with related entity details if found, None otherwise
        """
        query = (
            select(
                ExamAttemptHistory,
                Candidate.full_name,
                Exam.exam_name,
                ExamType.type_name.label("exam_type")
            )
            .join(CandidateExam, ExamAttemptHistory.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
            .outerjoin(ExamType, Exam.type_id == ExamType.type_id)
            .filter(ExamAttemptHistory.attempt_history_id == attempt_history_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        attempt, candidate_name, exam_name, exam_type = row
        
        # Get attendance_verified_by name if available
        verified_by_name = None
        
        if hasattr(attempt, 'attendance_verified_by') and attempt.attendance_verified_by:
            user_query = select(User.name).filter(User.user_id == attempt.attendance_verified_by)
            user_result = await self.db.execute(user_query)
            verified_by_name = user_result.scalar_one_or_none()
        
        # Get subject scores if available
        subject_scores = await self._get_subject_scores(
            attempt.candidate_exam_id, 
            attempt.attempt_number
        )
        
        # Get candidate_id and exam_id from candidate_exam
        candidate_exam_query = (
            select(CandidateExam.candidate_id, CandidateExam.exam_id)
            .filter(CandidateExam.candidate_exam_id == attempt.candidate_exam_id)
        )
        
        candidate_exam_result = await self.db.execute(candidate_exam_query)
        candidate_exam_row = candidate_exam_result.first()
        
        candidate_id = None
        exam_id = None
        if candidate_exam_row:
            candidate_id, exam_id = candidate_exam_row
        
        # Prepare base response dict with attributes we know exist
        response_dict = {
            "attempt_history_id": attempt.attempt_history_id,
            "candidate_exam_id": attempt.candidate_exam_id,
            "candidate_id": candidate_id,
            "exam_id": exam_id,
            "attempt_number": attempt.attempt_number,
            "attempt_date": attempt.attempt_date,
            "result": attempt.result,
            "notes": attempt.notes,
            "created_at": attempt.created_at,
            "updated_at": attempt.updated_at,
            "candidate_name": candidate_name,
            "exam_name": exam_name,
            "exam_type": exam_type,
            "attendance_verified_by_name": verified_by_name,
            "subject_scores": subject_scores
        }
        
        # Add optional attributes if they exist
        optional_attributes = [
            "status", "check_in_time", "start_time", "end_time", "total_score", 
            "attendance_verified_by", "disqualification_reason", "cancellation_reason", 
            "metadata"
        ]
        
        for attr in optional_attributes:
            if hasattr(attempt, attr):
                response_dict[attr] = getattr(attempt, attr)
        
        return response_dict
    
    async def get_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all attempt history entries for a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of attempt history entries for the specified candidate
        """
        filters = {"candidate_id": candidate_id}
        attempts, _ = await self.get_all(filters=filters)
        return attempts
    
    async def get_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all attempt history entries for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of attempt history entries for the specified exam
        """
        filters = {"exam_id": exam_id}
        attempts, _ = await self.get_all(filters=filters)
        return attempts
    
    async def get_by_candidate_and_exam(
        self, 
        candidate_id: str, 
        exam_id: str, 
        attempt_number: Optional[int] = None
    ) -> List[Dict]:
        """
        Get attempt history entries for a specific candidate and exam.
        
        Args:
            candidate_id: The ID of the candidate
            exam_id: The ID of the exam
            attempt_number: Optional specific attempt number to retrieve
            
        Returns:
            List of attempt history entries for the specified candidate and exam
        """
        filters = {
            "candidate_id": candidate_id,
            "exam_id": exam_id
        }
        
        if attempt_number:
            filters["attempt_number"] = attempt_number
        
        attempts, _ = await self.get_all(filters=filters)
        return attempts
    
    async def get_latest_attempt(self, candidate_id: str, exam_id: str) -> Optional[Dict]:
        """
        Get the latest attempt history entry for a specific candidate and exam.
        
        Args:
            candidate_id: The ID of the candidate
            exam_id: The ID of the exam
            
        Returns:
            The latest attempt history entry if found, None otherwise
        """
        query = (
            select(
                ExamAttemptHistory,
                Candidate.full_name,
                Exam.exam_name,
                ExamType.type_name.label("exam_type")
            )
            .join(CandidateExam, ExamAttemptHistory.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
            .outerjoin(ExamType, Exam.type_id == ExamType.type_id)
            .filter(
                CandidateExam.candidate_id == candidate_id,
                CandidateExam.exam_id == exam_id
            )
            .order_by(desc(ExamAttemptHistory.attempt_number))
            .limit(1)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        attempt, candidate_name, exam_name, exam_type = row
        
        # Get attendance_verified_by name if available
        verified_by_name = None
        
        if hasattr(attempt, 'attendance_verified_by') and attempt.attendance_verified_by:
            user_query = select(User.name).filter(User.user_id == attempt.attendance_verified_by)
            user_result = await self.db.execute(user_query)
            verified_by_name = user_result.scalar_one_or_none()
        
        # Get subject scores if available
        subject_scores = await self._get_subject_scores(
            attempt.candidate_exam_id, 
            attempt.attempt_number
        )
        
        # Get candidate_id and exam_id from candidate_exam
        candidate_exam_query = (
            select(CandidateExam.candidate_id, CandidateExam.exam_id)
            .filter(CandidateExam.candidate_exam_id == attempt.candidate_exam_id)
        )
        
        candidate_exam_result = await self.db.execute(candidate_exam_query)
        candidate_exam_row = candidate_exam_result.first()
        
        candidate_id = None
        exam_id = None
        if candidate_exam_row:
            candidate_id, exam_id = candidate_exam_row
        
        # Prepare base response dict with attributes we know exist
        response_dict = {
            "attempt_history_id": attempt.attempt_history_id,
            "candidate_exam_id": attempt.candidate_exam_id,
            "candidate_id": candidate_id,
            "exam_id": exam_id,
            "attempt_number": attempt.attempt_number,
            "attempt_date": attempt.attempt_date,
            "result": attempt.result,
            "notes": attempt.notes,
            "created_at": attempt.created_at,
            "updated_at": attempt.updated_at,
            "candidate_name": candidate_name,
            "exam_name": exam_name,
            "exam_type": exam_type,
            "attendance_verified_by_name": verified_by_name,
            "subject_scores": subject_scores
        }
        
        # Add optional attributes if they exist
        optional_attributes = [
            "status", "check_in_time", "start_time", "end_time", "total_score", 
            "attendance_verified_by", "disqualification_reason", "cancellation_reason", 
            "metadata"
        ]
        
        for attr in optional_attributes:
            if hasattr(attempt, attr):
                response_dict[attr] = getattr(attempt, attr)
        
        return response_dict
    
    async def get_next_attempt_number(self, candidate_id: str, exam_id: str) -> int:
        """
        Get the next attempt number for a specific candidate and exam.
        
        Args:
            candidate_id: The ID of the candidate
            exam_id: The ID of the exam
            
        Returns:
            The next attempt number (1 if no previous attempts)
        """
        # First, find the candidate_exam_id
        candidate_exam_query = (
            select(CandidateExam.candidate_exam_id)
            .filter(
                CandidateExam.candidate_id == candidate_id,
                CandidateExam.exam_id == exam_id
            )
        )
        
        candidate_exam_result = await self.db.execute(candidate_exam_query)
        candidate_exam_id = candidate_exam_result.scalar_one_or_none()
        
        if not candidate_exam_id:
            return 1
        
        # Then get the max attempt number
        query = (
            select(func.max(ExamAttemptHistory.attempt_number))
            .filter(
                ExamAttemptHistory.candidate_exam_id == candidate_exam_id
            )
        )
        
        result = await self.db.execute(query)
        max_attempt = result.scalar_one_or_none()
        
        return (max_attempt or 0) + 1
    
    async def get_next_attempt_number_by_candidate_exam_id(self, candidate_exam_id: str) -> int:
        """
        Get the next attempt number for a specific candidate exam relationship.
        
        Args:
            candidate_exam_id: The ID of the candidate exam relationship
            
        Returns:
            The next attempt number (1 if no previous attempts)
        """
        query = (
            select(func.max(ExamAttemptHistory.attempt_number))
            .filter(
                ExamAttemptHistory.candidate_exam_id == candidate_exam_id
            )
        )
        
        result = await self.db.execute(query)
        max_attempt = result.scalar_one_or_none()
        
        return (max_attempt or 0) + 1
    
    async def create(self, attempt_data: Dict[str, Any]) -> ExamAttemptHistory:
        """
        Create a new attempt history entry.
        
        Args:
            attempt_data: Dictionary containing the attempt history data
            
        Returns:
            The created attempt history entry
        """
        # Create a new attempt history entry
        new_attempt = ExamAttemptHistory(**attempt_data)
        
        # Add to session and commit
        self.db.add(new_attempt)
        await self.db.commit()
        await self.db.refresh(new_attempt)
        
        logger.info(f"Created attempt history entry with ID: {new_attempt.attempt_history_id}")
        return new_attempt
    
    async def update(self, attempt_history_id: str, attempt_data: Dict[str, Any]) -> Optional[ExamAttemptHistory]:
        """
        Update an existing attempt history entry.
        
        Args:
            attempt_history_id: The unique identifier of the attempt history entry
            attempt_data: Dictionary containing the updated attempt history data
            
        Returns:
            The updated attempt history entry if found, None otherwise
        """
        # Add updated_at timestamp
        attempt_data["updated_at"] = datetime.utcnow()
        
        # Update the attempt history entry
        query = (
            update(ExamAttemptHistory)
            .where(ExamAttemptHistory.attempt_history_id == attempt_history_id)
            .values(**attempt_data)
            .returning(ExamAttemptHistory)
        )
        
        result = await self.db.execute(query)
        updated_attempt = result.scalar_one_or_none()
        
        if not updated_attempt:
            logger.warning(f"Attempt history entry with ID {attempt_history_id} not found for update")
            return None
        
        await self.db.commit()
        logger.info(f"Updated attempt history entry with ID: {attempt_history_id}")
        return updated_attempt
    
    async def delete(self, attempt_history_id: str) -> bool:
        """
        Delete an attempt history entry.
        
        Args:
            attempt_history_id: The unique identifier of the attempt history entry
            
        Returns:
            True if the attempt history entry was deleted, False otherwise
        """
        # Delete the attempt history entry
        query = (
            delete(ExamAttemptHistory)
            .where(ExamAttemptHistory.attempt_history_id == attempt_history_id)
            .returning(ExamAttemptHistory.attempt_history_id)
        )
        
        result = await self.db.execute(query)
        deleted_id = result.scalar_one_or_none()
        
        if not deleted_id:
            logger.warning(f"Attempt history entry with ID {attempt_history_id} not found for deletion")
            return False
        
        await self.db.commit()
        logger.info(f"Deleted attempt history entry with ID: {attempt_history_id}")
        return True
    
    async def _get_subject_scores(
        self, 
        candidate_exam_id: str, 
        attempt_number: int
    ) -> List[Dict[str, Any]]:
        """
        Get the subject scores for a specific attempt.
        
        Args:
            candidate_exam_id: The ID of the candidate exam relationship
            attempt_number: The attempt number
            
        Returns:
            List of subject scores with details
        """
        # First, get the exam_id from candidate_exam
        exam_id_query = (
            select(CandidateExam.exam_id)
            .filter(CandidateExam.candidate_exam_id == candidate_exam_id)
        )
        
        exam_id_result = await self.db.execute(exam_id_query)
        exam_id = exam_id_result.scalar_one_or_none()
        
        if not exam_id:
            return []
        
        # Get the exam_subject_ids for the exam
        exam_subject_query = (
            select(ExamSubject.exam_subject_id, Subject.subject_name, Subject.subject_code)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .filter(ExamSubject.exam_id == exam_id)
        )
        
        exam_subject_result = await self.db.execute(exam_subject_query)
        exam_subjects = exam_subject_result.fetchall()
        
        # Get the scores for each exam_subject for this specific attempt
        subject_scores = []
        
        for exam_subject_id, subject_name, subject_code in exam_subjects:
            score_query = (
                select(ExamScore.score_value, ExamScore.status)
                .filter(
                    ExamScore.candidate_exam_id == candidate_exam_id,
                    ExamScore.exam_subject_id == exam_subject_id,
                    ExamScore.attempt_number == attempt_number
                )
            )
            
            score_result = await self.db.execute(score_query)
            score_row = score_result.first()
            
            if score_row:
                score_value, status = score_row
                subject_scores.append({
                    "subject_name": subject_name,
                    "subject_code": subject_code,
                    "score": score_value,
                    "status": status
                })
        
        return subject_scores
    
    async def get_attempts_by_candidate_exam_id(self, candidate_exam_id: str) -> List[Dict]:
        """
        Get all attempt history entries for a specific candidate exam relationship.
        
        Args:
            candidate_exam_id: The ID of the candidate exam relationship
            
        Returns:
            List of attempt history entries for the specified candidate exam
        """
        filters = {"candidate_exam_id": candidate_exam_id}
        attempts, _ = await self.get_all(filters=filters)
        return attempts 