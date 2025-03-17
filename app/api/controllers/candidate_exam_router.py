"""
Candidate Exam router module.

This module provides API endpoints for managing candidate exam registrations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path, Body
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.candidate_exam import (
    CandidateExamCreate,
    CandidateExamUpdate,
    CandidateExamResponse,
    CandidateExamDetailResponse,
    CandidateExamListResponse,
    ExamStatus
)
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.exam_repository import ExamRepository
from app.services.candidate_exam_service import CandidateExamService

router = APIRouter(
    prefix="/candidate-exams",
    tags=["Candidate Exams"],
    responses={404: {"description": "Not found"}}
)

async def get_candidate_exam_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for CandidateExamService.
    
    Args:
        db: Database session
        
    Returns:
        CandidateExamService: Service instance for candidate exam registration business logic
    """
    repository = CandidateExamRepository(db)
    candidate_repository = CandidateRepository(db)
    exam_repository = ExamRepository(db)
    return CandidateExamService(
        repository, 
        candidate_repository, 
        exam_repository
    )

@router.get("/", response_model=CandidateExamListResponse, summary="List Candidate Exam Registrations")
async def get_candidate_exam_registrations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for candidate name or exam name"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    status: Optional[ExamStatus] = Query(None, description="Filter by status (Registered, Attended, Absent)"),
    service: CandidateExamService = Depends(get_candidate_exam_service)
):
    """
    Retrieve a list of candidate exam registrations with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        search: Search term for candidate name or exam name
        candidate_id: Filter by candidate ID
        exam_id: Filter by exam ID
        status: Filter by status
        service: CandidateExamService instance
        
    Returns:
        List of candidate exam registrations
    """
    registrations, total = await service.get_all_registrations(
        skip=skip, 
        limit=limit,
        search=search,
        candidate_id=candidate_id,
        exam_id=exam_id,
        status=status.value if status else None
    )
    
    return CandidateExamListResponse(
        items=registrations,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{candidate_exam_id}", response_model=CandidateExamDetailResponse, summary="Get Candidate Exam Registration")
async def get_candidate_exam_registration(
    candidate_exam_id: str = Path(..., description="The unique identifier of the candidate exam registration"),
    service: CandidateExamService = Depends(get_candidate_exam_service)
):
    """
    Retrieve a specific candidate exam registration by ID.
    
    Args:
        candidate_exam_id: The unique identifier of the candidate exam registration
        service: CandidateExamService instance
        
    Returns:
        The candidate exam registration if found
        
    Raises:
        HTTPException: If the candidate exam registration is not found
    """
    registration = await service.get_registration_by_id(candidate_exam_id)
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam registration with ID {candidate_exam_id} not found"
        )
    
    return registration

@router.get("/candidate/{candidate_id}", response_model=List[CandidateExamResponse], summary="Get Candidate's Exam Registrations")
async def get_candidate_exam_registrations_by_candidate(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    service: CandidateExamService = Depends(get_candidate_exam_service)
):
    """
    Retrieve all exam registrations for a specific candidate.
    
    Args:
        candidate_id: The ID of the candidate
        service: CandidateExamService instance
        
    Returns:
        List of exam registrations for the specified candidate
    """
    registrations = await service.get_registrations_by_candidate_id(candidate_id)
    return registrations

@router.get("/exam/{exam_id}", response_model=List[CandidateExamResponse], summary="Get Exam's Candidate Registrations")
async def get_candidate_exam_registrations_by_exam(
    exam_id: str = Path(..., description="The ID of the exam"),
    service: CandidateExamService = Depends(get_candidate_exam_service)
):
    """
    Retrieve all candidate registrations for a specific exam.
    
    Args:
        exam_id: The ID of the exam
        service: CandidateExamService instance
        
    Returns:
        List of candidate registrations for the specified exam
    """
    registrations = await service.get_registrations_by_exam_id(exam_id)
    return registrations

