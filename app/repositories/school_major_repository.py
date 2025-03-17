"""
School-Major repository module.

This module provides database operations for school-major relationships,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join
from sqlalchemy.sql import expression

from app.domain.models.school_major import SchoolMajor
from app.domain.models.school import School
from app.domain.models.major import Major
from app.services.id_service import generate_model_id

logger = logging.getLogger(__name__)

class SchoolMajorRepository:
    """Repository for managing SchoolMajor entities in the database."""
    
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
    ) -> tuple[List[Dict], int]:
        """
        Get all school-major relationships with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of school-major relationships with details and total count
        """
        # Join query to get school and major names
        query = (
            select(
                SchoolMajor,
                School.school_name,
                Major.major_name
            )
            .join(School, SchoolMajor.school_id == School.school_id)
            .join(Major, SchoolMajor.major_id == Major.major_id)
        )
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                if hasattr(SchoolMajor, field) and value is not None:
                    query = query.filter(getattr(SchoolMajor, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include school and major names
        school_majors = []
        for sm, school_name, major_name in result:
            sm_dict = {
                "school_major_id": sm.school_major_id,
                "school_id": sm.school_id,
                "major_id": sm.major_id,
                "start_year": sm.start_year,
                "additional_info": sm.additional_info,
                "created_at": sm.created_at,
                "updated_at": sm.updated_at,
                "school_name": school_name,
                "major_name": major_name,
                "is_active": sm.is_active
            }
            school_majors.append(sm_dict)
        
        return school_majors, total or 0
    
    async def get_by_id(self, school_major_id: str) -> Optional[Dict]:
        """
        Get a school-major relationship by its ID, including school and major names.
        
        Args:
            school_major_id: The unique identifier of the school-major relationship
            
        Returns:
            The school-major relationship with school and major names if found, None otherwise
        """
        query = (
            select(
                SchoolMajor,
                School.school_name,
                Major.major_name
            )
            .join(School, SchoolMajor.school_id == School.school_id)
            .join(Major, SchoolMajor.major_id == Major.major_id)
            .filter(SchoolMajor.school_major_id == school_major_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        sm, school_name, major_name = row
        return {
            "school_major_id": sm.school_major_id,
            "school_id": sm.school_id,
            "major_id": sm.major_id,
            "start_year": sm.start_year,
            "additional_info": sm.additional_info,
            "created_at": sm.created_at,
            "updated_at": sm.updated_at,
            "school_name": school_name,
            "major_name": major_name,
            "is_active": sm.is_active
        }
    
    async def get_by_school_and_major(self, school_id: str, major_id: str) -> Optional[SchoolMajor]:
        """
        Get a school-major relationship by school ID and major ID.
        
        Args:
            school_id: The ID of the school
            major_id: The ID of the major
            
        Returns:
            The school-major relationship if found, None otherwise
        """
        query = select(SchoolMajor).filter(
            SchoolMajor.school_id == school_id,
            SchoolMajor.major_id == major_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, school_major_data: Dict[str, Any]) -> SchoolMajor:
        """
        Create a new school-major relationship.
        
        Args:
            school_major_data: Dictionary containing the school-major relationship data
            
        Returns:
            The created school-major relationship
        """
        # Ensure school_major_id is set
        if 'school_major_id' not in school_major_data or not school_major_data['school_major_id']:
            school_major_data['school_major_id'] = generate_model_id("SchoolMajor")
            logger.info(f"Generated new ID for SchoolMajor: {school_major_data['school_major_id']}")
        
        # Create a new school-major relationship
        new_school_major = SchoolMajor(**school_major_data)
        
        # Add to session and commit
        self.db.add(new_school_major)
        await self.db.commit()
        await self.db.refresh(new_school_major)
        
        logger.info(f"Created school-major relationship with ID: {new_school_major.school_major_id}")
        return new_school_major
    
    async def update(self, school_major_id: str, school_major_data: Dict[str, Any]) -> Optional[SchoolMajor]:
        """
        Update a school-major relationship.
        
        Args:
            school_major_id: The unique identifier of the school-major relationship
            school_major_data: Dictionary containing the updated data
            
        Returns:
            The updated school-major relationship if found, None otherwise
        """
        # Get the raw SchoolMajor object first
        query = select(SchoolMajor).filter(SchoolMajor.school_major_id == school_major_id)
        result = await self.db.execute(query)
        existing_sm = result.scalar_one_or_none()
        
        if not existing_sm:
            return None
        
        # Update the school-major relationship
        update_stmt = (
            update(SchoolMajor)
            .where(SchoolMajor.school_major_id == school_major_id)
            .values(**school_major_data)
            .returning(SchoolMajor)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_school_major = result.scalar_one_or_none()
        if updated_school_major:
            logger.info(f"Updated school-major relationship with ID: {school_major_id}")
        
        return updated_school_major
    
    async def delete(self, school_major_id: str) -> bool:
        """
        Delete a school-major relationship.
        
        Args:
            school_major_id: The unique identifier of the school-major relationship
            
        Returns:
            True if the school-major relationship was deleted, False otherwise
        """
        # Check if the school-major relationship exists
        query = select(SchoolMajor).filter(SchoolMajor.school_major_id == school_major_id)
        result = await self.db.execute(query)
        existing_sm = result.scalar_one_or_none()
        
        if not existing_sm:
            return False
        
        # Delete the school-major relationship
        delete_stmt = delete(SchoolMajor).where(SchoolMajor.school_major_id == school_major_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted school-major relationship with ID: {school_major_id}")
        return True 