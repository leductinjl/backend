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
    AttemptStatus,
    AttemptResult
)

router = APIRouter(
    prefix="/exam-attempt-history",
    tags=["Exam Attempt History"],
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
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    attempt_number: Optional[int] = Query(None, ge=1, description="Filter by attempt number"),
    status: Optional[AttemptStatus] = Query(None, description="Filter by attempt status"),
    result: Optional[AttemptResult] = Query(None, description="Filter by attempt result"),
    attempt_date_from: Optional[date] = Query(None, description="Filter by minimum attempt date"),
    attempt_date_to: Optional[date] = Query(None, description="Filter by maximum attempt date"),
    attendance_verified_by: Optional[str] = Query(None, description="Filter by user who verified attendance"),
    min_score: Optional[float] = Query(None, ge=0, description="Filter by minimum total score"),
    max_score: Optional[float] = Query(None, description="Filter by maximum total score"),
    sort_field: Optional[str] = Query(None, description="Field to sort by"),
    sort_dir: Optional[str] = Query(None, description="Sort direction ('asc' or 'desc')"),
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
            candidate_id=candidate_id,
            exam_id=exam_id,
            attempt_number=attempt_number,
            status=status.value if status else None,
            result=result.value if result else None,
            attempt_date_from=attempt_date_from,
            attempt_date_to=attempt_date_to,
            attendance_verified_by=attendance_verified_by,
            min_score=min_score,
            max_score=max_score,
            sort_field=sort_field,
            sort_dir=sort_dir
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
    "/{attempt_id}", 
    response_model=ExamAttemptHistoryDetailResponse,
    summary="Get an exam attempt history entry by ID"
)
async def get_exam_attempt_history_by_id(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryDetailResponse:
    """
    Get an exam attempt history entry by its ID.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        
    Returns:
        ExamAttemptHistoryDetailResponse: The exam attempt history entry details
        
    Raises:
        HTTPException: If the attempt history entry is not found
    """
    attempt = await service.get_attempt_by_id(attempt_id)
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam attempt history entry with ID {attempt_id} not found"
        )
    
    return ExamAttemptHistoryDetailResponse(**attempt)

