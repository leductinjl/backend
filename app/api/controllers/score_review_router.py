"""
Score Review router module.

This module provides API endpoints for managing score reviews.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path, Body
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date

from app.infrastructure.database.connection import get_db
from app.api.dto.score_review import (
    ScoreReviewCreate,
    ScoreReviewUpdate,
    ScoreReviewResponse,
    ScoreReviewDetailResponse,
    ScoreReviewListResponse,
    ReviewStatus,
    ReviewPriority
)
from app.repositories.score_review_repository import ScoreReviewRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.services.score_review_service import ScoreReviewService

router = APIRouter(
    prefix="/score-reviews",
    tags=["Score Reviews"],
    responses={404: {"description": "Not found"}}
)

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
    return ScoreReviewService(repository, exam_score_repository)

@router.get("/", response_model=ScoreReviewListResponse, summary="List Score Reviews")
async def get_score_reviews(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for candidate name/code, exam name, or subject name/code"),
    status: Optional[ReviewStatus] = Query(None, description="Filter by review status"),
    priority: Optional[ReviewPriority] = Query(None, description="Filter by review priority"),
    score_id: Optional[str] = Query(None, description="Filter by exam score ID"),
    requested_by: Optional[str] = Query(None, description="Filter by user who requested the review"),
    assigned_to: Optional[str] = Query(None, description="Filter by user assigned to the review"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    created_after: Optional[date] = Query(None, description="Filter by reviews created after date"),
    created_before: Optional[date] = Query(None, description="Filter by reviews created before date"),
    resolved_after: Optional[date] = Query(None, description="Filter by reviews resolved after date"),
    resolved_before: Optional[date] = Query(None, description="Filter by reviews resolved before date"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Retrieve a list of score reviews with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        search: Search term for candidate name/code, exam name, or subject name/code
        status: Filter by review status
        priority: Filter by review priority
        score_id: Filter by exam score ID
        requested_by: Filter by user who requested the review
        assigned_to: Filter by user assigned to the review
        candidate_id: Filter by candidate ID
        exam_id: Filter by exam ID
        subject_id: Filter by subject ID
        created_after: Filter by reviews created after date
        created_before: Filter by reviews created before date
        resolved_after: Filter by reviews resolved after date
        resolved_before: Filter by reviews resolved before date
        service: ScoreReviewService instance
        
    Returns:
        List of score reviews
    """
    reviews, total = await service.get_all_reviews(
        skip=skip, 
        limit=limit,
        search=search,
        status=status.value if status else None,
        priority=priority.value if priority else None,
        score_id=score_id,
        requested_by=requested_by,
        assigned_to=assigned_to,
        candidate_id=candidate_id,
        exam_id=exam_id,
        subject_id=subject_id,
        created_after=created_after.isoformat() if created_after else None,
        created_before=created_before.isoformat() if created_before else None,
        resolved_after=resolved_after.isoformat() if resolved_after else None,
        resolved_before=resolved_before.isoformat() if resolved_before else None
    )
    
    return ScoreReviewListResponse(
        items=reviews,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{review_id}", response_model=ScoreReviewDetailResponse, summary="Get Score Review")
async def get_score_review(
    review_id: str = Path(..., description="The unique identifier of the score review"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Retrieve a specific score review by ID.
    
    Args:
        review_id: The unique identifier of the score review
        service: ScoreReviewService instance
        
    Returns:
        The score review if found
        
    Raises:
        HTTPException: If the score review is not found
    """
    review = await service.get_review_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {review_id} not found"
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

@router.get("/requested-by/{user_id}", response_model=List[ScoreReviewResponse], summary="Get Reviews by Requester")
async def get_reviews_by_requester(
    user_id: str = Path(..., description="The ID of the user who requested the reviews"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Retrieve all reviews requested by a specific user.
    
    Args:
        user_id: The ID of the user who requested the reviews
        service: ScoreReviewService instance
        
    Returns:
        List of reviews requested by the specified user
    """
    reviews = await service.get_reviews_by_requested_by(user_id)
    return reviews

@router.get("/assigned-to/{user_id}", response_model=List[ScoreReviewResponse], summary="Get Reviews by Assignee")
async def get_reviews_by_assignee(
    user_id: str = Path(..., description="The ID of the user assigned to the reviews"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Retrieve all reviews assigned to a specific user.
    
    Args:
        user_id: The ID of the user assigned to the reviews
        service: ScoreReviewService instance
        
    Returns:
        List of reviews assigned to the specified user
    """
    reviews = await service.get_reviews_by_assigned_to(user_id)
    return reviews

@router.get("/candidate/{candidate_id}", response_model=List[ScoreReviewResponse], summary="Get Reviews by Candidate")
async def get_reviews_by_candidate(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Retrieve all reviews related to a specific candidate.
    
    Args:
        candidate_id: The ID of the candidate
        service: ScoreReviewService instance
        
    Returns:
        List of reviews related to the specified candidate
    """
    reviews = await service.get_reviews_by_candidate_id(candidate_id)
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

@router.put("/{review_id}", response_model=ScoreReviewResponse, summary="Update Score Review")
async def update_score_review(
    review_id: str = Path(..., description="The unique identifier of the score review"),
    review: ScoreReviewUpdate = None,
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Update a score review.
    
    Args:
        review_id: The unique identifier of the score review
        review: Updated score review data
        service: ScoreReviewService instance
        
    Returns:
        The updated score review
        
    Raises:
        HTTPException: If the score review is not found
    """
    updated_review = await service.update_review(
        review_id, 
        review.model_dump(exclude_unset=True) if review else {}
    )
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {review_id} not found"
        )
    
    return updated_review

@router.patch("/{review_id}", response_model=ScoreReviewResponse, summary="Partially Update Score Review")
async def partially_update_score_review(
    review_id: str = Path(..., description="The unique identifier of the score review"),
    review: ScoreReviewUpdate = None,
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Partially update a score review.
    
    Args:
        review_id: The unique identifier of the score review
        review: Partial score review data
        service: ScoreReviewService instance
        
    Returns:
        The updated score review
        
    Raises:
        HTTPException: If the score review is not found
    """
    updated_review = await service.update_review(
        review_id, 
        review.model_dump(exclude_unset=True, exclude_none=True) if review else {}
    )
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {review_id} not found"
        )
    
    return updated_review

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Score Review")
async def delete_score_review(
    review_id: str = Path(..., description="The unique identifier of the score review"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Delete a score review.
    
    Args:
        review_id: The unique identifier of the score review
        service: ScoreReviewService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the score review is not found
    """
    deleted = await service.delete_review(review_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {review_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{review_id}/assign", response_model=ScoreReviewResponse, summary="Assign Score Review")
async def assign_score_review(
    review_id: str = Path(..., description="The unique identifier of the score review"),
    assigned_to: str = Body(..., embed=True, description="The ID of the user to assign the review to"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Assign a score review to a user.
    
    Args:
        review_id: The unique identifier of the score review
        assigned_to: The ID of the user to assign the review to
        service: ScoreReviewService instance
        
    Returns:
        The updated score review
        
    Raises:
        HTTPException: If the score review is not found
    """
    updated_review = await service.assign_review(review_id, assigned_to)
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {review_id} not found"
        )
    
    return updated_review

@router.patch("/{review_id}/status", response_model=ScoreReviewResponse, summary="Update Review Status")
async def update_review_status(
    review_id: str = Path(..., description="The unique identifier of the score review"),
    status: ReviewStatus = Body(..., embed=True, description="The new status"),
    resolution_notes: Optional[str] = Body(None, embed=True, description="Notes about the resolution"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Update the status of a score review.
    
    Args:
        review_id: The unique identifier of the score review
        status: The new status
        resolution_notes: Notes about the resolution
        service: ScoreReviewService instance
        
    Returns:
        The updated score review
        
    Raises:
        HTTPException: If the score review is not found
    """
    updated_review = await service.update_review_status(review_id, status.value, resolution_notes)
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {review_id} not found"
        )
    
    return updated_review

@router.patch("/{review_id}/approve", response_model=Dict, summary="Approve Review")
async def approve_review(
    review_id: str = Path(..., description="The unique identifier of the score review"),
    resolution_notes: Optional[str] = Body(None, embed=True, description="Notes about the resolution"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Approve a score review and update the associated exam score.
    
    Args:
        review_id: The unique identifier of the score review
        resolution_notes: Notes about the resolution
        service: ScoreReviewService instance
        
    Returns:
        Dictionary with the updated review and score information
        
    Raises:
        HTTPException: If the score review is not found or has no expected score
    """
    result = await service.approve_review(review_id, resolution_notes)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to approve review. Review not found or has no expected score."
        )
    
    return {
        "review": result["review"],
        "score": result["score"],
        "message": "Review approved and score updated successfully."
    }

@router.patch("/{review_id}/reject", response_model=ScoreReviewResponse, summary="Reject Review")
async def reject_review(
    review_id: str = Path(..., description="The unique identifier of the score review"),
    resolution_notes: str = Body(..., embed=True, description="Notes explaining the rejection reason"),
    service: ScoreReviewService = Depends(get_score_review_service)
):
    """
    Reject a score review.
    
    Args:
        review_id: The unique identifier of the score review
        resolution_notes: Notes explaining the rejection reason
        service: ScoreReviewService instance
        
    Returns:
        The updated score review
        
    Raises:
        HTTPException: If the score review is not found
    """
    updated_review = await service.reject_review(review_id, resolution_notes)
    if not updated_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score review with ID {review_id} not found"
        )
    
    return updated_review