@router.post(
    "/", 
    response_model=CandidateExamResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Candidate Exam Registration"
)
async def create_candidate_exam_registration(
    registration: CandidateExamCreate,
    service: CandidateExamService = Depends(get_candidate_exam_service)
):
    """
    Create a new candidate exam registration.
    
    Args:
        registration: Candidate exam registration data
        service: CandidateExamService instance
        
    Returns:
        The created candidate exam registration
        
    Raises:
        HTTPException: If the candidate or exam doesn't exist, or if a registration already exists
    """
    new_registration = await service.create_registration(registration.model_dump())
    if not new_registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create candidate exam registration. Candidate or exam may not exist, or a registration already exists."
        )
    
    return new_registration

@router.put("/{candidate_exam_id}", response_model=CandidateExamResponse, summary="Update Candidate Exam Registration")
async def update_candidate_exam_registration(
    candidate_exam_id: str = Path(..., description="The unique identifier of the candidate exam registration"),
    registration: CandidateExamUpdate = None,
    service: CandidateExamService = Depends(get_candidate_exam_service)
):
    """
    Update a candidate exam registration.
    
    Args:
        candidate_exam_id: The unique identifier of the candidate exam registration
        registration: Updated candidate exam registration data
        service: CandidateExamService instance
        
    Returns:
        The updated candidate exam registration
        
    Raises:
        HTTPException: If the candidate exam registration is not found
    """
    updated_registration = await service.update_registration(
        candidate_exam_id, 
        registration.model_dump(exclude_unset=True) if registration else {}
    )
    if not updated_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam registration with ID {candidate_exam_id} not found"
        )
    
    return updated_registration

@router.patch("/{candidate_exam_id}", response_model=CandidateExamResponse, summary="Partially Update Candidate Exam Registration")
async def partially_update_candidate_exam_registration(
    candidate_exam_id: str = Path(..., description="The unique identifier of the candidate exam registration"),
    registration: CandidateExamUpdate = None,
    service: CandidateExamService = Depends(get_candidate_exam_service)
):
    """
    Partially update a candidate exam registration.
    
    Args:
        candidate_exam_id: The unique identifier of the candidate exam registration
        registration: Partial candidate exam registration data
        service: CandidateExamService instance
        
    Returns:
        The updated candidate exam registration
        
    Raises:
        HTTPException: If the candidate exam registration is not found
    """
    updated_registration = await service.update_registration(
        candidate_exam_id, 
        registration.model_dump(exclude_unset=True, exclude_none=True) if registration else {}
    )
    if not updated_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam registration with ID {candidate_exam_id} not found"
        )
    
    return updated_registration

@router.delete("/{candidate_exam_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Candidate Exam Registration")
async def delete_candidate_exam_registration(
    candidate_exam_id: str = Path(..., description="The unique identifier of the candidate exam registration"),
    service: CandidateExamService = Depends(get_candidate_exam_service)
):
    """
    Delete a candidate exam registration.
    
    Args:
        candidate_exam_id: The unique identifier of the candidate exam registration
        service: CandidateExamService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the candidate exam registration is not found
    """
    deleted = await service.delete_registration(candidate_exam_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam registration with ID {candidate_exam_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{candidate_exam_id}/status", response_model=CandidateExamResponse, summary="Update Registration Status")
async def update_registration_status(
    candidate_exam_id: str = Path(..., description="The unique identifier of the candidate exam registration"),
    status: ExamStatus = Body(..., embed=True, description="The new status"),
    service: CandidateExamService = Depends(get_candidate_exam_service)
):
    """
    Update status for a candidate's exam registration.
    
    Args:
        candidate_exam_id: The unique identifier of the candidate exam registration
        status: The new status
        service: CandidateExamService instance
        
    Returns:
        The updated candidate exam registration
        
    Raises:
        HTTPException: If the candidate exam registration is not found
    """
    updated_registration = await service.update_status(
        candidate_exam_id, 
        status.value
    )
    if not updated_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam registration with ID {candidate_exam_id} not found"
        )
    
    return updated_registration