"""
Exam Subject router module.

This module provides API endpoints for managing exam subjects.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.exam_subject import (
    ExamSubjectCreate,
    ExamSubjectUpdate,
    ExamSubjectResponse,
    ExamSubjectDetailResponse,
    ExamSubjectListResponse
)
from app.repositories.exam_subject_repository import ExamSubjectRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.subject_repository import SubjectRepository
from app.services.exam_subject_service import ExamSubjectService

router = APIRouter(
    prefix="/exam-subjects",
    tags=["Exam Subjects"],
    responses={404: {"description": "Not found"}}
)

async def get_exam_subject_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ExamSubjectService.
    
    Args:
        db: Database session
        
    Returns:
        ExamSubjectService: Service instance for exam subject business logic
    """
    repository = ExamSubjectRepository(db)
    exam_repository = ExamRepository(db)
    subject_repository = SubjectRepository(db)
    return ExamSubjectService(repository, exam_repository, subject_repository)

@router.get("/", response_model=ExamSubjectListResponse, summary="List Exam Subjects")
async def get_exam_subjects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    is_required: Optional[bool] = Query(None, description="Filter by required status"),
    service: ExamSubjectService = Depends(get_exam_subject_service)
):
    """
    Retrieve a list of exam subjects with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        exam_id: Optional filter by exam ID
        subject_id: Optional filter by subject ID
        is_required: Optional filter by required status
        service: ExamSubjectService instance
        
    Returns:
        List of exam subjects
    """
    exam_subjects, total = await service.get_all_exam_subjects(
        skip=skip, 
        limit=limit, 
        exam_id=exam_id,
        subject_id=subject_id,
        is_required=is_required
    )
    
    return ExamSubjectListResponse(
        items=exam_subjects,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{exam_subject_id}", response_model=ExamSubjectDetailResponse, summary="Get Exam Subject")
async def get_exam_subject(
    exam_subject_id: str = Path(..., description="The unique identifier of the exam subject"),
    service: ExamSubjectService = Depends(get_exam_subject_service)
):
    """
    Retrieve a specific exam subject by ID.
    
    Args:
        exam_subject_id: The unique identifier of the exam subject
        service: ExamSubjectService instance
        
    Returns:
        The exam subject if found
        
    Raises:
        HTTPException: If the exam subject is not found
    """
    exam_subject = await service.get_exam_subject_by_id(exam_subject_id)
    if not exam_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam subject with ID {exam_subject_id} not found"
        )
    
    return exam_subject

@router.get("/exam/{exam_id}", response_model=List[ExamSubjectResponse], summary="Get Exam Subjects by Exam ID")
async def get_exam_subjects_by_exam(
    exam_id: str = Path(..., description="The ID of the exam"),
    service: ExamSubjectService = Depends(get_exam_subject_service)
):
    """
    Retrieve all exam subjects for a specific exam.
    
    Args:
        exam_id: The ID of the exam
        service: ExamSubjectService instance
        
    Returns:
        List of exam subjects for the specified exam
    """
    exam_subjects = await service.get_exam_subjects_by_exam_id(exam_id)
    return exam_subjects

@router.get("/subject/{subject_id}", response_model=List[ExamSubjectResponse], summary="Get Exam Subjects by Subject ID")
async def get_exam_subjects_by_subject(
    subject_id: str = Path(..., description="The ID of the subject"),
    service: ExamSubjectService = Depends(get_exam_subject_service)
):
    """
    Retrieve all exam subjects for a specific subject.
    
    Args:
        subject_id: The ID of the subject
        service: ExamSubjectService instance
        
    Returns:
        List of exam subjects for the specified subject
    """
    exam_subjects = await service.get_exam_subjects_by_subject_id(subject_id)
    return exam_subjects

@router.post(
    "/", 
    response_model=ExamSubjectResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam Subject"
)
async def create_exam_subject(
    exam_subject: ExamSubjectCreate,
    service: ExamSubjectService = Depends(get_exam_subject_service)
):
    """
    Create a new exam subject.
    
    Args:
        exam_subject: Exam subject data
        service: ExamSubjectService instance
        
    Returns:
        The created exam subject
        
    Raises:
        HTTPException: If the exam or subject doesn't exist, or if an exam subject already exists
    """
    new_exam_subject = await service.create_exam_subject(exam_subject.model_dump())
    if not new_exam_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create exam subject. Exam or subject may not exist, or an exam subject already exists."
        )
    
    return new_exam_subject

@router.put("/{exam_subject_id}", response_model=ExamSubjectResponse, summary="Update Exam Subject")
async def update_exam_subject(
    exam_subject_id: str = Path(..., description="The unique identifier of the exam subject"),
    exam_subject: ExamSubjectUpdate = None,
    service: ExamSubjectService = Depends(get_exam_subject_service)
):
    """
    Update an exam subject.
    
    Args:
        exam_subject_id: The unique identifier of the exam subject
        exam_subject: Updated exam subject data
        service: ExamSubjectService instance
        
    Returns:
        The updated exam subject
        
    Raises:
        HTTPException: If the exam subject is not found
    """
    updated_exam_subject = await service.update_exam_subject(
        exam_subject_id, 
        exam_subject.model_dump(exclude_unset=True) if exam_subject else {}
    )
    if not updated_exam_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam subject with ID {exam_subject_id} not found"
        )
    
    return updated_exam_subject

@router.patch("/{exam_subject_id}", response_model=ExamSubjectResponse, summary="Partially Update Exam Subject")
async def partially_update_exam_subject(
    exam_subject_id: str = Path(..., description="The unique identifier of the exam subject"),
    exam_subject: ExamSubjectUpdate = None,
    service: ExamSubjectService = Depends(get_exam_subject_service)
):
    """
    Partially update an exam subject.
    
    Args:
        exam_subject_id: The unique identifier of the exam subject
        exam_subject: Partial exam subject data
        service: ExamSubjectService instance
        
    Returns:
        The updated exam subject
        
    Raises:
        HTTPException: If the exam subject is not found
    """
    updated_exam_subject = await service.update_exam_subject(
        exam_subject_id, 
        exam_subject.model_dump(exclude_unset=True, exclude_none=True) if exam_subject else {}
    )
    if not updated_exam_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam subject with ID {exam_subject_id} not found"
        )
    
    return updated_exam_subject

@router.delete("/{exam_subject_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Exam Subject")
async def delete_exam_subject(
    exam_subject_id: str = Path(..., description="The unique identifier of the exam subject"),
    service: ExamSubjectService = Depends(get_exam_subject_service)
):
    """
    Delete an exam subject.
    
    Args:
        exam_subject_id: The unique identifier of the exam subject
        service: ExamSubjectService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the exam subject is not found
    """
    deleted = await service.delete_exam_subject(exam_subject_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam subject with ID {exam_subject_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 