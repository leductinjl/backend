"""
Candidate Exam Subject service module.

This module provides service functions for candidate exam subject operations,
handling business logic for candidate registrations to specific exam subjects.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from app.repositories.candidate_exam_subject_repository import CandidateExamSubjectRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.repositories.exam_subject_repository import ExamSubjectRepository
from app.domain.models.candidate_exam_subject import RegistrationStatus

class CandidateExamSubjectService:
    """Service for candidate exam subject registration operations."""
    
    def __init__(
        self,
        repository: CandidateExamSubjectRepository,
        candidate_exam_repository: CandidateExamRepository = None,
        exam_subject_repository: ExamSubjectRepository = None
    ):
        """
        Initialize with repositories.
        
        Args:
            repository: CandidateExamSubjectRepository instance
            candidate_exam_repository: Optional CandidateExamRepository instance
            exam_subject_repository: Optional ExamSubjectRepository instance
        """
        self.repository = repository
        self.candidate_exam_repository = candidate_exam_repository
        self.exam_subject_repository = exam_subject_repository
        self.logger = logging.getLogger(__name__)
    
    async def get_all_registrations(
        self,
        skip: int = 0,
        limit: int = 100,
        candidate_id: Optional[str] = None,
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        candidate_exam_id: Optional[str] = None,
        exam_subject_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Any], int]:
        """
        Get all candidate exam subject registrations with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            candidate_id: Filter by candidate ID
            exam_id: Filter by exam ID
            subject_id: Filter by subject ID
            candidate_exam_id: Filter by candidate exam ID
            exam_subject_id: Filter by exam subject ID
            status: Filter by registration status
            
        Returns:
            Tuple of (list of registrations, total count)
        """
        try:
            registrations, total = await self.repository.get_all(
                skip=skip,
                limit=limit,
                candidate_id=candidate_id,
                exam_id=exam_id,
                subject_id=subject_id,
                candidate_exam_id=candidate_exam_id,
                exam_subject_id=exam_subject_id,
                status=status
            )
            return registrations, total
        except Exception as e:
            self.logger.error(f"Error getting candidate exam subject registrations: {str(e)}")
            raise
    
    async def get_registration_by_id(self, candidate_exam_subject_id: str) -> Optional[Any]:
        """
        Get a specific candidate exam subject registration by ID.
        
        Args:
            candidate_exam_subject_id: ID of the registration to retrieve
            
        Returns:
            The registration if found, None otherwise
        """
        try:
            return await self.repository.get_by_id(candidate_exam_subject_id)
        except Exception as e:
            self.logger.error(f"Error getting candidate exam subject registration {candidate_exam_subject_id}: {str(e)}")
            raise
    
    async def get_registrations_by_candidate(
        self, 
        candidate_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Any], int]:
        """
        Get all exam subject registrations for a specific candidate.
        
        Args:
            candidate_id: ID of the candidate
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of registrations, total count)
        """
        try:
            return await self.repository.get_by_candidate(
                candidate_id=candidate_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Error getting registrations for candidate {candidate_id}: {str(e)}")
            raise
    
    async def get_registrations_by_candidate_exam(
        self, 
        candidate_exam_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Any], int]:
        """
        Get all subject registrations for a specific candidate exam.
        
        Args:
            candidate_exam_id: ID of the candidate exam
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of registrations, total count)
        """
        try:
            return await self.repository.get_by_candidate_exam(
                candidate_exam_id=candidate_exam_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Error getting registrations for candidate exam {candidate_exam_id}: {str(e)}")
            raise
    
    async def get_registrations_by_exam_subject(
        self, 
        exam_subject_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Any], int]:
        """
        Get all candidate registrations for a specific exam subject.
        
        Args:
            exam_subject_id: ID of the exam subject
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of registrations, total count)
        """
        try:
            return await self.repository.get_by_exam_subject(
                exam_subject_id=exam_subject_id,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Error getting registrations for exam subject {exam_subject_id}: {str(e)}")
            raise
    
    async def get_candidate_exam_schedule(self, candidate_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete exam schedule for a candidate with room and location details.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of dictionaries with complete exam schedule information
        """
        try:
            return await self.repository.get_candidate_exam_schedule(candidate_id)
        except Exception as e:
            self.logger.error(f"Error getting exam schedule for candidate {candidate_id}: {str(e)}")
            raise
    
    async def get_candidate_exam_scores(
        self, 
        candidate_id: str, 
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all exam scores for a candidate with optional filtering by exam and subject.
        
        Args:
            candidate_id: ID of the candidate
            exam_id: Optional ID of the exam to filter by
            subject_id: Optional ID of the subject to filter by
            
        Returns:
            List of dictionaries with score information
        """
        try:
            return await self.repository.get_candidate_exam_scores(
                candidate_id=candidate_id,
                exam_id=exam_id,
                subject_id=subject_id
            )
        except Exception as e:
            self.logger.error(f"Error getting exam scores for candidate {candidate_id}: {str(e)}")
            raise
    
    async def create_registration(self, registration_data: Dict[str, Any]) -> Optional[Any]:
        """
        Create a new candidate exam subject registration.
        
        Args:
            registration_data: Dictionary with registration data
            
        Returns:
            Created registration object or None if creation failed
        """
        try:
            # Validate if the candidate exam exists
            if self.candidate_exam_repository and 'candidate_exam_id' in registration_data:
                candidate_exam = await self.candidate_exam_repository.get_by_id(
                    registration_data['candidate_exam_id']
                )
                if not candidate_exam:
                    self.logger.error(f"Cannot create registration: Candidate exam {registration_data['candidate_exam_id']} not found")
                    return None
            
            # Validate if the exam subject exists
            if self.exam_subject_repository and 'exam_subject_id' in registration_data:
                exam_subject = await self.exam_subject_repository.get_by_id(
                    registration_data['exam_subject_id']
                )
                if not exam_subject:
                    self.logger.error(f"Cannot create registration: Exam subject {registration_data['exam_subject_id']} not found")
                    return None
            
            # Create the registration
            return await self.repository.create(registration_data)
        except Exception as e:
            self.logger.error(f"Error creating candidate exam subject registration: {str(e)}")
            raise
    
    async def update_registration(
        self, 
        candidate_exam_subject_id: str, 
        registration_data: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Update a candidate exam subject registration.
        
        Args:
            candidate_exam_subject_id: ID of the registration to update
            registration_data: Dictionary with updated data
            
        Returns:
            Updated registration object or None if not found
        """
        try:
            return await self.repository.update(
                candidate_exam_subject_id=candidate_exam_subject_id,
                candidate_exam_subject_data=registration_data
            )
        except Exception as e:
            self.logger.error(f"Error updating candidate exam subject registration {candidate_exam_subject_id}: {str(e)}")
            raise
    
    async def delete_registration(self, candidate_exam_subject_id: str) -> bool:
        """
        Delete a candidate exam subject registration.
        
        Args:
            candidate_exam_subject_id: ID of the registration to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.repository.delete(candidate_exam_subject_id)
        except Exception as e:
            self.logger.error(f"Error deleting candidate exam subject registration {candidate_exam_subject_id}: {str(e)}")
            raise
    
    async def confirm_registration(self, candidate_exam_subject_id: str) -> Optional[Any]:
        """
        Confirm a candidate's registration for an exam subject.
        
        Args:
            candidate_exam_subject_id: ID of the registration to confirm
            
        Returns:
            Updated registration object or None if not found
        """
        try:
            return await self.repository.update(
                candidate_exam_subject_id=candidate_exam_subject_id,
                candidate_exam_subject_data={
                    "status": RegistrationStatus.CONFIRMED
                }
            )
        except Exception as e:
            self.logger.error(f"Error confirming candidate exam subject registration {candidate_exam_subject_id}: {str(e)}")
            raise
    
    async def withdraw_registration(self, candidate_exam_subject_id: str, reason: Optional[str] = None) -> Optional[Any]:
        """
        Withdraw a candidate's registration for an exam subject.
        
        Args:
            candidate_exam_subject_id: ID of the registration to withdraw
            reason: Optional reason for withdrawal
            
        Returns:
            Updated registration object or None if not found
        """
        try:
            update_data = {
                "status": RegistrationStatus.WITHDRAWN
            }
            
            if reason:
                update_data["notes"] = reason
                
            return await self.repository.update(
                candidate_exam_subject_id=candidate_exam_subject_id,
                candidate_exam_subject_data=update_data
            )
        except Exception as e:
            self.logger.error(f"Error withdrawing candidate exam subject registration {candidate_exam_subject_id}: {str(e)}")
            raise
    
    async def mark_absent(self, candidate_exam_subject_id: str, reason: Optional[str] = None) -> Optional[Any]:
        """
        Mark a candidate as absent for an exam subject.
        
        Args:
            candidate_exam_subject_id: ID of the registration to mark as absent
            reason: Optional reason for absence
            
        Returns:
            Updated registration object or None if not found
        """
        try:
            update_data = {
                "status": RegistrationStatus.ABSENT
            }
            
            if reason:
                update_data["notes"] = reason
                
            return await self.repository.update(
                candidate_exam_subject_id=candidate_exam_subject_id,
                candidate_exam_subject_data=update_data
            )
        except Exception as e:
            self.logger.error(f"Error marking candidate as absent for exam subject {candidate_exam_subject_id}: {str(e)}")
            raise
    
    async def mark_completed(self, candidate_exam_subject_id: str) -> Optional[Any]:
        """
        Mark a candidate's exam subject as completed.
        
        Args:
            candidate_exam_subject_id: ID of the registration to mark as completed
            
        Returns:
            Updated registration object or None if not found
        """
        try:
            return await self.repository.update(
                candidate_exam_subject_id=candidate_exam_subject_id,
                candidate_exam_subject_data={
                    "status": RegistrationStatus.COMPLETED
                }
            )
        except Exception as e:
            self.logger.error(f"Error marking candidate exam subject as completed {candidate_exam_subject_id}: {str(e)}")
            raise
