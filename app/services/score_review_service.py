"""
Score Review service module.

This module provides business logic for score reviews, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select
from datetime import datetime

from app.repositories.score_review_repository import ScoreReviewRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.domain.models.score_review import ScoreReview
from app.domain.models.exam_score import ExamScore

logger = logging.getLogger(__name__)

class ScoreReviewService:
    """Service for handling score review business logic."""
    
    def __init__(
        self, 
        repository: ScoreReviewRepository,
        exam_score_repository: Optional[ExamScoreRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for score review data access
            exam_score_repository: Repository for exam score data access
        """
        self.repository = repository
        self.exam_score_repository = exam_score_repository
    
    async def get_all_reviews(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        score_id: Optional[str] = None,
        requested_by: Optional[str] = None,
        assigned_to: Optional[str] = None,
        candidate_id: Optional[str] = None,
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        resolved_after: Optional[str] = None,
        resolved_before: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all score reviews with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            search: Optional search term for filtering
            status: Optional filter by review status
            priority: Optional filter by review priority
            score_id: Optional filter by exam score ID
            requested_by: Optional filter by user who requested the review
            assigned_to: Optional filter by user assigned to the review
            candidate_id: Optional filter by candidate ID
            exam_id: Optional filter by exam ID
            subject_id: Optional filter by subject ID
            created_after: Optional filter by reviews created after date (YYYY-MM-DD)
            created_before: Optional filter by reviews created before date (YYYY-MM-DD)
            resolved_after: Optional filter by reviews resolved after date (YYYY-MM-DD)
            resolved_before: Optional filter by reviews resolved before date (YYYY-MM-DD)
            
        Returns:
            Tuple containing the list of score reviews and total count
        """
        filters = {}
        if search:
            filters["search"] = search
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if score_id:
            filters["score_id"] = score_id
        if requested_by:
            filters["requested_by"] = requested_by
        if assigned_to:
            filters["assigned_to"] = assigned_to
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
        if resolved_after:
            filters["resolved_after"] = resolved_after
        if resolved_before:
            filters["resolved_before"] = resolved_before
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_review_by_id(self, review_id: str) -> Optional[Dict]:
        """
        Get a score review by its ID.
        
        Args:
            review_id: The unique identifier of the score review
            
        Returns:
            The score review if found, None otherwise
        """
        return await self.repository.get_by_id(review_id)
    
    async def get_reviews_by_score_id(self, score_id: str) -> List[Dict]:
        """
        Get all reviews for a specific exam score.
        
        Args:
            score_id: The ID of the exam score
            
        Returns:
            List of reviews for the specified exam score
        """
        return await self.repository.get_by_score_id(score_id)
    
    async def get_reviews_by_requested_by(self, user_id: str) -> List[Dict]:
        """
        Get all reviews requested by a specific user.
        
        Args:
            user_id: The ID of the user who requested the reviews
            
        Returns:
            List of reviews requested by the specified user
        """
        return await self.repository.get_by_requested_by(user_id)
    
    async def get_reviews_by_assigned_to(self, user_id: str) -> List[Dict]:
        """
        Get all reviews assigned to a specific user.
        
        Args:
            user_id: The ID of the user who is assigned to the reviews
            
        Returns:
            List of reviews assigned to the specified user
        """
        return await self.repository.get_by_assigned_to(user_id)
    
    async def get_reviews_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all reviews related to a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of reviews related to the specified candidate
        """
        return await self.repository.get_by_candidate_id(candidate_id)
    
    async def create_review(self, review_data: Dict[str, Any]) -> Optional[ScoreReview]:
        """
        Create a new score review after validating the exam score ID.
        
        Args:
            review_data: Dictionary containing the score review data
            
        Returns:
            The created score review if successful, None otherwise
        """
        # Validate that exam score exists if repository is provided
        if self.exam_score_repository:
            score = await self.exam_score_repository.get_by_id(review_data["score_id"])
            
            if not score:
                logger.error(f"Exam score with ID {review_data['score_id']} not found")
                return None
        
        # Create the review
        return await self.repository.create(review_data)
    
    async def update_review(self, review_id: str, review_data: Dict[str, Any]) -> Optional[ScoreReview]:
        """
        Update a score review.
        
        Args:
            review_id: The unique identifier of the score review
            review_data: Dictionary containing the updated data
            
        Returns:
            The updated score review if found, None otherwise
        """
        # Get existing review to check status transitions
        existing_review_dict = await self.repository.get_by_id(review_id)
        if not existing_review_dict:
            logger.error(f"Score review with ID {review_id} not found")
            return None
        
        # Special handling for status transitions
        if "status" in review_data and review_data["status"] != existing_review_dict["status"]:
            # If status is changing to a completed state (APPROVED, REJECTED, COMPLETED), set resolved_at
            if review_data["status"] in ["approved", "rejected", "completed"] and not review_data.get("resolved_at"):
                review_data["resolved_at"] = datetime.now()
                logger.info(f"Automatically set resolved_at for review {review_id} with status {review_data['status']}")
        
        # Remove any empty fields
        cleaned_data = {k: v for k, v in review_data.items() if v is not None}
        
        # Don't update if no fields to update
        if not cleaned_data:
            # Just return the existing record without database operation
            query = select(ScoreReview).filter(ScoreReview.review_id == review_id)
            result = await self.repository.db.execute(query)
            return result.scalar_one_or_none()
        
        return await self.repository.update(review_id, cleaned_data)
    
    async def delete_review(self, review_id: str) -> bool:
        """
        Delete a score review.
        
        Args:
            review_id: The unique identifier of the score review
            
        Returns:
            True if the score review was deleted, False otherwise
        """
        return await self.repository.delete(review_id)
    
    async def assign_review(self, review_id: str, assigned_to: str) -> Optional[ScoreReview]:
        """
        Assign a score review to a user.
        
        Args:
            review_id: The unique identifier of the score review
            assigned_to: The ID of the user to assign the review to
            
        Returns:
            The updated score review if found, None otherwise
        """
        update_data = {
            "assigned_to": assigned_to,
            "status": "in_progress"  # Change status to in_progress when assigned
        }
        
        return await self.update_review(review_id, update_data)
    
    async def update_review_status(self, review_id: str, status: str, resolution_notes: Optional[str] = None) -> Optional[ScoreReview]:
        """
        Update the status of a score review.
        
        Args:
            review_id: The unique identifier of the score review
            status: The new status
            resolution_notes: Optional notes about the resolution
            
        Returns:
            The updated score review if found, None otherwise
        """
        update_data = {
            "status": status
        }
        
        # Add resolution notes if provided
        if resolution_notes:
            update_data["resolution_notes"] = resolution_notes
        
        # Set resolved_at for terminal statuses
        if status in ["approved", "rejected", "completed"]:
            update_data["resolved_at"] = datetime.now()
        
        return await self.update_review(review_id, update_data)
    
    async def approve_review(self, review_id: str, resolution_notes: Optional[str] = None) -> Optional[Dict]:
        """
        Approve a score review and update the associated exam score.
        
        Args:
            review_id: The unique identifier of the score review
            resolution_notes: Optional notes about the resolution
            
        Returns:
            Dictionary with the updated review and score information if successful, None otherwise
        """
        # Get the review to check the expected score
        review = await self.repository.get_by_id(review_id)
        if not review:
            logger.error(f"Score review with ID {review_id} not found")
            return None
        
        if not review["expected_score"]:
            logger.error(f"Score review with ID {review_id} has no expected score")
            return None
        
        # Update the score if exam_score_repository is provided
        updated_score = None
        if self.exam_score_repository:
            score_update = {
                "score": review["expected_score"],
                "status": "revised"  # Mark the score as revised
            }
            
            # Update the exam score
            updated_score = await self.exam_score_repository.update(review["score_id"], score_update)
            
            if not updated_score:
                logger.error(f"Failed to update exam score with ID {review['score_id']}")
                return None
        
        # Update the review status
        update_data = {
            "status": "approved",
            "resolved_at": datetime.now()
        }
        
        if resolution_notes:
            update_data["resolution_notes"] = resolution_notes
        
        # Update the review
        updated_review = await self.repository.update(review_id, update_data)
        
        return {
            "review": updated_review,
            "score": updated_score
        }
    
    async def reject_review(self, review_id: str, resolution_notes: str) -> Optional[ScoreReview]:
        """
        Reject a score review.
        
        Args:
            review_id: The unique identifier of the score review
            resolution_notes: Notes explaining the rejection reason
            
        Returns:
            The updated score review if found, None otherwise
        """
        update_data = {
            "status": "rejected",
            "resolution_notes": resolution_notes,
            "resolved_at": datetime.now()
        }
        
        return await self.update_review(review_id, update_data) 