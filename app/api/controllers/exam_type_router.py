"""
Exam Type router module.

This module provides API endpoints for managing exam types.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.exam_type import (
    ExamTypeCreate,
    ExamTypeUpdate,
    ExamTypeResponse,
    ExamTypeListResponse
)
from app.repositories.exam_type_repository import ExamTypeRepository
from app.services.exam_type_service import ExamTypeService

router = APIRouter(
    prefix="/exam-types",
    tags=["Exam Types"],
    responses={404: {"description": "Not found"}}
)

async def get_exam_type_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ExamTypeService.
    
    Args:
        db: Database session
        
    Returns:
        ExamTypeService: Service instance for exam type business logic
    """
    repository = ExamTypeRepository(db)
    return ExamTypeService(repository)

@router.get("/", response_model=ExamTypeListResponse, summary="List Exam Types")
async def get_exam_types(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: ExamTypeService = Depends(get_exam_type_service)
):
    """
    Retrieve a list of exam types with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        is_active: Optional filter by active status
        service: ExamTypeService instance
        
    Returns:
        List of exam types
    """
    exam_types, total = await service.get_all_exam_types(
        skip=skip, 
        limit=limit, 
        is_active=is_active
    )
    
    return ExamTypeListResponse(
        items=exam_types,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{type_id}", response_model=ExamTypeResponse, summary="Get Exam Type")
async def get_exam_type(
    type_id: str,
    service: ExamTypeService = Depends(get_exam_type_service)
):
    """
    Retrieve a specific exam type by ID.
    
    Args:
        type_id: The unique identifier of the exam type
        service: ExamTypeService instance
        
    Returns:
        The exam type if found
        
    Raises:
        HTTPException: If the exam type is not found
    """
    exam_type = await service.get_exam_type_by_id(type_id)
    if not exam_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam type with ID {type_id} not found"
        )
    
    return exam_type

@router.post(
    "/", 
    response_model=ExamTypeResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam Type"
)
async def create_exam_type(
    exam_type: ExamTypeCreate,
    service: ExamTypeService = Depends(get_exam_type_service)
):
    """
    Create a new exam type.
    
    Args:
        exam_type: Exam type data
        service: ExamTypeService instance
        
    Returns:
        The created exam type
    """
    return await service.create_exam_type(exam_type.model_dump())

@router.put("/{type_id}", response_model=ExamTypeResponse, summary="Update Exam Type")
async def update_exam_type(
    type_id: str,
    exam_type: ExamTypeUpdate,
    service: ExamTypeService = Depends(get_exam_type_service)
):
    """
    Update an exam type.
    
    Args:
        type_id: The unique identifier of the exam type
        exam_type: Updated exam type data
        service: ExamTypeService instance
        
    Returns:
        The updated exam type
        
    Raises:
        HTTPException: If the exam type is not found
    """
    updated_exam_type = await service.update_exam_type(type_id, exam_type.model_dump(exclude_unset=True))
    if not updated_exam_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam type with ID {type_id} not found"
        )
    
    return updated_exam_type

@router.patch("/{type_id}", response_model=ExamTypeResponse, summary="Partially Update Exam Type")
async def partially_update_exam_type(
    type_id: str,
    exam_type: ExamTypeUpdate,
    service: ExamTypeService = Depends(get_exam_type_service)
):
    """
    Partially update an exam type.
    
    Args:
        type_id: The unique identifier of the exam type
        exam_type: Partial exam type data
        service: ExamTypeService instance
        
    Returns:
        The updated exam type
        
    Raises:
        HTTPException: If the exam type is not found
    """
    updated_exam_type = await service.update_exam_type(
        type_id, 
        exam_type.model_dump(exclude_unset=True, exclude_none=True)
    )
    if not updated_exam_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam type with ID {type_id} not found"
        )
    
    return updated_exam_type

@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Exam Type")
async def delete_exam_type(
    type_id: str,
    service: ExamTypeService = Depends(get_exam_type_service)
):
    """
    Delete an exam type.
    
    Args:
        type_id: The unique identifier of the exam type
        service: ExamTypeService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the exam type is not found
    """
    deleted = await service.delete_exam_type(type_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam type with ID {type_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 