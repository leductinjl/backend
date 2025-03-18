"""
Award router module.

This module provides API endpoints for managing award entries,
such as medals, certifications, and other distinctions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Response, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.infrastructure.database.connection import get_db
from app.repositories.award_repository import AwardRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.services.award_service import AwardService
from app.api.dto.award import (
    AwardCreate,
    AwardUpdate,
    AwardResponse,
    AwardListResponse
)

router = APIRouter(
    prefix="/awards",
    tags=["Awards"],
    responses={404: {"description": "Not found"}}
)

async def get_award_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for AwardService.
    
    Args:
        db: Database session
        
    Returns:
        AwardService: Service instance for award business logic
    """
    award_repository = AwardRepository(db)
    candidate_exam_repository = CandidateExamRepository(db)
    return AwardService(award_repository, candidate_exam_repository)

@router.get("/", response_model=AwardListResponse, summary="List Awards")
async def get_awards(
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    candidate_exam_id: Optional[str] = Query(None, description="Filter by candidate exam ID"),
    award_type: Optional[str] = Query(None, description="Filter by award type (First, Second, Third, Gold Medal, Silver Medal)"),
    education_level: Optional[str] = Query(None, description="Filter by education level"),
    award_date_from: Optional[date] = Query(None, description="Filter by minimum award date"),
    award_date_to: Optional[date] = Query(None, description="Filter by maximum award date"),
    service: AwardService = Depends(get_award_service)
):
    """
    Get list of awards.
    
    This endpoint returns a list of all awards, with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        candidate_exam_id: Filter by candidate exam ID
        award_type: Filter by award type (First, Second, Third, Gold Medal, Silver Medal)
        education_level: Filter by education level
        award_date_from: Filter by minimum award date
        award_date_to: Filter by maximum award date
        service: AwardService (injected)
        
    Returns:
        List of awards with pagination metadata
    """
    try:
        return await service.get_all_awards(
            skip, 
            limit, 
            candidate_exam_id, 
            award_type, 
            education_level, 
            award_date_from, 
            award_date_to
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving awards: {str(e)}"
        )

@router.get("/{award_id}", response_model=AwardResponse, summary="Get Award Details")
async def get_award(
    award_id: str = Path(..., description="ID of the award to retrieve"),
    service: AwardService = Depends(get_award_service)
):
    """
    Get detailed information about an award by ID.
    
    This endpoint returns detailed information about an award based on ID.
    
    Args:
        award_id: ID of the award to retrieve
        service: AwardService (injected)
        
    Returns:
        Detailed information about the award
        
    Raises:
        HTTPException: If award not found or error occurs
    """
    try:
        award = await service.get_award_by_id(award_id)
        if not award:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Award with ID {award_id} not found"
            )
        return award
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving award: {str(e)}"
        )

@router.get("/candidate-exam/{candidate_exam_id}", response_model=AwardListResponse, summary="Get Awards by Candidate Exam")
async def get_awards_by_candidate_exam(
    candidate_exam_id: str = Path(..., description="ID of the candidate exam"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: AwardService = Depends(get_award_service)
):
    """
    Get all awards for a specific candidate exam.
    
    This endpoint returns all awards associated with a specific candidate exam.
    
    Args:
        candidate_exam_id: ID of the candidate exam
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: AwardService (injected)
        
    Returns:
        List of awards for the specified candidate exam with pagination metadata
    """
    try:
        return await service.get_awards_by_candidate_exam(candidate_exam_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving awards for candidate exam {candidate_exam_id}: {str(e)}"
        )

@router.get("/candidate/{candidate_id}", response_model=AwardListResponse, summary="Get Awards by Candidate")
async def get_awards_by_candidate(
    candidate_id: str = Path(..., description="ID of the candidate"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: AwardService = Depends(get_award_service)
):
    """
    Get all awards for a specific candidate across all exams.
    
    This endpoint returns all awards associated with a specific candidate across all exams.
    
    Args:
        candidate_id: ID of the candidate
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: AwardService (injected)
        
    Returns:
        List of awards for the specified candidate with pagination metadata
    """
    try:
        return await service.get_awards_by_candidate_id(candidate_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving awards for candidate {candidate_id}: {str(e)}"
        )

@router.get("/type/{award_type}", response_model=AwardListResponse, summary="Get Awards by Type")
async def get_awards_by_type(
    award_type: str = Path(..., description="Type of the award"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: AwardService = Depends(get_award_service)
):
    """
    Get all awards of a specific type.
    
    This endpoint returns all awards of a specific type.
    
    Args:
        award_type: Type of the award (First, Second, Third, Gold Medal, Silver Medal)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: AwardService (injected)
        
    Returns:
        List of awards of the specified type with pagination metadata
    """
    try:
        return await service.get_awards_by_award_type(award_type, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving awards for award type {award_type}: {str(e)}"
        )

@router.post("/", response_model=AwardResponse, status_code=status.HTTP_201_CREATED, summary="Create Award")
async def create_award(
    award_data: AwardCreate = Body(..., description="Award information to create"),
    service: AwardService = Depends(get_award_service)
):
    """
    Create a new award.
    
    This endpoint creates a new award with the provided information.
    
    Args:
        award_data: Award information to create
        service: AwardService (injected)
        
    Returns:
        Created award information
        
    Raises:
        HTTPException: If an error occurs during award creation
    """
    try:
        return await service.create_award(award_data.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred while creating award: {str(e)}"
        )

@router.put("/{award_id}", response_model=AwardResponse, summary="Update Award")
async def update_award(
    award_id: str = Path(..., description="ID of the award to update"),
    award_data: AwardUpdate = Body(..., description="Updated award information"),
    service: AwardService = Depends(get_award_service)
):
    """
    Update an existing award.
    
    This endpoint updates information of an existing award.
    
    Args:
        award_id: ID of the award to update
        award_data: Updated award information
        service: AwardService (injected)
        
    Returns:
        Updated award information
        
    Raises:
        HTTPException: If award not found or error occurs
    """
    try:
        award = await service.update_award(
            award_id, 
            award_data.model_dump(exclude_unset=True)
        )
        if not award:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Award with ID {award_id} not found"
            )
        return award
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating award: {str(e)}"
        )

@router.delete("/{award_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Award")
async def delete_award(
    award_id: str = Path(..., description="ID of the award to delete"),
    service: AwardService = Depends(get_award_service)
):
    """
    Delete an award.
    
    This endpoint removes an award from the system.
    
    Args:
        award_id: ID of the award to delete
        service: AwardService (injected)
        
    Returns:
        No content (HTTP 204)
        
    Raises:
        HTTPException: If award not found or error occurs
    """
    try:
        deleted = await service.delete_award(award_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Award with ID {award_id} not found"
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting award: {str(e)}"
        ) 