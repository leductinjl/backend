"""
Candidate Exam service module.

This module provides business logic for candidate exam registrations, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select
from datetime import datetime, date

from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.exam_repository import ExamRepository
from app.domain.models.candidate_exam import CandidateExam

logger = logging.getLogger(__name__)

class CandidateExamService:
    """Service for handling candidate exam registration business logic."""
    
    def __init__(
        self, 
        repository: CandidateExamRepository,
        candidate_repository: Optional[CandidateRepository] = None,
        exam_repository: Optional[ExamRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for candidate exam registration data access
            candidate_repository: Repository for candidate data access
            exam_repository: Repository for exam data access
        """
        self.repository = repository
        self.candidate_repository = candidate_repository
        self.exam_repository = exam_repository
    
    async def get_all_registrations(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        candidate_id: Optional[str] = None,
        exam_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all candidate exam registrations with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            search: Optional search term to find matching candidate or exam names
            candidate_id: Optional filter by candidate ID
            exam_id: Optional filter by exam ID
            status: Optional filter by status
            
        Returns:
            Tuple containing the list of candidate exam registrations and total count
        """
        filters = {}
        if search:
            filters["search"] = search
        if candidate_id:
            filters["candidate_id"] = candidate_id
        if exam_id:
            filters["exam_id"] = exam_id
        if status:
            filters["status"] = status
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_registration_by_id(self, candidate_exam_id: str) -> Optional[Dict]:
        """
        Get a candidate exam registration by its ID.
        
        Args:
            candidate_exam_id: The unique identifier of the candidate exam registration
            
        Returns:
            The candidate exam registration if found, None otherwise
        """
        return await self.repository.get_by_id(candidate_exam_id)
    
    async def get_registrations_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all exam registrations for a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of exam registrations for the specified candidate
        """
        return await self.repository.get_by_candidate_id(candidate_id)
    
    async def get_registrations_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all candidate registrations for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of candidate registrations for the specified exam
        """
        return await self.repository.get_by_exam_id(exam_id)
    
    async def create_registration(self, registration_data: Dict[str, Any]) -> Optional[CandidateExam]:
        """
        Create a new candidate exam registration after validating the candidate and exam IDs.
        
        Args:
            registration_data: Dictionary containing the registration data
            
        Returns:
            The created candidate exam registration if successful, None otherwise
        """
        # Validate that candidate and exam exist if repositories are provided
        if self.candidate_repository and self.exam_repository:
            candidate = await self.candidate_repository.get_by_id(registration_data["candidate_id"])
            exam = await self.exam_repository.get_by_id(registration_data["exam_id"])
            
            if not candidate:
                logger.error(f"Candidate with ID {registration_data['candidate_id']} not found")
                return None
                
            if not exam:
                logger.error(f"Exam with ID {registration_data['exam_id']} not found")
                return None
        
        # Check if a registration with the same candidate and exam already exists
        existing_registration = await self.repository.get_by_candidate_and_exam(
            registration_data["candidate_id"], 
            registration_data["exam_id"]
        )
        
        if existing_registration:
            logger.error(f"Registration for candidate ID {registration_data['candidate_id']} and exam ID {registration_data['exam_id']} already exists")
            return None
        
        # Set registration date if not provided
        if "registration_date" not in registration_data or not registration_data["registration_date"]:
            registration_data["registration_date"] = date.today()
        
        # Create the registration
        return await self.repository.create(registration_data)
    
    async def update_registration(self, candidate_exam_id: str, registration_data: Dict[str, Any]) -> Optional[CandidateExam]:
        """
        Update a candidate exam registration.
        
        Args:
            candidate_exam_id: The unique identifier of the candidate exam registration
            registration_data: Dictionary containing the updated data
            
        Returns:
            The updated candidate exam registration if found, None otherwise
        """
        # Get existing registration
        existing_registration_dict = await self.repository.get_by_id(candidate_exam_id)
        if not existing_registration_dict:
            logger.error(f"Candidate exam registration with ID {candidate_exam_id} not found")
            return None
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in registration_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            # Just return the existing record without database operation
            query = select(CandidateExam).filter(CandidateExam.candidate_exam_id == candidate_exam_id)
            result = await self.repository.db.execute(query)
            return result.scalar_one_or_none()
        
        return await self.repository.update(candidate_exam_id, cleaned_data)
    
    async def delete_registration(self, candidate_exam_id: str) -> bool:
        """
        Delete a candidate exam registration.
        
        Args:
            candidate_exam_id: The unique identifier of the candidate exam registration
            
        Returns:
            True if the candidate exam registration was deleted, False otherwise
        """
        return await self.repository.delete(candidate_exam_id)
    
    async def update_status(self, candidate_exam_id: str, status: str) -> Optional[CandidateExam]:
        """
        Update status for a candidate's exam registration.
        
        Args:
            candidate_exam_id: The unique identifier of the candidate exam registration
            status: The new status
            
        Returns:
            The updated candidate exam registration if found, None otherwise
        """
        update_data = {
            "status": status
        }
        
        return await self.update_registration(candidate_exam_id, update_data) 