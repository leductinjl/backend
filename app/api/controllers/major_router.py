"""
Major router module.

This module provides API endpoints for managing majors (fields of study).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.major import (
    MajorCreate,
    MajorUpdate,
    MajorResponse,
    MajorListResponse
)
from app.repositories.major_repository import MajorRepository
from app.services.major_service import MajorService
from app.services.id_service import generate_model_id

router = APIRouter(
    prefix="/majors",
    tags=["Majors"],
    responses={404: {"description": "Not found"}}
)

async def get_major_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for MajorService.
    
    Args:
        db: Database session
        
    Returns:
        MajorService: Service instance for major business logic
    """
    repository = MajorRepository(db)
    return MajorService(repository)

@router.get("/", response_model=MajorListResponse, summary="List Majors")
async def get_majors(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: MajorService = Depends(get_major_service)
):
    """
    Retrieve a list of majors with pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: MajorService instance
        
    Returns:
        List of majors
    """
    majors, total = await service.get_all_majors(
        skip=skip, 
        limit=limit
    )
    
    return MajorListResponse(
        items=majors,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{major_id}", response_model=MajorResponse, summary="Get Major")
async def get_major(
    major_id: str,
    service: MajorService = Depends(get_major_service)
):
    """
    Retrieve a specific major by ID.
    
    Args:
        major_id: The unique identifier of the major
        service: MajorService instance
        
    Returns:
        The major if found
        
    Raises:
        HTTPException: If the major is not found
    """
    major = await service.get_major_by_id(major_id)
    if not major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Major with ID {major_id} not found"
        )
    
    return major

@router.post(
    "/", 
    response_model=MajorResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Major"
)
async def create_major(
    major: MajorCreate,
    service: MajorService = Depends(get_major_service)
):
    """
    Create a new major.
    
    Args:
        major: Major data
        service: MajorService instance
        
    Returns:
        The created major
    """
    # Ensure major_id is explicitly set
    major_data = major.model_dump()
    major_data["major_id"] = generate_model_id("Major")
    
    return await service.create_major(major_data)

@router.put("/{major_id}", response_model=MajorResponse, summary="Update Major")
async def update_major(
    major_id: str,
    major: MajorUpdate,
    service: MajorService = Depends(get_major_service)
):
    """
    Update a major.
    
    Args:
        major_id: The unique identifier of the major
        major: Updated major data
        service: MajorService instance
        
    Returns:
        The updated major
        
    Raises:
        HTTPException: If the major is not found
    """
    updated_major = await service.update_major(major_id, major.model_dump(exclude_unset=True))
    if not updated_major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Major with ID {major_id} not found"
        )
    
    return updated_major

@router.patch("/{major_id}", response_model=MajorResponse, summary="Partially Update Major")
async def partially_update_major(
    major_id: str,
    major: MajorUpdate,
    service: MajorService = Depends(get_major_service)
):
    """
    Partially update a major.
    
    Args:
        major_id: The unique identifier of the major
        major: Partial major data
        service: MajorService instance
        
    Returns:
        The updated major
        
    Raises:
        HTTPException: If the major is not found
    """
    updated_major = await service.update_major(
        major_id, 
        major.model_dump(exclude_unset=True, exclude_none=True)
    )
    if not updated_major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Major with ID {major_id} not found"
        )
    
    return updated_major

@router.delete("/{major_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Major")
async def delete_major(
    major_id: str,
    service: MajorService = Depends(get_major_service)
):
    """
    Delete a major.
    
    Args:
        major_id: The unique identifier of the major
        service: MajorService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the major is not found
    """
    deleted = await service.delete_major(major_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Major with ID {major_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 