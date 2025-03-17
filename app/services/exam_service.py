"""
Exam service module.

This module provides business logic for exams, bridging
the API layer with the repository layer.
"""

import logging
from datetime import date
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select

from app.repositories.exam_repository import ExamRepository
from app.repositories.exam_type_repository import ExamTypeRepository
from app.repositories.management_unit_repository import ManagementUnitRepository
from app.domain.models.exam import Exam

logger = logging.getLogger(__name__)

class ExamService:
    """Service for handling exam business logic."""
    
    def __init__(
        self, 
        repository: ExamRepository,
        exam_type_repository: Optional[ExamTypeRepository] = None,
        management_unit_repository: Optional[ManagementUnitRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for exam data access
            exam_type_repository: Repository for exam type data access
            management_unit_repository: Repository for management unit data access
        """
        self.repository = repository
        self.exam_type_repository = exam_type_repository
        self.management_unit_repository = management_unit_repository
    
    async def get_all_exams(
        self, 
        skip: int = 0, 
        limit: int = 100,
        exam_type_id: Optional[str] = None,
        management_unit_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        start_date_from: Optional[date] = None,
        start_date_to: Optional[date] = None,
        end_date_from: Optional[date] = None,
        end_date_to: Optional[date] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all exams with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            exam_type_id: Optional filter by exam type ID
            management_unit_id: Optional filter by management unit ID
            is_active: Optional filter by active status
            start_date_from: Optional filter for exams starting from this date
            start_date_to: Optional filter for exams starting before this date
            end_date_from: Optional filter for exams ending from this date
            end_date_to: Optional filter for exams ending before this date
            
        Returns:
            Tuple containing the list of exams and total count
        """
        filters = {}
        if exam_type_id:
            filters["type_id"] = exam_type_id
        if management_unit_id:
            filters["organizing_unit_id"] = management_unit_id
        if is_active is not None:
            filters["is_active"] = is_active
        if start_date_from:
            filters["start_date"] = start_date_from
        if end_date_to:
            filters["end_date"] = end_date_to
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_exam_by_id(self, exam_id: str) -> Optional[Dict]:
        """
        Get an exam by its ID.
        
        Args:
            exam_id: The unique identifier of the exam
            
        Returns:
            The exam if found, None otherwise
        """
        return await self.repository.get_by_id(exam_id)
    
    async def create_exam(self, exam_data: Dict[str, Any]) -> Optional[Exam]:
        """
        Create a new exam after validating the exam type and management unit IDs.
        
        Args:
            exam_data: Dictionary containing the exam data
            
        Returns:
            The created exam if successful, None otherwise
        """
        # Validate that exam type and management unit exist if repositories are provided
        if self.exam_type_repository and self.management_unit_repository:
            exam_type = await self.exam_type_repository.get_by_id(exam_data["type_id"])
            management_unit = await self.management_unit_repository.get_by_id(exam_data["organizing_unit_id"])
            
            if not exam_type:
                logger.error(f"Exam type with ID {exam_data['type_id']} not found")
                return None
                
            if not management_unit:
                logger.error(f"Management unit with ID {exam_data['organizing_unit_id']} not found")
                return None
        
        # Validate dates
        start_date = exam_data.get("start_date")
        end_date = exam_data.get("end_date")
        
        if start_date and end_date and start_date > end_date:
            logger.error("Start date cannot be after end date")
            return None
        
        # Create the exam
        return await self.repository.create(exam_data)
    
    async def update_exam(self, exam_id: str, exam_data: Dict[str, Any]) -> Optional[Exam]:
        """
        Update an exam after validating the data.
        
        Args:
            exam_id: The unique identifier of the exam
            exam_data: Dictionary containing the updated data
            
        Returns:
            The updated exam if found and valid, None otherwise
        """
        # Get existing exam
        existing_exam_dict = await self.repository.get_by_id(exam_id)
        if not existing_exam_dict:
            logger.error(f"Exam with ID {exam_id} not found")
            return None
            
        # Validate foreign keys if provided
        if "type_id" in exam_data and self.exam_type_repository:
            exam_type = await self.exam_type_repository.get_by_id(exam_data["type_id"])
            if not exam_type:
                logger.error(f"Exam type with ID {exam_data['type_id']} not found")
                return None
                
        if "organizing_unit_id" in exam_data and self.management_unit_repository:
            management_unit = await self.management_unit_repository.get_by_id(exam_data["organizing_unit_id"])
            if not management_unit:
                logger.error(f"Management unit with ID {exam_data['organizing_unit_id']} not found")
                return None
        
        # Validate dates
        start_date = exam_data.get("start_date", existing_exam_dict.get("start_date"))
        end_date = exam_data.get("end_date", existing_exam_dict.get("end_date"))
        
        if start_date and end_date and start_date > end_date:
            logger.error("Start date cannot be after end date")
            return None
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in exam_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            # Just return the existing record without database operation
            query = select(Exam).filter(Exam.exam_id == exam_id)
            result = await self.repository.db.execute(query)
            return result.scalar_one_or_none()
        
        return await self.repository.update(exam_id, cleaned_data)
    
    async def delete_exam(self, exam_id: str) -> bool:
        """
        Delete an exam.
        
        Args:
            exam_id: The unique identifier of the exam
            
        Returns:
            True if the exam was deleted, False otherwise
        """
        return await self.repository.delete(exam_id) 