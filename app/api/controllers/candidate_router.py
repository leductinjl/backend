"""
Candidate router module.

This module provides endpoints for accessing and managing candidate information.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path, Body, Response
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.candidate import (
    CandidateResponse, 
    CandidateDetailResponse,
    CandidateCreate,
    CandidateUpdate,
    PersonalInfoUpdate
)
from app.api.dto.education_history import EducationHistoryResponse
# from app.api.dto.candidate_exam import ExamHistoryResponse, SubjectScore
from app.repositories.candidate_repository import CandidateRepository
from app.services.candidate_service import CandidateService

router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
    responses={404: {"description": "Not found"}}
)

async def get_candidate_service(
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency injection for CandidateService
    
    Args:
        db: Database session
        
    Returns:
        CandidateService: Service instance to handle business logic related to candidates
    """
    candidate_repo = CandidateRepository(db)
    return CandidateService(candidate_repo)

@router.get("/", response_model=List[CandidateResponse], summary="List Candidates")
async def get_candidates(
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Get list of candidates.
    
    This endpoint returns a list of all candidates, with pagination support.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: CandidateService (injected)
        
    Returns:
        List[CandidateResponse]: List of candidates
    """
    try:
        candidates = await service.get_all_candidates(skip, limit)
        return candidates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving candidate list: {str(e)}"
        )

@router.get("/{candidate_id}", response_model=CandidateDetailResponse, summary="Get Candidate Details")
async def get_candidate(
    candidate_id: str = Path(..., description="ID of the candidate"),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Get detailed information about a candidate by ID.
    
    This endpoint returns detailed information about a candidate based on ID.
    
    Args:
        candidate_id: ID of the candidate
        service: CandidateService (injected)
        
    Returns:
        CandidateDetailResponse: Detailed information about the candidate
        
    Raises:
        HTTPException: If candidate not found or error occurs
    """
    try:
        candidate = await service.get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {candidate_id} not found"
            )
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving candidate information: {str(e)}"
        )

@router.get("/search/", response_model=List[CandidateResponse], summary="Search Candidates")
async def search_candidates(
    q: str = Query(..., min_length=1, description="Search keyword"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Search candidates by keyword.
    
    This endpoint searches for candidates based on name or personal information.
    
    Args:
        q: Search keyword
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: CandidateService (injected)
        
    Returns:
        List[CandidateResponse]: List of candidates matching the keyword
    """
    try:
        candidates = await service.search_candidates(q, skip, limit)
        return candidates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while searching for candidates: {str(e)}"
        )

@router.post("/", response_model=CandidateDetailResponse, status_code=status.HTTP_201_CREATED, summary="Create Candidate")
async def create_candidate(
    candidate_data: CandidateCreate = Body(..., description="Candidate information to create"),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Create a new candidate.
    
    This endpoint creates a new candidate with the provided personal information.
    
    Args:
        candidate_data: Candidate information to create
        service: CandidateService (injected)
        
    Returns:
        CandidateDetailResponse: Detailed information of the created candidate
        
    Raises:
        HTTPException: If an error occurs during candidate creation
    """
    try:
        candidate = await service.create_candidate(candidate_data.model_dump())
        return candidate
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create new candidate: {str(e)}"
        )

@router.put("/{candidate_id}", response_model=CandidateDetailResponse, summary="Update Candidate")
async def update_candidate(
    candidate_id: str = Path(..., description="ID of the candidate to update"),
    candidate_data: CandidateUpdate = Body(..., description="Candidate information to update"),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Update candidate information.
    
    This endpoint updates information of an existing candidate.
    
    Args:
        candidate_id: ID of the candidate to update
        candidate_data: Candidate information to update
        service: CandidateService (injected)
        
    Returns:
        CandidateDetailResponse: Detailed information of the updated candidate
        
    Raises:
        HTTPException: If candidate not found or an error occurs during update
    """
    try:
        candidate = await service.update_candidate(candidate_id, candidate_data.model_dump(exclude_unset=True))
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {candidate_id} not found"
            )
        
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating candidate: {str(e)}"
        )

@router.put("/{candidate_id}/personal-info", response_model=CandidateDetailResponse, summary="Update Candidate Personal Info")
async def update_personal_info(
    candidate_id: str = Path(..., description="ID of the candidate whose personal info to update"),
    personal_info_data: PersonalInfoUpdate = Body(..., description="Personal information to update"),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Update only the personal information of a candidate.
    
    This endpoint updates only the personal information of an existing candidate,
    leaving the candidate's basic data unchanged.
    
    Args:
        candidate_id: ID of the candidate whose personal info to update
        personal_info_data: Personal information to update
        service: CandidateService (injected)
        
    Returns:
        CandidateDetailResponse: Detailed information of the candidate after update
        
    Raises:
        HTTPException: If candidate not found or an error occurs during update
    """
    try:
        candidate = await service.update_candidate_personal_info(
            candidate_id, 
            personal_info_data.model_dump(exclude_unset=True)
        )
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {candidate_id} not found"
            )
        
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating personal information: {str(e)}"
        )

@router.patch("/{candidate_id}", response_model=CandidateDetailResponse, summary="Partially Update Candidate")
async def patch_candidate(
    candidate_id: str = Path(..., description="ID of the candidate to update"),
    candidate_data: CandidateUpdate = Body(..., description="Partial candidate information to update"),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Partially update candidate information.
    
    This endpoint performs a partial update on candidate information, updating only 
    the fields that are provided in the request body, while leaving other fields unchanged.
    This is in contrast to PUT which conceptually replaces the entire resource.
    
    Args:
        candidate_id: ID of the candidate to partially update
        candidate_data: Partial candidate information to update
        service: CandidateService (injected)
        
    Returns:
        CandidateDetailResponse: Detailed information of the updated candidate
        
    Raises:
        HTTPException: If candidate not found or an error occurs during update
    """
    try:
        # Use the same service method as PUT but it's clear this is for partial updates
        candidate = await service.update_candidate(candidate_id, candidate_data.model_dump(exclude_unset=True))
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {candidate_id} not found"
            )
        
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while partially updating candidate: {str(e)}"
        )

@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Candidate")
async def delete_candidate(
    candidate_id: str = Path(..., description="ID of the candidate to delete"),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Delete a candidate.
    
    This endpoint removes a candidate from the system.
    
    Args:
        candidate_id: ID of the candidate to delete
        service: CandidateService (injected)
        
    Returns:
        No content (HTTP 204)
        
    Raises:
        HTTPException: If candidate not found or error occurs
    """
    try:
        deleted = await service.delete_candidate(candidate_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {candidate_id} not found"
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting candidate: {str(e)}"
        ) 