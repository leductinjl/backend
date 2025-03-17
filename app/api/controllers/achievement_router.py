"""
Achievement router module.

This module provides API endpoints for managing achievement entries,
such as research, community service, sports, and arts accomplishments.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Response, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.infrastructure.database.connection import get_db
from app.api.dto.achievement import (
    AchievementCreate,
    AchievementUpdate,
    AchievementResponse,
    AchievementListResponse
)
from app.repositories.achievement_repository import AchievementRepository
from app.services.achievement_service import AchievementService

router = APIRouter(
    prefix="/achievements",
    tags=["Achievements"],
    responses={404: {"description": "Not found"}}
)

async def get_achievement_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for AchievementService
    
    Args:
        db: Database session
        
    Returns:
        AchievementService: Service instance for achievement business logic
    """
    repository = AchievementRepository(db)
    return AchievementService(repository)

@router.get("/", response_model=AchievementListResponse, summary="List Achievements")
async def get_achievements(
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    candidate_exam_id: Optional[str] = Query(None, description="Filter by candidate exam ID"),
    achievement_type: Optional[str] = Query(None, description="Filter by achievement type (Research, Community Service, Sports, Arts)"),
    organization: Optional[str] = Query(None, description="Filter by organization"),
    education_level: Optional[str] = Query(None, description="Filter by education level"),
    achievement_date_from: Optional[date] = Query(None, description="Filter by minimum achievement date"),
    achievement_date_to: Optional[date] = Query(None, description="Filter by maximum achievement date"),
    search: Optional[str] = Query(None, description="Search term for achievement name"),
    service: AchievementService = Depends(get_achievement_service)
):
    """
    Get list of achievements.
    
    This endpoint returns a list of all achievements, with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        candidate_exam_id: Filter by candidate exam ID
        achievement_type: Filter by achievement type (Research, Community Service, Sports, Arts)
        organization: Filter by organization
        education_level: Filter by education level
        achievement_date_from: Filter by minimum achievement date
        achievement_date_to: Filter by maximum achievement date
        search: Search term for achievement name
        service: AchievementService (injected)
        
    Returns:
        List of achievements with pagination metadata
    """
    try:
        return await service.get_all_achievements(
            skip, 
            limit, 
            candidate_exam_id, 
            achievement_type,
            organization,
            education_level,
            achievement_date_from, 
            achievement_date_to,
            search
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving achievements: {str(e)}"
        )

@router.get("/{achievement_id}", response_model=AchievementResponse, summary="Get Achievement Details")
async def get_achievement(
    achievement_id: str = Path(..., description="ID of the achievement to retrieve"),
    service: AchievementService = Depends(get_achievement_service)
):
    """
    Get detailed information about an achievement by ID.
    
    This endpoint returns detailed information about an achievement based on ID.
    
    Args:
        achievement_id: ID of the achievement to retrieve
        service: AchievementService (injected)
        
    Returns:
        Detailed information about the achievement
        
    Raises:
        HTTPException: If achievement not found or error occurs
    """
    try:
        achievement = await service.get_achievement_by_id(achievement_id)
        if not achievement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Achievement with ID {achievement_id} not found"
            )
        return achievement
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving achievement: {str(e)}"
        )

@router.get("/candidate-exam/{candidate_exam_id}", response_model=AchievementListResponse, summary="Get Achievements by Candidate Exam")
async def get_achievements_by_candidate_exam(
    candidate_exam_id: str = Path(..., description="ID of the candidate exam"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: AchievementService = Depends(get_achievement_service)
):
    """
    Get all achievements for a specific candidate exam.
    
    This endpoint returns all achievements associated with a specific candidate exam.
    
    Args:
        candidate_exam_id: ID of the candidate exam
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: AchievementService (injected)
        
    Returns:
        List of achievements for the specified candidate exam with pagination metadata
    """
    try:
        return await service.get_achievements_by_candidate_exam(candidate_exam_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving achievements for candidate exam {candidate_exam_id}: {str(e)}"
        )

@router.get("/type/{achievement_type}", response_model=AchievementListResponse, summary="Get Achievements by Type")
async def get_achievements_by_type(
    achievement_type: str = Path(..., description="Type of the achievement"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: AchievementService = Depends(get_achievement_service)
):
    """
    Get all achievements of a specific type.
    
    This endpoint returns all achievements of a specific type.
    
    Args:
        achievement_type: Type of the achievement (Research, Community Service, Sports, Arts)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: AchievementService (injected)
        
    Returns:
        List of achievements of the specified type with pagination metadata
    """
    try:
        return await service.get_achievements_by_achievement_type(achievement_type, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving achievements for achievement type {achievement_type}: {str(e)}"
        )

@router.get("/organization/{organization}", response_model=AchievementListResponse, summary="Get Achievements by Organization")
async def get_achievements_by_organization(
    organization: str = Path(..., description="Name of the organization"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: AchievementService = Depends(get_achievement_service)
):
    """
    Get all achievements recognized by a specific organization.
    
    This endpoint returns all achievements associated with a specific organization.
    
    Args:
        organization: Name of the organization
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: AchievementService (injected)
        
    Returns:
        List of achievements by the specified organization with pagination metadata
    """
    try:
        return await service.get_achievements_by_organization(organization, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving achievements for organization {organization}: {str(e)}"
        )

@router.post("/", response_model=AchievementResponse, status_code=status.HTTP_201_CREATED, summary="Create Achievement")
async def create_achievement(
    achievement_data: AchievementCreate = Body(..., description="Achievement information to create"),
    service: AchievementService = Depends(get_achievement_service)
):
    """
    Create a new achievement.
    
    This endpoint creates a new achievement with the provided information.
    
    Args:
        achievement_data: Achievement information to create
        service: AchievementService (injected)
        
    Returns:
        Created achievement information
        
    Raises:
        HTTPException: If an error occurs during achievement creation
    """
    try:
        return await service.create_achievement(achievement_data.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred while creating achievement: {str(e)}"
        )

@router.put("/{achievement_id}", response_model=AchievementResponse, summary="Update Achievement")
async def update_achievement(
    achievement_id: str = Path(..., description="ID of the achievement to update"),
    achievement_data: AchievementUpdate = Body(..., description="Updated achievement information"),
    service: AchievementService = Depends(get_achievement_service)
):
    """
    Update an existing achievement.
    
    This endpoint updates information of an existing achievement.
    
    Args:
        achievement_id: ID of the achievement to update
        achievement_data: Updated achievement information
        service: AchievementService (injected)
        
    Returns:
        Updated achievement information
        
    Raises:
        HTTPException: If achievement not found or error occurs
    """
    try:
        achievement = await service.update_achievement(
            achievement_id, 
            achievement_data.model_dump(exclude_unset=True)
        )
        if not achievement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Achievement with ID {achievement_id} not found"
            )
        return achievement
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating achievement: {str(e)}"
        )

@router.delete("/{achievement_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Achievement")
async def delete_achievement(
    achievement_id: str = Path(..., description="ID of the achievement to delete"),
    service: AchievementService = Depends(get_achievement_service)
):
    """
    Delete an achievement.
    
    This endpoint removes an achievement from the system.
    
    Args:
        achievement_id: ID of the achievement to delete
        service: AchievementService (injected)
        
    Returns:
        No content (HTTP 204)
        
    Raises:
        HTTPException: If achievement not found or error occurs
    """
    try:
        deleted = await service.delete_achievement(achievement_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Achievement with ID {achievement_id} not found"
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting achievement: {str(e)}"
        ) 