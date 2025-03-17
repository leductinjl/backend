"""
Candidate Credential router module.

This module defines API endpoints for managing external credentials of candidates,
including certificates, awards, recognitions, and achievements from external sources.
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.services.candidate_credential_service import CandidateCredentialService
from app.api.dto.candidate_credential import (
    CandidateCredentialCreate,
    CandidateCredentialUpdate,
    CandidateCredentialResponse,
    CandidateCredentialListResponse
)

router = APIRouter(
    prefix="/candidate-credentials",
    tags=["Candidate Credentials"],
    responses={404: {"description": "Not found"}}
)

async def get_credential_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for CandidateCredentialService.
    
    Args:
        db: Database session
        
    Returns:
        CandidateCredentialService: Service instance for credential business logic
    """
    return CandidateCredentialService(db)

@router.get(
    "",
    response_model=CandidateCredentialListResponse,
    summary="List candidate credentials",
    description="Retrieve a list of candidate credentials with optional filtering and pagination."
)
async def get_credentials(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    credential_type: Optional[str] = Query(None, description="Filter by credential type (CERTIFICATE, AWARD, RECOGNITION, ACHIEVEMENT)"),
    issuing_organization: Optional[str] = Query(None, description="Filter by issuing organization"),
    issue_date_from: Optional[date] = Query(None, description="Filter by minimum issue date"),
    issue_date_to: Optional[date] = Query(None, description="Filter by maximum issue date"),
    service: CandidateCredentialService = Depends(get_credential_service)
):
    """
    Retrieve a list of candidate credentials with optional filtering and pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        candidate_id: Optional filter by candidate ID
        credential_type: Optional filter by credential type
        issuing_organization: Optional filter by issuing organization
        issue_date_from: Optional filter by minimum issue date
        issue_date_to: Optional filter by maximum issue date
        service: CandidateCredentialService instance
    """
    try:
        credentials, total = await service.get_credentials(
            skip=skip,
            limit=limit,
            candidate_id=candidate_id,
            credential_type=credential_type,
            issuing_organization=issuing_organization,
            issue_date_from=issue_date_from,
            issue_date_to=issue_date_to
        )
        
        # Convert to response DTOs
        credential_responses = [
            CandidateCredentialResponse.from_orm(credential)
            for credential in credentials
        ]
        
        return CandidateCredentialListResponse(
            items=credential_responses,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving candidate credentials: {str(e)}"
        )

@router.get(
    "/{credential_id}",
    response_model=CandidateCredentialResponse,
    summary="Get credential by ID",
    description="Retrieve a specific candidate credential by its ID."
)
async def get_credential(
    credential_id: str = Path(..., description="ID of the credential to retrieve"),
    service: CandidateCredentialService = Depends(get_credential_service)
):
    """
    Retrieve a specific candidate credential by its ID.
    
    Args:
        credential_id: ID of the credential to retrieve
        service: CandidateCredentialService instance
    """
    try:
        credential = await service.get_credential_by_id(credential_id)
        
        return CandidateCredentialResponse.from_orm(credential)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving the credential: {str(e)}"
        )

@router.get(
    "/candidate/{candidate_id}",
    response_model=CandidateCredentialListResponse,
    summary="Get credentials for a candidate",
    description="Retrieve all credentials for a specific candidate."
)
async def get_credentials_by_candidate(
    candidate_id: str = Path(..., description="ID of the candidate"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    credential_type: Optional[str] = Query(None, description="Filter by credential type"),
    service: CandidateCredentialService = Depends(get_credential_service)
):
    """
    Retrieve all credentials for a specific candidate with pagination.
    
    Args:
        candidate_id: ID of the candidate
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        credential_type: Optional filter by credential type
        service: CandidateCredentialService instance
    """
    try:
        credentials, total = await service.get_credentials_by_candidate(
            candidate_id=candidate_id,
            credential_type=credential_type,
            skip=skip,
            limit=limit
        )
        
        # Convert to response DTOs
        credential_responses = [
            CandidateCredentialResponse.from_orm(credential)
            for credential in credentials
        ]
        
        return CandidateCredentialListResponse(
            items=credential_responses,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving candidate credentials: {str(e)}"
        )

@router.post(
    "",
    response_model=CandidateCredentialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new credential",
    description="Create a new external credential for a candidate."
)
async def create_credential(
    credential_data: CandidateCredentialCreate,
    service: CandidateCredentialService = Depends(get_credential_service)
):
    """
    Create a new external credential for a candidate.
    
    Args:
        credential_data: Data for creating the credential
        service: CandidateCredentialService instance
    """
    try:
        created_credential = await service.create_credential(credential_data)
        
        return CandidateCredentialResponse.from_orm(created_credential)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the credential: {str(e)}"
        )

@router.put(
    "/{credential_id}",
    response_model=CandidateCredentialResponse,
    summary="Update a credential",
    description="Update an existing candidate credential."
)
async def update_credential(
    credential_id: str = Path(..., description="ID of the credential to update"),
    credential_data: CandidateCredentialUpdate = ...,
    service: CandidateCredentialService = Depends(get_credential_service)
):
    """
    Update an existing candidate credential.
    
    Args:
        credential_id: ID of the credential to update
        credential_data: Data for updating the credential
        service: CandidateCredentialService instance
    """
    try:
        updated_credential = await service.update_credential(
            credential_id=credential_id,
            credential_data=credential_data
        )
        
        return CandidateCredentialResponse.from_orm(updated_credential)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the credential: {str(e)}"
        )

@router.delete(
    "/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a credential",
    description="Delete an existing candidate credential."
)
async def delete_credential(
    credential_id: str = Path(..., description="ID of the credential to delete"),
    service: CandidateCredentialService = Depends(get_credential_service)
):
    """
    Delete an existing candidate credential.
    
    Args:
        credential_id: ID of the credential to delete
        service: CandidateCredentialService instance
    """
    try:
        await service.delete_credential(credential_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the credential: {str(e)}"
        ) 