"""
Major repository module.

This module provides database operations for majors (fields of study),
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.sql import expression

from app.domain.models.major import Major
from app.services.id_service import generate_model_id

logger = logging.getLogger(__name__)

class MajorRepository:
    """Repository for managing Major entities in the database."""
    
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
    ) -> tuple[List[Major], int]:
        """
        Get all majors with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of majors and total count
        """
        # Base query
        query = select(Major)
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                if hasattr(Major, field) and value is not None:
                    query = query.filter(getattr(Major, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        majors = result.scalars().all()
        
        return majors, total or 0
    
    async def get_by_id(self, major_id: str) -> Optional[Major]:
        """
        Get a major by its ID.
        
        Args:
            major_id: The unique identifier of the major
            
        Returns:
            The major if found, None otherwise
        """
        query = select(Major).filter(Major.major_id == major_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, major_data: Dict[str, Any]) -> Major:
        """
        Create a new major.
        
        Args:
            major_data: Dictionary containing the major data
            
        Returns:
            The created major
        """
        # Ensure major_id is set
        if 'major_id' not in major_data or not major_data['major_id']:
            major_data['major_id'] = generate_model_id("Major")
            logger.info(f"Generated new ID for Major: {major_data['major_id']}")
        
        # Create a new major
        new_major = Major(**major_data)
        
        # Add to session and commit
        self.db.add(new_major)
        await self.db.commit()
        await self.db.refresh(new_major)
        
        logger.info(f"Created major with ID: {new_major.major_id}")
        return new_major
    
    async def update(self, major_id: str, major_data: Dict[str, Any]) -> Optional[Major]:
        """
        Update a major.
        
        Args:
            major_id: The unique identifier of the major
            major_data: Dictionary containing the updated data
            
        Returns:
            The updated major if found, None otherwise
        """
        # Check if the major exists
        major = await self.get_by_id(major_id)
        if not major:
            return None
        
        # Update the major
        update_stmt = (
            update(Major)
            .where(Major.major_id == major_id)
            .values(**major_data)
            .returning(Major)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_major = result.scalar_one_or_none()
        if updated_major:
            logger.info(f"Updated major with ID: {major_id}")
        
        return updated_major
    
    async def delete(self, major_id: str) -> bool:
        """
        Delete a major.
        
        Args:
            major_id: The unique identifier of the major
            
        Returns:
            True if the major was deleted, False otherwise
        """
        # Check if the major exists
        major = await self.get_by_id(major_id)
        if not major:
            return False
        
        # Delete the major
        delete_stmt = delete(Major).where(Major.major_id == major_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted major with ID: {major_id}")
        return True 