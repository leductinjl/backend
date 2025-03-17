"""
School-Major router module.

This module provides API endpoints for managing school-major relationships.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.school_major import (
    SchoolMajorCreate,
    SchoolMajorUpdate,
    SchoolMajorResponse,
    SchoolMajorDetailResponse,
    SchoolMajorListResponse
)
from app.repositories.school_major_repository import SchoolMajorRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.major_repository import MajorRepository
from app.services.school_major_service import SchoolMajorService
from app.services.id_service import generate_model_id

router = APIRouter(
    prefix="/school-majors",
    tags=["School Majors"],
    responses={404: {"description": "Not found"}}
)

async def get_school_major_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for SchoolMajorService.
    
    Args:
        db: Database session
        
    Returns:
        SchoolMajorService: Service instance for school-major relationship business logic
    """
    repository = SchoolMajorRepository(db)
    school_repository = SchoolRepository(db)
    major_repository = MajorRepository(db)
    return SchoolMajorService(repository, school_repository, major_repository)

@router.get("/", response_model=SchoolMajorListResponse, summary="List School-Major Relationships")
async def get_school_majors(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    school_id: Optional[str] = Query(None, description="Filter by school ID"),
    major_id: Optional[str] = Query(None, description="Filter by major ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: SchoolMajorService = Depends(get_school_major_service)
):
    """
    Retrieve a list of school-major relationships with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        school_id: Optional filter by school ID
        major_id: Optional filter by major ID
        is_active: Optional filter by active status
        service: SchoolMajorService instance
        
    Returns:
        List of school-major relationships
    """
    school_majors, total = await service.get_all_school_majors(
        skip=skip, 
        limit=limit, 
        school_id=school_id,
        major_id=major_id,
        is_active=is_active
    )
    
    return SchoolMajorListResponse(
        items=school_majors,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{school_major_id}", response_model=SchoolMajorDetailResponse, summary="Get School-Major Relationship")
async def get_school_major(
    school_major_id: str = Path(..., description="The unique identifier of the school-major relationship"),
    service: SchoolMajorService = Depends(get_school_major_service)
):
    """
    Retrieve a specific school-major relationship by ID.
    
    Args:
        school_major_id: The unique identifier of the school-major relationship
        service: SchoolMajorService instance
        
    Returns:
        The school-major relationship if found
        
    Raises:
        HTTPException: If the school-major relationship is not found
    """
    school_major = await service.get_school_major_by_id(school_major_id)
    if not school_major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School-major relationship with ID {school_major_id} not found"
        )
    
    return school_major

@router.post(
    "/", 
    response_model=SchoolMajorResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create School-Major Relationship"
)
async def create_school_major(
    school_major: SchoolMajorCreate,
    service: SchoolMajorService = Depends(get_school_major_service)
):
    """
    Create a new school-major relationship.
    
    Args:
        school_major: School-major relationship data
        service: SchoolMajorService instance
        
    Returns:
        The created school-major relationship
        
    Raises:
        HTTPException: If the school or major doesn't exist, or if the relationship already exists
    """
    # Ensure school_major_id is explicitly set
    school_major_data = school_major.model_dump()
    school_major_data["school_major_id"] = generate_model_id("SchoolMajor")
    
    new_school_major = await service.create_school_major(school_major_data)
    if not new_school_major:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create school-major relationship. School or major may not exist, or relationship may already exist."
        )
    
    return new_school_major

@router.put("/{school_major_id}", response_model=SchoolMajorResponse, summary="Update School-Major Relationship")
async def update_school_major(
    school_major_id: str = Path(..., description="The unique identifier of the school-major relationship"),
    school_major: SchoolMajorUpdate = None,
    service: SchoolMajorService = Depends(get_school_major_service)
):
    """
    Update a school-major relationship.
    
    Args:
        school_major_id: The unique identifier of the school-major relationship
        school_major: Updated school-major relationship data
        service: SchoolMajorService instance
        
    Returns:
        The updated school-major relationship
        
    Raises:
        HTTPException: If the school-major relationship is not found
    """
    updated_school_major = await service.update_school_major(
        school_major_id, 
        school_major.model_dump(exclude_unset=True) if school_major else {}
    )
    if not updated_school_major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School-major relationship with ID {school_major_id} not found"
        )
    
    return updated_school_major

@router.patch("/{school_major_id}", response_model=SchoolMajorResponse, summary="Partially Update School-Major Relationship")
async def partially_update_school_major(
    school_major_id: str = Path(..., description="The unique identifier of the school-major relationship"),
    school_major: SchoolMajorUpdate = None,
    service: SchoolMajorService = Depends(get_school_major_service)
):
    """
    Partially update a school-major relationship.
    
    Args:
        school_major_id: The unique identifier of the school-major relationship
        school_major: Partial school-major relationship data
        service: SchoolMajorService instance
        
    Returns:
        The updated school-major relationship
        
    Raises:
        HTTPException: If the school-major relationship is not found
    """
    updated_school_major = await service.update_school_major(
        school_major_id, 
        school_major.model_dump(exclude_unset=True, exclude_none=True) if school_major else {}
    )
    if not updated_school_major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School-major relationship with ID {school_major_id} not found"
        )
    
    return updated_school_major

@router.delete("/{school_major_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete School-Major Relationship")
async def delete_school_major(
    school_major_id: str = Path(..., description="The unique identifier of the school-major relationship"),
    service: SchoolMajorService = Depends(get_school_major_service)
):
    """
    Delete a school-major relationship.
    
    Args:
        school_major_id: The unique identifier of the school-major relationship
        service: SchoolMajorService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the school-major relationship is not found
    """
    deleted = await service.delete_school_major(school_major_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School-major relationship with ID {school_major_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 