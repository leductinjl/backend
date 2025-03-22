"""
Candidate Exam Subject router module.

This module provides API endpoints for managing candidate-exam-subject registrations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.candidate_exam_subject import (
    CandidateExamSubjectCreate,
    CandidateExamSubjectUpdate,
    CandidateExamSubjectResponse,
    CandidateExamSubjectDetailResponse,
    CandidateExamSubjectListResponse,
    RegistrationStatusEnum
)
from app.repositories.candidate_exam_subject_repository import CandidateExamSubjectRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.repositories.exam_subject_repository import ExamSubjectRepository
from app.services.candidate_exam_subject_service import CandidateExamSubjectService

router = APIRouter(
    prefix="/candidate-exam-subjects",
    tags=["Candidate Exam Subjects"],
    responses={404: {"description": "Not found"}}
)

async def get_candidate_exam_subject_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for CandidateExamSubjectService.
    
    Args:
        db: Database session
        
    Returns:
        CandidateExamSubjectService: Service instance for candidate exam subject registration business logic
    """
    repository = CandidateExamSubjectRepository(db)
    candidate_exam_repository = CandidateExamRepository(db)
    exam_subject_repository = ExamSubjectRepository(db)
    return CandidateExamSubjectService(
        repository, 
        candidate_exam_repository, 
        exam_subject_repository
    )

@router.get("/", response_model=CandidateExamSubjectListResponse, summary="List Candidate Exam Subject Registrations")
async def get_candidate_exam_subject_registrations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    candidate_exam_id: Optional[str] = Query(None, description="Filter by candidate exam ID"),
    exam_subject_id: Optional[str] = Query(None, description="Filter by exam subject ID"),
    status: Optional[RegistrationStatusEnum] = Query(None, description="Filter by registration status"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Retrieve a list of candidate exam subject registrations with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        candidate_id: Filter by candidate ID
        exam_id: Filter by exam ID
        subject_id: Filter by subject ID
        candidate_exam_id: Filter by candidate exam ID
        exam_subject_id: Filter by exam subject ID
        status: Filter by status
        service: CandidateExamSubjectService instance
        
    Returns:
        List of candidate exam subject registrations
    """
    registrations, total = await service.get_all_registrations(
        skip=skip, 
        limit=limit,
        candidate_id=candidate_id,
        exam_id=exam_id,
        subject_id=subject_id,
        candidate_exam_id=candidate_exam_id,
        exam_subject_id=exam_subject_id,
        status=status.value if status else None
    )
    
    return CandidateExamSubjectListResponse(
        items=registrations,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{candidate_exam_subject_id}", response_model=CandidateExamSubjectDetailResponse, summary="Get Candidate Exam Subject Registration")
async def get_candidate_exam_subject_registration(
    candidate_exam_subject_id: str = Path(..., description="The unique identifier of the candidate exam subject registration"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Retrieve a specific candidate exam subject registration by ID.
    
    Args:
        candidate_exam_subject_id: The unique identifier of the candidate exam subject registration
        service: CandidateExamSubjectService instance
        
    Returns:
        The candidate exam subject registration if found
        
    Raises:
        HTTPException: If the candidate exam subject registration is not found
    """
    registration = await service.get_registration_by_id(candidate_exam_subject_id)
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam subject registration with ID {candidate_exam_subject_id} not found"
        )
    
    return registration

