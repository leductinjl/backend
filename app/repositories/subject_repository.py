"""
Subject repository module.

This module provides database operations for subjects (academic courses),
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.sql import expression

from app.domain.models.subject import Subject

logger = logging.getLogger(__name__)

class SubjectRepository:
    """Repository for managing Subject entities in the database."""
    
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
    ) -> tuple[List[Subject], int]:
        """
        Get all subjects with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of subjects and total count
        """
        # Base query
        query = select(Subject)
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                if hasattr(Subject, field) and value is not None:
                    query = query.filter(getattr(Subject, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        subjects = result.scalars().all()
        
        return subjects, total or 0
    
    async def get_by_id(self, subject_id: str) -> Optional[Subject]:
        """
        Get a subject by its ID.
        
        Args:
            subject_id: The unique identifier of the subject
            
        Returns:
            The subject if found, None otherwise
        """
        query = select(Subject).filter(Subject.subject_id == subject_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, subject_data: Dict[str, Any]) -> Subject:
        """
        Create a new subject.
        
        Args:
            subject_data: Dictionary containing the subject data
            
        Returns:
            The created subject
        """
        # Create a new subject
        new_subject = Subject(**subject_data)
        
        # Add to session and commit
        self.db.add(new_subject)
        await self.db.commit()
        await self.db.refresh(new_subject)
        
        logger.info(f"Created subject with ID: {new_subject.subject_id}")
        return new_subject
    
    async def update(self, subject_id: str, subject_data: Dict[str, Any]) -> Optional[Subject]:
        """
        Update a subject.
        
        Args:
            subject_id: The unique identifier of the subject
            subject_data: Dictionary containing the updated data
            
        Returns:
            The updated subject if found, None otherwise
        """
        # Check if the subject exists
        subject = await self.get_by_id(subject_id)
        if not subject:
            return None
        
        # Update the subject
        update_stmt = (
            update(Subject)
            .where(Subject.subject_id == subject_id)
            .values(**subject_data)
            .returning(Subject)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_subject = result.scalar_one_or_none()
        if updated_subject:
            logger.info(f"Updated subject with ID: {subject_id}")
        
        return updated_subject
    
    async def delete(self, subject_id: str) -> bool:
        """
        Delete a subject.
        
        Args:
            subject_id: The unique identifier of the subject
            
        Returns:
            True if the subject was deleted, False otherwise
        """
        # Check if the subject exists
        subject = await self.get_by_id(subject_id)
        if not subject:
            return False
        
        # Delete the subject
        delete_stmt = delete(Subject).where(Subject.subject_id == subject_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted subject with ID: {subject_id}")
        return True 