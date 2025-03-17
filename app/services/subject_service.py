"""
Subject service module.

This module provides business logic for subjects (academic courses), bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from app.repositories.subject_repository import SubjectRepository
from app.domain.models.subject import Subject

logger = logging.getLogger(__name__)

class SubjectService:
    """Service for handling subject business logic."""
    
    def __init__(self, repository: SubjectRepository):
        """
        Initialize the service with a repository.
        
        Args:
            repository: Repository for subject data access
        """
        self.repository = repository
    
    async def get_all_subjects(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Subject], int]:
        """
        Get all subjects with pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple containing the list of subjects and total count
        """
        return await self.repository.get_all(skip=skip, limit=limit, filters={})
    
    async def get_subject_by_id(self, subject_id: str) -> Optional[Subject]:
        """
        Get a subject by its ID.
        
        Args:
            subject_id: The unique identifier of the subject
            
        Returns:
            The subject if found, None otherwise
        """
        return await self.repository.get_by_id(subject_id)
    
    async def create_subject(self, subject_data: Dict[str, Any]) -> Subject:
        """
        Create a new subject.
        
        Args:
            subject_data: Dictionary containing the subject data
            
        Returns:
            The created subject
        """
        # Validate input data if needed
        
        # Create the subject
        return await self.repository.create(subject_data)
    
    async def update_subject(self, subject_id: str, subject_data: Dict[str, Any]) -> Optional[Subject]:
        """
        Update a subject.
        
        Args:
            subject_id: The unique identifier of the subject
            subject_data: Dictionary containing the updated data
            
        Returns:
            The updated subject if found, None otherwise
        """
        # Validate input data if needed
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in subject_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            return await self.get_subject_by_id(subject_id)
        
        return await self.repository.update(subject_id, cleaned_data)
    
    async def delete_subject(self, subject_id: str) -> bool:
        """
        Delete a subject.
        
        Args:
            subject_id: The unique identifier of the subject
            
        Returns:
            True if the subject was deleted, False otherwise
        """
        return await self.repository.delete(subject_id) 