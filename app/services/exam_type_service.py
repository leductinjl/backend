"""
Exam Type service module.

This module provides business logic for exam types, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from app.repositories.exam_type_repository import ExamTypeRepository
from app.domain.models.exam_type import ExamType

logger = logging.getLogger(__name__)

class ExamTypeService:
    """Service for handling exam type business logic."""
    
    def __init__(self, repository: ExamTypeRepository):
        """
        Initialize the service with a repository.
        
        Args:
            repository: Repository for exam type data access
        """
        self.repository = repository
    
    async def get_all_exam_types(
        self, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> Tuple[List[ExamType], int]:
        """
        Get all exam types with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            is_active: Optional filter by active status
            
        Returns:
            Tuple containing the list of exam types and total count
        """
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_exam_type_by_id(self, type_id: str) -> Optional[ExamType]:
        """
        Get an exam type by its ID.
        
        Args:
            type_id: The unique identifier of the exam type
            
        Returns:
            The exam type if found, None otherwise
        """
        return await self.repository.get_by_id(type_id)
    
    async def create_exam_type(self, exam_type_data: Dict[str, Any]) -> ExamType:
        """
        Create a new exam type.
        
        Args:
            exam_type_data: Dictionary containing the exam type data
            
        Returns:
            The created exam type
        """
        # Validate input data if needed
        
        # Create the exam type
        return await self.repository.create(exam_type_data)
    
    async def update_exam_type(self, type_id: str, exam_type_data: Dict[str, Any]) -> Optional[ExamType]:
        """
        Update an exam type.
        
        Args:
            type_id: The unique identifier of the exam type
            exam_type_data: Dictionary containing the updated data
            
        Returns:
            The updated exam type if found, None otherwise
        """
        # Validate input data if needed
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in exam_type_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            return await self.get_exam_type_by_id(type_id)
        
        return await self.repository.update(type_id, cleaned_data)
    
    async def delete_exam_type(self, type_id: str) -> bool:
        """
        Delete an exam type.
        
        Args:
            type_id: The unique identifier of the exam type
            
        Returns:
            True if the exam type was deleted, False otherwise
        """
        return await self.repository.delete(type_id) 