@router.get(
    "/candidate/{candidate_id}", 
    response_model=List[ExamAttemptHistoryDetailResponse],
    summary="Get exam attempt history entries by candidate ID"
)
async def get_exam_attempt_history_by_candidate(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> List[ExamAttemptHistoryDetailResponse]:
    """
    Get all exam attempt history entries for a specific candidate.
    
    Args:
        candidate_id: The ID of the candidate
        
    Returns:
        List[ExamAttemptHistoryDetailResponse]: List of exam attempt history entries
        
    Raises:
        HTTPException: If no attempts are found or there's an error
    """
    attempts = await service.get_attempts_by_candidate_id(candidate_id)
    
    return [ExamAttemptHistoryDetailResponse(**attempt) for attempt in attempts]

@router.get(
    "/exam/{exam_id}", 
    response_model=List[ExamAttemptHistoryDetailResponse],
    summary="Get exam attempt history entries by exam ID"
)
async def get_exam_attempt_history_by_exam(
    exam_id: str = Path(..., description="The ID of the exam"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> List[ExamAttemptHistoryDetailResponse]:
    """
    Get all exam attempt history entries for a specific exam.
    
    Args:
        exam_id: The ID of the exam
        
    Returns:
        List[ExamAttemptHistoryDetailResponse]: List of exam attempt history entries
        
    Raises:
        HTTPException: If no attempts are found or there's an error
    """
    attempts = await service.get_attempts_by_exam_id(exam_id)
    
    return [ExamAttemptHistoryDetailResponse(**attempt) for attempt in attempts]

@router.get(
    "/candidate/{candidate_id}/exam/{exam_id}", 
    response_model=List[ExamAttemptHistoryDetailResponse],
    summary="Get exam attempt history entries by candidate ID and exam ID"
)
async def get_exam_attempt_history_by_candidate_and_exam(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    exam_id: str = Path(..., description="The ID of the exam"),
    attempt_number: Optional[int] = Query(None, ge=1, description="Specific attempt number to retrieve"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> List[ExamAttemptHistoryDetailResponse]:
    """
    Get exam attempt history entries for a specific candidate and exam.
    
    Args:
        candidate_id: The ID of the candidate
        exam_id: The ID of the exam
        attempt_number: Optional specific attempt number to retrieve
        
    Returns:
        List[ExamAttemptHistoryDetailResponse]: List of exam attempt history entries
        
    Raises:
        HTTPException: If no attempts are found or there's an error
    """
    attempts = await service.get_attempts_by_candidate_and_exam(
        candidate_id=candidate_id,
        exam_id=exam_id,
        attempt_number=attempt_number
    )
    
    return [ExamAttemptHistoryDetailResponse(**attempt) for attempt in attempts]

@router.get(
    "/candidate/{candidate_id}/exam/{exam_id}/latest", 
    response_model=ExamAttemptHistoryDetailResponse,
    summary="Get the latest exam attempt history entry for a candidate and exam"
)
async def get_latest_exam_attempt(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    exam_id: str = Path(..., description="The ID of the exam"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryDetailResponse:
    """
    Get the latest exam attempt history entry for a specific candidate and exam.
    
    Args:
        candidate_id: The ID of the candidate
        exam_id: The ID of the exam
        
    Returns:
        ExamAttemptHistoryDetailResponse: The latest exam attempt history entry details
        
    Raises:
        HTTPException: If no attempt is found
    """
    attempt = await service.get_latest_attempt(candidate_id, exam_id)
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No exam attempts found for candidate {candidate_id} and exam {exam_id}"
        )
    
    return ExamAttemptHistoryDetailResponse(**attempt)

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
    Create a new exam attempt history entry after validating the candidate and exam IDs.
    
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
            detail="Failed to create exam attempt history entry. Please check that the candidate and exam exist and that the candidate is registered for the exam."
        )
    
    return ExamAttemptHistoryResponse.model_validate(attempt)

@router.put(
    "/{attempt_id}", 
    response_model=ExamAttemptHistoryResponse,
    summary="Update an exam attempt history entry"
)
async def update_exam_attempt_history(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    attempt_data: ExamAttemptHistoryUpdate = Body(..., description="Updated attempt history data"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Update an existing exam attempt history entry.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        attempt_data: Updated attempt history data
        
    Returns:
        ExamAttemptHistoryResponse: The updated exam attempt history entry
        
    Raises:
        HTTPException: If the entry could not be updated or was not found
    """
    updated_attempt = await service.update_attempt(attempt_id, attempt_data.model_dump(exclude_unset=True))
    
    if not updated_attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam attempt history entry with ID {attempt_id} not found"
        )
    
    return ExamAttemptHistoryResponse.model_validate(updated_attempt)

@router.delete(
    "/{attempt_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an exam attempt history entry"
)
async def delete_exam_attempt_history(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> Response:
    """
    Delete an exam attempt history entry.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        
    Returns:
        Response: Empty response with 204 status code
        
    Raises:
        HTTPException: If the entry could not be deleted or was not found
    """
    success = await service.delete_attempt(attempt_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam attempt history entry with ID {attempt_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/{attempt_id}/check-in",
    response_model=ExamAttemptHistoryResponse,
    summary="Check in a candidate for an exam"
)
async def check_in_candidate(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    check_in_time: Optional[datetime] = Body(None, description="Time of check-in"),
    verified_by: Optional[str] = Body(None, description="ID of the user who verified the check-in"),
    notes: Optional[str] = Body(None, description="Additional notes about the check-in"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Check in a candidate for an exam.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        check_in_time: Time of check-in (defaults to current time)
        verified_by: ID of the user who verified the check-in
        notes: Additional notes about the check-in
        
    Returns:
        ExamAttemptHistoryResponse: The updated exam attempt history entry
        
    Raises:
        HTTPException: If the check-in could not be performed or entry was not found
    """
    updated_attempt = await service.check_in_candidate(
        attempt_id=attempt_id,
        check_in_time=check_in_time,
        verified_by=verified_by,
        notes=notes
    )
    
    if not updated_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not check in candidate. Please check that the attempt exists and is in a valid state."
        )
    
    return ExamAttemptHistoryResponse.model_validate(updated_attempt)

@router.post(
    "/{attempt_id}/start",
    response_model=ExamAttemptHistoryResponse,
    summary="Start an exam for a candidate"
)
async def start_exam(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    start_time: Optional[datetime] = Body(None, description="Time of exam start"),
    notes: Optional[str] = Body(None, description="Additional notes about the exam start"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Start an exam for a candidate.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        start_time: Time of exam start (defaults to current time)
        notes: Additional notes about the exam start
        
    Returns:
        ExamAttemptHistoryResponse: The updated exam attempt history entry
        
    Raises:
        HTTPException: If the exam could not be started or entry was not found
    """
    updated_attempt = await service.start_exam(
        attempt_id=attempt_id,
        start_time=start_time,
        notes=notes
    )
    
    if not updated_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not start exam. Please check that the attempt exists and is in a valid state."
        )
    
    return ExamAttemptHistoryResponse.model_validate(updated_attempt)

@router.post(
    "/{attempt_id}/complete",
    response_model=ExamAttemptHistoryResponse,
    summary="Complete an exam for a candidate"
)
async def complete_exam(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    end_time: Optional[datetime] = Body(None, description="Time of exam completion"),
    notes: Optional[str] = Body(None, description="Additional notes about the exam completion"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Complete an exam for a candidate.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        end_time: Time of exam completion (defaults to current time)
        notes: Additional notes about the exam completion
        
    Returns:
        ExamAttemptHistoryResponse: The updated exam attempt history entry
        
    Raises:
        HTTPException: If the exam could not be completed or entry was not found
    """
    updated_attempt = await service.complete_exam(
        attempt_id=attempt_id,
        end_time=end_time,
        notes=notes
    )
    
    if not updated_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not complete exam. Please check that the attempt exists and is in a valid state."
        )
    
    return ExamAttemptHistoryResponse.model_validate(updated_attempt)

@router.post(
    "/{attempt_id}/absent",
    response_model=ExamAttemptHistoryResponse,
    summary="Mark a candidate as absent for an exam"
)
async def mark_as_absent(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    verified_by: Optional[str] = Body(None, description="ID of the user who verified the absence"),
    notes: Optional[str] = Body(None, description="Additional notes about the absence"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Mark a candidate as absent for an exam.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        verified_by: ID of the user who verified the absence
        notes: Additional notes about the absence
        
    Returns:
        ExamAttemptHistoryResponse: The updated exam attempt history entry
        
    Raises:
        HTTPException: If the candidate could not be marked as absent or entry was not found
    """
    updated_attempt = await service.mark_as_absent(
        attempt_id=attempt_id,
        verified_by=verified_by,
        notes=notes
    )
    
    if not updated_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not mark candidate as absent. Please check that the attempt exists and is in a valid state."
        )
    
    return ExamAttemptHistoryResponse.model_validate(updated_attempt)

@router.post(
    "/{attempt_id}/disqualify",
    response_model=ExamAttemptHistoryResponse,
    summary="Disqualify a candidate from an exam"
)
async def disqualify_candidate(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    disqualification_reason: str = Body(..., description="Reason for disqualification"),
    verified_by: Optional[str] = Body(None, description="ID of the user who verified the disqualification"),
    notes: Optional[str] = Body(None, description="Additional notes about the disqualification"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Disqualify a candidate from an exam.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        disqualification_reason: Reason for disqualification
        verified_by: ID of the user who verified the disqualification
        notes: Additional notes about the disqualification
        
    Returns:
        ExamAttemptHistoryResponse: The updated exam attempt history entry
        
    Raises:
        HTTPException: If the candidate could not be disqualified or entry was not found
    """
    updated_attempt = await service.disqualify_candidate(
        attempt_id=attempt_id,
        disqualification_reason=disqualification_reason,
        verified_by=verified_by,
        notes=notes
    )
    
    if not updated_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not disqualify candidate. Please check that the attempt exists and is in a valid state."
        )
    
    return ExamAttemptHistoryResponse.model_validate(updated_attempt)

@router.post(
    "/{attempt_id}/cancel",
    response_model=ExamAttemptHistoryResponse,
    summary="Cancel an exam attempt"
)
async def cancel_attempt(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    cancellation_reason: str = Body(..., description="Reason for cancellation"),
    notes: Optional[str] = Body(None, description="Additional notes about the cancellation"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Cancel an exam attempt.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        cancellation_reason: Reason for cancellation
        notes: Additional notes about the cancellation
        
    Returns:
        ExamAttemptHistoryResponse: The updated exam attempt history entry
        
    Raises:
        HTTPException: If the attempt could not be cancelled or entry was not found
    """
    updated_attempt = await service.cancel_attempt(
        attempt_id=attempt_id,
        cancellation_reason=cancellation_reason,
        notes=notes
    )
    
    if not updated_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not cancel attempt. Please check that the attempt exists."
        )
    
    return ExamAttemptHistoryResponse.model_validate(updated_attempt)

@router.post(
    "/{attempt_id}/result",
    response_model=ExamAttemptHistoryResponse,
    summary="Update the result of an exam attempt"
)
async def update_attempt_result(
    attempt_id: str = Path(..., description="The ID of the exam attempt history entry"),
    result: AttemptResult = Body(..., description="Result of the attempt"),
    total_score: Optional[float] = Body(None, ge=0, description="Total score achieved in the attempt"),
    notes: Optional[str] = Body(None, description="Additional notes about the result"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Update the result of an exam attempt.
    
    Args:
        attempt_id: The ID of the exam attempt history entry
        result: Result of the attempt (passed, failed, or inconclusive)
        total_score: Total score achieved in the attempt
        notes: Additional notes about the result
        
    Returns:
        ExamAttemptHistoryResponse: The updated exam attempt history entry
        
    Raises:
        HTTPException: If the result could not be updated or entry was not found
    """
    updated_attempt = await service.update_attempt_result(
        attempt_id=attempt_id,
        result=result.value,
        total_score=total_score,
        notes=notes
    )
    
    if not updated_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not update result. Please check that the attempt exists and is in a completed state."
        )
    
    return ExamAttemptHistoryResponse.model_validate(updated_attempt)

@router.post(
    "/register",
    response_model=ExamAttemptHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new attempt for a candidate to take an exam"
)
async def register_new_attempt(
    candidate_id: str = Body(..., description="The ID of the candidate"),
    exam_id: str = Body(..., description="The ID of the exam"),
    attempt_date: date = Body(..., description="Date of the exam attempt"),
    notes: Optional[str] = Body(None, description="Additional notes about the attempt"),
    metadata: Optional[dict] = Body(None, description="Additional metadata for the attempt"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> ExamAttemptHistoryResponse:
    """
    Register a new attempt for a candidate to take an exam.
    
    Args:
        candidate_id: The ID of the candidate
        exam_id: The ID of the exam
        attempt_date: Date of the exam attempt
        notes: Additional notes about the attempt
        metadata: Additional metadata for the attempt
        
    Returns:
        ExamAttemptHistoryResponse: The created exam attempt history entry
        
    Raises:
        HTTPException: If the attempt could not be registered or validation fails
    """
    attempt = await service.register_new_attempt(
        candidate_id=candidate_id,
        exam_id=exam_id,
        attempt_date=attempt_date,
        notes=notes,
        metadata=metadata
    )
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register new attempt. Please check that the candidate and exam exist and that the candidate is registered for the exam."
        )
    
    return ExamAttemptHistoryResponse.model_validate(attempt)

@router.get(
    "/candidate/{candidate_id}/exam/{exam_id}/count",
    response_model=int,
    summary="Get the number of attempts a candidate has made for a specific exam"
)
async def get_candidate_attempt_count(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    exam_id: str = Path(..., description="The ID of the exam"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> int:
    """
    Get the number of attempts a candidate has made for a specific exam.
    
    Args:
        candidate_id: The ID of the candidate
        exam_id: The ID of the exam
        
    Returns:
        int: The number of attempts
    """
    return await service.get_candidate_attempt_count(candidate_id, exam_id)

@router.get(
    "/candidate/{candidate_id}/exam/{exam_id}/has-passed",
    response_model=bool,
    summary="Check if a candidate has passed a specific exam"
)
async def has_passed_exam(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    exam_id: str = Path(..., description="The ID of the exam"),
    service: ExamAttemptHistoryService = Depends(get_exam_attempt_history_service)
) -> bool:
    """
    Check if a candidate has passed a specific exam in any of their attempts.
    
    Args:
        candidate_id: The ID of the candidate
        exam_id: The ID of the exam
        
    Returns:
        bool: True if the candidate has passed the exam, False otherwise
    """
    return await service.has_passed_exam(candidate_id, exam_id) 