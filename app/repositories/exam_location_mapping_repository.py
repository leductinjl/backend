"""
Exam Location Mapping repository module.

This module provides database operations for exam location mappings,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.sql import expression

from app.domain.models.exam_location_mapping import ExamLocationMapping
from app.domain.models.exam_location import ExamLocation
from app.domain.models.exam import Exam

logger = logging.getLogger(__name__)

class ExamLocationMappingRepository:
    """Repository for managing ExamLocationMapping entities in the database."""
    
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
        Get all exam location mappings with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of exam location mappings with details and total count
        """
        # Join query to get exam and location names
        query = (
            select(
                ExamLocationMapping,
                Exam.exam_name,
                ExamLocation.location_name
            )
            .join(Exam, ExamLocationMapping.exam_id == Exam.exam_id)
            .join(ExamLocation, ExamLocationMapping.location_id == ExamLocation.location_id)
        )
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                if hasattr(ExamLocationMapping, field) and value is not None:
                    query = query.filter(getattr(ExamLocationMapping, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include exam and location names
        mappings = []
        for mapping, exam_name, location_name in result:
            mapping_dict = {
                "mapping_id": mapping.mapping_id,
                "exam_id": mapping.exam_id,
                "location_id": mapping.location_id,
                "is_primary": mapping.is_primary,
                "is_active": mapping.is_active,
                "mapping_metadata": mapping.mapping_metadata,
                "created_at": mapping.created_at,
                "updated_at": mapping.updated_at,
                "exam_name": exam_name,
                "location_name": location_name
            }
            mappings.append(mapping_dict)
        
        return mappings, total or 0
    
    async def get_by_id(self, mapping_id: str) -> Optional[Dict]:
        """
        Get an exam location mapping by its ID, including exam and location names.
        
        Args:
            mapping_id: The unique identifier of the exam location mapping
            
        Returns:
            The exam location mapping with exam and location names if found, None otherwise
        """
        query = (
            select(
                ExamLocationMapping,
                Exam.exam_name,
                ExamLocation.location_name
            )
            .join(Exam, ExamLocationMapping.exam_id == Exam.exam_id)
            .join(ExamLocation, ExamLocationMapping.location_id == ExamLocation.location_id)
            .filter(ExamLocationMapping.mapping_id == mapping_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        mapping, exam_name, location_name = row
        return {
            "mapping_id": mapping.mapping_id,
            "exam_id": mapping.exam_id,
            "location_id": mapping.location_id,
            "is_primary": mapping.is_primary,
            "is_active": mapping.is_active,
            "mapping_metadata": mapping.mapping_metadata,
            "created_at": mapping.created_at,
            "updated_at": mapping.updated_at,
            "exam_name": exam_name,
            "location_name": location_name
        }
    
    async def get_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all exam location mappings for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of exam location mappings for the specified exam
        """
        query = (
            select(
                ExamLocationMapping,
                ExamLocation.location_name
            )
            .join(ExamLocation, ExamLocationMapping.location_id == ExamLocation.location_id)
            .filter(ExamLocationMapping.exam_id == exam_id)
        )
        
        result = await self.db.execute(query)
        
        mappings = []
        for mapping, location_name in result:
            mapping_dict = {
                "mapping_id": mapping.mapping_id,
                "exam_id": mapping.exam_id,
                "location_id": mapping.location_id,
                "is_primary": mapping.is_primary,
                "is_active": mapping.is_active,
                "mapping_metadata": mapping.mapping_metadata,
                "created_at": mapping.created_at,
                "updated_at": mapping.updated_at,
                "location_name": location_name
            }
            mappings.append(mapping_dict)
        
        return mappings
    
    async def get_by_location_id(self, location_id: str) -> List[Dict]:
        """
        Get all exam location mappings for a specific location.
        
        Args:
            location_id: The ID of the exam location
            
        Returns:
            List of exam location mappings for the specified location
        """
        query = (
            select(
                ExamLocationMapping,
                Exam.exam_name
            )
            .join(Exam, ExamLocationMapping.exam_id == Exam.exam_id)
            .filter(ExamLocationMapping.location_id == location_id)
        )
        
        result = await self.db.execute(query)
        
        mappings = []
        for mapping, exam_name in result:
            mapping_dict = {
                "mapping_id": mapping.mapping_id,
                "exam_id": mapping.exam_id,
                "location_id": mapping.location_id,
                "is_primary": mapping.is_primary,
                "is_active": mapping.is_active,
                "mapping_metadata": mapping.mapping_metadata,
                "created_at": mapping.created_at,
                "updated_at": mapping.updated_at,
                "exam_name": exam_name
            }
            mappings.append(mapping_dict)
        
        return mappings
        
    async def get_by_exam_and_location(self, exam_id: str, location_id: str) -> Optional[Dict]:
        """
        Get a mapping by exam ID and location ID.
        
        Args:
            exam_id: The ID of the exam
            location_id: The ID of the exam location
            
        Returns:
            The exam location mapping if found, None otherwise
        """
        query = (
            select(ExamLocationMapping)
            .filter(
                and_(
                    ExamLocationMapping.exam_id == exam_id,
                    ExamLocationMapping.location_id == location_id
                )
            )
        )
        
        result = await self.db.execute(query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            return None
        
        return {
            "mapping_id": mapping.mapping_id,
            "exam_id": mapping.exam_id,
            "location_id": mapping.location_id,
            "is_primary": mapping.is_primary,
            "is_active": mapping.is_active,
            "mapping_metadata": mapping.mapping_metadata,
            "created_at": mapping.created_at,
            "updated_at": mapping.updated_at
        }
    
    async def create(self, mapping_data: Dict[str, Any]) -> ExamLocationMapping:
        """
        Create a new exam location mapping.
        
        Args:
            mapping_data: Dictionary containing the exam location mapping data
            
        Returns:
            The created exam location mapping
        """
        # Handle metadata to mapping_metadata conversion for backward compatibility
        if "metadata" in mapping_data:
            mapping_data["mapping_metadata"] = mapping_data.pop("metadata")
            
        # Create a new exam location mapping
        new_mapping = ExamLocationMapping(**mapping_data)
        
        # Add to session and commit
        self.db.add(new_mapping)
        await self.db.commit()
        await self.db.refresh(new_mapping)
        
        logger.info(f"Created exam location mapping with ID: {new_mapping.mapping_id}")
        return new_mapping
    
    async def update(self, mapping_id: str, mapping_data: Dict[str, Any]) -> Optional[ExamLocationMapping]:
        """
        Update an exam location mapping.
        
        Args:
            mapping_id: The unique identifier of the exam location mapping
            mapping_data: Dictionary containing the updated data
            
        Returns:
            The updated exam location mapping if found, None otherwise
        """
        # Handle metadata to mapping_metadata conversion for backward compatibility
        if "metadata" in mapping_data:
            mapping_data["mapping_metadata"] = mapping_data.pop("metadata")
            
        # Get the raw ExamLocationMapping object first
        query = select(ExamLocationMapping).filter(ExamLocationMapping.mapping_id == mapping_id)
        result = await self.db.execute(query)
        existing_mapping = result.scalar_one_or_none()
        
        if not existing_mapping:
            return None
        
        # Update the exam location mapping
        update_stmt = (
            update(ExamLocationMapping)
            .where(ExamLocationMapping.mapping_id == mapping_id)
            .values(**mapping_data)
            .returning(ExamLocationMapping)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_mapping = result.scalar_one_or_none()
        if updated_mapping:
            logger.info(f"Updated exam location mapping with ID: {mapping_id}")
        
        return updated_mapping
    
    async def delete(self, mapping_id: str) -> bool:
        """
        Delete an exam location mapping.
        
        Args:
            mapping_id: The unique identifier of the exam location mapping
            
        Returns:
            True if the exam location mapping was deleted, False otherwise
        """
        # Check if the exam location mapping exists
        query = select(ExamLocationMapping).filter(ExamLocationMapping.mapping_id == mapping_id)
        result = await self.db.execute(query)
        existing_mapping = result.scalar_one_or_none()
        
        if not existing_mapping:
            return False
        
        # Delete the exam location mapping
        delete_stmt = delete(ExamLocationMapping).where(ExamLocationMapping.mapping_id == mapping_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted exam location mapping with ID: {mapping_id}")
        return True 