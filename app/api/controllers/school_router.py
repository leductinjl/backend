"""
School router module.

This module provides API endpoints for managing schools.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.school import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse,
    SchoolListResponse
)
from app.repositories.school_repository import SchoolRepository
from app.services.school_service import SchoolService
from app.services.id_service import generate_model_id

router = APIRouter(
    prefix="/schools",
    tags=["Schools"],
    responses={404: {"description": "Not found"}}
)

async def get_school_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for SchoolService.
    
    Args:
        db: Database session
        
    Returns:
        SchoolService: Service instance for school business logic
    """
    repository = SchoolRepository(db)
    return SchoolService(repository)

@router.get("/", response_model=SchoolListResponse, summary="List Schools")
async def get_schools(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: SchoolService = Depends(get_school_service)
):
    """
    Retrieve a list of schools with pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: SchoolService instance
        
    Returns:
        List of schools
    """
    schools, total = await service.get_all_schools(
        skip=skip, 
        limit=limit
    )
    
    return SchoolListResponse(
        items=schools,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{school_id}", response_model=SchoolResponse, summary="Get School")
async def get_school(
    school_id: str,
    service: SchoolService = Depends(get_school_service)
):
    """
    Retrieve a specific school by ID.
    
    Args:
        school_id: The unique identifier of the school
        service: SchoolService instance
        
    Returns:
        The school if found
        
    Raises:
        HTTPException: If the school is not found
    """
    school = await service.get_school_by_id(school_id)
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with ID {school_id} not found"
        )
    
    return school

@router.post(
    "/", 
    response_model=SchoolResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create School"
)
async def create_school(
    school: SchoolCreate,
    service: SchoolService = Depends(get_school_service)
):
    """
    Create a new school.
    
    Args:
        school: School data
        service: SchoolService instance
        
    Returns:
        The created school
    """
    # Ensure school_id is explicitly set
    school_data = school.model_dump()
    school_data["school_id"] = generate_model_id("School")
    
    return await service.create_school(school_data)

@router.put("/{school_id}", response_model=SchoolResponse, summary="Update School")
async def update_school(
    school_id: str,
    school: SchoolUpdate,
    service: SchoolService = Depends(get_school_service)
):
    """
    Update a school.
    
    Args:
        school_id: The unique identifier of the school
        school: Updated school data
        service: SchoolService instance
        
    Returns:
        The updated school
        
    Raises:
        HTTPException: If the school is not found
    """
    updated_school = await service.update_school(school_id, school.model_dump(exclude_unset=True))
    if not updated_school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with ID {school_id} not found"
        )
    
    return updated_school

@router.patch("/{school_id}", response_model=SchoolResponse, summary="Partially Update School")
async def partially_update_school(
    school_id: str,
    school: SchoolUpdate,
    service: SchoolService = Depends(get_school_service)
):
    """
    Partially update a school.
    
    Args:
        school_id: The unique identifier of the school
        school: Partial school data
        service: SchoolService instance
        
    Returns:
        The updated school
        
    Raises:
        HTTPException: If the school is not found
    """
    updated_school = await service.update_school(
        school_id, 
        school.model_dump(exclude_unset=True, exclude_none=True)
    )
    if not updated_school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with ID {school_id} not found"
        )
    
    return updated_school

@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete School")
async def delete_school(
    school_id: str,
    service: SchoolService = Depends(get_school_service)
):
    """
    Delete a school.
    
    Args:
        school_id: The unique identifier of the school
        service: SchoolService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the school is not found
    """
    deleted = await service.delete_school(school_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with ID {school_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 