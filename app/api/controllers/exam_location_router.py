"""
Exam Location router module.

This module provides API endpoints for managing exam locations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.exam_location import (
    ExamLocationCreate,
    ExamLocationUpdate,
    ExamLocationResponse,
    ExamLocationDetailResponse,
    ExamLocationListResponse
)
from app.repositories.exam_location_repository import ExamLocationRepository
from app.repositories.exam_repository import ExamRepository
from app.services.exam_location_service import ExamLocationService

router = APIRouter(
    prefix="/exam-locations",
    tags=["Exam Locations"],
    responses={404: {"description": "Not found"}}
)

async def get_exam_location_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ExamLocationService.
    
    Args:
        db: Database session
        
    Returns:
        ExamLocationService: Service instance for exam location business logic
    """
    repository = ExamLocationRepository(db)
    exam_repository = ExamRepository(db)
    return ExamLocationService(repository, exam_repository)

@router.get("/", response_model=ExamLocationListResponse, summary="List Exam Locations")
async def get_exam_locations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    country: Optional[str] = Query(None, description="Filter by country"),
    service: ExamLocationService = Depends(get_exam_location_service)
):
    """
    Retrieve a list of exam locations with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        exam_id: Optional filter by exam ID
        is_active: Optional filter by active status
        city: Optional filter by city
        country: Optional filter by country
        service: ExamLocationService instance
        
    Returns:
        List of exam locations
    """
    locations, total = await service.get_all_exam_locations(
        skip=skip, 
        limit=limit, 
        exam_id=exam_id,
        is_active=is_active,
        city=city,
        country=country
    )
    
    return ExamLocationListResponse(
        items=locations,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{location_id}", response_model=ExamLocationDetailResponse, summary="Get Exam Location")
async def get_exam_location(
    location_id: str = Path(..., description="The unique identifier of the exam location"),
    service: ExamLocationService = Depends(get_exam_location_service)
):
    """
    Retrieve a specific exam location by ID.
    
    Args:
        location_id: The unique identifier of the exam location
        service: ExamLocationService instance
        
    Returns:
        The exam location if found
        
    Raises:
        HTTPException: If the exam location is not found
    """
    location = await service.get_exam_location_by_id(location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam location with ID {location_id} not found"
        )
    
    return location

@router.get("/exam/{exam_id}", response_model=List[ExamLocationResponse], summary="Get Exam Locations by Exam ID")
async def get_exam_locations_by_exam(
    exam_id: str = Path(..., description="The ID of the exam"),
    service: ExamLocationService = Depends(get_exam_location_service)
):
    """
    Retrieve all exam locations for a specific exam.
    
    Args:
        exam_id: The ID of the exam
        service: ExamLocationService instance
        
    Returns:
        List of exam locations for the specified exam
    """
    locations = await service.get_locations_by_exam_id(exam_id)
    return locations

@router.post(
    "/", 
    response_model=ExamLocationDetailResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam Location"
)
async def create_exam_location(
    location: ExamLocationCreate,
    service: ExamLocationService = Depends(get_exam_location_service)
):
    """
    Create a new exam location.
    
    Args:
        location: Exam location data
        service: ExamLocationService instance
        
    Returns:
        The created exam location
        
    Raises:
        HTTPException: If the exam doesn't exist when exam_id is provided
    """
    new_location = await service.create_exam_location(location.model_dump())
    if not new_location:
        # Chỉ báo lỗi nếu exam_id được cung cấp nhưng không tìm thấy exam tương ứng
        if location.exam_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create exam location. Exam with ID {location.exam_id} not found."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create exam location due to an internal error."
            )
    
    return new_location

@router.put("/{location_id}", response_model=ExamLocationDetailResponse, summary="Update Exam Location")
async def update_exam_location(
    location_id: str = Path(..., description="The unique identifier of the exam location"),
    location: ExamLocationUpdate = None,
    service: ExamLocationService = Depends(get_exam_location_service)
):
    """
    Update an exam location.
    
    Args:
        location_id: The unique identifier of the exam location
        location: Updated exam location data
        service: ExamLocationService instance
        
    Returns:
        The updated exam location
        
    Raises:
        HTTPException: If the exam location is not found, or if the exam doesn't exist
    """
    updated_location = await service.update_exam_location(
        location_id, 
        location.model_dump(exclude_unset=True) if location else {}
    )
    if not updated_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam location with ID {location_id} not found or update failed due to invalid exam ID"
        )
    
    return updated_location

@router.patch("/{location_id}", response_model=ExamLocationDetailResponse, summary="Partially Update Exam Location")
async def partially_update_exam_location(
    location_id: str = Path(..., description="The unique identifier of the exam location"),
    location: ExamLocationUpdate = None,
    service: ExamLocationService = Depends(get_exam_location_service)
):
    """
    Partially update an exam location.
    
    Args:
        location_id: The unique identifier of the exam location
        location: Partial exam location data
        service: ExamLocationService instance
        
    Returns:
        The updated exam location
        
    Raises:
        HTTPException: If the exam location is not found, or if the exam doesn't exist
    """
    updated_location = await service.update_exam_location(
        location_id, 
        location.model_dump(exclude_unset=True, exclude_none=True) if location else {}
    )
    if not updated_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam location with ID {location_id} not found or update failed due to invalid exam ID"
        )
    
    return updated_location

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Exam Location")
async def delete_exam_location(
    location_id: str = Path(..., description="The unique identifier of the exam location"),
    service: ExamLocationService = Depends(get_exam_location_service)
):
    """
    Delete an exam location.
    
    Args:
        location_id: The unique identifier of the exam location
        service: ExamLocationService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the exam location is not found
    """
    deleted = await service.delete_exam_location(location_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam location with ID {location_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 