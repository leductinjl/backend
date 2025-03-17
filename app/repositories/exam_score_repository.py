"""
Exam Score repository module.

This module provides database operations for exam scores,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join, and_, or_
from sqlalchemy.sql import expression

from app.domain.models.exam_score import ExamScore
from app.domain.models.exam_subject import ExamSubject
from app.domain.models.candidate import Candidate
from app.domain.models.candidate_exam import CandidateExam
from app.domain.models.exam import Exam
from app.domain.models.subject import Subject
from app.services.id_service import generate_model_id

logger = logging.getLogger(__name__)

class ExamScoreRepository:
    """Repository for managing ExamScore entities in the database."""
    
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
        Get all exam scores with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of exam scores with details and total count
        """
        # Join query to get candidate, exam, and subject names through exam_subject
        query = (
            select(
                ExamScore,
                Candidate.candidate_id,
                Candidate.full_name.label("candidate_name"),
                Exam.exam_id,
                Exam.exam_name,
                Subject.subject_id,
                Subject.subject_name,
                Subject.subject_code,
                ExamSubject.max_score,
                ExamSubject.passing_score
            )
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
        )
        
        # Apply filters if any
        if filters:
            filter_conditions = []
            
            for field, value in filters.items():
                if field == "search" and value:
                    # Search in candidate name, exam name, or subject name
                    search_term = f"%{value}%"
                    filter_conditions.append(
                        or_(
                            Candidate.full_name.ilike(search_term),
                            Exam.exam_name.ilike(search_term),
                            Subject.subject_name.ilike(search_term)
                        )
                    )
                elif field == "candidate_id" and value:
                    filter_conditions.append(Candidate.candidate_id == value)
                elif field == "exam_id" and value:
                    filter_conditions.append(Exam.exam_id == value)
                elif field == "subject_id" and value:
                    filter_conditions.append(Subject.subject_id == value)
                elif field == "min_score" and value is not None:
                    filter_conditions.append(ExamScore.score >= value)
                elif field == "max_score" and value is not None:
                    filter_conditions.append(ExamScore.score <= value)
                elif field == "score_date" and value:
                    filter_conditions.append(func.date(ExamScore.graded_at) == value)
                elif hasattr(ExamScore, field) and value is not None:
                    if isinstance(value, list):
                        filter_conditions.append(getattr(ExamScore, field).in_(value))
                    else:
                        filter_conditions.append(getattr(ExamScore, field) == value)
            
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include related entity names
        scores = []
        for score, candidate_id, candidate_name, exam_id, exam_name, subject_id, subject_name, subject_code, max_score, passing_score in result:
            score_dict = {
                "exam_score_id": score.exam_score_id,
                "exam_subject_id": score.exam_subject_id,
                "score": score.score,
                "status": score.status,
                "graded_by": score.graded_by,
                "graded_at": score.graded_at,
                "notes": score.notes,
                "score_metadata": score.score_metadata,
                "created_at": score.created_at,
                "updated_at": score.updated_at,
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "exam_id": exam_id,
                "exam_name": exam_name,
                "subject_id": subject_id,
                "subject_name": subject_name,
                "subject_code": subject_code,
                "max_score": max_score,
                "passing_score": passing_score
            }
            scores.append(score_dict)
        
        return scores, total or 0
    
    async def get_by_id(self, exam_score_id: str) -> Optional[Dict]:
        """
        Get an exam score by its ID, including related entity names.
        
        Args:
            exam_score_id: The unique identifier of the exam score
            
        Returns:
            The exam score with related entity names if found, None otherwise
        """
        query = (
            select(
                ExamScore,
                Candidate.candidate_id,
                Candidate.full_name.label("candidate_name"),
                Exam.exam_id,
                Exam.exam_name,
                Subject.subject_id,
                Subject.subject_name,
                Subject.subject_code,
                ExamSubject.max_score,
                ExamSubject.passing_score
            )
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(ExamScore.exam_score_id == exam_score_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        score, candidate_id, candidate_name, exam_id, exam_name, subject_id, subject_name, subject_code, max_score, passing_score = row
        return {
            "exam_score_id": score.exam_score_id,
            "exam_subject_id": score.exam_subject_id,
            "score": score.score,
            "status": score.status,
            "graded_by": score.graded_by,
            "graded_at": score.graded_at,
            "notes": score.notes,
            "score_metadata": score.score_metadata,
            "created_at": score.created_at,
            "updated_at": score.updated_at,
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "exam_id": exam_id,
            "exam_name": exam_name,
            "subject_id": subject_id,
            "subject_name": subject_name,
            "subject_code": subject_code,
            "max_score": max_score,
            "passing_score": passing_score
        }
    
    async def get_by_exam_subject_id(self, exam_subject_id: str) -> List[Dict]:
        """
        Get all scores for a specific exam subject.
        
        Args:
            exam_subject_id: The ID of the exam subject
            
        Returns:
            List of scores for the specified exam subject
        """
        query = (
            select(
                ExamScore,
                Candidate.candidate_id,
                Candidate.full_name.label("candidate_name"),
                Exam.exam_id,
                Exam.exam_name,
                Subject.subject_id,
                Subject.subject_name,
                Subject.subject_code
            )
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(ExamScore.exam_subject_id == exam_subject_id)
        )
        
        result = await self.db.execute(query)
        
        scores = []
        for score, candidate_id, candidate_name, exam_id, exam_name, subject_id, subject_name, subject_code in result:
            score_dict = {
                "exam_score_id": score.exam_score_id,
                "exam_subject_id": score.exam_subject_id,
                "score": score.score,
                "status": score.status,
                "graded_by": score.graded_by,
                "graded_at": score.graded_at,
                "notes": score.notes,
                "score_metadata": score.score_metadata,
                "created_at": score.created_at,
                "updated_at": score.updated_at,
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "exam_id": exam_id,
                "exam_name": exam_name,
                "subject_id": subject_id,
                "subject_name": subject_name,
                "subject_code": subject_code
            }
            scores.append(score_dict)
        
        return scores
    
    async def get_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all scores for a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of scores for the specified candidate
        """
        query = (
            select(
                ExamScore,
                Exam.exam_id,
                Exam.exam_name,
                Subject.subject_id,
                Subject.subject_name,
                Subject.subject_code
            )
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(Candidate.candidate_id == candidate_id)
        )
        
        result = await self.db.execute(query)
        
        scores = []
        for score, exam_id, exam_name, subject_id, subject_name, subject_code in result:
            score_dict = {
                "exam_score_id": score.exam_score_id,
                "exam_subject_id": score.exam_subject_id,
                "score": score.score,
                "status": score.status,
                "graded_by": score.graded_by,
                "graded_at": score.graded_at,
                "notes": score.notes,
                "score_metadata": score.score_metadata,
                "created_at": score.created_at,
                "updated_at": score.updated_at,
                "exam_id": exam_id,
                "exam_name": exam_name,
                "subject_id": subject_id,
                "subject_name": subject_name,
                "subject_code": subject_code
            }
            scores.append(score_dict)
        
        return scores
    
    async def get_by_exam_subject_candidate(self, exam_subject_id: str, candidate_id: str) -> Optional[ExamScore]:
        """
        Get an exam score by exam subject ID and candidate ID.
        
        Args:
            exam_subject_id: The ID of the exam subject
            candidate_id: The ID of the candidate
            
        Returns:
            The exam score if found, None otherwise
        """
        query = (
            select(ExamScore)
            .join(ExamSubject, ExamScore.exam_subject_id == ExamSubject.exam_subject_id)
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(CandidateExam, Exam.exam_id == CandidateExam.exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(
                ExamScore.exam_subject_id == exam_subject_id,
                Candidate.candidate_id == candidate_id
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, score_data: Dict[str, Any]) -> ExamScore:
        """
        Create a new exam score.
        
        Args:
            score_data: Dictionary containing the exam score data
            
        Returns:
            The created exam score
        """
        # Ensure exam_score_id is generated if not provided
        if 'exam_score_id' not in score_data or not score_data['exam_score_id']:
            score_data['exam_score_id'] = generate_model_id("ExamScore")
            logger.info(f"Generated new exam score ID: {score_data['exam_score_id']}")
            
        # Rename metadata to score_metadata if needed
        if 'metadata' in score_data:
            score_data['score_metadata'] = score_data.pop('metadata')
            
        # Create a new exam score
        new_score = ExamScore(**score_data)
        
        # Add to session and commit
        self.db.add(new_score)
        await self.db.commit()
        await self.db.refresh(new_score)
        
        logger.info(f"Created exam score with ID: {new_score.exam_score_id}")
        return new_score
    
    async def update(self, exam_score_id: str, score_data: Dict[str, Any]) -> Optional[ExamScore]:
        """
        Update an exam score.
        
        Args:
            exam_score_id: The unique identifier of the exam score
            score_data: Dictionary containing the updated data
            
        Returns:
            The updated exam score if found, None otherwise
        """
        # Rename metadata to score_metadata if needed
        if 'metadata' in score_data:
            score_data['score_metadata'] = score_data.pop('metadata')
            
        # Get the raw ExamScore object first
        query = select(ExamScore).filter(ExamScore.exam_score_id == exam_score_id)
        result = await self.db.execute(query)
        existing_score = result.scalar_one_or_none()
        
        if not existing_score:
            return None
        
        # Update the exam score
        update_stmt = (
            update(ExamScore)
            .where(ExamScore.exam_score_id == exam_score_id)
            .values(**score_data)
            .returning(ExamScore)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_score = result.scalar_one_or_none()
        if updated_score:
            logger.info(f"Updated exam score with ID: {exam_score_id}")
        
        return updated_score
    
    async def delete(self, exam_score_id: str) -> bool:
        """
        Delete an exam score.
        
        Args:
            exam_score_id: The unique identifier of the exam score
            
        Returns:
            True if the exam score was deleted, False otherwise
        """
        # Check if the exam score exists
        query = select(ExamScore).filter(ExamScore.exam_score_id == exam_score_id)
        result = await self.db.execute(query)
        existing_score = result.scalar_one_or_none()
        
        if not existing_score:
            return False
        
        # Delete the exam score
        delete_stmt = delete(ExamScore).where(ExamScore.exam_score_id == exam_score_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted exam score with ID: {exam_score_id}")
        return True 