"""
Exam Attempt History router module.

This module provides API endpoints for managing exam attempt history records,
including creating, retrieving, updating, and deleting attempt history entries,
as well as special actions like checking in candidates and updating attempt statuses.
"""

from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.services.exam_attempt_history_service import ExamAttemptHistoryService
from app.repositories.exam_attempt_history_repository import ExamAttemptHistoryRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.api.dto.exam_attempt_history import (
    ExamAttemptHistoryCreate,
    ExamAttemptHistoryUpdate, 
    ExamAttemptHistoryResponse,
    ExamAttemptHistoryDetailResponse,
    ExamAttemptHistoryListResponse,
    RegisterAttemptRequest
)

router = APIRouter(
    prefix="/exam-attempt-histories",
    tags=["Attempt Histories"],
    responses={404: {"description": "Not found"}},
)

async def get_exam_attempt_history_service(
    db: AsyncSession = Depends(get_db)
) -> ExamAttemptHistoryService:
    """
    Dependency for providing ExamAttemptHistoryService instance.
    
    Args:
        db: Database session
        
    Returns:
        ExamAttemptHistoryService instance
    """
    return ExamAttemptHistoryService(
        repository=ExamAttemptHistoryRepository(db),
        candidate_repository=CandidateRepository(db),
        exam_repository=ExamRepository(db),
        candidate_exam_repository=CandidateExamRepository(db),
        exam_score_repository=ExamScoreRepository(db)
    )

@router.get(
    "/", 
    response_model=ExamAttemptHistoryListResponse,
    summary="List exam attempt history entries"
)
async def get_exam_attempt_history(
    skip: int = Query(0, ge=0, description="Skip first N records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of records returned"),
    search: Optional[str] = Query(None, description="Search term for filtering"),
    candidate_exam_id: Optional[str] = Query(None, description="Filter by candidate exam ID"),
    attempt_number: Optional[int] = Query(None, ge=1, description="Filter by attempt number"),
    result: Optional[str] = Query(None, description="Filter by attempt result"),
    attempt_date_from: Optional[date] = Query(None, description="Filter by minimum attempt date"),
    attempt_date_to: Optional[date] = Query(None, description="Filter by maximum attempt date"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryListResponse:
    """
    List exam attempt history entries with pagination and optional filtering.
    
    Returns:
        ExamAttemptHistoryListResponse: Object containing list of exam attempts and pagination information
    
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        attempts, total = await service.get_all_attempts(
            skip=skip,
            limit=limit,
            search=search,
            candidate_exam_id=candidate_exam_id,
            attempt_number=attempt_number,
            result=result,
            attempt_date_from=attempt_date_from,
            attempt_date_to=attempt_date_to
        )
        
        return ExamAttemptHistoryListResponse(
            items=[ExamAttemptHistoryDetailResponse(**attempt) for attempt in attempts],
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            size=limit,
            pages=(total + limit - 1) // limit if limit > 0 else 1
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve exam attempt history entries: {str(e)}"
        )

@router.get(
    "/{attempt_history_id}", 
    response_model=ExamAttemptHistoryDetailResponse,
    summary="Get an exam attempt history entry by ID"
)
async def get_exam_attempt_history_by_id(
    attempt_history_id: str = Path(..., description="The ID of the exam attempt history entry"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryDetailResponse:
    """
    Get an exam attempt history entry by its ID.
    
    Args:
        attempt_history_id: The ID of the exam attempt history entry
        
    Returns:
        ExamAttemptHistoryDetailResponse: The exam attempt history entry details
        
    Raises:
        HTTPException: If the attempt history entry is not found
    """
    attempt = await service.get_attempt_by_id(attempt_history_id)
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam attempt history entry with ID {attempt_history_id} not found"
        )
    
    return ExamAttemptHistoryDetailResponse(**attempt)

@router.get(
    "/candidate-exam/{candidate_exam_id}", 
    response_model=List[ExamAttemptHistoryDetailResponse],
    summary="Get exam attempt history entries by candidate exam ID"
)
async def get_exam_attempt_history_by_candidate_exam(
    candidate_exam_id: str = Path(..., description="The ID of the candidate exam relationship"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> List[ExamAttemptHistoryDetailResponse]:
    """
    Get all exam attempt history entries for a specific candidate exam.
    
    Args:
        candidate_exam_id: The ID of the candidate exam relationship
        
    Returns:
        List[ExamAttemptHistoryDetailResponse]: List of exam attempt history entries
        
    Raises:
        HTTPException: If no attempts are found or there's an error
    """
    attempts = await service.get_attempts_by_candidate_exam_id(candidate_exam_id)
    
    return [ExamAttemptHistoryDetailResponse(**attempt) for attempt in attempts]

@router.post(
    "/", 
    response_model=ExamAttemptHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new exam attempt history entry"
)
async def create_exam_attempt_history(
    attempt_data: ExamAttemptHistoryCreate,
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Create a new exam attempt history entry.
    
    Args:
        attempt_data: Data for creating a new exam attempt history entry
        
    Returns:
        ExamAttemptHistoryResponse: The created exam attempt history entry
        
    Raises:
        HTTPException: If the entry could not be created or validation fails
    """
    attempt = await service.create_attempt(attempt_data.model_dump())
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create exam attempt history entry"
        )
    
    return ExamAttemptHistoryResponse.model_validate(attempt)

@router.put(
    "/{attempt_history_id}", 
    response_model=ExamAttemptHistoryResponse,
    summary="Update an exam attempt history entry"
)
async def update_exam_attempt_history(
    attempt_history_id: str = Path(..., description="The ID of the exam attempt history entry"),
    attempt_data: ExamAttemptHistoryUpdate = Body(..., description="Updated attempt history data"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Update an existing exam attempt history entry.
    
    Args:
        attempt_history_id: The ID of the exam attempt history entry
        attempt_data: Updated attempt history data
        
    Returns:
        ExamAttemptHistoryResponse: The updated exam attempt history entry
        
    Raises:
        HTTPException: If the entry could not be updated or was not found
    """
    updated_attempt = await service.update_attempt(attempt_history_id, attempt_data.model_dump(exclude_unset=True))
    
    if not updated_attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam attempt history entry with ID {attempt_history_id} not found"
        )
    
    return ExamAttemptHistoryResponse.model_validate(updated_attempt)

@router.delete(
    "/{attempt_history_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an exam attempt history entry"
)
async def delete_exam_attempt_history(
    attempt_history_id: str = Path(..., description="The ID of the exam attempt history entry"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> Response:
    """
    Delete an exam attempt history entry.
    
    Args:
        attempt_history_id: The ID of the exam attempt history entry
        
    Returns:
        Response: Empty response with 204 status code
        
    Raises:
        HTTPException: If the entry could not be deleted or was not found
    """
    success = await service.delete_attempt(attempt_history_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam attempt history entry with ID {attempt_history_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/register",
    response_model=ExamAttemptHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new attempt"
)
async def register_new_attempt(
    attempt_data: RegisterAttemptRequest,
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Register a new attempt for a candidate exam.
    
    Args:
        attempt_data: Data for registering a new attempt
        
    Returns:
        ExamAttemptHistoryResponse: The created exam attempt history entry
    """
    attempt = await service.register_new_attempt(
        candidate_exam_id=attempt_data.candidate_exam_id,
        attempt_date=attempt_data.attempt_date,
        notes=attempt_data.notes
    )
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register new attempt"
        )
    
    return ExamAttemptHistoryResponse.model_validate(attempt) 