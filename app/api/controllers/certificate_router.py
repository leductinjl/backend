"""
Certificate router module.

This module provides API endpoints for managing certificates issued to candidates.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path, Body, Response
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.infrastructure.database.connection import get_db
from app.api.dto.certificate import (
    CertificateCreate,
    CertificateUpdate,
    CertificateResponse,
    CertificateDetailResponse,
    CertificateListResponse
)
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.services.certificate_service import CertificateService

router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"],
    responses={404: {"description": "Not found"}}
)

async def get_certificate_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for CertificateService.
    
    Args:
        db: Database session
        
    Returns:
        CertificateService: Service instance for certificate business logic
    """
    certificate_repository = CertificateRepository(db)
    candidate_repository = CandidateRepository(db)
    exam_repository = ExamRepository(db)
    candidate_exam_repository = CandidateExamRepository(db)
    
    return CertificateService(
        certificate_repository,
        candidate_repository,
        exam_repository,
        candidate_exam_repository
    )

@router.get("/", response_model=CertificateListResponse, summary="List Certificates")
async def get_certificates(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for certificate number or related information"),
    candidate_exam_id: Optional[str] = Query(None, description="Filter by candidate exam ID"),
    issue_date_after: Optional[date] = Query(None, description="Filter by certificates issued after date"),
    issue_date_before: Optional[date] = Query(None, description="Filter by certificates issued before date"),
    sort_field: Optional[str] = Query(None, description="Field to sort by"),
    sort_dir: Optional[str] = Query(None, description="Sort direction ('asc' or 'desc')"),
    service: CertificateService = Depends(get_certificate_service)
):
    """
    Retrieve a list of certificates with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        search: Search term for filtering
        candidate_exam_id: Filter by candidate exam ID
        issue_date_after: Filter by certificates issued after date
        issue_date_before: Filter by certificates issued before date
        sort_field: Field to sort by
        sort_dir: Sort direction ('asc' or 'desc')
        service: CertificateService instance
        
    Returns:
        Paginated list of certificates
    """
    certificates, total = await service.get_all_certificates(
        skip=skip,
        limit=limit,
        search=search,
        candidate_exam_id=candidate_exam_id,
        issue_date_after=issue_date_after,
        issue_date_before=issue_date_before,
        sort_field=sort_field,
        sort_dir=sort_dir
    )
    
    return CertificateListResponse(
        items=certificates,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{certificate_id}", response_model=CertificateDetailResponse, summary="Get Certificate by ID")
async def get_certificate(
    certificate_id: str = Path(..., description="The unique identifier of the certificate"),
    service: CertificateService = Depends(get_certificate_service)
):
    """
    Retrieve a specific certificate by its ID.
    
    Args:
        certificate_id: The unique identifier of the certificate
        service: CertificateService instance
        
    Returns:
        The certificate if found
        
    Raises:
        HTTPException: If the certificate is not found
    """
    certificate = await service.get_certificate_by_id(certificate_id)
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID {certificate_id} not found"
        )
    
    return certificate

@router.get("/candidate-exam/{candidate_exam_id}", response_model=List[CertificateDetailResponse], summary="Get Certificates by Candidate Exam ID")
async def get_certificates_by_candidate_exam(
    candidate_exam_id: str = Path(..., description="The ID of the candidate exam"),
    service: CertificateService = Depends(get_certificate_service)
):
    """
    Retrieve all certificates for a specific candidate exam.
    
    Args:
        candidate_exam_id: The ID of the candidate exam
        service: CertificateService instance
        
    Returns:
        List of certificates for the specified candidate exam
    """
    certificates = await service.get_certificates_by_candidate_exam_id(candidate_exam_id)
    return certificates

@router.post(
    "/", 
    response_model=CertificateDetailResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Certificate"
)
async def create_certificate(
    certificate_data: CertificateCreate = Body(..., description="Certificate data to create"),
    service: CertificateService = Depends(get_certificate_service)
):
    """
    Create a new certificate.
    
    Args:
        certificate_data: Certificate data to create
        service: CertificateService instance
        
    Returns:
        The created certificate
        
    Raises:
        HTTPException: If the certificate creation fails
    """
    certificate = await service.create_certificate(certificate_data.model_dump())
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate creation failed. Check that the candidate exam ID exists."
        )
    
    return await service.get_certificate_by_id(certificate.certificate_id)

@router.put("/{certificate_id}", response_model=CertificateDetailResponse, summary="Update Certificate")
async def update_certificate(
    certificate_id: str = Path(..., description="The unique identifier of the certificate"),
    certificate_data: CertificateUpdate = Body(..., description="Certificate data to update"),
    service: CertificateService = Depends(get_certificate_service)
):
    """
    Update an existing certificate.
    
    Args:
        certificate_id: The unique identifier of the certificate
        certificate_data: Certificate data to update
        service: CertificateService instance
        
    Returns:
        The updated certificate
        
    Raises:
        HTTPException: If the certificate is not found
    """
    certificate = await service.update_certificate(certificate_id, certificate_data.model_dump(exclude_unset=True))
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID {certificate_id} not found"
        )
    
    return await service.get_certificate_by_id(certificate_id)

@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Certificate")
async def delete_certificate(
    certificate_id: str = Path(..., description="The unique identifier of the certificate"),
    service: CertificateService = Depends(get_certificate_service)
):
    """
    Delete a certificate.
    
    Args:
        certificate_id: The unique identifier of the certificate
        service: CertificateService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the certificate is not found
    """
    deleted = await service.delete_certificate(certificate_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID {certificate_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)