"""
Education Level router module.

This module provides API endpoints for managing education levels.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Response, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.education_level import (
    EducationLevelCreate,
    EducationLevelUpdate,
    EducationLevelResponse,
    EducationLevelListResponse
)
from app.repositories.education_level_repository import EducationLevelRepository
from app.services.education_level_service import EducationLevelService

router = APIRouter(
    prefix="/education-levels",
    tags=["Education Levels"],
    responses={404: {"description": "Not found"}}
)

async def get_education_level_service(db: AsyncSession = Depends(get_db)):
    """Dependency to inject EducationLevelService into endpoints."""
    repository = EducationLevelRepository(db)
    return EducationLevelService(repository)

@router.get("/", response_model=EducationLevelListResponse, summary="List Education Levels")
async def get_education_levels(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    code: Optional[str] = Query(None, description="Filter by code (partial match)"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    service: EducationLevelService = Depends(get_education_level_service)
):
    """
    Retrieve a list of education levels with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        code: Filter by code (partial match)
        name: Filter by name (partial match)
        
    Returns:
        List of education levels with pagination metadata
    """
    try:
        return await service.get_all_education_levels(
            skip=skip,
            limit=limit,
            code=code,
            name=name
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve education levels: {str(e)}"
        )

@router.get("/{education_level_id}", response_model=EducationLevelResponse, summary="Get Education Level")
async def get_education_level(
    education_level_id: str = Path(..., description="ID of the education level to retrieve"),
    service: EducationLevelService = Depends(get_education_level_service)
):
    """
    Retrieve detailed information about a specific education level.
    
    Args:
        education_level_id: ID of the education level to retrieve
        
    Returns:
        Education level details
        
    Raises:
        HTTPException: If the education level is not found
    """
    try:
        education_level = await service.get_education_level_by_id(education_level_id)
        if not education_level:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education level with ID {education_level_id} not found"
            )
        return education_level
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve education level: {str(e)}"
        )

@router.get("/code/{code}", response_model=EducationLevelResponse, summary="Get Education Level by Code")
async def get_education_level_by_code(
    code: str = Path(..., description="Code of the education level to retrieve"),
    service: EducationLevelService = Depends(get_education_level_service)
):
    """
    Retrieve detailed information about a specific education level by its code.
    
    Args:
        code: Unique code of the education level
        
    Returns:
        Education level details
        
    Raises:
        HTTPException: If the education level is not found
    """
    try:
        education_level = await service.get_education_level_by_code(code)
        if not education_level:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education level with code {code} not found"
            )
        return education_level
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve education level: {str(e)}"
        )

@router.post("/", response_model=EducationLevelResponse, status_code=status.HTTP_201_CREATED, summary="Create Education Level")
async def create_education_level(
    education_level_data: EducationLevelCreate = Body(..., description="Education level data"),
    service: EducationLevelService = Depends(get_education_level_service)
):
    """
    Create a new education level.
    
    Args:
        education_level_data: Education level data
        
    Returns:
        Created education level
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        return await service.create_education_level(education_level_data.dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create education level: {str(e)}"
        )

@router.put("/{education_level_id}", response_model=EducationLevelResponse, summary="Update Education Level")
async def update_education_level(
    education_level_id: str = Path(..., description="ID of the education level to update"),
    education_level_data: EducationLevelUpdate = Body(..., description="Updated education level data"),
    service: EducationLevelService = Depends(get_education_level_service)
):
    """
    Update an existing education level.
    
    Args:
        education_level_id: ID of the education level to update
        education_level_data: Updated education level data
        
    Returns:
        Updated education level
        
    Raises:
        HTTPException: If the education level is not found or update fails
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in education_level_data.dict().items() if v is not None}
        
        education_level = await service.update_education_level(education_level_id, update_data)
        if not education_level:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education level with ID {education_level_id} not found"
            )
        return education_level
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update education level: {str(e)}"
        )

@router.delete("/{education_level_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Education Level")
async def delete_education_level(
    education_level_id: str = Path(..., description="ID of the education level to delete"),
    service: EducationLevelService = Depends(get_education_level_service)
):
    """
    Delete an education level.
    
    Args:
        education_level_id: ID of the education level to delete
        
    Returns:
        No content
        
    Raises:
        HTTPException: If the education level is not found or deletion fails
    """
    try:
        deleted = await service.delete_education_level(education_level_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education level with ID {education_level_id} not found"
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete education level: {str(e)}"
        ) 