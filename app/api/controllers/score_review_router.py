"""
Score Review router module.

This module provides API endpoints for managing score reviews.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path, Body
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
import logging

from app.infrastructure.database.connection import get_db
from app.api.dto.score_review import (
    ScoreReviewCreate,
    ScoreReviewUpdate,
    ScoreReviewResponse,
    ScoreReviewDetailResponse,
    ScoreReviewListResponse
)
from app.repositories.score_review_repository import ScoreReviewRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.repositories.exam_score_history_repository import ExamScoreHistoryRepository
from app.services.score_review_service import ScoreReviewService

router = APIRouter(
    prefix="/score-reviews",
    tags=["Score Reviews"],
    responses={404: {"description": "Not found"}}
)

logger = logging.getLogger(__name__)

async def get_score_review_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ScoreReviewService.
    
    Args:
        db: Database session
        
    Returns:
        ScoreReviewService: Service instance for score review business logic
    """
    repository = ScoreReviewRepository(db)
    exam_score_repository = ExamScoreRepository(db)
    history_repository = ExamScoreHistoryRepository(db)
    return ScoreReviewService(repository, exam_score_repository, history_repository)

@router.get("/", response_model=ScoreReviewListResponse, summary="List Score Reviews")
async def get_score_reviews(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for candidate name/code, exam name, or subject name/code"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    score_id: Optional[str] = Query(None, description="Filter by exam score ID"),
    request_date_from: Optional[date] = Query(None, description="Filter by request date from"),
    request_date_to: Optional[date] = Query(None, description="Filter by request date to"),
    review_date_from: Optional[date] = Query(None, description="Filter by review date from"),
    review_date_to: Optional[date] = Query(None, description="Filter by review date to"),
    created_after: Optional[date] = Query(None, description="Filter by reviews created after date"),
    created_before: Optional[date] = Query(None, description="Filter by reviews created before date"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Retrieve a list of score reviews with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
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
        service: ScoreReviewService instance
        
    Returns:
        List of score reviews
    """
    reviews, total = await service.get_all_reviews(
        skip=skip, 
        limit=limit,
        search=search,
        review_status=review_status,
        score_id=score_id,
        request_date_from=request_date_from.isoformat() if request_date_from else None,
        request_date_to=request_date_to.isoformat() if request_date_to else None,
        review_date_from=review_date_from.isoformat() if review_date_from else None,
        review_date_to=review_date_to.isoformat() if review_date_to else None,
        created_after=created_after.isoformat() if created_after else None,
        created_before=created_before.isoformat() if created_before else None
    )
    
    return ScoreReviewListResponse(
        items=reviews,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{score_review_id}", response_model=ScoreReviewDetailResponse, summary="Get Score Review")
async def get_score_review(
    score_review_id: str = Path(..., description="The unique identifier of the score review"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Retrieve a specific score review by ID.
    
    Args:
        score_review_id: The unique identifier of the score review
        service: ScoreReviewService instance
        
    Returns:
        The score review if found
        
    Raises:
        HTTPException: If the score review is not found
    """
    review = await service.get_review_by_id(score_review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {score_review_id} not found"
        )
    
    return review

@router.get("/score/{score_id}", response_model=List[ScoreReviewResponse], summary="Get Reviews by Score ID")
async def get_reviews_by_score(
    score_id: str = Path(..., description="The ID of the exam score"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Retrieve all reviews for a specific exam score.
    
    Args:
        score_id: The ID of the exam score
        service: ScoreReviewService instance
        
    Returns:
        List of reviews for the specified exam score
    """
    reviews = await service.get_reviews_by_score_id(score_id)
    return reviews

@router.post(
    "/", 
    response_model=ScoreReviewResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Score Review"
)
async def create_score_review(
    review: ScoreReviewCreate,
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Create a new score review.
    
    Args:
        review: Score review data
        service: ScoreReviewService instance
        
    Returns:
        The created score review
        
    Raises:
        HTTPException: If the exam score doesn't exist
    """
    new_review = await service.create_review(review.model_dump())
    if not new_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create score review. Exam score may not exist."
        )
    
    return new_review

@router.put("/{score_review_id}", response_model=ScoreReviewResponse, summary="Update Score Review")
async def update_score_review(
    score_review_id: str = Path(..., description="The unique identifier of the score review"),
    review: ScoreReviewUpdate = None,
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Update a score review.
    
    Args:
        score_review_id: The unique identifier of the score review
        review: Updated score review data
        service: ScoreReviewService instance
        
    Returns:
        The updated score review
        
    Raises:
        HTTPException: If the score review is not found
    """
    updated_review = await service.update_review(
        score_review_id, 
        review.model_dump(exclude_unset=True) if review else {}
    )
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {score_review_id} not found"
        )
    
    return updated_review

@router.patch("/{score_review_id}", response_model=ScoreReviewResponse, summary="Partially Update Score Review")
async def partially_update_score_review(
    score_review_id: str = Path(..., description="The unique identifier of the score review"),
    review: ScoreReviewUpdate = None,
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Partially update a score review.
    
    Args:
        score_review_id: The unique identifier of the score review
        review: Partial score review data
        service: ScoreReviewService instance
        
    Returns:
        The updated score review
        
    Raises:
        HTTPException: If the score review is not found
    """
    updated_review = await service.update_review(
        score_review_id, 
        review.model_dump(exclude_unset=True, exclude_none=True) if review else {}
    )
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {score_review_id} not found"
        )
    
    return updated_review

@router.delete("/{score_review_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Score Review")
async def delete_score_review(
    score_review_id: str = Path(..., description="The unique identifier of the score review"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Delete a score review.
    
    Args:
        score_review_id: The unique identifier of the score review
        service: ScoreReviewService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the score review is not found
    """
    deleted = await service.delete_review(score_review_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {score_review_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{score_review_id}/status", response_model=ScoreReviewResponse, summary="Update Review Status")
async def update_review_status(
    score_review_id: str = Path(..., description="The unique identifier of the score review"),
    review_status: str = Body(..., embed=True, description="The new status"),
    review_result: Optional[str] = Body(None, embed=True, description="Result of the review"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Update the status of a score review.
    
    Args:
        score_review_id: The unique identifier of the score review
        review_status: The new status
        review_result: Result of the review
        service: ScoreReviewService instance
        
    Returns:
        The updated score review
        
    Raises:
        HTTPException: If the score review is not found
    """
    update_data = {
        "review_status": review_status,
    }
    
    if review_result:
        update_data["review_result"] = review_result
    
    # Set review_date for completed reviews
    if review_status in ["approved", "rejected", "completed"]:
        update_data["review_date"] = date.today()
    
    updated_review = await service.update_review(score_review_id, update_data)
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {score_review_id} not found"
        )
    
    return updated_review

@router.patch("/{score_review_id}/complete", response_model=Dict, summary="Complete Review")
async def complete_review(
    score_review_id: str = Path(..., description="The unique identifier of the score review"),
    reviewed_score: float = Body(..., embed=True, description="The final reviewed score"),
    review_result: str = Body(..., embed=True, description="Result of the review"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Complete a score review and update the associated exam score.
    
    Args:
        score_review_id: The unique identifier of the score review
        reviewed_score: The final reviewed score
        review_result: Result of the review
        service: ScoreReviewService instance
        
    Returns:
        Dictionary with the updated review and score information
        
    Raises:
        HTTPException: If the score review is not found
    """
    logger.info(f"Completing review {score_review_id} with score {reviewed_score} and result {review_result}")
    
    result = await service.complete_review(score_review_id, reviewed_score, review_result)
    if not result:
        logger.error(f"Failed to complete review {score_review_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to complete review. Review not found."
        )
    
    logger.info(f"Review {score_review_id} completed successfully")
    
    # Extract score_id safely from the result
    score_id = None
    if isinstance(result, dict) and "review" in result:
        review = result["review"]
        if hasattr(review, "score_id"):
            score_id = review.score_id
        elif isinstance(review, dict) and "score_id" in review:
            score_id = review["score_id"]
    
    return {
        "message": "Review completed and score updated successfully.",
        "review_id": score_review_id,
        "score_id": score_id,
        "reviewed_score": float(reviewed_score) if reviewed_score else None,
        "status": "completed"
    }