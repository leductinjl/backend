"""
Exam repository module.

This module provides database operations for exams,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join
from sqlalchemy.sql import expression

from app.domain.models.exam import Exam
from app.domain.models.exam_type import ExamType
from app.domain.models.management_unit import ManagementUnit
from app.services.id_service import generate_model_id

logger = logging.getLogger(__name__)

class ExamRepository:
    """Repository for managing Exam entities in the database."""
    
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
        Get all exams with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of exams with details and total count
        """
        # Join query to get exam type and management unit names
        query = (
            select(
                Exam,
                ExamType.type_name.label("exam_type_name"),
                ManagementUnit.unit_name.label("management_unit_name")
            )
            .join(ExamType, Exam.type_id == ExamType.type_id)
            .join(ManagementUnit, Exam.organizing_unit_id == ManagementUnit.unit_id)
        )
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                if hasattr(Exam, field) and value is not None:
                    if field in ['start_date', 'end_date']:
                        # For date fields, use >= for start dates and <= for end dates
                        if 'start' in field:
                            query = query.filter(getattr(Exam, field) >= value)
                        elif 'end' in field:
                            query = query.filter(getattr(Exam, field) <= value)
                    else:
                        # For other fields, use equality
                        query = query.filter(getattr(Exam, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include related entities' names
        exams = []
        for exam, exam_type_name, management_unit_name in result:
            exam_dict = {
                "exam_id": exam.exam_id,
                "type_id": exam.type_id,
                "exam_name": exam.exam_name,
                "additional_info": exam.additional_info,
                "start_date": exam.start_date,
                "end_date": exam.end_date,
                "scope": exam.scope,
                "organizing_unit_id": exam.organizing_unit_id,
                "is_active": exam.is_active,  # Use actual value from database
                "exam_metadata": exam.exam_metadata,
                "created_at": exam.created_at,
                "updated_at": exam.updated_at,
                "exam_type_name": exam_type_name,
                "management_unit_name": management_unit_name
            }
            exams.append(exam_dict)
        
        return exams, total or 0
    
    async def get_by_id(self, exam_id: str) -> Optional[Dict]:
        """
        Get an exam by its ID, including related entity names.
        
        Args:
            exam_id: The unique identifier of the exam
            
        Returns:
            The exam with related entity names if found, None otherwise
        """
        query = (
            select(
                Exam,
                ExamType.type_name.label("exam_type_name"),
                ManagementUnit.unit_name.label("management_unit_name")
            )
            .join(ExamType, Exam.type_id == ExamType.type_id)
            .join(ManagementUnit, Exam.organizing_unit_id == ManagementUnit.unit_id)
            .filter(Exam.exam_id == exam_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        exam, exam_type_name, management_unit_name = row
        return {
            "exam_id": exam.exam_id,
            "type_id": exam.type_id,
            "exam_name": exam.exam_name,
            "additional_info": exam.additional_info,
            "start_date": exam.start_date,
            "end_date": exam.end_date,
            "scope": exam.scope,
            "organizing_unit_id": exam.organizing_unit_id,
            "is_active": exam.is_active,  # Use actual value from database
            "exam_metadata": exam.exam_metadata,
            "created_at": exam.created_at,
            "updated_at": exam.updated_at,
            "exam_type_name": exam_type_name,
            "management_unit_name": management_unit_name
        }
    
    async def create(self, exam_data: Dict[str, Any]) -> Exam:
        """
        Create a new exam.
        
        Args:
            exam_data: Dictionary containing the exam data
            
        Returns:
            The created exam
        """
        # Ensure exam_id is set
        if 'exam_id' not in exam_data or not exam_data['exam_id']:
            exam_data['exam_id'] = generate_model_id("Exam")
            logger.info(f"Generated new exam ID: {exam_data['exam_id']}")
            
        # Create a new exam
        new_exam = Exam(**exam_data)
        
        # Add to session and commit
        self.db.add(new_exam)
        await self.db.commit()
        await self.db.refresh(new_exam)
        
        logger.info(f"Created exam with ID: {new_exam.exam_id}")
        return new_exam
    
    async def update(self, exam_id: str, exam_data: Dict[str, Any]) -> Optional[Exam]:
        """
        Update an exam.
        
        Args:
            exam_id: The unique identifier of the exam
            exam_data: Dictionary containing the updated data
            
        Returns:
            The updated exam if found, None otherwise
        """
        # Get the raw Exam object first
        query = select(Exam).filter(Exam.exam_id == exam_id)
        result = await self.db.execute(query)
        existing_exam = result.scalar_one_or_none()
        
        if not existing_exam:
            return None
        
        # Update the exam
        update_stmt = (
            update(Exam)
            .where(Exam.exam_id == exam_id)
            .values(**exam_data)
            .returning(Exam)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_exam = result.scalar_one_or_none()
        if updated_exam:
            logger.info(f"Updated exam with ID: {exam_id}")
        
        return updated_exam
    
    async def delete(self, exam_id: str) -> bool:
        """
        Delete an exam.
        
        Args:
            exam_id: The unique identifier of the exam
            
        Returns:
            True if the exam was deleted, False otherwise
        """
        # Check if the exam exists
        query = select(Exam).filter(Exam.exam_id == exam_id)
        result = await self.db.execute(query)
        existing_exam = result.scalar_one_or_none()
        
        if not existing_exam:
            return False
        
        # Delete the exam
        delete_stmt = delete(Exam).where(Exam.exam_id == exam_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted exam with ID: {exam_id}")
        return True 