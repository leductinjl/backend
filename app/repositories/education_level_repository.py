"""
Education Level repository module.

This module provides database access methods for the EducationLevel model,
including CRUD operations and queries for retrieving education levels with filtering.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from app.domain.models.education_level import EducationLevel
import logging

class EducationLevelRepository:
    """Repository for database operations on education levels."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        
    async def get_all(self, skip: int = 0, limit: int = 100, code: str = None, name: str = None):
        """
        Retrieve a list of education levels with optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            code: Filter by code (partial match)
            name: Filter by name (partial match)
            
        Returns:
            Tuple of (list of education levels, total count)
        """
        try:
            # Build query with filters
            filters = []
            if code:
                filters.append(EducationLevel.code.ilike(f"%{code}%"))
            if name:
                filters.append(EducationLevel.name.ilike(f"%{name}%"))
                
            # Base query
            query = select(EducationLevel).order_by(EducationLevel.display_order)
            
            # Apply filters if any
            if filters:
                for f in filters:
                    query = query.where(f)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            education_levels = result.scalars().all()
            
            return education_levels, total
            
        except Exception as e:
            self.logger.error(f"Error getting education levels: {str(e)}")
            raise
            
    async def get_by_id(self, education_level_id: str):
        """
        Get an education level by ID.
        
        Args:
            education_level_id: ID of the education level to retrieve
            
        Returns:
            EducationLevel object or None if not found
        """
        try:
            query = select(EducationLevel).where(EducationLevel.education_level_id == education_level_id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            self.logger.error(f"Error getting education level with ID {education_level_id}: {str(e)}")
            raise
            
    async def get_by_code(self, code: str):
        """
        Get an education level by its code.
        
        Args:
            code: Unique code of the education level
            
        Returns:
            EducationLevel object or None if not found
        """
        try:
            query = select(EducationLevel).where(EducationLevel.code == code)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            self.logger.error(f"Error getting education level with code {code}: {str(e)}")
            raise
            
    async def create(self, education_level_data: dict):
        """
        Create a new education level.
        
        Args:
            education_level_data: Dictionary with education level data
            
        Returns:
            Created EducationLevel object
        """
        try:
            education_level = EducationLevel(**education_level_data)
            self.db.add(education_level)
            await self.db.flush()
            await self.db.refresh(education_level)
            return education_level
        except Exception as e:
            self.logger.error(f"Error creating education level: {str(e)}")
            raise
            
    async def update(self, education_level_id: str, education_level_data: dict):
        """
        Update an education level by ID.
        
        Args:
            education_level_id: ID of the education level to update
            education_level_data: Dictionary with updated data
            
        Returns:
            Updated EducationLevel object or None if not found
        """
        try:
            # Get the education level
            education_level = await self.get_by_id(education_level_id)
            if not education_level:
                return None
                
            # Update the education level
            stmt = (
                update(EducationLevel)
                .where(EducationLevel.education_level_id == education_level_id)
                .values(**education_level_data)
            )
            await self.db.execute(stmt)
            
            # Refresh and return the education level
            await self.db.refresh(education_level)
            return education_level
        except Exception as e:
            self.logger.error(f"Error updating education level with ID {education_level_id}: {str(e)}")
            raise
            
    async def delete(self, education_level_id: str):
        """
        Delete an education level by ID.
        
        Args:
            education_level_id: ID of the education level to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            stmt = delete(EducationLevel).where(EducationLevel.education_level_id == education_level_id)
            result = await self.db.execute(stmt)
            return result.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error deleting education level with ID {education_level_id}: {str(e)}")
            raise 