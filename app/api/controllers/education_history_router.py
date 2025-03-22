"""
Education History router module.

This module provides API endpoints for managing education history entries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Response, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.education_history import (
    EducationHistoryCreate,
    EducationHistoryUpdate,
    EducationHistoryResponse,
    EducationHistoryListResponse
)
from app.repositories.education_history_repository import EducationHistoryRepository
from app.services.education_history_service import EducationHistoryService

router = APIRouter(
    prefix="/education-histories",
    tags=["Education Histories"],
    responses={404: {"description": "Not found"}}
)

async def get_education_history_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for EducationHistoryService
    
    Args:
        db: Database session
        
    Returns:
        EducationHistoryService: Service instance for education history business logic
    """
    repository = EducationHistoryRepository(db)
    return EducationHistoryService(repository)

@router.get("/", response_model=EducationHistoryListResponse, summary="List Education Histories")
async def get_education_histories(
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    school_id: Optional[str] = Query(None, description="Filter by school ID"),
    education_level: Optional[str] = Query(None, description="Filter by education level"),
    start_year: Optional[int] = Query(None, description="Filter by minimum start year"),
    end_year: Optional[int] = Query(None, description="Filter by maximum end year"),
    service: EducationHistoryService = Depends(get_education_history_service)
):
    """
    Get list of education history entries.
    
    This endpoint returns a list of all education history entries, with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        candidate_id: Filter by candidate ID
        school_id: Filter by school ID
        education_level: Filter by education level (Primary, Secondary, High School)
        start_year: Filter by minimum start year
        end_year: Filter by maximum end year
        service: EducationHistoryService (injected)
        
    Returns:
        List of education history entries with pagination metadata
    """
    try:
        return await service.get_all_education_histories(
            skip, 
            limit, 
            candidate_id, 
            school_id, 
            education_level, 
            start_year, 
            end_year
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving education histories: {str(e)}"
        )

@router.get("/{education_history_id}", response_model=EducationHistoryResponse, summary="Get Education History Details")
async def get_education_history(
    education_history_id: str = Path(..., description="ID of the education history to retrieve"),
    service: EducationHistoryService = Depends(get_education_history_service)
):
    """
    Get detailed information about an education history entry by ID.
    
    This endpoint returns detailed information about an education history entry based on ID.
    
    Args:
        education_history_id: ID of the education history to retrieve
        service: EducationHistoryService (injected)
        
    Returns:
        Detailed information about the education history entry
        
    Raises:
        HTTPException: If education history not found or error occurs
    """
    try:
        education_history = await service.get_education_history_by_id(education_history_id)
        if not education_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education history with ID {education_history_id} not found"
            )
        return education_history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving education history: {str(e)}"
        )

@router.get("/candidate/{candidate_id}", response_model=EducationHistoryListResponse, summary="Get Education Histories by Candidate")
async def get_education_histories_by_candidate(
    candidate_id: str = Path(..., description="ID of the candidate"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: EducationHistoryService = Depends(get_education_history_service)
):
    """
    Get all education history entries for a specific candidate.
    
    This endpoint returns all education history entries associated with a specific candidate.
    
    Args:
        candidate_id: ID of the candidate
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: EducationHistoryService (injected)
        
    Returns:
        List of education history entries for the specified candidate with pagination metadata
    """
    try:
        return await service.get_education_histories_by_candidate(candidate_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving education histories for candidate {candidate_id}: {str(e)}"
        )

@router.get("/school/{school_id}", response_model=EducationHistoryListResponse, summary="Get Education Histories by School")
async def get_education_histories_by_school(
    school_id: str = Path(..., description="ID of the school"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: EducationHistoryService = Depends(get_education_history_service)
):
    """
    Get all education history entries for a specific school.
    
    This endpoint returns all education history entries associated with a specific school.
    
    Args:
        school_id: ID of the school
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: EducationHistoryService (injected)
        
    Returns:
        List of education history entries for the specified school with pagination metadata
    """
    try:
        return await service.get_education_histories_by_school(school_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving education histories for school {school_id}: {str(e)}"
        )

@router.post("/", response_model=EducationHistoryResponse, status_code=status.HTTP_201_CREATED, summary="Create Education History")
async def create_education_history(
    education_history_data: EducationHistoryCreate = Body(..., description="Education history information to create"),
    service: EducationHistoryService = Depends(get_education_history_service)
):
    """
    Create a new education history entry.
    
    This endpoint creates a new education history entry with the provided information.
    
    Args:
        education_history_data: Education history information to create
        service: EducationHistoryService (injected)
        
    Returns:
        Created education history information
        
    Raises:
        HTTPException: If an error occurs during education history creation
    """
    try:
        return await service.create_education_history(education_history_data.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred while creating education history: {str(e)}"
        )

@router.put("/{education_history_id}", response_model=EducationHistoryResponse, summary="Update Education History")
async def update_education_history(
    education_history_id: str = Path(..., description="ID of the education history to update"),
    education_history_data: EducationHistoryUpdate = Body(..., description="Updated education history information"),
    service: EducationHistoryService = Depends(get_education_history_service)
):
    """
    Update an existing education history entry.
    
    This endpoint updates information of an existing education history entry.
    
    Args:
        education_history_id: ID of the education history to update
        education_history_data: Updated education history information
        service: EducationHistoryService (injected)
        
    Returns:
        Updated education history information
        
    Raises:
        HTTPException: If education history not found or error occurs
    """
    try:
        education_history = await service.update_education_history(
            education_history_id, 
            education_history_data.model_dump(exclude_unset=True)
        )
        if not education_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education history with ID {education_history_id} not found"
            )
        return education_history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating education history: {str(e)}"
        )

@router.delete("/{education_history_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Education History")
async def delete_education_history(
    education_history_id: str = Path(..., description="ID of the education history to delete"),
    service: EducationHistoryService = Depends(get_education_history_service)
):
    """
    Delete an education history entry.
    
    This endpoint removes an education history entry from the system.
    
    Args:
        education_history_id: ID of the education history to delete
        service: EducationHistoryService (injected)
        
    Returns:
        No content (HTTP 204)
        
    Raises:
        HTTPException: If education history not found or error occurs
    """
    try:
        deleted = await service.delete_education_history(education_history_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education history with ID {education_history_id} not found"
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting education history: {str(e)}"
        )

@router.get("/{education_history_id}/degrees", summary="Get Degrees by Education History")
async def get_degrees_by_education_history(
    education_history_id: str = Path(..., description="ID of the education history"),
    service: EducationHistoryService = Depends(get_education_history_service)
):
    """
    Get all degrees associated with a specific education history.
    
    This endpoint returns all degrees that are associated with an education history,
    allowing to see which degrees were earned through a specific educational path.
    
    Args:
        education_history_id: ID of the education history
        service: EducationHistoryService (injected)
        
    Returns:
        List of degrees associated with the education history
        
    Raises:
        HTTPException: If education history not found or error occurs
    """
    try:
        education_history = await service.get_education_history_by_id(education_history_id)
        if not education_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education history with ID {education_history_id} not found"
            )
            
        degrees = await service.get_degrees_by_education_history(education_history_id)
        return degrees
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving degrees for education history: {str(e)}"
        ) 