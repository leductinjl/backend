"""
Exam Location Mapping service module.

This module provides business logic for exam location mappings, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select

from app.repositories.exam_location_mapping_repository import ExamLocationMappingRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.exam_location_repository import ExamLocationRepository
from app.domain.models.exam_location_mapping import ExamLocationMapping

logger = logging.getLogger(__name__)

class ExamLocationMappingService:
    """Service for handling exam location mapping business logic."""
    
    def __init__(
        self, 
        repository: ExamLocationMappingRepository,
        exam_repository: Optional[ExamRepository] = None,
        exam_location_repository: Optional[ExamLocationRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for exam location mapping data access
            exam_repository: Repository for exam data access
            exam_location_repository: Repository for exam location data access
        """
        self.repository = repository
        self.exam_repository = exam_repository
        self.exam_location_repository = exam_location_repository
    
    async def get_all_mappings(
        self, 
        skip: int = 0, 
        limit: int = 100,
        exam_id: Optional[str] = None,
        location_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_primary: Optional[bool] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all exam location mappings with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            exam_id: Optional filter by exam ID
            location_id: Optional filter by location ID
            is_active: Optional filter by active status
            is_primary: Optional filter by primary status
            
        Returns:
            Tuple containing the list of exam location mappings and total count
        """
        filters = {}
        if exam_id:
            filters["exam_id"] = exam_id
        if location_id:
            filters["location_id"] = location_id
        if is_active is not None:
            filters["is_active"] = is_active
        if is_primary is not None:
            filters["is_primary"] = is_primary
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_mapping_by_id(self, mapping_id: str) -> Optional[Dict]:
        """
        Get an exam location mapping by its ID.
        
        Args:
            mapping_id: The unique identifier of the exam location mapping
            
        Returns:
            The exam location mapping if found, None otherwise
        """
        return await self.repository.get_by_id(mapping_id)
    
    async def get_mappings_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all exam location mappings for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of exam location mappings for the specified exam
        """
        return await self.repository.get_by_exam_id(exam_id)
    
    async def get_mappings_by_location_id(self, location_id: str) -> List[Dict]:
        """
        Get all exam location mappings for a specific location.
        
        Args:
            location_id: The ID of the exam location
            
        Returns:
            List of exam location mappings for the specified location
        """
        return await self.repository.get_by_location_id(location_id)
    
    async def create_mapping(self, mapping_data: Dict[str, Any]) -> Optional[ExamLocationMapping]:
        """
        Create a new exam location mapping after validating the exam and location IDs.
        
        Args:
            mapping_data: Dictionary containing the exam location mapping data
            
        Returns:
            The created exam location mapping if successful, None otherwise
        """
        # If metadata is provided, rename to mapping_metadata to match model
        if "metadata" in mapping_data:
            mapping_data["mapping_metadata"] = mapping_data.pop("metadata")
            
        # Validate that exam and location exist if repositories are provided
        if self.exam_repository and self.exam_location_repository:
            exam = await self.exam_repository.get_by_id(mapping_data["exam_id"])
            location = await self.exam_location_repository.get_by_id(mapping_data["location_id"])
            
            if not exam:
                logger.error(f"Exam with ID {mapping_data['exam_id']} not found")
                return None
                
            if not location:
                logger.error(f"Exam location with ID {mapping_data['location_id']} not found")
                return None
        
        # Check if a mapping with the same exam and location already exists
        existing_mapping = await self.repository.get_by_exam_and_location(
            mapping_data["exam_id"], 
            mapping_data["location_id"]
        )
        
        if existing_mapping:
            logger.error(f"Mapping for exam ID {mapping_data['exam_id']} and location ID {mapping_data['location_id']} already exists")
            return None
        
        # If this mapping is marked as primary, ensure no other primary mappings exist for this exam
        if mapping_data.get("is_primary", False):
            # Get all mappings for this exam
            existing_mappings = await self.repository.get_by_exam_id(mapping_data["exam_id"])
            
            # Check if any are marked as primary
            for existing in existing_mappings:
                if existing.get("is_primary", False):
                    logger.warning(f"Another primary mapping already exists for exam ID {mapping_data['exam_id']}. Setting all others to non-primary.")
                    # Update the existing primary mapping to non-primary
                    await self.repository.update(existing["mapping_id"], {"is_primary": False})
        
        # Create the exam location mapping
        return await self.repository.create(mapping_data)
    
    async def update_mapping(self, mapping_id: str, mapping_data: Dict[str, Any]) -> Optional[ExamLocationMapping]:
        """
        Update an exam location mapping.
        
        Args:
            mapping_id: The unique identifier of the exam location mapping
            mapping_data: Dictionary containing the updated data
            
        Returns:
            The updated exam location mapping if found, None otherwise
        """
        # If metadata is provided, rename to mapping_metadata to match model
        if "metadata" in mapping_data:
            mapping_data["mapping_metadata"] = mapping_data.pop("metadata")
            
        # Get existing mapping
        existing_mapping_dict = await self.repository.get_by_id(mapping_id)
        if not existing_mapping_dict:
            logger.error(f"Exam location mapping with ID {mapping_id} not found")
            return None
        
        # Check if this mapping is being set as primary
        if mapping_data.get("is_primary", False):
            # Get all mappings for this exam
            existing_mappings = await self.repository.get_by_exam_id(existing_mapping_dict["exam_id"])
            
            # Check if any are marked as primary (other than this one)
            for existing in existing_mappings:
                if existing["mapping_id"] != mapping_id and existing.get("is_primary", False):
                    logger.warning(f"Another primary mapping already exists for exam ID {existing_mapping_dict['exam_id']}. Setting all others to non-primary.")
                    # Update the existing primary mapping to non-primary
                    await self.repository.update(existing["mapping_id"], {"is_primary": False})
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in mapping_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            # Just return the existing record without database operation
            query = select(ExamLocationMapping).filter(ExamLocationMapping.mapping_id == mapping_id)
            result = await self.repository.db.execute(query)
            return result.scalar_one_or_none()
        
        return await self.repository.update(mapping_id, cleaned_data)
    
    async def delete_mapping(self, mapping_id: str) -> bool:
        """
        Delete an exam location mapping.
        
        Args:
            mapping_id: The unique identifier of the exam location mapping
            
        Returns:
            True if the exam location mapping was deleted, False otherwise
        """
        return await self.repository.delete(mapping_id) 