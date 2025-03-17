"""
Recognition router module.

This module provides API endpoints for managing recognition entries,
such as certificates of completion or participation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Response, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.infrastructure.database.connection import get_db
from app.api.dto.recognition import (
    RecognitionCreate,
    RecognitionUpdate,
    RecognitionResponse,
    RecognitionListResponse
)
from app.repositories.recognition_repository import RecognitionRepository
from app.services.recognition_service import RecognitionService

router = APIRouter(
    prefix="/recognitions",
    tags=["Recognitions"],
    responses={404: {"description": "Not found"}}
)

async def get_recognition_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for RecognitionService
    
    Args:
        db: Database session
        
    Returns:
        RecognitionService: Service instance for recognition business logic
    """
    repository = RecognitionRepository(db)
    return RecognitionService(repository)

@router.get("/", response_model=RecognitionListResponse, summary="List Recognitions")
async def get_recognitions(
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    candidate_exam_id: Optional[str] = Query(None, description="Filter by candidate exam ID"),
    recognition_type: Optional[str] = Query(None, description="Filter by recognition type (Completion, Participation, Appreciation)"),
    issuing_organization: Optional[str] = Query(None, description="Filter by issuing organization"),
    issue_date_from: Optional[date] = Query(None, description="Filter by minimum issue date"),
    issue_date_to: Optional[date] = Query(None, description="Filter by maximum issue date"),
    service: RecognitionService = Depends(get_recognition_service)
):
    """
    Get list of recognitions.
    
    This endpoint returns a list of all recognitions, with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        candidate_exam_id: Filter by candidate exam ID
        recognition_type: Filter by recognition type (Completion, Participation, Appreciation)
        issuing_organization: Filter by issuing organization
        issue_date_from: Filter by minimum issue date
        issue_date_to: Filter by maximum issue date
        service: RecognitionService (injected)
        
    Returns:
        List of recognitions with pagination metadata
    """
    try:
        return await service.get_all_recognitions(
            skip, 
            limit, 
            candidate_exam_id, 
            recognition_type, 
            issuing_organization, 
            issue_date_from, 
            issue_date_to
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving recognitions: {str(e)}"
        )

@router.get("/{recognition_id}", response_model=RecognitionResponse, summary="Get Recognition Details")
async def get_recognition(
    recognition_id: str = Path(..., description="ID of the recognition to retrieve"),
    service: RecognitionService = Depends(get_recognition_service)
):
    """
    Get detailed information about a recognition by ID.
    
    This endpoint returns detailed information about a recognition based on ID.
    
    Args:
        recognition_id: ID of the recognition to retrieve
        service: RecognitionService (injected)
        
    Returns:
        Detailed information about the recognition
        
    Raises:
        HTTPException: If recognition not found or error occurs
    """
    try:
        recognition = await service.get_recognition_by_id(recognition_id)
        if not recognition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recognition with ID {recognition_id} not found"
            )
        return recognition
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving recognition: {str(e)}"
        )

@router.get("/candidate-exam/{candidate_exam_id}", response_model=RecognitionListResponse, summary="Get Recognitions by Candidate Exam")
async def get_recognitions_by_candidate_exam(
    candidate_exam_id: str = Path(..., description="ID of the candidate exam"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: RecognitionService = Depends(get_recognition_service)
):
    """
    Get all recognitions for a specific candidate exam.
    
    This endpoint returns all recognitions associated with a specific candidate exam.
    
    Args:
        candidate_exam_id: ID of the candidate exam
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: RecognitionService (injected)
        
    Returns:
        List of recognitions for the specified candidate exam with pagination metadata
    """
    try:
        return await service.get_recognitions_by_candidate_exam(candidate_exam_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving recognitions for candidate exam {candidate_exam_id}: {str(e)}"
        )

@router.get("/organization/{organization}", response_model=RecognitionListResponse, summary="Get Recognitions by Issuing Organization")
async def get_recognitions_by_organization(
    organization: str = Path(..., description="Name of the issuing organization"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: RecognitionService = Depends(get_recognition_service)
):
    """
    Get all recognitions issued by a specific organization.
    
    This endpoint returns all recognitions issued by a specific organization.
    
    Args:
        organization: Name of the issuing organization
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: RecognitionService (injected)
        
    Returns:
        List of recognitions issued by the specified organization with pagination metadata
    """
    try:
        return await service.get_recognitions_by_issuing_organization(organization, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving recognitions for organization {organization}: {str(e)}"
        )

@router.post("/", response_model=RecognitionResponse, status_code=status.HTTP_201_CREATED, summary="Create Recognition")
async def create_recognition(
    recognition_data: RecognitionCreate = Body(..., description="Recognition information to create"),
    service: RecognitionService = Depends(get_recognition_service)
):
    """
    Create a new recognition.
    
    This endpoint creates a new recognition with the provided information.
    
    Args:
        recognition_data: Recognition information to create
        service: RecognitionService (injected)
        
    Returns:
        Created recognition information
        
    Raises:
        HTTPException: If an error occurs during recognition creation
    """
    try:
        return await service.create_recognition(recognition_data.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred while creating recognition: {str(e)}"
        )

@router.put("/{recognition_id}", response_model=RecognitionResponse, summary="Update Recognition")
async def update_recognition(
    recognition_id: str = Path(..., description="ID of the recognition to update"),
    recognition_data: RecognitionUpdate = Body(..., description="Updated recognition information"),
    service: RecognitionService = Depends(get_recognition_service)
):
    """
    Update an existing recognition.
    
    This endpoint updates information of an existing recognition.
    
    Args:
        recognition_id: ID of the recognition to update
        recognition_data: Updated recognition information
        service: RecognitionService (injected)
        
    Returns:
        Updated recognition information
        
    Raises:
        HTTPException: If recognition not found or error occurs
    """
    try:
        recognition = await service.update_recognition(
            recognition_id, 
            recognition_data.model_dump(exclude_unset=True)
        )
        if not recognition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recognition with ID {recognition_id} not found"
            )
        return recognition
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating recognition: {str(e)}"
        )

@router.delete("/{recognition_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Recognition")
async def delete_recognition(
    recognition_id: str = Path(..., description="ID of the recognition to delete"),
    service: RecognitionService = Depends(get_recognition_service)
):
    """
    Delete a recognition.
    
    This endpoint removes a recognition from the system.
    
    Args:
        recognition_id: ID of the recognition to delete
        service: RecognitionService (injected)
        
    Returns:
        No content (HTTP 204)
        
    Raises:
        HTTPException: If recognition not found or error occurs
    """
    try:
        deleted = await service.delete_recognition(recognition_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recognition with ID {recognition_id} not found"
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting recognition: {str(e)}"
        ) 