@router.get("/candidate/{candidate_id}", response_model=CandidateExamSubjectListResponse, summary="Get Candidate's Exam Subject Registrations")
async def get_candidate_exam_subject_registrations_by_candidate(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Retrieve all exam subject registrations for a specific candidate.
    
    Args:
        candidate_id: The ID of the candidate
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: CandidateExamSubjectService instance
        
    Returns:
        List of exam subject registrations for the specified candidate
    """
    registrations, total = await service.get_registrations_by_candidate(
        candidate_id=candidate_id,
        skip=skip,
        limit=limit
    )
    
    return CandidateExamSubjectListResponse(
        items=registrations,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/candidate-exam/{candidate_exam_id}", response_model=CandidateExamSubjectListResponse, summary="Get Candidate Exam's Subject Registrations")
async def get_candidate_exam_subject_registrations_by_candidate_exam(
    candidate_exam_id: str = Path(..., description="The ID of the candidate exam"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Retrieve all subject registrations for a specific candidate exam.
    
    Args:
        candidate_exam_id: The ID of the candidate exam
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: CandidateExamSubjectService instance
        
    Returns:
        List of subject registrations for the specified candidate exam
    """
    registrations, total = await service.get_registrations_by_candidate_exam(
        candidate_exam_id=candidate_exam_id,
        skip=skip,
        limit=limit
    )
    
    return CandidateExamSubjectListResponse(
        items=registrations,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/exam-subject/{exam_subject_id}", response_model=CandidateExamSubjectListResponse, summary="Get Exam Subject's Candidate Registrations")
async def get_candidate_exam_subject_registrations_by_exam_subject(
    exam_subject_id: str = Path(..., description="The ID of the exam subject"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Retrieve all candidate registrations for a specific exam subject.
    
    Args:
        exam_subject_id: The ID of the exam subject
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: CandidateExamSubjectService instance
        
    Returns:
        List of candidate registrations for the specified exam subject
    """
    registrations, total = await service.get_registrations_by_exam_subject(
        exam_subject_id=exam_subject_id,
        skip=skip,
        limit=limit
    )
    
    return CandidateExamSubjectListResponse(
        items=registrations,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/candidate/{candidate_id}/schedule", summary="Get Candidate's Exam Schedule")
async def get_candidate_exam_schedule(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Retrieve the complete exam schedule for a candidate with room and location details.
    
    Args:
        candidate_id: The ID of the candidate
        service: CandidateExamSubjectService instance
        
    Returns:
        Complete exam schedule information for the candidate
    """
    schedule = await service.get_candidate_exam_schedule(candidate_id)
    return schedule

@router.get("/candidate/{candidate_id}/scores", summary="Get Candidate's Exam Scores")
async def get_candidate_exam_scores(
    candidate_id: str = Path(..., description="The ID of the candidate"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Retrieve all exam scores for a candidate with optional filtering by exam and subject.
    
    Args:
        candidate_id: The ID of the candidate
        exam_id: Optional ID of the exam to filter by
        subject_id: Optional ID of the subject to filter by
        service: CandidateExamSubjectService instance
        
    Returns:
        Exam score information for the candidate
    """
    scores = await service.get_candidate_exam_scores(
        candidate_id=candidate_id,
        exam_id=exam_id,
        subject_id=subject_id
    )
    return scores

@router.post(
    "/", 
    response_model=CandidateExamSubjectResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Candidate Exam Subject Registration"
)
async def create_candidate_exam_subject_registration(
    registration: CandidateExamSubjectCreate,
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Create a new candidate exam subject registration.
    
    Args:
        registration: Candidate exam subject registration data
        service: CandidateExamSubjectService instance
        
    Returns:
        The created candidate exam subject registration
        
    Raises:
        HTTPException: If the candidate exam or exam subject doesn't exist
    """
    new_registration = await service.create_registration(registration.model_dump())
    if not new_registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create candidate exam subject registration. Candidate exam or exam subject may not exist."
        )
    
    return new_registration

@router.put("/{candidate_exam_subject_id}", response_model=CandidateExamSubjectResponse, summary="Update Candidate Exam Subject Registration")
async def update_candidate_exam_subject_registration(
    candidate_exam_subject_id: str = Path(..., description="The unique identifier of the candidate exam subject registration"),
    registration: CandidateExamSubjectUpdate = None,
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Update a candidate exam subject registration.
    
    Args:
        candidate_exam_subject_id: The unique identifier of the candidate exam subject registration
        registration: Updated candidate exam subject registration data
        service: CandidateExamSubjectService instance
        
    Returns:
        The updated candidate exam subject registration
        
    Raises:
        HTTPException: If the candidate exam subject registration is not found
    """
    updated_registration = await service.update_registration(
        candidate_exam_subject_id, 
        registration.model_dump(exclude_unset=True) if registration else {}
    )
    if not updated_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam subject registration with ID {candidate_exam_subject_id} not found"
        )
    
    return updated_registration

@router.patch("/{candidate_exam_subject_id}", response_model=CandidateExamSubjectResponse, summary="Partially Update Candidate Exam Subject Registration")
async def partially_update_candidate_exam_subject_registration(
    candidate_exam_subject_id: str = Path(..., description="The unique identifier of the candidate exam subject registration"),
    registration: CandidateExamSubjectUpdate = None,
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Partially update a candidate exam subject registration.
    
    Args:
        candidate_exam_subject_id: The unique identifier of the candidate exam subject registration
        registration: Partial candidate exam subject registration data
        service: CandidateExamSubjectService instance
        
    Returns:
        The updated candidate exam subject registration
        
    Raises:
        HTTPException: If the candidate exam subject registration is not found
    """
    updated_registration = await service.update_registration(
        candidate_exam_subject_id, 
        registration.model_dump(exclude_unset=True, exclude_none=True) if registration else {}
    )
    if not updated_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam subject registration with ID {candidate_exam_subject_id} not found"
        )
    
    return updated_registration

@router.delete("/{candidate_exam_subject_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Candidate Exam Subject Registration")
async def delete_candidate_exam_subject_registration(
    candidate_exam_subject_id: str = Path(..., description="The unique identifier of the candidate exam subject registration"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Delete a candidate exam subject registration.
    
    Args:
        candidate_exam_subject_id: The unique identifier of the candidate exam subject registration
        service: CandidateExamSubjectService instance
        
    Raises:
        HTTPException: If the candidate exam subject registration is not found
    """
    deleted = await service.delete_registration(candidate_exam_subject_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam subject registration with ID {candidate_exam_subject_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{candidate_exam_subject_id}/confirm", response_model=CandidateExamSubjectResponse, summary="Confirm Candidate Exam Subject Registration")
async def confirm_candidate_exam_subject_registration(
    candidate_exam_subject_id: str = Path(..., description="The unique identifier of the candidate exam subject registration"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Confirm a candidate's registration for an exam subject.
    
    Args:
        candidate_exam_subject_id: The unique identifier of the candidate exam subject registration
        service: CandidateExamSubjectService instance
        
    Returns:
        The updated candidate exam subject registration
        
    Raises:
        HTTPException: If the candidate exam subject registration is not found
    """
    updated_registration = await service.confirm_registration(candidate_exam_subject_id)
    if not updated_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam subject registration with ID {candidate_exam_subject_id} not found"
        )
    
    return updated_registration

@router.post("/{candidate_exam_subject_id}/withdraw", response_model=CandidateExamSubjectResponse, summary="Withdraw Candidate Exam Subject Registration")
async def withdraw_candidate_exam_subject_registration(
    candidate_exam_subject_id: str = Path(..., description="The unique identifier of the candidate exam subject registration"),
    reason: Optional[str] = Query(None, description="Reason for withdrawal"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Withdraw a candidate's registration for an exam subject.
    
    Args:
        candidate_exam_subject_id: The unique identifier of the candidate exam subject registration
        reason: Optional reason for withdrawal
        service: CandidateExamSubjectService instance
        
    Returns:
        The updated candidate exam subject registration
        
    Raises:
        HTTPException: If the candidate exam subject registration is not found
    """
    updated_registration = await service.withdraw_registration(candidate_exam_subject_id, reason)
    if not updated_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam subject registration with ID {candidate_exam_subject_id} not found"
        )
    
    return updated_registration

@router.post("/{candidate_exam_subject_id}/absent", response_model=CandidateExamSubjectResponse, summary="Mark Candidate as Absent")
async def mark_candidate_absent(
    candidate_exam_subject_id: str = Path(..., description="The unique identifier of the candidate exam subject registration"),
    reason: Optional[str] = Query(None, description="Reason for absence"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Mark a candidate as absent for an exam subject.
    
    Args:
        candidate_exam_subject_id: The unique identifier of the candidate exam subject registration
        reason: Optional reason for absence
        service: CandidateExamSubjectService instance
        
    Returns:
        The updated candidate exam subject registration
        
    Raises:
        HTTPException: If the candidate exam subject registration is not found
    """
    updated_registration = await service.mark_absent(candidate_exam_subject_id, reason)
    if not updated_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam subject registration with ID {candidate_exam_subject_id} not found"
        )
    
    return updated_registration

@router.post("/{candidate_exam_subject_id}/complete", response_model=CandidateExamSubjectResponse, summary="Mark Candidate Exam Subject as Completed")
async def mark_candidate_exam_subject_completed(
    candidate_exam_subject_id: str = Path(..., description="The unique identifier of the candidate exam subject registration"),
    service: CandidateExamSubjectService = Depends(get_candidate_exam_subject_service)
):
    """
    Mark a candidate's exam subject as completed.
    
    Args:
        candidate_exam_subject_id: The unique identifier of the candidate exam subject registration
        service: CandidateExamSubjectService instance
        
    Returns:
        The updated candidate exam subject registration
        
    Raises:
        HTTPException: If the candidate exam subject registration is not found
    """
    updated_registration = await service.mark_completed(candidate_exam_subject_id)
    if not updated_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate exam subject registration with ID {candidate_exam_subject_id} not found"
        )
    
    return updated_registration 