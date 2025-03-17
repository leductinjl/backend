"""
Exam router module.

This module provides API endpoints for managing exams.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path
from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.exam import (
    ExamCreate,
    ExamUpdate,
    ExamResponse,
    ExamDetailResponse,
    ExamListResponse
)
from app.repositories.exam_repository import ExamRepository
from app.repositories.exam_type_repository import ExamTypeRepository
from app.repositories.management_unit_repository import ManagementUnitRepository
from app.services.exam_service import ExamService

router = APIRouter(
    prefix="/exams",
    tags=["Exams"],
    responses={404: {"description": "Not found"}}
)

async def get_exam_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ExamService.
    
    Args:
        db: Database session
        
    Returns:
        ExamService: Service instance for exam business logic
    """
    repository = ExamRepository(db)
    exam_type_repository = ExamTypeRepository(db)
    management_unit_repository = ManagementUnitRepository(db)
    return ExamService(repository, exam_type_repository, management_unit_repository)

@router.get("/", response_model=ExamListResponse, summary="List Exams")
async def get_exams(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    type_id: Optional[str] = Query(None, description="Filter by exam type ID"),
    organizing_unit_id: Optional[str] = Query(None, description="Filter by organizing unit ID"),
    scope: Optional[str] = Query(None, description="Filter by exam scope (School, Provincial, National, International)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    start_date_from: Optional[date] = Query(None, description="Filter for exams starting from this date"),
    start_date_to: Optional[date] = Query(None, description="Filter for exams starting before this date"),
    end_date_from: Optional[date] = Query(None, description="Filter for exams ending from this date"),
    end_date_to: Optional[date] = Query(None, description="Filter for exams ending before this date"),
    service: ExamService = Depends(get_exam_service)
):
    """
    Retrieve a list of exams with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        type_id: Optional filter by exam type ID
        organizing_unit_id: Optional filter by organizing unit ID
        scope: Optional filter by exam scope
        is_active: Optional filter by active status
        start_date_from: Optional filter for exams starting from this date
        start_date_to: Optional filter for exams starting before this date
        end_date_from: Optional filter for exams ending from this date
        end_date_to: Optional filter for exams ending before this date
        service: ExamService instance
        
    Returns:
        List of exams
    """
    exams, total = await service.get_all_exams(
        skip=skip, 
        limit=limit, 
        exam_type_id=type_id,
        management_unit_id=organizing_unit_id,
        is_active=is_active,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        end_date_from=end_date_from,
        end_date_to=end_date_to
    )
    
    return ExamListResponse(
        items=exams,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{exam_id}", response_model=ExamDetailResponse, summary="Get Exam")
async def get_exam(
    exam_id: str = Path(..., description="The unique identifier of the exam"),
    service: ExamService = Depends(get_exam_service)
):
    """
    Retrieve a specific exam by ID.
    
    Args:
        exam_id: The unique identifier of the exam
        service: ExamService instance
        
    Returns:
        The exam if found
        
    Raises:
        HTTPException: If the exam is not found
    """
    exam = await service.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam with ID {exam_id} not found"
        )
    
    return exam

@router.post(
    "/", 
    response_model=ExamResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam"
)
async def create_exam(
    exam: ExamCreate,
    service: ExamService = Depends(get_exam_service)
):
    """
    Create a new exam.
    
    Args:
        exam: Exam data
        service: ExamService instance
        
    Returns:
        The created exam
        
    Raises:
        HTTPException: If the exam type or organizing unit doesn't exist, or if dates are invalid
    """
    new_exam = await service.create_exam(exam.model_dump())
    if not new_exam:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create exam. Exam type or organizing unit may not exist, or dates may be invalid."
        )
    
    return new_exam

@router.put("/{exam_id}", response_model=ExamResponse, summary="Update Exam")
async def update_exam(
    exam_id: str = Path(..., description="The unique identifier of the exam"),
    exam: ExamUpdate = None,
    service: ExamService = Depends(get_exam_service)
):
    """
    Update an exam.
    
    Args:
        exam_id: The unique identifier of the exam
        exam: Updated exam data
        service: ExamService instance
        
    Returns:
        The updated exam
        
    Raises:
        HTTPException: If the exam is not found, or if foreign keys don't exist, or if dates are invalid
    """
    updated_exam = await service.update_exam(
        exam_id, 
        exam.model_dump(exclude_unset=True) if exam else {}
    )
    if not updated_exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam with ID {exam_id} not found or update failed due to validation errors"
        )
    
    return updated_exam

@router.patch("/{exam_id}", response_model=ExamResponse, summary="Partially Update Exam")
async def partially_update_exam(
    exam_id: str = Path(..., description="The unique identifier of the exam"),
    exam: ExamUpdate = None,
    service: ExamService = Depends(get_exam_service)
):
    """
    Partially update an exam.
    
    Args:
        exam_id: The unique identifier of the exam
        exam: Partial exam data
        service: ExamService instance
        
    Returns:
        The updated exam
        
    Raises:
        HTTPException: If the exam is not found, or if foreign keys don't exist, or if dates are invalid
    """
    updated_exam = await service.update_exam(
        exam_id, 
        exam.model_dump(exclude_unset=True, exclude_none=True) if exam else {}
    )
    if not updated_exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam with ID {exam_id} not found or update failed due to validation errors"
        )
    
    return updated_exam

@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Exam")
async def delete_exam(
    exam_id: str = Path(..., description="The unique identifier of the exam"),
    service: ExamService = Depends(get_exam_service)
):
    """
    Delete an exam.
    
    Args:
        exam_id: The unique identifier of the exam
        service: ExamService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the exam is not found
    """
    deleted = await service.delete_exam(exam_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam with ID {exam_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 