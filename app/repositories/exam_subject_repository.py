"""
Exam Subject repository module.

This module provides database operations for exam subjects,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join
from sqlalchemy.sql import expression

from app.domain.models.exam_subject import ExamSubject
from app.domain.models.exam import Exam
from app.domain.models.subject import Subject
from app.services.id_service import generate_model_id

logger = logging.getLogger(__name__)

class ExamSubjectRepository:
    """Repository for managing ExamSubject entities in the database."""
    
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
        Get all exam subjects with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of exam subjects with details and total count
        """
        # Join query to get exam and subject names
        query = (
            select(
                ExamSubject,
                Exam.exam_name,
                Subject.subject_name,
                Subject.subject_code
            )
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
        )
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                if hasattr(ExamSubject, field) and value is not None:
                    query = query.filter(getattr(ExamSubject, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include related entity names
        exam_subjects = []
        for exam_subject, exam_name, subject_name, subject_code in result:
            exam_subject_dict = {
                "exam_subject_id": exam_subject.exam_subject_id,
                "exam_id": exam_subject.exam_id,
                "subject_id": exam_subject.subject_id,
                "weight": exam_subject.weight,
                "passing_score": exam_subject.passing_score,
                "max_score": exam_subject.max_score,
                "is_required": exam_subject.is_required,
                "exam_date": exam_subject.exam_date,
                "duration_minutes": exam_subject.duration_minutes,
                "subject_metadata": exam_subject.subject_metadata,
                "created_at": exam_subject.created_at,
                "updated_at": exam_subject.updated_at,
                "exam_name": exam_name,
                "subject_name": subject_name,
                "subject_code": subject_code
            }
            exam_subjects.append(exam_subject_dict)
        
        return exam_subjects, total or 0
    
    async def get_by_id(self, exam_subject_id: str) -> Optional[Dict]:
        """
        Get an exam subject by its ID, including related entity names.
        
        Args:
            exam_subject_id: The unique identifier of the exam subject
            
        Returns:
            The exam subject with related entity names if found, None otherwise
        """
        query = (
            select(
                ExamSubject,
                Exam.exam_name,
                Subject.subject_name,
                Subject.subject_code
            )
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .filter(ExamSubject.exam_subject_id == exam_subject_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        exam_subject, exam_name, subject_name, subject_code = row
        return {
            "exam_subject_id": exam_subject.exam_subject_id,
            "exam_id": exam_subject.exam_id,
            "subject_id": exam_subject.subject_id,
            "weight": exam_subject.weight,
            "passing_score": exam_subject.passing_score,
            "max_score": exam_subject.max_score,
            "is_required": exam_subject.is_required,
            "exam_date": exam_subject.exam_date,
            "duration_minutes": exam_subject.duration_minutes,
            "subject_metadata": exam_subject.subject_metadata,
            "created_at": exam_subject.created_at,
            "updated_at": exam_subject.updated_at,
            "exam_name": exam_name,
            "subject_name": subject_name,
            "subject_code": subject_code
        }
    
    async def get_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all exam subjects for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of exam subjects for the specified exam
        """
        query = (
            select(
                ExamSubject,
                Subject.subject_name,
                Subject.subject_code
            )
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .filter(ExamSubject.exam_id == exam_id)
        )
        
        result = await self.db.execute(query)
        
        exam_subjects = []
        for exam_subject, subject_name, subject_code in result:
            exam_subject_dict = {
                "exam_subject_id": exam_subject.exam_subject_id,
                "exam_id": exam_subject.exam_id,
                "subject_id": exam_subject.subject_id,
                "weight": exam_subject.weight,
                "passing_score": exam_subject.passing_score,
                "max_score": exam_subject.max_score,
                "is_required": exam_subject.is_required,
                "exam_date": exam_subject.exam_date,
                "duration_minutes": exam_subject.duration_minutes,
                "subject_metadata": exam_subject.subject_metadata,
                "created_at": exam_subject.created_at,
                "updated_at": exam_subject.updated_at,
                "subject_name": subject_name,
                "subject_code": subject_code
            }
            exam_subjects.append(exam_subject_dict)
        
        return exam_subjects
    
    async def get_by_subject_id(self, subject_id: str) -> List[Dict]:
        """
        Get all exam subjects for a specific subject.
        
        Args:
            subject_id: The ID of the subject
            
        Returns:
            List of exam subjects for the specified subject
        """
        query = (
            select(
                ExamSubject,
                Exam.exam_name
            )
            .join(Exam, ExamSubject.exam_id == Exam.exam_id)
            .filter(ExamSubject.subject_id == subject_id)
        )
        
        result = await self.db.execute(query)
        
        exam_subjects = []
        for exam_subject, exam_name in result:
            exam_subject_dict = {
                "exam_subject_id": exam_subject.exam_subject_id,
                "exam_id": exam_subject.exam_id,
                "subject_id": exam_subject.subject_id,
                "weight": exam_subject.weight,
                "passing_score": exam_subject.passing_score,
                "max_score": exam_subject.max_score,
                "is_required": exam_subject.is_required,
                "exam_date": exam_subject.exam_date,
                "duration_minutes": exam_subject.duration_minutes,
                "subject_metadata": exam_subject.subject_metadata,
                "created_at": exam_subject.created_at,
                "updated_at": exam_subject.updated_at,
                "exam_name": exam_name
            }
            exam_subjects.append(exam_subject_dict)
        
        return exam_subjects
    
    async def get_by_exam_and_subject(self, exam_id: str, subject_id: str) -> Optional[ExamSubject]:
        """
        Get an exam subject by exam ID and subject ID.
        
        Args:
            exam_id: The ID of the exam
            subject_id: The ID of the subject
            
        Returns:
            The exam subject if found, None otherwise
        """
        query = select(ExamSubject).filter(
            ExamSubject.exam_id == exam_id,
            ExamSubject.subject_id == subject_id
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, exam_subject_data: Dict[str, Any]) -> ExamSubject:
        """
        Create a new exam subject.
        
        Args:
            exam_subject_data: Dictionary containing the exam subject data
            
        Returns:
            The created exam subject
        """
        # Ensure exam_subject_id is generated if not provided
        if 'exam_subject_id' not in exam_subject_data or not exam_subject_data['exam_subject_id']:
            exam_subject_data['exam_subject_id'] = generate_model_id("ExamSubject")
            logger.info(f"Generated new exam subject ID: {exam_subject_data['exam_subject_id']}")
        
        # Create a new exam subject
        new_exam_subject = ExamSubject(**exam_subject_data)
        
        # Add to session and commit
        self.db.add(new_exam_subject)
        await self.db.commit()
        await self.db.refresh(new_exam_subject)
        
        logger.info(f"Created exam subject with ID: {new_exam_subject.exam_subject_id}")
        return new_exam_subject
    
    async def update(self, exam_subject_id: str, exam_subject_data: Dict[str, Any]) -> Optional[ExamSubject]:
        """
        Update an exam subject.
        
        Args:
            exam_subject_id: The unique identifier of the exam subject
            exam_subject_data: Dictionary containing the updated data
            
        Returns:
            The updated exam subject if found, None otherwise
        """
        # Get the raw ExamSubject object first
        query = select(ExamSubject).filter(ExamSubject.exam_subject_id == exam_subject_id)
        result = await self.db.execute(query)
        existing_exam_subject = result.scalar_one_or_none()
        
        if not existing_exam_subject:
            return None
        
        # Update the exam subject
        update_stmt = (
            update(ExamSubject)
            .where(ExamSubject.exam_subject_id == exam_subject_id)
            .values(**exam_subject_data)
            .returning(ExamSubject)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_exam_subject = result.scalar_one_or_none()
        if updated_exam_subject:
            logger.info(f"Updated exam subject with ID: {exam_subject_id}")
        
        return updated_exam_subject
    
    async def delete(self, exam_subject_id: str) -> bool:
        """
        Delete an exam subject.
        
        Args:
            exam_subject_id: The unique identifier of the exam subject
            
        Returns:
            True if the exam subject was deleted, False otherwise
        """
        # Check if the exam subject exists
        query = select(ExamSubject).filter(ExamSubject.exam_subject_id == exam_subject_id)
        result = await self.db.execute(query)
        existing_exam_subject = result.scalar_one_or_none()
        
        if not existing_exam_subject:
            return False
        
        # Delete the exam subject
        delete_stmt = delete(ExamSubject).where(ExamSubject.exam_subject_id == exam_subject_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted exam subject with ID: {exam_subject_id}")
        return True 