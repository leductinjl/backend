"""
Exam Attempt History service module.

This module provides business logic for exam attempt history entries, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

from app.repositories.exam_attempt_history_repository import ExamAttemptHistoryRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.domain.models.exam_attempt_history import ExamAttemptHistory

logger = logging.getLogger(__name__)

class ExamAttemptHistoryService:
    """Service for handling exam attempt history business logic."""
    
    def __init__(
        self, 
        repository: ExamAttemptHistoryRepository,
        candidate_repository: Optional[CandidateRepository] = None,
        exam_repository: Optional[ExamRepository] = None,
        candidate_exam_repository: Optional[CandidateExamRepository] = None,
        exam_score_repository: Optional[ExamScoreRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for exam attempt history data access
            candidate_repository: Repository for candidate data access
            exam_repository: Repository for exam data access
            candidate_exam_repository: Repository for candidate exam registration data access
            exam_score_repository: Repository for exam score data access
        """
        self.repository = repository
        self.candidate_repository = candidate_repository
        self.exam_repository = exam_repository
        self.candidate_exam_repository = candidate_exam_repository
        self.exam_score_repository = exam_score_repository
    
    async def get_all_attempts(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        candidate_id: Optional[str] = None,
        exam_id: Optional[str] = None,
        attempt_number: Optional[int] = None,
        status: Optional[str] = None,
        result: Optional[str] = None,
        attempt_date_from: Optional[date] = None,
        attempt_date_to: Optional[date] = None,
        attendance_verified_by: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        sort_field: Optional[str] = None,
        sort_dir: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all exam attempt history entries with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            search: Optional search term for filtering
            candidate_id: Optional filter by candidate ID
            exam_id: Optional filter by exam ID
            attempt_number: Optional filter by attempt number
            status: Optional filter by attempt status
            result: Optional filter by attempt result
            attempt_date_from: Optional filter by minimum attempt date
            attempt_date_to: Optional filter by maximum attempt date
            attendance_verified_by: Optional filter by user who verified attendance
            min_score: Optional filter by minimum total score
            max_score: Optional filter by maximum total score
            sort_field: Optional field to sort by
            sort_dir: Optional sort direction ('asc' or 'desc')
            
        Returns:
            Tuple containing the list of attempt history entries and total count
        """
        filters = {}
        if search:
            filters["search"] = search
        if candidate_id:
            filters["candidate_id"] = candidate_id
        if exam_id:
            filters["exam_id"] = exam_id
        if attempt_number:
            filters["attempt_number"] = attempt_number
        if status:
            filters["status"] = status
        if result:
            filters["result"] = result
        if attempt_date_from:
            filters["attempt_date_from"] = attempt_date_from
        if attempt_date_to:
            filters["attempt_date_to"] = attempt_date_to
        if attendance_verified_by:
            filters["attendance_verified_by"] = attendance_verified_by
        if min_score is not None:
            filters["min_score"] = min_score
        if max_score is not None:
            filters["max_score"] = max_score
        if sort_field:
            filters["sort_field"] = sort_field
        if sort_dir:
            filters["sort_dir"] = sort_dir
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_attempt_by_id(self, attempt_id: str) -> Optional[Dict]:
        """
        Get an attempt history entry by its ID.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            
        Returns:
            The attempt history entry if found, None otherwise
        """
        return await self.repository.get_by_id(attempt_id)
    
    async def get_attempts_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all attempt history entries for a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of attempt history entries for the specified candidate
        """
        return await self.repository.get_by_candidate_id(candidate_id)
    
    async def get_attempts_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all attempt history entries for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of attempt history entries for the specified exam
        """
        return await self.repository.get_by_exam_id(exam_id)
    
    async def get_attempts_by_candidate_and_exam(
        self, 
        candidate_id: str, 
        exam_id: str, 
        attempt_number: Optional[int] = None
    ) -> List[Dict]:
        """
        Get attempt history entries for a specific candidate and exam.
        
        Args:
            candidate_id: The ID of the candidate
            exam_id: The ID of the exam
            attempt_number: Optional specific attempt number to retrieve
            
        Returns:
            List of attempt history entries for the specified candidate and exam
        """
        return await self.repository.get_by_candidate_and_exam(
            candidate_id=candidate_id,
            exam_id=exam_id,
            attempt_number=attempt_number
        )
    
    async def get_latest_attempt(self, candidate_id: str, exam_id: str) -> Optional[Dict]:
        """
        Get the latest attempt history entry for a specific candidate and exam.
        
        Args:
            candidate_id: The ID of the candidate
            exam_id: The ID of the exam
            
        Returns:
            The latest attempt history entry if found, None otherwise
        """
        return await self.repository.get_latest_attempt(candidate_id, exam_id)
    
    async def create_attempt(self, attempt_data: Dict[str, Any]) -> Optional[ExamAttemptHistory]:
        """
        Create a new attempt history entry.
        
        Args:
            attempt_data: Dictionary containing the attempt history data
            
        Returns:
            The created attempt history entry if successful, None otherwise
        """
        # Validate that candidate_exam exists if repository is provided
        if self.candidate_exam_repository:
            candidate_exam = await self.candidate_exam_repository.get_by_id(attempt_data["candidate_exam_id"])
            
            if not candidate_exam:
                logger.error(f"Candidate exam with ID {attempt_data['candidate_exam_id']} not found")
                return None
        
        # If attempt_number is not provided, determine the next attempt number
        if "attempt_number" not in attempt_data:
            attempt_data["attempt_number"] = await self.repository.get_next_attempt_number_by_candidate_exam_id(
                attempt_data["candidate_exam_id"]
            )
        
        # Create the attempt history entry
        return await self.repository.create(attempt_data)
    
    async def update_attempt(self, attempt_id: str, attempt_data: Dict[str, Any]) -> Optional[ExamAttemptHistory]:
        """
        Update an existing attempt history entry.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            attempt_data: Dictionary containing the updated attempt history data
            
        Returns:
            The updated attempt history entry if found, None otherwise
        """
        # Check if attempt exists
        existing_attempt = await self.repository.get_by_id(attempt_id)
        
        if not existing_attempt:
            logger.error(f"Attempt history entry with ID {attempt_id} not found")
            return None
        
        # Update the attempt history entry
        return await self.repository.update(attempt_id, attempt_data)
    
    async def delete_attempt(self, attempt_id: str) -> bool:
        """
        Delete an attempt history entry.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            
        Returns:
            True if the attempt history entry was deleted, False otherwise
        """
        return await self.repository.delete(attempt_id)
    
    async def check_in_candidate(
        self, 
        attempt_id: str, 
        check_in_time: Optional[datetime] = None, 
        verified_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[ExamAttemptHistory]:
        """
        Check in a candidate for an exam.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            check_in_time: Time of check-in (defaults to current time)
            verified_by: ID of the user who verified the check-in
            notes: Additional notes about the check-in
            
        Returns:
            The updated attempt history entry if found, None otherwise
        """
        # Check if attempt exists
        existing_attempt = await self.repository.get_by_id(attempt_id)
        
        if not existing_attempt:
            logger.error(f"Attempt history entry with ID {attempt_id} not found")
            return None
        
        # Validate current status
        if existing_attempt["status"] not in ["registered"]:
            logger.error(f"Cannot check in candidate. Current status is {existing_attempt['status']}")
            return None
        
        # Update the attempt history entry
        update_data = {
            "status": "checked_in",
            "check_in_time": check_in_time or datetime.utcnow()
        }
        
        if verified_by:
            update_data["attendance_verified_by"] = verified_by
        
        if notes:
            update_data["notes"] = notes
        
        return await self.repository.update(attempt_id, update_data)
    
    async def start_exam(
        self, 
        attempt_id: str, 
        start_time: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Optional[ExamAttemptHistory]:
        """
        Start an exam for a candidate.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            start_time: Time of exam start (defaults to current time)
            notes: Additional notes about the exam start
            
        Returns:
            The updated attempt history entry if found, None otherwise
        """
        # Check if attempt exists
        existing_attempt = await self.repository.get_by_id(attempt_id)
        
        if not existing_attempt:
            logger.error(f"Attempt history entry with ID {attempt_id} not found")
            return None
        
        # Validate current status
        if existing_attempt["status"] not in ["registered", "checked_in"]:
            logger.error(f"Cannot start exam. Current status is {existing_attempt['status']}")
            return None
        
        # Update the attempt history entry
        update_data = {
            "status": "in_progress",
            "start_time": start_time or datetime.utcnow()
        }
        
        # If not already checked in, set check-in time to the same as start time
        if existing_attempt["status"] == "registered":
            update_data["check_in_time"] = update_data["start_time"]
        
        if notes:
            update_data["notes"] = notes
        
        return await self.repository.update(attempt_id, update_data)
    
    async def complete_exam(
        self, 
        attempt_id: str, 
        end_time: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Optional[ExamAttemptHistory]:
        """
        Complete an exam for a candidate.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            end_time: Time of exam completion (defaults to current time)
            notes: Additional notes about the exam completion
            
        Returns:
            The updated attempt history entry if found, None otherwise
        """
        # Check if attempt exists
        existing_attempt = await self.repository.get_by_id(attempt_id)
        
        if not existing_attempt:
            logger.error(f"Attempt history entry with ID {attempt_id} not found")
            return None
        
        # Validate current status
        if existing_attempt["status"] not in ["in_progress"]:
            logger.error(f"Cannot complete exam. Current status is {existing_attempt['status']}")
            return None
        
        # Update the attempt history entry
        update_data = {
            "status": "completed",
            "end_time": end_time or datetime.utcnow()
        }
        
        if notes:
            update_data["notes"] = notes
        
        return await self.repository.update(attempt_id, update_data)
    
    async def mark_as_absent(
        self, 
        attempt_id: str, 
        verified_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[ExamAttemptHistory]:
        """
        Mark a candidate as absent for an exam.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            verified_by: ID of the user who verified the absence
            notes: Additional notes about the absence
            
        Returns:
            The updated attempt history entry if found, None otherwise
        """
        # Check if attempt exists
        existing_attempt = await self.repository.get_by_id(attempt_id)
        
        if not existing_attempt:
            logger.error(f"Attempt history entry with ID {attempt_id} not found")
            return None
        
        # Validate current status
        if existing_attempt["status"] not in ["registered"]:
            logger.error(f"Cannot mark as absent. Current status is {existing_attempt['status']}")
            return None
        
        # Update the attempt history entry
        update_data = {
            "status": "absent",
            "result": "failed"
        }
        
        if verified_by:
            update_data["attendance_verified_by"] = verified_by
        
        if notes:
            update_data["notes"] = notes
        
        return await self.repository.update(attempt_id, update_data)
    
    async def disqualify_candidate(
        self, 
        attempt_id: str, 
        disqualification_reason: str,
        verified_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[ExamAttemptHistory]:
        """
        Disqualify a candidate from an exam.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            disqualification_reason: Reason for disqualification
            verified_by: ID of the user who verified the disqualification
            notes: Additional notes about the disqualification
            
        Returns:
            The updated attempt history entry if found, None otherwise
        """
        # Check if attempt exists
        existing_attempt = await self.repository.get_by_id(attempt_id)
        
        if not existing_attempt:
            logger.error(f"Attempt history entry with ID {attempt_id} not found")
            return None
        
        # Validate current status
        if existing_attempt["status"] not in ["registered", "checked_in", "in_progress"]:
            logger.error(f"Cannot disqualify candidate. Current status is {existing_attempt['status']}")
            return None
        
        # Update the attempt history entry
        update_data = {
            "status": "disqualified",
            "result": "failed",
            "disqualification_reason": disqualification_reason
        }
        
        if verified_by:
            update_data["attendance_verified_by"] = verified_by
        
        if notes:
            update_data["notes"] = notes
        
        # Set end time if the exam was in progress
        if existing_attempt["status"] == "in_progress":
            update_data["end_time"] = datetime.utcnow()
        
        return await self.repository.update(attempt_id, update_data)
    
    async def cancel_attempt(
        self, 
        attempt_id: str, 
        cancellation_reason: str,
        notes: Optional[str] = None
    ) -> Optional[ExamAttemptHistory]:
        """
        Cancel an exam attempt.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            cancellation_reason: Reason for cancellation
            notes: Additional notes about the cancellation
            
        Returns:
            The updated attempt history entry if found, None otherwise
        """
        # Check if attempt exists
        existing_attempt = await self.repository.get_by_id(attempt_id)
        
        if not existing_attempt:
            logger.error(f"Attempt history entry with ID {attempt_id} not found")
            return None
        
        # Update the attempt history entry
        update_data = {
            "status": "cancelled",
            "result": "inconclusive",
            "cancellation_reason": cancellation_reason
        }
        
        if notes:
            update_data["notes"] = notes
        
        # Set end time if the exam was in progress
        if existing_attempt["status"] == "in_progress":
            update_data["end_time"] = datetime.utcnow()
        
        return await self.repository.update(attempt_id, update_data)
    
    async def update_attempt_result(
        self, 
        attempt_id: str, 
        result: str,
        total_score: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Optional[ExamAttemptHistory]:
        """
        Update the result of an exam attempt.
        
        Args:
            attempt_id: The unique identifier of the attempt history entry
            result: Result of the attempt (passed, failed, or inconclusive)
            total_score: Total score achieved in the attempt
            notes: Additional notes about the result
            
        Returns:
            The updated attempt history entry if found, None otherwise
        """
        # Check if attempt exists
        existing_attempt = await self.repository.get_by_id(attempt_id)
        
        if not existing_attempt:
            logger.error(f"Attempt history entry with ID {attempt_id} not found")
            return None
        
        # Validate current status
        if existing_attempt["status"] not in ["completed"]:
            logger.error(f"Cannot update result. Current status is {existing_attempt['status']}")
            return None
        
        # Update the attempt history entry
        update_data = {
            "result": result
        }
        
        if total_score is not None:
            update_data["total_score"] = total_score
        
        if notes:
            update_data["notes"] = notes
        
        return await self.repository.update(attempt_id, update_data)
    
    async def register_new_attempt(
        self, 
        candidate_exam_id: str, 
        attempt_date: date,
        notes: Optional[str] = None
    ) -> Optional[ExamAttemptHistory]:
        """
        Register a new attempt for a candidate exam.
        
        Args:
            candidate_exam_id: The ID of the candidate exam relationship
            attempt_date: Date of the exam attempt
            notes: Additional notes about the attempt
            
        Returns:
            The created attempt history entry if successful, None otherwise
        """
        # Validate that candidate_exam exists
        if self.candidate_exam_repository:
            candidate_exam = await self.candidate_exam_repository.get_by_id(candidate_exam_id)
            
            if not candidate_exam:
                logger.error(f"Candidate exam with ID {candidate_exam_id} not found")
                return None
        
        # Get the next attempt number
        attempt_number = await self.repository.get_next_attempt_number_by_candidate_exam_id(candidate_exam_id)
        
        # Create the attempt history entry
        attempt_data = {
            "candidate_exam_id": candidate_exam_id,
            "attempt_number": attempt_number,
            "attempt_date": attempt_date,
            "notes": notes
        }
        
        return await self.repository.create(attempt_data)
    
    async def get_candidate_attempt_count(self, candidate_id: str, exam_id: str) -> int:
        """
        Get the number of attempts a candidate has made for a specific exam.
        
        Args:
            candidate_id: The ID of the candidate
            exam_id: The ID of the exam
            
        Returns:
            The number of attempts
        """
        attempts = await self.repository.get_by_candidate_and_exam(candidate_id, exam_id)
        return len(attempts)
    
    async def has_passed_exam(self, candidate_id: str, exam_id: str) -> bool:
        """
        Check if a candidate has passed a specific exam in any of their attempts.
        
        Args:
            candidate_id: The ID of the candidate
            exam_id: The ID of the exam
            
        Returns:
            True if the candidate has passed the exam, False otherwise
        """
        attempts = await self.repository.get_by_candidate_and_exam(candidate_id, exam_id)
        
        for attempt in attempts:
            if attempt["result"] == "passed":
                return True
        
        return False 