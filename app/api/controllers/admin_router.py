"""
Admin router module.

This module provides endpoints for admin operations like managing candidates,
exams, schools, and other administrative tasks. All endpoints in this router
require admin authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.infrastructure.database.connection import get_db
from app.infrastructure.ontology.neo4j_connection import get_neo4j
from app.infrastructure.cache.redis_connection import get_redis
from app.repositories.candidate_repository import CandidateRepository
from app.graph_repositories.candidate_graph_repository import CandidateGraphRepository
from app.services.candidate_service import CandidateService
from app.api.dto.candidate import (
    CandidateCreate, 
    CandidateUpdate, 
    CandidateResponse, 
    CandidateDetailResponse
)
# Import auth router
from app.api.controllers.admin_auth import router as auth_router

# Create main admin router
router = APIRouter()

# Include the auth router
router.include_router(auth_router, tags=["Admin Authentication"])

# Dependency to check if user is authenticated as admin
async def get_current_admin(request: Request):
    """
    Dependency to verify admin authentication.
    
    The authentication middleware already handles token validation,
    but this provides an extra check and clearer error messages.
    
    Args:
        request: The HTTP request with admin user information
        
    Returns:
        dict: Admin user information
        
    Raises:
        HTTPException: If user is not authenticated as admin
    """
    if not request.state.is_authenticated or not request.state.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return request.state.user

async def get_candidate_service(
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j)
):
    """Dependency to inject CandidateService into API endpoints"""
    candidate_repo = CandidateRepository(db)
    candidate_graph_repo = CandidateGraphRepository(neo4j)
    return CandidateService(candidate_repo, candidate_graph_repo)

@router.get("/dashboard", summary="Admin Dashboard")
async def admin_dashboard(admin: dict = Depends(get_current_admin)):
    """
    Admin dashboard overview.
    
    Returns summary information for the admin dashboard including counts
    of candidates, exams, and schools in the system.
    
    Args:
        admin: The authenticated admin user (from dependency)
        
    Returns:
        dict: Dashboard summary data
    """
    # Here you would typically gather dashboard stats
    return {
        "admin": admin["email"],
        "dashboard": {
            "candidate_count": 0,  # Replace with actual count
            "exam_count": 0,       # Replace with actual count
            "school_count": 0      # Replace with actual count
        }
    }

@router.post("/candidates", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED, summary="Create Candidate")
async def create_candidate(
    candidate: CandidateCreate,
    admin: dict = Depends(get_current_admin),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Create a new candidate in the system.
    
    This endpoint allows admins to create new candidate entries
    with their personal information.
    
    Args:
        candidate: The candidate data to create
        admin: The authenticated admin user (from dependency)
        service: The CandidateService instance (from dependency)
        
    Returns:
        CandidateResponse: The created candidate
    """
    return await service.create_candidate(candidate.dict())

@router.put("/candidates/{candidate_id}", response_model=CandidateResponse, summary="Update Candidate")
async def update_candidate(
    candidate_id: str,
    candidate: CandidateUpdate,
    admin: dict = Depends(get_current_admin),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Update an existing candidate's information.
    
    This endpoint allows admins to update candidate information
    such as personal details and education records.
    
    Args:
        candidate_id: The ID of the candidate to update
        candidate: The updated candidate data
        admin: The authenticated admin user (from dependency)
        service: The CandidateService instance (from dependency)
        
    Returns:
        CandidateResponse: The updated candidate
        
    Raises:
        HTTPException: If candidate not found
    """
    updated_candidate = await service.update_candidate(candidate_id, candidate.dict(exclude_unset=True))
    if not updated_candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found"
        )
    return updated_candidate

@router.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Candidate")
async def delete_candidate(
    candidate_id: str,
    admin: dict = Depends(get_current_admin),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Delete a candidate from the system.
    
    This endpoint allows admins to permanently remove a candidate
    and all associated data from the system.
    
    Args:
        candidate_id: The ID of the candidate to delete
        admin: The authenticated admin user (from dependency)
        service: The CandidateService instance (from dependency)
        
    Raises:
        HTTPException: If candidate not found
    """
    deleted = await service.delete_candidate(candidate_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found"
        )

# Additional admin routes for managing exams, schools, etc. would go here