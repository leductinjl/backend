"""
Exam Score History service module.

This module provides business logic for exam score history entries, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select
from datetime import datetime

from app.repositories.exam_score_history_repository import ExamScoreHistoryRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.domain.models.exam_score_history import ExamScoreHistory
from app.domain.models.exam_score import ExamScore

logger = logging.getLogger(__name__)

class ExamScoreHistoryService:
    """Service for handling exam score history business logic."""
    
    def __init__(
        self, 
        repository: ExamScoreHistoryRepository,
        exam_score_repository: Optional[ExamScoreRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for exam score history data access
            exam_score_repository: Repository for exam score data access
        """
        self.repository = repository
        self.exam_score_repository = exam_score_repository
    
    async def get_all_history_entries(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        score_id: Optional[str] = None,
        changed_by: Optional[str] = None,
        candidate_id: Optional[str] = None,
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all score history entries with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            search: Optional search term for filtering
            score_id: Optional filter by score ID
            changed_by: Optional filter by user who made the change
            candidate_id: Optional filter by candidate ID
            exam_id: Optional filter by exam ID
            subject_id: Optional filter by subject ID
            created_after: Optional filter by entries created after date (YYYY-MM-DD)
            created_before: Optional filter by entries created before date (YYYY-MM-DD)
            
        Returns:
            Tuple containing the list of score history entries and total count
        """
        filters = {}
        if search:
            filters["search"] = search
        if score_id:
            filters["score_id"] = score_id
        if changed_by:
            filters["changed_by"] = changed_by
        if candidate_id:
            filters["candidate_id"] = candidate_id
        if exam_id:
            filters["exam_id"] = exam_id
        if subject_id:
            filters["subject_id"] = subject_id
        if created_after:
            filters["created_after"] = created_after
        if created_before:
            filters["created_before"] = created_before
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_history_by_id(self, history_id: str) -> Optional[Dict]:
        """
        Get a score history entry by its ID.
        
        Args:
            history_id: The unique identifier of the score history entry
            
        Returns:
            The score history entry if found, None otherwise
        """
        return await self.repository.get_by_id(history_id)
    
    async def get_history_by_score_id(self, score_id: str) -> List[Dict]:
        """
        Get all history entries for a specific exam score.
        
        Args:
            score_id: The ID of the exam score
            
        Returns:
            List of history entries for the specified exam score
        """
        return await self.repository.get_by_score_id(score_id)
    
    async def get_history_by_review_id(self, review_id: str) -> List[Dict]:
        """
        Get all history entries related to a specific score review.
        
        Args:
            review_id: The ID of the score review
            
        Returns:
            List of history entries related to the specified score review
        """
        return await self.repository.get_by_review_id(review_id)
    
    async def get_history_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all score history entries for a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of score history entries for the specified candidate
        """
        return await self.repository.get_by_candidate_id(candidate_id)
    
    async def create_history_entry(self, history_data: Dict[str, Any]) -> Optional[ExamScoreHistory]:
        """
        Create a new score history entry after validating the score ID.
        
        Args:
            history_data: Dictionary containing the score history data
            
        Returns:
            The created score history entry if successful, None otherwise
        """
        # Validate that exam score exists if repository is provided
        if self.exam_score_repository:
            score = await self.exam_score_repository.get_by_id(history_data["score_id"])
            
            if not score:
                logger.error(f"Exam score with ID {history_data['score_id']} not found")
                return None
        
        # Create the history entry
        return await self.repository.create(history_data)
    
    async def track_score_change(
        self, 
        score_id: str, 
        previous_score: Optional[float], 
        new_score: Optional[float], 
        changed_by: Optional[str], 
        change_type: str, 
        reason: Optional[str] = None, 
        review_id: Optional[str] = None, 
        metadata: Optional[Dict] = None
    ) -> Optional[ExamScoreHistory]:
        """
        Track a score change by creating a history entry.
        
        Args:
            score_id: ID of the exam score that was changed
            previous_score: Previous score value before the change
            new_score: New score value after the change
            changed_by: ID of the user who made the change
            change_type: Type of change that occurred
            reason: Reason for the change
            review_id: ID of the score review if the change was due to a review
            metadata: Additional metadata for the history entry
            
        Returns:
            The created history entry if successful, None otherwise
        """
        # Validate that exam score exists if repository is provided
        if self.exam_score_repository:
            score = await self.exam_score_repository.get_by_id(score_id)
            
            if not score:
                logger.error(f"Exam score with ID {score_id} not found")
                return None
        
        # Create the history entry
        return await self.repository.create_from_score_change(
            score_id=score_id,
            previous_score=previous_score,
            new_score=new_score,
            changed_by=changed_by,
            change_type=change_type,
            reason=reason
        )
    
    async def track_score_creation(
        self,
        score_id: str,
        score_value: Optional[float],
        created_by: Optional[str],
        metadata: Optional[Dict] = None
    ) -> Optional[ExamScoreHistory]:
        """
        Track the creation of a new score.
        
        Args:
            score_id: ID of the newly created exam score
            score_value: Initial score value
            created_by: ID of the user who created the score
            metadata: Additional metadata for the history entry
            
        Returns:
            The created history entry if successful, None otherwise
        """
        return await self.track_score_change(
            score_id=score_id,
            previous_score=None,
            new_score=score_value,
            changed_by=created_by,
            change_type="created",
            reason="Initial score creation",
            metadata=metadata
        )
    
    async def track_score_grading(
        self,
        score_id: str,
        previous_score: Optional[float],
        new_score: float,
        graded_by: str,
        reason: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[ExamScoreHistory]:
        """
        Track the grading of a score.
        
        Args:
            score_id: ID of the exam score that was graded
            previous_score: Previous score value before grading
            new_score: New score value after grading
            graded_by: ID of the user who graded the score
            reason: Reason for the grading
            metadata: Additional metadata for the history entry
            
        Returns:
            The created history entry if successful, None otherwise
        """
        return await self.track_score_change(
            score_id=score_id,
            previous_score=previous_score,
            new_score=new_score,
            changed_by=graded_by,
            change_type="graded",
            reason=reason or "Score graded",
            metadata=metadata
        )
    
    async def track_score_revision(
        self,
        score_id: str,
        previous_score: float,
        new_score: float,
        revised_by: str,
        review_id: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[ExamScoreHistory]:
        """
        Track a score revision, typically from a review.
        
        Args:
            score_id: ID of the exam score that was revised
            previous_score: Previous score value before revision
            new_score: New score value after revision
            revised_by: ID of the user who revised the score
            review_id: ID of the score review if the revision was due to a review
            reason: Reason for the revision
            metadata: Additional metadata for the history entry
            
        Returns:
            The created history entry if successful, None otherwise
        """
        return await self.track_score_change(
            score_id=score_id,
            previous_score=previous_score,
            new_score=new_score,
            changed_by=revised_by,
            change_type="revised",
            reason=reason or "Score revised",
            review_id=review_id,
            metadata=metadata
        ) 