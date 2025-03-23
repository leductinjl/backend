"""
Admin router module.

This module provides endpoints for admin operations like managing candidates,
exams, schools, and other administrative tasks. All endpoints in this router
require admin authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import pytz
import logging

from app.infrastructure.database.connection import get_db
from app.infrastructure.ontology.neo4j_connection import get_neo4j
from app.infrastructure.cache.redis_connection import get_redis
from app.repositories.candidate_repository import CandidateRepository
from app.graph_repositories.candidate_graph_repository import CandidateGraphRepository
from app.services.candidate_service import CandidateService
from app.services.id_service import generate_model_id
from app.api.dto.candidate import (
    CandidateCreate, 
    CandidateUpdate, 
    CandidateResponse, 
    CandidateDetailResponse
)
from app.api.dto.admin import AdminRegisterRequest, AdminLoginResponse
# Import auth functions
from app.api.controllers.admin_auth import admin_login, admin_register
from app.domain.models.invitation import Invitation

# Create main admin router
router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}}
)

logger = logging.getLogger(__name__)

# Add authentication endpoints directly
@router.post("/register", response_model=AdminLoginResponse, summary="Admin Registration")
async def register_endpoint(
    register_data: AdminRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new admin user.
    
    This endpoint creates a new admin user in the system with the provided
    credentials and returns an access token. Requires a valid invitation code.
    """
    return await admin_register(register_data, db)

@router.post("/login", response_model=AdminLoginResponse, summary="Admin Login")
async def login_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate an admin user.
    
    This endpoint authenticates admin credentials against the database
    and returns an access token if valid.
    """
    return await admin_login(form_data, db)

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

@router.post("/invitations", status_code=status.HTTP_201_CREATED, summary="Generate Invitation Code")
async def generate_invitation(
    email: Optional[str] = None,
    expiration_days: int = 7,
    admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new invitation code for admin registration.
    
    This endpoint allows existing admins to create invitation codes
    that can be used to register new admin users.
    
    Args:
        email: Optional email to restrict the invitation to
        expiration_days: Number of days until the invitation expires
        admin: The authenticated admin user (from dependency)
        db: Database session
        
    Returns:
        dict: The generated invitation details
    """
    # Generate a unique invitation code
    invitation_code = str(uuid.uuid4())[:8].upper()
    
    # Calculate expiration date
    expires_at = datetime.now(pytz.UTC) + timedelta(days=expiration_days)
    
    # Create invitation
    new_invitation = Invitation(
        invitation_id=generate_model_id("Invitation"),
        code=invitation_code,
        email=email,
        created_by=admin["sub"],
        expires_at=expires_at
    )
    
    # Save to database
    db.add(new_invitation)
    await db.commit()
    
    # Return invitation details
    return {
        "invitation_id": new_invitation.invitation_id,
        "code": invitation_code,
        "email": email,
        "expires_at": expires_at.isoformat(),
        "created_by": admin["email"]
    }

@router.get("/invitations", summary="List Invitation Codes")
async def list_invitations(
    admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all invitation codes.
    
    This endpoint returns all invitation codes generated by the system,
    showing their status and usage.
    
    Args:
        admin: The authenticated admin user (from dependency)
        db: Database session
        
    Returns:
        list: List of invitation codes
    """
    # Query all invitations using SQLAlchemy 2.0 syntax
    from sqlalchemy import select, desc
    result = await db.execute(
        select(Invitation).order_by(desc(Invitation.created_at))
    )
    invitations = result.scalars().all()
    
    # Format and return results
    return [
        {
            "invitation_id": inv.invitation_id,
            "code": inv.code,
            "email": inv.email,
            "is_used": inv.is_used,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "used_at": inv.used_at.isoformat() if inv.used_at else None,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None
        }
        for inv in invitations
    ]

@router.post("/sync/neo4j", response_model=dict)
async def synchronize_to_neo4j(
    resync_ontology: bool = True,
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j),
    admin: dict = Depends(get_current_admin)
):
    """
    Đồng bộ dữ liệu từ PostgreSQL sang Neo4j knowledge graph.
    
    Endpoint này sẽ đồng bộ tất cả các entity và mối quan hệ giữa chúng.
    
    Args:
        resync_ontology: Nếu True, tạo lại các mối quan hệ IS_A trong ontology cho tất cả node hiện có
    """
    from app.services.sync import MainSyncService
    
    try:
        sync_service = MainSyncService(session=db, driver=neo4j._driver)
        results = await sync_service.sync_all_entities()
        
        return {
            "status": "success",
            "message": "Data synchronized to Neo4j",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error synchronizing data to Neo4j: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error during synchronization: {str(e)}",
            "results": {}
        }

# Additional admin routes for managing exams, schools, etc. would go here