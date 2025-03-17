"""
Exam Location Mapping router module.

This module provides API endpoints for managing exam location mappings.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.exam_location_mapping import (
    ExamLocationMappingCreate,
    ExamLocationMappingUpdate,
    ExamLocationMappingResponse,
    ExamLocationMappingDetailResponse,
    ExamLocationMappingListResponse
)
from app.repositories.exam_location_mapping_repository import ExamLocationMappingRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.exam_location_repository import ExamLocationRepository
from app.services.exam_location_mapping_service import ExamLocationMappingService

router = APIRouter(
    prefix="/exam-location-mappings",
    tags=["Exam Location Mappings"],
    responses={404: {"description": "Not found"}}
)

async def get_exam_location_mapping_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ExamLocationMappingService.
    
    Args:
        db: Database session
        
    Returns:
        ExamLocationMappingService: Service instance for exam location mapping business logic
    """
    repository = ExamLocationMappingRepository(db)
    exam_repository = ExamRepository(db)
    location_repository = ExamLocationRepository(db)
    return ExamLocationMappingService(repository, exam_repository, location_repository)

@router.get("/", response_model=ExamLocationMappingListResponse, summary="List Exam Location Mappings")
async def get_exam_location_mappings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_primary: Optional[bool] = Query(None, description="Filter by primary status"),
    service: ExamLocationMappingService = Depends(get_exam_location_mapping_service)
):
    """
    Retrieve a list of exam location mappings with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        exam_id: Optional filter by exam ID
        location_id: Optional filter by location ID
        is_active: Optional filter by active status
        is_primary: Optional filter by primary status
        service: ExamLocationMappingService instance
        
    Returns:
        List of exam location mappings
    """
    mappings, total = await service.get_all_mappings(
        skip=skip, 
        limit=limit, 
        exam_id=exam_id,
        location_id=location_id,
        is_active=is_active,
        is_primary=is_primary
    )
    
    return ExamLocationMappingListResponse(
        items=mappings,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{mapping_id}", response_model=ExamLocationMappingDetailResponse, summary="Get Exam Location Mapping")
async def get_exam_location_mapping(
    mapping_id: str = Path(..., description="The unique identifier of the exam location mapping"),
    service: ExamLocationMappingService = Depends(get_exam_location_mapping_service)
):
    """
    Retrieve a specific exam location mapping by ID.
    
    Args:
        mapping_id: The unique identifier of the exam location mapping
        service: ExamLocationMappingService instance
        
    Returns:
        The exam location mapping if found
        
    Raises:
        HTTPException: If the exam location mapping is not found
    """
    mapping = await service.get_mapping_by_id(mapping_id)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam location mapping with ID {mapping_id} not found"
        )
    
    return mapping

@router.get("/exam/{exam_id}", response_model=List[ExamLocationMappingResponse], summary="Get Exam Location Mappings by Exam ID")
async def get_exam_location_mappings_by_exam(
    exam_id: str = Path(..., description="The ID of the exam"),
    service: ExamLocationMappingService = Depends(get_exam_location_mapping_service)
):
    """
    Retrieve all exam location mappings for a specific exam.
    
    Args:
        exam_id: The ID of the exam
        service: ExamLocationMappingService instance
        
    Returns:
        List of exam location mappings for the specified exam
    """
    mappings = await service.get_mappings_by_exam_id(exam_id)
    return mappings

@router.get("/location/{location_id}", response_model=List[ExamLocationMappingResponse], summary="Get Exam Location Mappings by Location ID")
async def get_exam_location_mappings_by_location(
    location_id: str = Path(..., description="The ID of the exam location"),
    service: ExamLocationMappingService = Depends(get_exam_location_mapping_service)
):
    """
    Retrieve all exam location mappings for a specific location.
    
    Args:
        location_id: The ID of the exam location
        service: ExamLocationMappingService instance
        
    Returns:
        List of exam location mappings for the specified location
    """
    mappings = await service.get_mappings_by_location_id(location_id)
    return mappings

@router.post(
    "/", 
    response_model=ExamLocationMappingResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam Location Mapping"
)
async def create_exam_location_mapping(
    mapping: ExamLocationMappingCreate,
    service: ExamLocationMappingService = Depends(get_exam_location_mapping_service)
):
    """
    Create a new exam location mapping.
    
    Args:
        mapping: Exam location mapping data
        service: ExamLocationMappingService instance
        
    Returns:
        The created exam location mapping
        
    Raises:
        HTTPException: If the exam or location doesn't exist, or if a mapping already exists
    """
    new_mapping = await service.create_mapping(mapping.model_dump())
    if not new_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create exam location mapping. Exam or location may not exist, or a mapping already exists."
        )
    
    return new_mapping

@router.put("/{mapping_id}", response_model=ExamLocationMappingResponse, summary="Update Exam Location Mapping")
async def update_exam_location_mapping(
    mapping_id: str = Path(..., description="The unique identifier of the exam location mapping"),
    mapping: ExamLocationMappingUpdate = None,
    service: ExamLocationMappingService = Depends(get_exam_location_mapping_service)
):
    """
    Update an exam location mapping.
    
    Args:
        mapping_id: The unique identifier of the exam location mapping
        mapping: Updated exam location mapping data
        service: ExamLocationMappingService instance
        
    Returns:
        The updated exam location mapping
        
    Raises:
        HTTPException: If the exam location mapping is not found
    """
    updated_mapping = await service.update_mapping(
        mapping_id, 
        mapping.model_dump(exclude_unset=True) if mapping else {}
    )
    if not updated_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam location mapping with ID {mapping_id} not found"
        )
    
    return updated_mapping

@router.patch("/{mapping_id}", response_model=ExamLocationMappingResponse, summary="Partially Update Exam Location Mapping")
async def partially_update_exam_location_mapping(
    mapping_id: str = Path(..., description="The unique identifier of the exam location mapping"),
    mapping: ExamLocationMappingUpdate = None,
    service: ExamLocationMappingService = Depends(get_exam_location_mapping_service)
):
    """
    Partially update an exam location mapping.
    
    Args:
        mapping_id: The unique identifier of the exam location mapping
        mapping: Partial exam location mapping data
        service: ExamLocationMappingService instance
        
    Returns:
        The updated exam location mapping
        
    Raises:
        HTTPException: If the exam location mapping is not found
    """
    updated_mapping = await service.update_mapping(
        mapping_id, 
        mapping.model_dump(exclude_unset=True, exclude_none=True) if mapping else {}
    )
    if not updated_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam location mapping with ID {mapping_id} not found"
        )
    
    return updated_mapping

@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Exam Location Mapping")
async def delete_exam_location_mapping(
    mapping_id: str = Path(..., description="The unique identifier of the exam location mapping"),
    service: ExamLocationMappingService = Depends(get_exam_location_mapping_service)
):
    """
    Delete an exam location mapping.
    
    Args:
        mapping_id: The unique identifier of the exam location mapping
        service: ExamLocationMappingService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the exam location mapping is not found
    """
    deleted = await service.delete_mapping(mapping_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam location mapping with ID {mapping_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 