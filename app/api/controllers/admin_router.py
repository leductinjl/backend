"""
Admin router module.

This module provides endpoints for admin operations like managing candidates,
exams, schools, and other administrative tasks. All endpoints in this router
require admin authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, Path
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
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
from app.services.sync.main_sync_service import MainSyncService, EntityType
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

logger = logging.getLogger(__name__)

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

# Create auth router for login/register endpoints (no authentication required)
auth_router = APIRouter(
    prefix="/admin",
    tags=["Admin Authentication"],
    responses={404: {"description": "Not found"}},
)

# Create main admin router (requires authentication)
router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
)

# Add authentication endpoints to auth_router
@auth_router.post("/register", response_model=AdminLoginResponse, summary="Admin Registration", include_in_schema=True)
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

@auth_router.post("/login", response_model=AdminLoginResponse, summary="Admin Login", include_in_schema=True)
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

async def get_candidate_service(
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j)
):
    """Dependency to inject CandidateService into API endpoints"""
    candidate_repo = CandidateRepository(db)
    candidate_graph_repo = CandidateGraphRepository(neo4j)
    return CandidateService(candidate_repo, candidate_graph_repo)

async def get_sync_service(
    entity_type: EntityType,
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j)
) -> MainSyncService:
    """
    Dependency to get the appropriate sync service for an entity type.
    
    Args:
        entity_type: Type of entity to sync
        db: Database session
        neo4j: Neo4j connection
        
    Returns:
        MainSyncService instance configured for the entity type
    """
    return MainSyncService(session=db, driver=neo4j._driver)

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

@router.post("/sync/neo4j", response_model=dict, summary="Synchronize Data to Neo4j")
async def synchronize_to_neo4j(
    sync_mode: str = "full",  # Options: "full", "nodes", "relationships"
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j),
    admin: dict = Depends(get_current_admin)
):
    """
    Đồng bộ dữ liệu từ PostgreSQL sang Neo4j knowledge graph.
    
    Endpoint này sẽ đồng bộ các node hoặc mối quan hệ tùy theo mode được chọn.
    
    Args:
        sync_mode: Chế độ đồng bộ hóa:
                  - "full": Đồng bộ cả nodes và relationships (mặc định)
                  - "nodes": Chỉ đồng bộ nodes
                  - "relationships": Chỉ đồng bộ relationships
        
        limit: Giới hạn số lượng thực thể xử lý cho mỗi loại
    """
    # Validate sync_mode
    valid_modes = ["full", "nodes", "relationships"]
    if sync_mode not in valid_modes:
        return {
            "status": "error",
            "message": f"Invalid sync mode: {sync_mode}. Valid modes are: {', '.join(valid_modes)}"
        }
    
    try:
        sync_service = MainSyncService(session=db, driver=neo4j._driver)
        results = {}
        
        # Handle different sync modes
        if sync_mode == "full":
            # First sync all nodes
            node_results = await sync_service.sync_all_nodes(limit=limit)
            
            # Then sync all relationships
            relationship_results = await sync_service.sync_all_relationships(limit=limit)
            
            # Combine results
            results = {
                "nodes": node_results,
                "relationships": relationship_results
            }
            
            message = "Full synchronization completed (nodes and relationships)"
                
        elif sync_mode == "nodes":
            # Only synchronize nodes
            results = await sync_service.sync_all_nodes(limit=limit)
            message = "Node synchronization completed"
                
        elif sync_mode == "relationships":
            # Only synchronize relationships
            results = await sync_service.sync_all_relationships(limit=limit)
            message = "Relationship synchronization completed"
        
        return {
            "status": "success",
            "message": message,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error during Neo4j synchronization: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error during synchronization: {str(e)}",
            "results": {}
        }

@router.post("/sync/neo4j/nodes", response_model=dict, summary="Synchronize Only Nodes to Neo4j")
async def synchronize_only_nodes(
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j),
    admin: dict = Depends(get_current_admin)
):
    """
    Đồng bộ chỉ các node từ PostgreSQL sang Neo4j, không đồng bộ quan hệ.
    
    Endpoint này là bước 1 trong quy trình đồng bộ 2 bước: đầu tiên tạo tất cả các node,
    sau đó mới tạo các mối quan hệ. Cách tiếp cận này giúp tránh lỗi tham chiếu
    khi tạo mối quan hệ giữa các node chưa tồn tại.
    
    Args:
        limit: Giới hạn số lượng thực thể xử lý cho mỗi loại
    """
    try:
        sync_service = MainSyncService(session=db, driver=neo4j._driver)
        
        # Synchronize all nodes
        results = await sync_service.sync_all_nodes(limit=limit)
        
        return {
            "status": "success",
            "message": "Node synchronization completed",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error during Neo4j node synchronization: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error during node synchronization: {str(e)}",
            "results": {}
        }

@router.post("/sync/neo4j/relationships", response_model=dict, summary="Synchronize Only Relationships to Neo4j")
async def synchronize_only_relationships(
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j),
    admin: dict = Depends(get_current_admin)
):
    """
    Đồng bộ chỉ các mối quan hệ giữa các node đã tồn tại trong Neo4j.
    
    Endpoint này là bước 2 trong quy trình đồng bộ 2 bước. Nó giả định rằng
    tất cả các node đã được tạo trước đó và chỉ đồng bộ các mối quan hệ giữa chúng.
    
    Args:
        limit: Giới hạn số lượng thực thể xử lý cho mỗi loại
    """
    try:
        sync_service = MainSyncService(session=db, driver=neo4j._driver)
        
        # Synchronize all relationships
        results = await sync_service.sync_all_relationships(limit=limit)
        
        return {
            "status": "success",
            "message": "Relationship synchronization completed",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error during Neo4j relationship synchronization: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error during relationship synchronization: {str(e)}",
            "results": {}
        }

@router.post("/sync/neo4j/entity/{entity_type}/relationships", response_model=dict, summary="Synchronize Relationships for a Specific Entity Type")
async def synchronize_entity_relationships(
    entity_type: str = Path(..., description="Entity type (score, subject, candidate, etc.)"),
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j),
    admin: dict = Depends(get_current_admin)
):
    """
    Đồng bộ mối quan hệ cho một loại entity cụ thể.
    
    Endpoint này cho phép đồng bộ mối quan hệ chỉ cho một loại entity được chỉ định,
    giúp kiểm tra và debug quá trình đồng bộ cho từng loại dữ liệu riêng biệt.
    
    Args:
        entity_type: Loại entity cần đồng bộ (score, subject, exam, candidate, etc.)
        limit: Giới hạn số lượng entity xử lý
    """
    try:
        # Kiểm tra entity_type là một giá trị hợp lệ
        valid_entity_types = [
            "subject", "score", "score_review", "exam", "candidate", 
            "achievement", "award", "certificate", "credential", "degree", 
            "exam_location", "exam_room", "exam_schedule", "major", 
            "management_unit", "recognition", "school"
        ]
        
        entity_type_lower = entity_type.lower()
        if entity_type_lower not in valid_entity_types:
            return {
                "status": "error",
                "message": f"Invalid entity type: {entity_type}. Valid types are: {', '.join(valid_entity_types)}"
            }
            
        sync_service = MainSyncService(session=db, driver=neo4j._driver)
        
        # Synchronize relationships for the specific entity type
        # EntityType là Literal nên chỉ cần truyền string
        results = await sync_service.sync_all_relationships(entity_type=entity_type_lower, limit=limit)
        
        return {
            "status": "success",
            "message": f"Relationship synchronization completed for {entity_type}",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error during entity relationship synchronization: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error during relationship synchronization for {entity_type}: {str(e)}",
            "results": {}
        }

# Additional admin routes for managing exams, schools, etc. would go here