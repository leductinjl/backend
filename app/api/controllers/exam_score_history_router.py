"""
Exam Score History router module.

This module provides API endpoints for accessing exam score history entries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.infrastructure.database.connection import get_db
from app.api.dto.exam_score_history import (
    ExamScoreHistoryResponse,
    ExamScoreHistoryDetailResponse,
    ExamScoreHistoryListResponse,
    ChangeType
)
from app.repositories.exam_score_history_repository import ExamScoreHistoryRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.services.exam_score_history_service import ExamScoreHistoryService

router = APIRouter(
    prefix="/exam-score-histories",
    tags=["Exam Score Histories"],
    responses={404: {"description": "Not found"}}
)

async def get_exam_score_history_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ExamScoreHistoryService.
    
    Args:
        db: Database session
        
    Returns:
        ExamScoreHistoryService: Service instance for exam score history business logic
    """
    repository = ExamScoreHistoryRepository(db)
    exam_score_repository = ExamScoreRepository(db)
    return ExamScoreHistoryService(repository, exam_score_repository)

@router.get("/", response_model=ExamScoreHistoryListResponse, summary="List Score History Entries")
async def get_score_history_entries(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for candidate name/code, exam name, or subject name/code"),
    score_id: Optional[str] = Query(None, description="Filter by exam score ID"),
    changed_by: Optional[str] = Query(None, description="Filter by user who made the change"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    created_after: Optional[date] = Query(None, description="Filter by entries created after date"),
    created_before: Optional[date] = Query(None, description="Filter by entries created before date"),
    service: ExamScoreHistoryService = Depends(get_exam_score_history_service)
):
    """
    Retrieve a list of score history entries with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        search: Search term for candidate name/code, exam name, or subject name/code
        score_id: Filter by exam score ID
        changed_by: Filter by user who made the change
        candidate_id: Filter by candidate ID
        exam_id: Filter by exam ID
        subject_id: Filter by subject ID
        created_after: Filter by entries created after date
        created_before: Filter by entries created before date
        service: ExamScoreHistoryService instance
        
    Returns:
        List of score history entries
    """
    entries, total = await service.get_all_history_entries(
        skip=skip, 
        limit=limit,
        search=search,
        score_id=score_id,
        changed_by=changed_by,
        candidate_id=candidate_id,
        exam_id=exam_id,
        subject_id=subject_id,
        created_after=created_after.isoformat() if created_after else None,
        created_before=created_before.isoformat() if created_before else None
    )
    
    return ExamScoreHistoryListResponse(
        items=entries,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{history_id}", response_model=ExamScoreHistoryDetailResponse, summary="Get Score History Entry")
async def get_score_history_entry(
    history_id: str = Path(..., description="The unique identifier of the score history entry"),
    service: ExamScoreHistoryService = Depends(get_exam_score_history_service)
):
    """
    Retrieve a specific score history entry by ID.
    
    Args:
        history_id: The unique identifier of the score history entry
        service: ExamScoreHistoryService instance
        
    Returns:
        The score history entry if found
        
    Raises:
        HTTPException: If the score history entry is not found
    """
    entry = await service.get_history_by_id(history_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score history entry with ID {history_id} not found"
        )
    
    return entry

@router.get("/score/{score_id}", response_model=List[ExamScoreHistoryResponse], summary="Get History by Score ID")
async def get_history_by_score(
    score_id: str = Path(..., description="The ID of the exam score"),
    service: ExamScoreHistoryService = Depends(get_exam_score_history_service)
):
    """
    Retrieve all history entries for a specific exam score.
    
    Args:
        score_id: The ID of the exam score
        service: ExamScoreHistoryService instance
        
    Returns:
        List of history entries for the specified exam score
    """
    entries = await service.get_history_by_score_id(score_id)
    return entries

@router.get("/review/{review_id}", response_model=List[ExamScoreHistoryResponse], summary="Get History by Review ID")
async def get_history_by_review(
    review_id: str = Path(..., description="The ID of the score review"),
    service: ExamScoreHistoryService = Depends(get_exam_score_history_service)
):
    """
    Retrieve all history entries related to a specific score review.
    
    Args:
        review_id: The ID of the score review
        service: ExamScoreHistoryService instance
        
    Returns:
        List of history entries related to the specified score review
    """
    entries = await service.get_history_by_review_id(review_id)
    return entries

@router.get("/candidate/{candidate_id}", response_model=List[ExamScoreHistoryResponse], summary="Get History by Candidate ID")
async def get_history_by_candidate(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    service: ExamScoreHistoryService = Depends(get_exam_score_history_service)
):
    """
    Retrieve all score history entries for a specific candidate.
    
    Args:
        candidate_id: The ID of the candidate
        service: ExamScoreHistoryService instance
        
    Returns:
        List of score history entries for the specified candidate
    """
    entries = await service.get_history_by_candidate_id(candidate_id)
    return entries 