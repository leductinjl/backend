"""
Exam Score service module.

This module provides business logic for exam scores, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select
from datetime import datetime

from app.repositories.exam_score_repository import ExamScoreRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.repositories.exam_subject_repository import ExamSubjectRepository
from app.domain.models.exam_score import ExamScore

logger = logging.getLogger(__name__)

class ExamScoreService:
    """Service for handling exam score business logic."""
    
    def __init__(
        self, 
        repository: ExamScoreRepository,
        candidate_exam_repository: Optional[CandidateExamRepository] = None,
        exam_subject_repository: Optional[ExamSubjectRepository] = None,
        history_service = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for exam score data access
            candidate_exam_repository: Repository for candidate exam data access
            exam_subject_repository: Repository for exam subject data access
            history_service: Service for tracking score history
        """
        self.repository = repository
        self.candidate_exam_repository = candidate_exam_repository
        self.exam_subject_repository = exam_subject_repository
        self.history_service = history_service
    
    async def get_all_scores(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        candidate_id: Optional[str] = None,
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        status: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        score_date: Optional[str] = None,
        graded_by: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all exam scores with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            search: Optional search term to find matching candidate or subject
            candidate_id: Optional filter by candidate ID
            exam_id: Optional filter by exam ID
            subject_id: Optional filter by subject ID
            status: Optional filter by score status
            min_score: Optional filter by minimum score
            max_score: Optional filter by maximum score
            score_date: Optional filter by score date (YYYY-MM-DD)
            graded_by: Optional filter by grader ID
            
        Returns:
            Tuple containing the list of exam scores and total count
        """
        filters = {}
        if search:
            filters["search"] = search
        if candidate_id:
            filters["candidate_id"] = candidate_id
        if exam_id:
            filters["exam_id"] = exam_id
        if subject_id:
            filters["subject_id"] = subject_id
        if status:
            filters["status"] = status
        if min_score is not None:
            filters["min_score"] = min_score
        if max_score is not None:
            filters["max_score"] = max_score
        if score_date:
            filters["score_date"] = score_date
        if graded_by:
            filters["graded_by"] = graded_by
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_score_by_id(self, score_id: str) -> Optional[Dict]:
        """
        Get an exam score by its ID.
        
        Args:
            score_id: The unique identifier of the exam score
            
        Returns:
            The exam score if found, None otherwise
        """
        return await self.repository.get_by_id(score_id)
    
    async def get_scores_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all scores for a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of scores for the specified candidate
        """
        return await self.repository.get_by_candidate_id(candidate_id)
    
    async def get_scores_by_exam_subject_id(self, exam_subject_id: str) -> List[Dict]:
        """
        Get all scores for a specific exam subject.
        
        Args:
            exam_subject_id: The ID of the exam subject
            
        Returns:
            List of scores for the specified exam subject
        """
        return await self.repository.get_by_exam_subject_id(exam_subject_id)
    
    async def create_score(self, score_data: Dict[str, Any]) -> Optional[ExamScore]:
        """
        Create a new exam score.
        
        Args:
            score_data: Dictionary containing the exam score data
            
        Returns:
            The created exam score if successful, None otherwise
        """
        # Validate that exam subject exists if repository is provided
        if self.exam_subject_repository:
            exam_subject = await self.exam_subject_repository.get_by_id(score_data["exam_subject_id"])
            
            if not exam_subject:
                logger.error(f"Exam subject with ID {score_data['exam_subject_id']} not found")
                return None
        
        # Check if a score with the same exam subject already exists for this candidate
        # We need to get the candidate_id from the exam_subject's exam
        
        # If score is being set and graded_at is not provided, set it to now
        if "score" in score_data and score_data["score"] is not None and "graded_at" not in score_data:
            score_data["graded_at"] = datetime.now()
            
            # Also set status to GRADED if not specified
            if "status" not in score_data:
                score_data["status"] = "graded"
        
        # Create the exam score
        return await self.repository.create(score_data)
    
    async def update_score(self, score_id: str, score_data: Dict[str, Any]) -> Optional[ExamScore]:
        """
        Update an exam score.
        
        Args:
            score_id: The unique identifier of the exam score
            score_data: Dictionary containing the updated data
            
        Returns:
            The updated exam score if found, None otherwise
        """
        # Get existing score
        existing_score_dict = await self.repository.get_by_id(score_id)
        if not existing_score_dict:
            logger.error(f"Exam score with ID {score_id} not found")
            return None
        
        # Track score changes if score is being updated
        previous_score = None
        if "score" in score_data and score_data["score"] is not None:
            previous_score = existing_score_dict.get("score")
            # If score is changing and was previously null, set graded_at to now
            if existing_score_dict["score"] is None:
                score_data["graded_at"] = datetime.now()
                
                # Also set status to GRADED if not specified in the update
                if "status" not in score_data:
                    score_data["status"] = "graded"
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in score_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            # Just return the existing record without database operation
            query = select(ExamScore).filter(ExamScore.exam_score_id == score_id)
            result = await self.repository.db.execute(query)
            return result.scalar_one_or_none()
        
        # Update the score
        updated_score = await self.repository.update(score_id, cleaned_data)
        
        # Create history entry if score changed and history service is available
        if self.history_service and "score" in cleaned_data and previous_score != cleaned_data["score"]:
            await self.history_service.track_score_change(
                score_id=score_id,
                previous_score=previous_score,
                new_score=cleaned_data["score"],
                changed_by=cleaned_data.get("graded_by"),
                change_type="updated",
                reason=f"Score updated from {previous_score} to {cleaned_data['score']}"
            )
        
        return updated_score
    
    async def delete_score(self, score_id: str) -> bool:
        """
        Delete an exam score.
        
        Args:
            score_id: The unique identifier of the exam score
            
        Returns:
            True if the exam score was deleted, False otherwise
        """
        return await self.repository.delete(score_id)
    
    async def grade_score(self, score_id: str, score_value: float, graded_by: Optional[str] = None, notes: Optional[str] = None) -> Optional[ExamScore]:
        """
        Grade an exam score.
        
        Args:
            score_id: The unique identifier of the exam score
            score_value: The score value
            graded_by: ID of the user who graded the exam
            notes: Optional notes about the grading
            
        Returns:
            The updated exam score if found, None otherwise
        """
        update_data = {
            "score": score_value,
            "status": "graded",
            "graded_at": datetime.now()
        }
        
        if graded_by:
            update_data["graded_by"] = graded_by
            
        if notes:
            update_data["notes"] = notes
        
        return await self.update_score(score_id, update_data)
    
    async def update_score_status(self, score_id: str, status: str, notes: Optional[str] = None) -> Optional[ExamScore]:
        """
        Update the status of an exam score.
        
        Args:
            score_id: The unique identifier of the exam score
            status: The new status
            notes: Optional notes about the status change
            
        Returns:
            The updated exam score if found, None otherwise
        """
        update_data = {
            "status": status
        }
        
        if notes:
            update_data["notes"] = notes
        
        return await self.update_score(score_id, update_data)
    
    async def calculate_total_score(self, exam_id: str, candidate_id: str) -> Optional[float]:
        """
        Calculate the total weighted score for a candidate's exam.
        
        Args:
            exam_id: The ID of the exam
            candidate_id: The ID of the candidate
            
        Returns:
            The total weighted score if scores exist, None otherwise
        """
        # Get all scores for the candidate in the exam
        scores = await self.repository.get_by_candidate_id(candidate_id)
        
        # Filter scores for the specific exam
        exam_scores = [score for score in scores if score.get("exam_id") == exam_id]
        
        if not exam_scores:
            return None
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for score in exam_scores:
            if score.get("score") is not None and score.get("weight") is not None:
                total_weighted_score += float(score["score"]) * float(score["weight"])
                total_weight += float(score["weight"])
        
        if total_weight == 0:
            return None
            
        return total_weighted_score / total_weight 