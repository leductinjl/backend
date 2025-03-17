"""
Subject router module.

This module provides API endpoints for managing subjects (academic courses).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.subject import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectListResponse
)
from app.repositories.subject_repository import SubjectRepository
from app.services.subject_service import SubjectService

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"],
    responses={404: {"description": "Not found"}}
)

async def get_subject_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for SubjectService.
    
    Args:
        db: Database session
        
    Returns:
        SubjectService: Service instance for subject business logic
    """
    repository = SubjectRepository(db)
    return SubjectService(repository)

@router.get("/", response_model=SubjectListResponse, summary="List Subjects")
async def get_subjects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: SubjectService = Depends(get_subject_service)
):
    """
    Retrieve a list of subjects with pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: SubjectService instance
        
    Returns:
        List of subjects
    """
    subjects, total = await service.get_all_subjects(
        skip=skip, 
        limit=limit
    )
    
    return SubjectListResponse(
        items=subjects,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{subject_id}", response_model=SubjectResponse, summary="Get Subject")
async def get_subject(
    subject_id: str,
    service: SubjectService = Depends(get_subject_service)
):
    """
    Retrieve a specific subject by ID.
    
    Args:
        subject_id: The unique identifier of the subject
        service: SubjectService instance
        
    Returns:
        The subject if found
        
    Raises:
        HTTPException: If the subject is not found
    """
    subject = await service.get_subject_by_id(subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found"
        )
    
    return subject

@router.post(
    "/", 
    response_model=SubjectResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Subject"
)
async def create_subject(
    subject: SubjectCreate,
    service: SubjectService = Depends(get_subject_service)
):
    """
    Create a new subject.
    
    Args:
        subject: Subject data
        service: SubjectService instance
        
    Returns:
        The created subject
    """
    return await service.create_subject(subject.model_dump())

@router.put("/{subject_id}", response_model=SubjectResponse, summary="Update Subject")
async def update_subject(
    subject_id: str,
    subject: SubjectUpdate,
    service: SubjectService = Depends(get_subject_service)
):
    """
    Update a subject.
    
    Args:
        subject_id: The unique identifier of the subject
        subject: Updated subject data
        service: SubjectService instance
        
    Returns:
        The updated subject
        
    Raises:
        HTTPException: If the subject is not found
    """
    updated_subject = await service.update_subject(subject_id, subject.model_dump(exclude_unset=True))
    if not updated_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found"
        )
    
    return updated_subject

@router.patch("/{subject_id}", response_model=SubjectResponse, summary="Partially Update Subject")
async def partially_update_subject(
    subject_id: str,
    subject: SubjectUpdate,
    service: SubjectService = Depends(get_subject_service)
):
    """
    Partially update a subject.
    
    Args:
        subject_id: The unique identifier of the subject
        subject: Partial subject data
        service: SubjectService instance
        
    Returns:
        The updated subject
        
    Raises:
        HTTPException: If the subject is not found
    """
    updated_subject = await service.update_subject(
        subject_id, 
        subject.model_dump(exclude_unset=True, exclude_none=True)
    )
    if not updated_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found"
        )
    
    return updated_subject

@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Subject")
async def delete_subject(
    subject_id: str,
    service: SubjectService = Depends(get_subject_service)
):
    """
    Delete a subject.
    
    Args:
        subject_id: The unique identifier of the subject
        service: SubjectService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the subject is not found
    """
    deleted = await service.delete_subject(subject_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 