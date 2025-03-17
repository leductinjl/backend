"""
Management Unit service module.

This module provides business logic for management units, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from app.repositories.management_unit_repository import ManagementUnitRepository
from app.domain.models.management_unit import ManagementUnit

logger = logging.getLogger(__name__)

class ManagementUnitService:
    """Service for handling management unit business logic."""
    
    def __init__(self, repository: ManagementUnitRepository):
        """
        Initialize the service with a repository.
        
        Args:
            repository: Repository for management unit data access
        """
        self.repository = repository
    
    async def get_all_units(
        self, 
        skip: int = 0, 
        limit: int = 100,
        unit_type: Optional[str] = None
    ) -> Tuple[List[ManagementUnit], int]:
        """
        Get all management units with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            unit_type: Optional filter by unit type
            
        Returns:
            Tuple containing the list of management units and total count
        """
        filters = {}
        if unit_type:
            filters["unit_type"] = unit_type
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_unit_by_id(self, unit_id: str) -> Optional[ManagementUnit]:
        """
        Get a management unit by its ID.
        
        Args:
            unit_id: The unique identifier of the management unit
            
        Returns:
            The management unit if found, None otherwise
        """
        return await self.repository.get_by_id(unit_id)
    
    async def create_unit(self, unit_data: Dict[str, Any]) -> ManagementUnit:
        """
        Create a new management unit.
        
        Args:
            unit_data: Dictionary containing the management unit data
            
        Returns:
            The created management unit
        """
        # Validate input data if needed
        
        # Create the unit
        return await self.repository.create(unit_data)
    
    async def update_unit(self, unit_id: str, unit_data: Dict[str, Any]) -> Optional[ManagementUnit]:
        """
        Update a management unit.
        
        Args:
            unit_id: The unique identifier of the management unit
            unit_data: Dictionary containing the updated data
            
        Returns:
            The updated management unit if found, None otherwise
        """
        # Validate input data if needed
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in unit_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            return await self.get_unit_by_id(unit_id)
        
        return await self.repository.update(unit_id, cleaned_data)
    
    async def delete_unit(self, unit_id: str) -> bool:
        """
        Delete a management unit.
        
        Args:
            unit_id: The unique identifier of the management unit
            
        Returns:
            True if the unit was deleted, False otherwise
        """
        return await self.repository.delete(unit_id) 