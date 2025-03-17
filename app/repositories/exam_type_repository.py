"""
Exam Type repository module.

This module provides database operations for exam types,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.sql import expression

from app.domain.models.exam_type import ExamType
from app.services.id_service import generate_model_id

logger = logging.getLogger(__name__)

class ExamTypeRepository:
    """Repository for managing ExamType entities in the database."""
    
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
    ) -> tuple[List[ExamType], int]:
        """
        Get all exam types with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of exam types and total count
        """
        # Base query
        query = select(ExamType)
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                if hasattr(ExamType, field) and value is not None:
                    query = query.filter(getattr(ExamType, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        exam_types = result.scalars().all()
        
        return exam_types, total or 0
    
    async def get_by_id(self, type_id: str) -> Optional[ExamType]:
        """
        Get an exam type by its ID.
        
        Args:
            type_id: The unique identifier of the exam type
            
        Returns:
            The exam type if found, None otherwise
        """
        query = select(ExamType).filter(ExamType.type_id == type_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, exam_type_data: Dict[str, Any]) -> ExamType:
        """
        Create a new exam type.
        
        Args:
            exam_type_data: Dictionary containing the exam type data
            
        Returns:
            The created exam type
        """
        # Ensure type_id is set
        if 'type_id' not in exam_type_data:
            exam_type_data['type_id'] = generate_model_id("ExamType")
            
        # Create a new exam type
        new_exam_type = ExamType(**exam_type_data)
        
        # Add to session and commit
        self.db.add(new_exam_type)
        await self.db.commit()
        await self.db.refresh(new_exam_type)
        
        logger.info(f"Created exam type with ID: {new_exam_type.type_id}")
        return new_exam_type
    
    async def update(self, type_id: str, exam_type_data: Dict[str, Any]) -> Optional[ExamType]:
        """
        Update an exam type.
        
        Args:
            type_id: The unique identifier of the exam type
            exam_type_data: Dictionary containing the updated data
            
        Returns:
            The updated exam type if found, None otherwise
        """
        # Check if the exam type exists
        exam_type = await self.get_by_id(type_id)
        if not exam_type:
            return None
        
        # Update the exam type
        update_stmt = (
            update(ExamType)
            .where(ExamType.type_id == type_id)
            .values(**exam_type_data)
            .returning(ExamType)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_exam_type = result.scalar_one_or_none()
        if updated_exam_type:
            logger.info(f"Updated exam type with ID: {type_id}")
        
        return updated_exam_type
    
    async def delete(self, type_id: str) -> bool:
        """
        Delete an exam type.
        
        Args:
            type_id: The unique identifier of the exam type
            
        Returns:
            True if the exam type was deleted, False otherwise
        """
        # Check if the exam type exists
        exam_type = await self.get_by_id(type_id)
        if not exam_type:
            return False
        
        # Delete the exam type
        delete_stmt = delete(ExamType).where(ExamType.type_id == type_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted exam type with ID: {type_id}")
        return True 