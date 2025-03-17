"""
Exam Subject service module.

This module provides business logic for exam subjects, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select

from app.repositories.exam_subject_repository import ExamSubjectRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.subject_repository import SubjectRepository
from app.domain.models.exam_subject import ExamSubject

logger = logging.getLogger(__name__)

class ExamSubjectService:
    """Service for handling exam subject business logic."""
    
    def __init__(
        self, 
        repository: ExamSubjectRepository,
        exam_repository: Optional[ExamRepository] = None,
        subject_repository: Optional[SubjectRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for exam subject data access
            exam_repository: Repository for exam data access
            subject_repository: Repository for subject data access
        """
        self.repository = repository
        self.exam_repository = exam_repository
        self.subject_repository = subject_repository
    
    async def get_all_exam_subjects(
        self, 
        skip: int = 0, 
        limit: int = 100,
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        is_required: Optional[bool] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all exam subjects with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            exam_id: Optional filter by exam ID
            subject_id: Optional filter by subject ID
            is_required: Optional filter by required status
            
        Returns:
            Tuple containing the list of exam subjects and total count
        """
        filters = {}
        if exam_id:
            filters["exam_id"] = exam_id
        if subject_id:
            filters["subject_id"] = subject_id
        if is_required is not None:
            filters["is_required"] = is_required
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_exam_subject_by_id(self, exam_subject_id: str) -> Optional[Dict]:
        """
        Get an exam subject by its ID.
        
        Args:
            exam_subject_id: The unique identifier of the exam subject
            
        Returns:
            The exam subject if found, None otherwise
        """
        return await self.repository.get_by_id(exam_subject_id)
    
    async def get_exam_subjects_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all exam subjects for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of exam subjects for the specified exam
        """
        return await self.repository.get_by_exam_id(exam_id)
    
    async def get_exam_subjects_by_subject_id(self, subject_id: str) -> List[Dict]:
        """
        Get all exam subjects for a specific subject.
        
        Args:
            subject_id: The ID of the subject
            
        Returns:
            List of exam subjects for the specified subject
        """
        return await self.repository.get_by_subject_id(subject_id)
    
    async def create_exam_subject(self, exam_subject_data: Dict[str, Any]) -> Optional[ExamSubject]:
        """
        Create a new exam subject after validating the exam and subject IDs.
        
        Args:
            exam_subject_data: Dictionary containing the exam subject data
            
        Returns:
            The created exam subject if successful, None otherwise
        """
        # Validate that exam and subject exist if repositories are provided
        if self.exam_repository and self.subject_repository:
            exam = await self.exam_repository.get_by_id(exam_subject_data["exam_id"])
            subject = await self.subject_repository.get_by_id(exam_subject_data["subject_id"])
            
            if not exam:
                logger.error(f"Exam with ID {exam_subject_data['exam_id']} not found")
                return None
                
            if not subject:
                logger.error(f"Subject with ID {exam_subject_data['subject_id']} not found")
                return None
        
        # Check if an exam subject with the same exam and subject already exists
        existing_exam_subject = await self.repository.get_by_exam_and_subject(
            exam_subject_data["exam_id"], 
            exam_subject_data["subject_id"]
        )
        
        if existing_exam_subject:
            logger.error(f"Exam subject for exam ID {exam_subject_data['exam_id']} and subject ID {exam_subject_data['subject_id']} already exists")
            return None

        # Handle metadata to subject_metadata field name mapping
        if "metadata" in exam_subject_data:
            exam_subject_data["subject_metadata"] = exam_subject_data.pop("metadata")
        
        # Create the exam subject
        return await self.repository.create(exam_subject_data)
    
    async def update_exam_subject(self, exam_subject_id: str, exam_subject_data: Dict[str, Any]) -> Optional[ExamSubject]:
        """
        Update an exam subject.
        
        Args:
            exam_subject_id: The unique identifier of the exam subject
            exam_subject_data: Dictionary containing the updated data
            
        Returns:
            The updated exam subject if found, None otherwise
        """
        # Get existing exam subject
        existing_exam_subject_dict = await self.repository.get_by_id(exam_subject_id)
        if not existing_exam_subject_dict:
            logger.error(f"Exam subject with ID {exam_subject_id} not found")
            return None
        
        # Handle metadata to subject_metadata field name mapping
        if "metadata" in exam_subject_data:
            exam_subject_data["subject_metadata"] = exam_subject_data.pop("metadata")
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in exam_subject_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            # Just return the existing record without database operation
            query = select(ExamSubject).filter(ExamSubject.exam_subject_id == exam_subject_id)
            result = await self.repository.db.execute(query)
            return result.scalar_one_or_none()
        
        return await self.repository.update(exam_subject_id, cleaned_data)
    
    async def delete_exam_subject(self, exam_subject_id: str) -> bool:
        """
        Delete an exam subject.
        
        Args:
            exam_subject_id: The unique identifier of the exam subject
            
        Returns:
            True if the exam subject was deleted, False otherwise
        """
        return await self.repository.delete(exam_subject_id) 