"""
Score Review Service module.

This module provides business logic for managing score reviews.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select
from datetime import datetime
from decimal import Decimal

from app.repositories.score_review_repository import ScoreReviewRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.repositories.exam_score_history_repository import ExamScoreHistoryRepository
from app.domain.models.score_review import ScoreReview
from app.domain.models.exam_score import ExamScore

logger = logging.getLogger(__name__)

class ScoreReviewService:
    """Service for managing score reviews."""
    
    def __init__(
        self, 
        repository: ScoreReviewRepository, 
        exam_score_repository: ExamScoreRepository,
        history_repository: Optional[ExamScoreHistoryRepository] = None
    ):
        """
        Initialize the ScoreReviewService.
        
        Args:
            repository: ScoreReviewRepository instance
            exam_score_repository: ExamScoreRepository instance
            history_repository: ExamScoreHistoryRepository instance (optional)
        """
        self.repository = repository
        self.exam_score_repository = exam_score_repository
        self.history_repository = history_repository
    
    async def get_all_reviews(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        review_status: Optional[str] = None,
        score_id: Optional[str] = None,
        request_date_from: Optional[str] = None,
        request_date_to: Optional[str] = None,
        review_date_from: Optional[str] = None,
        review_date_to: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all score reviews with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search term for candidate name/code, exam name, or subject name/code
            review_status: Filter by review status
            score_id: Filter by exam score ID
            request_date_from: Filter by request date from
            request_date_to: Filter by request date to
            review_date_from: Filter by review date from
            review_date_to: Filter by review date to
            created_after: Filter by reviews created after date
            created_before: Filter by reviews created before date
            
        Returns:
            Tuple of (list of score reviews, total count)
        """
        filters = {}
        
        if search:
            filters["search"] = search
        if review_status:
            filters["review_status"] = review_status
        if score_id:
            filters["score_id"] = score_id
        if request_date_from:
            filters["request_date_from"] = request_date_from
        if request_date_to:
            filters["request_date_to"] = request_date_to
        if review_date_from:
            filters["review_date_from"] = review_date_from
        if review_date_to:
            filters["review_date_to"] = review_date_to
        if created_after:
            filters["created_after"] = created_after
        if created_before:
            filters["created_before"] = created_before
        
        reviews, total = await self.repository.get_all(skip=skip, limit=limit, filters=filters)
        return reviews, total
    
    async def get_review_by_id(self, score_review_id: str) -> Optional[Dict]:
        """
        Get a score review by ID.
        
        Args:
            score_review_id: The unique identifier of the score review
            
        Returns:
            Score review dict or None if not found
        """
        return await self.repository.get_by_id(score_review_id)
    
    async def get_reviews_by_score_id(self, score_id: str) -> List[Dict]:
        """
        Get all reviews for a specific exam score.
        
        Args:
            score_id: The ID of the exam score
            
        Returns:
            List of score reviews
        """
        return await self.repository.get_by_score_id(score_id)
    
    async def get_reviews_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all reviews related to a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of reviews related to the specified candidate
        """
        return await self.repository.get_by_candidate_id(candidate_id)
    
    async def create_review(self, review_data: Dict) -> Optional[Dict]:
        """
        Create a new score review.
        
        Args:
            review_data: Score review data
            
        Returns:
            Created score review or None if creation failed
        """
        # Validate that the exam score exists
        score_id = review_data.get("score_id")
        if score_id:
            score = await self.exam_score_repository.get_by_id(score_id)
            if not score:
                return None
            
            # Set original_score from the exam score if not provided
            if "original_score" not in review_data and score:
                review_data["original_score"] = score.get("score")
        
        # Set request_date if not provided
        if "request_date" not in review_data:
            review_data["request_date"] = datetime.now().date().isoformat()
        
        # Set initial review_status if not provided
        if "review_status" not in review_data:
            review_data["review_status"] = "pending"
        
        created_review = await self.repository.create(review_data)
        return created_review
    
    async def update_review(self, score_review_id: str, review_data: Dict) -> Optional[Dict]:
        """
        Update a score review.
        
        Args:
            score_review_id: The unique identifier of the score review
            review_data: Updated score review data
            
        Returns:
            Updated score review or None if not found
        """
        return await self.repository.update(score_review_id, review_data)
    
    async def delete_review(self, score_review_id: str) -> bool:
        """
        Delete a score review.
        
        Args:
            score_review_id: The unique identifier of the score review
            
        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(score_review_id)
    
    async def update_review_status(self, score_review_id: str, status: str, resolution_notes: Optional[str] = None) -> Optional[ScoreReview]:
        """
        Update the status of a score review.
        
        Args:
            score_review_id: The unique identifier of the score review
            status: The new status
            resolution_notes: Optional notes about the resolution
            
        Returns:
            The updated score review if found, None otherwise
        """
        update_data = {
            "review_status": status
        }
        
        # Add additional_info if provided
        if resolution_notes:
            update_data["additional_info"] = resolution_notes
        
        # Set review_date for terminal statuses
        if status in ["approved", "rejected", "completed"]:
            update_data["review_date"] = datetime.now().date()
        
        return await self.update_review(score_review_id, update_data)
    
    async def approve_review(self, score_review_id: str, resolution_notes: Optional[str] = None) -> Optional[Dict]:
        """
        Approve a score review and update the associated exam score.
        
        Args:
            score_review_id: The unique identifier of the score review
            resolution_notes: Optional notes about the resolution
            
        Returns:
            Dictionary with the updated review and score information if successful, None otherwise
        """
        # Get the review to check the reviewed score
        review = await self.repository.get_by_id(score_review_id)
        if not review:
            logger.error(f"Score review with ID {score_review_id} not found")
            return None
        
        if not review.get("reviewed_score"):
            logger.error(f"Score review with ID {score_review_id} has no reviewed score")
            return None
        
        # Update the score if exam_score_repository is provided
        updated_score = None
        if self.exam_score_repository:
            score_update = {
                "score": review["reviewed_score"],
                "status": "revised"
            }
            
            # Get original score before update for history tracking
            original_score = await self.exam_score_repository.get_by_id(review["score_id"])
            original_score_value = original_score.get("score") if original_score else None
            
            # Update the exam score
            updated_score = await self.exam_score_repository.update(review["score_id"], score_update)
            
            if not updated_score:
                logger.error(f"Failed to update exam score with ID {review['score_id']}")
                return None
                
            # Create history entry if history repository is available
            if self.history_repository and updated_score:
                # Create a history entry for the score change
                await self.history_repository.create_from_score_change(
                    score_id=review["score_id"],
                    previous_score=original_score_value,
                    new_score=review["reviewed_score"],
                    changed_by=None,  # Could be set from request context if available
                    change_type="REVIEW_APPROVED",
                    reason=resolution_notes or f"Score review {score_review_id} approved",
                    review_id=score_review_id,
                    metadata={
                        "review_status": "approved",
                        "original_score": str(original_score_value) if original_score_value else None,
                        "reviewed_score": str(review["reviewed_score"]) if review["reviewed_score"] else None,
                    }
                )
        
        # Update the review status
        update_data = {
            "review_status": "approved",
            "review_date": datetime.now().date()
        }
        
        if resolution_notes:
            update_data["additional_info"] = resolution_notes
        
        # Update the review
        updated_review = await self.repository.update(score_review_id, update_data)
        
        return {
            "review": updated_review,
            "score": updated_score
        }
    
    async def reject_review(self, score_review_id: str, resolution_notes: str) -> Optional[ScoreReview]:
        """
        Reject a score review.
        
        Args:
            score_review_id: The unique identifier of the score review
            resolution_notes: Notes explaining the rejection reason
            
        Returns:
            The updated score review if found, None otherwise
        """
        update_data = {
            "review_status": "rejected",
            "additional_info": resolution_notes,
            "review_date": datetime.now().date()
        }
        
        return await self.update_review(score_review_id, update_data)
    
    async def complete_review(
        self, 
        score_review_id: str, 
        reviewed_score: float, 
        review_result: str
    ) -> Optional[Dict]:
        """
        Complete a score review and update the associated exam score.
        
        Args:
            score_review_id: The unique identifier of the score review
            reviewed_score: The final reviewed score
            review_result: Result of the review
            
        Returns:
            Dict with updated review and score, or None if not found
        """
        # Get the review
        review = await self.repository.get_by_id(score_review_id)
        if not review:
            return None
        
        # Update the review
        update_data = {
            "review_status": "completed",
            "reviewed_score": Decimal(str(reviewed_score)),
            "review_result": review_result,
            "review_date": datetime.now().date().isoformat()
        }
        
        updated_review = await self.repository.update(score_review_id, update_data)
        if not updated_review:
            return None
        
        # Update the exam score if necessary
        score_id = review.get("score_id")
        if score_id and review_result == "approved":
            score = await self.exam_score_repository.get_by_id(score_id)
            if score:
                # Get the original score value for history tracking
                original_score_value = score.get("score")
                
                # Update the score
                await self.exam_score_repository.update(
                    score_id, 
                    {
                        "score": Decimal(str(reviewed_score)),
                        "last_modified_at": datetime.now().isoformat(),
                        "modified_reason": f"Score updated due to review {score_review_id}"
                    }
                )
                updated_score = await self.exam_score_repository.get_by_id(score_id)
                
                # Create history entry if history repository is available
                if self.history_repository and updated_score:
                    # Create a history entry for the score change
                    await self.history_repository.create_from_score_change(
                        score_id=score_id,
                        previous_score=original_score_value,
                        new_score=reviewed_score,
                        changed_by=None,  # Could be set from request context if available
                        change_type="REVIEW_COMPLETED",
                        reason=f"Score review {score_review_id} completed with result: {review_result}",
                        review_id=score_review_id,
                        metadata={
                            "review_status": "completed",
                            "review_result": review_result,
                            "original_score": str(original_score_value) if original_score_value else None,
                            "reviewed_score": str(reviewed_score)
                        }
                    )
                
                return {"review": updated_review, "score": updated_score}
        
        return {"review": updated_review, "score": None} 