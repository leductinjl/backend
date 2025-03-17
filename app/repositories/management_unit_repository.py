"""
Management Unit repository module.

This module provides database operations for management units,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.sql import expression

from app.domain.models.management_unit import ManagementUnit

logger = logging.getLogger(__name__)

class ManagementUnitRepository:
    """Repository for managing ManagementUnit entities in the database."""
    
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
    ) -> tuple[List[ManagementUnit], int]:
        """
        Get all management units with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of management units and total count
        """
        # Base query
        query = select(ManagementUnit)
        
        # Apply filters if any
        if filters:
            for field, value in filters.items():
                if hasattr(ManagementUnit, field) and value is not None:
                    query = query.filter(getattr(ManagementUnit, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        units = result.scalars().all()
        
        return units, total or 0
    
    async def get_by_id(self, unit_id: str) -> Optional[ManagementUnit]:
        """
        Get a management unit by its ID.
        
        Args:
            unit_id: The unique identifier of the management unit
            
        Returns:
            The management unit if found, None otherwise
        """
        query = select(ManagementUnit).filter(ManagementUnit.unit_id == unit_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, unit_data: Dict[str, Any]) -> ManagementUnit:
        """
        Create a new management unit.
        
        Args:
            unit_data: Dictionary containing the management unit data
            
        Returns:
            The created management unit
        """
        # Create a new management unit
        new_unit = ManagementUnit(**unit_data)
        
        # Add to session and commit
        self.db.add(new_unit)
        await self.db.commit()
        await self.db.refresh(new_unit)
        
        logger.info(f"Created management unit with ID: {new_unit.unit_id}")
        return new_unit
    
    async def update(self, unit_id: str, unit_data: Dict[str, Any]) -> Optional[ManagementUnit]:
        """
        Update a management unit.
        
        Args:
            unit_id: The unique identifier of the management unit
            unit_data: Dictionary containing the updated data
            
        Returns:
            The updated management unit if found, None otherwise
        """
        # Check if the unit exists
        unit = await self.get_by_id(unit_id)
        if not unit:
            return None
        
        # Update the unit
        update_stmt = (
            update(ManagementUnit)
            .where(ManagementUnit.unit_id == unit_id)
            .values(**unit_data)
            .returning(ManagementUnit)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_unit = result.scalar_one_or_none()
        if updated_unit:
            logger.info(f"Updated management unit with ID: {unit_id}")
        
        return updated_unit
    
    async def delete(self, unit_id: str) -> bool:
        """
        Delete a management unit.
        
        Args:
            unit_id: The unique identifier of the management unit
            
        Returns:
            True if the unit was deleted, False otherwise
        """
        # Check if the unit exists
        unit = await self.get_by_id(unit_id)
        if not unit:
            return False
        
        # Delete the unit
        delete_stmt = delete(ManagementUnit).where(ManagementUnit.unit_id == unit_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted management unit with ID: {unit_id}")
        return True 