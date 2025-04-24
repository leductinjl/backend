"""
School repository module.

This module provides database operations for schools,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.sql import expression

from app.domain.models.school import School
from app.services.id_service import generate_model_id

logger = logging.getLogger(__name__)

class SchoolRepository:
    """Repository for managing School entities in the database."""
    
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
    ) -> tuple[List[School], int]:
        """
        Get all schools with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of schools and total count
        """
        # Base query
        query = select(School)
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                if hasattr(School, field) and value is not None:
                    query = query.filter(getattr(School, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        schools = result.scalars().all()
        
        return schools, total or 0
    
    async def get_by_id(self, school_id: str) -> Optional[School]:
        """
        Get a school by its ID.
        
        Args:
            school_id: The unique identifier of the school
            
        Returns:
            The school if found, None otherwise
        """
        query = select(School).filter(School.school_id == school_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, school_data: Dict[str, Any]) -> School:
        """
        Create a new school.
        
        Args:
            school_data: Dictionary containing the school data
            
        Returns:
            The created school
        """
        # Ensure school_id is set
        if 'school_id' not in school_data or not school_data['school_id']:
            school_data['school_id'] = generate_model_id("School")
            logger.info(f"Generated new ID for School: {school_data['school_id']}")
        
        # Create a new school
        new_school = School(**school_data)
        
        # Add to session and commit
        self.db.add(new_school)
        await self.db.commit()
        await self.db.refresh(new_school)
        
        logger.info(f"Created school with ID: {new_school.school_id}")
        return new_school
    
    async def update(self, school_id: str, school_data: Dict[str, Any]) -> Optional[School]:
        """
        Update a school.
        
        Args:
            school_id: The unique identifier of the school
            school_data: Dictionary containing the updated data
            
        Returns:
            The updated school if found, None otherwise
        """
        # Check if the school exists
        school = await self.get_by_id(school_id)
        if not school:
            return None
        
        # Update the school
        update_stmt = (
            update(School)
            .where(School.school_id == school_id)
            .values(**school_data)
            .returning(School)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_school = result.scalar_one_or_none()
        if updated_school:
            logger.info(f"Updated school with ID: {school_id}")
        
        return updated_school
    
    async def delete(self, school_id: str) -> bool:
        """
        Delete a school.
        
        Args:
            school_id: The unique identifier of the school
            
        Returns:
            True if the school was deleted, False otherwise
        """
        # Check if the school exists
        school = await self.get_by_id(school_id)
        if not school:
            return False
        
        # Delete the school
        delete_stmt = delete(School).where(School.school_id == school_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted school with ID: {school_id}")
        return True 

    async def count(self) -> int:
        query = select(func.count()).select_from(School)
        result = await self.db.execute(query)
        return result.scalar_one() 