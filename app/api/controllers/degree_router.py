"""
Degree router module.

This module provides API endpoints for managing degrees.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Response, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.degree import (
    DegreeCreate,
    DegreeUpdate,
    DegreeResponse,
    DegreeListResponse
)
from app.repositories.degree_repository import DegreeRepository
from app.services.degree_service import DegreeService

router = APIRouter(
    prefix="/degrees",
    tags=["Degrees"],
    responses={404: {"description": "Not found"}}
)

async def get_degree_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for DegreeService
    
    Args:
        db: Database session
        
    Returns:
        DegreeService: Service instance for degree business logic
    """
    repository = DegreeRepository(db)
    return DegreeService(repository)

@router.get("/", response_model=DegreeListResponse, summary="List Degrees")
async def get_degrees(
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    major_id: Optional[str] = Query(None, description="Filter by major ID"),
    start_year: Optional[int] = Query(None, description="Filter by minimum start year"),
    end_year: Optional[int] = Query(None, description="Filter by maximum end year"),
    service: DegreeService = Depends(get_degree_service)
):
    """
    Get list of degrees.
    
    This endpoint returns a list of all degrees, with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        major_id: Filter by major ID
        start_year: Filter by minimum start year
        end_year: Filter by maximum end year
        service: DegreeService (injected)
        
    Returns:
        List of degrees with pagination metadata
    """
    try:
        return await service.get_all_degrees(skip, limit, major_id, start_year, end_year)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving degrees: {str(e)}"
        )

@router.get("/{degree_id}", response_model=DegreeResponse, summary="Get Degree Details")
async def get_degree(
    degree_id: str = Path(..., description="ID of the degree to retrieve"),
    service: DegreeService = Depends(get_degree_service)
):
    """
    Get detailed information about a degree by ID.
    
    This endpoint returns detailed information about a degree based on ID.
    
    Args:
        degree_id: ID of the degree to retrieve
        service: DegreeService (injected)
        
    Returns:
        Detailed information about the degree
        
    Raises:
        HTTPException: If degree not found or error occurs
    """
    try:
        degree = await service.get_degree_by_id(degree_id)
        if not degree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Degree with ID {degree_id} not found"
            )
        return degree
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving degree: {str(e)}"
        )

@router.get("/major/{major_id}", response_model=List[DegreeResponse], summary="Get Degrees by Major")
async def get_degrees_by_major(
    major_id: str = Path(..., description="ID of the major"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: DegreeService = Depends(get_degree_service)
):
    """
    Get all degrees for a specific major.
    
    This endpoint returns all degrees associated with a specific major.
    
    Args:
        major_id: ID of the major
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: DegreeService (injected)
        
    Returns:
        List of degrees for the specified major
    """
    try:
        return await service.get_degrees_by_major(major_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving degrees for major {major_id}: {str(e)}"
        )

@router.get("/candidate/{candidate_id}", response_model=DegreeListResponse, summary="Get Degrees by Candidate")
async def get_degrees_by_candidate(
    candidate_id: str = Path(..., description="ID of the candidate"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: DegreeService = Depends(get_degree_service)
):
    """
    Get all degrees for a specific candidate.
    
    This endpoint returns all degrees associated with a specific candidate based on their education history.
    
    Args:
        candidate_id: ID of the candidate
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: DegreeService (injected)
        
    Returns:
        List of degrees for the specified candidate with pagination metadata
    """
    try:
        return await service.get_degrees_by_candidate(candidate_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving degrees for candidate {candidate_id}: {str(e)}"
        )

@router.post("/", response_model=DegreeResponse, status_code=status.HTTP_201_CREATED, summary="Create Degree")
async def create_degree(
    degree_data: DegreeCreate = Body(..., description="Degree information to create"),
    service: DegreeService = Depends(get_degree_service)
):
    """
    Create a new degree.
    
    This endpoint creates a new degree with the provided information.
    
    Args:
        degree_data: Degree information to create
        service: DegreeService (injected)
        
    Returns:
        Created degree information
        
    Raises:
        HTTPException: If an error occurs during degree creation
    """
    try:
        return await service.create_degree(degree_data.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred while creating degree: {str(e)}"
        )

@router.put("/{degree_id}", response_model=DegreeResponse, summary="Update Degree")
async def update_degree(
    degree_id: str = Path(..., description="ID of the degree to update"),
    degree_data: DegreeUpdate = Body(..., description="Updated degree information"),
    service: DegreeService = Depends(get_degree_service)
):
    """
    Update an existing degree.
    
    This endpoint updates information of an existing degree.
    
    Args:
        degree_id: ID of the degree to update
        degree_data: Updated degree information
        service: DegreeService (injected)
        
    Returns:
        Updated degree information
        
    Raises:
        HTTPException: If degree not found or error occurs
    """
    try:
        degree = await service.update_degree(degree_id, degree_data.model_dump(exclude_unset=True))
        if not degree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Degree with ID {degree_id} not found"
            )
        return degree
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating degree: {str(e)}"
        )

@router.delete("/{degree_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Degree")
async def delete_degree(
    degree_id: str = Path(..., description="ID of the degree to delete"),
    service: DegreeService = Depends(get_degree_service)
):
    """
    Delete a degree.
    
    This endpoint removes a degree from the system.
    
    Args:
        degree_id: ID of the degree to delete
        service: DegreeService (injected)
        
    Returns:
        No content (HTTP 204)
        
    Raises:
        HTTPException: If degree not found or error occurs
    """
    try:
        deleted = await service.delete_degree(degree_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Degree with ID {degree_id} not found"
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting degree: {str(e)}"
        )

@router.post("/education-history/{education_history_id}", response_model=DegreeResponse, summary="Assign Degree to Education History")
async def assign_degree_to_education_history(
    education_history_id: str = Path(..., description="ID of the education history to associate with the degree"),
    degree_id: str = Query(..., description="ID of the degree to assign"),
    service: DegreeService = Depends(get_degree_service)
):
    """
    Assign a degree to a specific education history.
    
    This endpoint creates an association between a degree and an education history entry,
    making it possible to track which degrees were earned through which educational paths.
    
    Args:
        education_history_id: ID of the education history to associate with the degree
        degree_id: ID of the degree to assign
        service: DegreeService (injected)
        
    Returns:
        Updated degree information
        
    Raises:
        HTTPException: If degree or education history not found or error occurs
    """
    try:
        update_data = {"education_history_id": education_history_id}
        degree = await service.update_degree(degree_id, update_data)
        if not degree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Degree with ID {degree_id} not found"
            )
        return degree
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while assigning degree to education history: {str(e)}"
        ) 