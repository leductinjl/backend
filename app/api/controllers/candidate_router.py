"""
Candidate router module.

This module provides public endpoints for accessing candidate information.
All endpoints in this router are public and do not require authentication,
allowing candidates to freely access their information.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.infrastructure.ontology.neo4j_connection import get_neo4j
from app.api.dto.candidate import (
    CandidateResponse, 
    CandidateDetailResponse,
    EducationHistoryResponse,
    ExamHistoryResponse
)
from app.repositories.candidate_repository import CandidateRepository
from app.graph_repositories.candidate_graph_repository import CandidateGraphRepository
from app.services.candidate_service import CandidateService

router = APIRouter()

async def get_candidate_service(
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j)
):
    """
    Dependency injection cho CandidateService
    
    Args:
        db: Database session
        neo4j: Neo4j connection
        
    Returns:
        CandidateService: Service instance để xử lý logic nghiệp vụ liên quan đến thí sinh
    """
    candidate_repo = CandidateRepository(db)
    # Tạm thời sử dụng instance rỗng thay vì kết nối thực với Neo4j
    candidate_graph_repo = CandidateGraphRepository(neo4j_connection=neo4j)
    return CandidateService(candidate_repo, candidate_graph_repo)

@router.get("/", response_model=List[CandidateResponse], summary="List Candidates")
async def get_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Lấy danh sách thí sinh.
    
    Endpoint này trả về danh sách tất cả thí sinh, có hỗ trợ phân trang.
    
    Args:
        skip: Số bản ghi bỏ qua (dùng cho phân trang)
        limit: Số bản ghi tối đa trả về
        service: CandidateService (injected)
        
    Returns:
        List[CandidateResponse]: Danh sách thí sinh
    """
    try:
        candidates = await service.get_all_candidates(skip, limit)
        return candidates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đã xảy ra lỗi khi lấy danh sách thí sinh: {str(e)}"
        )

@router.get("/{candidate_id}", response_model=CandidateDetailResponse, summary="Get Candidate Details")
async def get_candidate(
    candidate_id: str,
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Lấy thông tin chi tiết của thí sinh theo ID.
    
    Endpoint này trả về thông tin chi tiết của một thí sinh dựa trên ID.
    
    Args:
        candidate_id: ID của thí sinh
        service: CandidateService (injected)
        
    Returns:
        CandidateDetailResponse: Thông tin chi tiết của thí sinh
        
    Raises:
        HTTPException: Nếu không tìm thấy thí sinh hoặc có lỗi xảy ra
    """
    try:
        candidate = await service.get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy thí sinh với ID {candidate_id}"
            )
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đã xảy ra lỗi khi lấy thông tin thí sinh: {str(e)}"
        )

@router.get("/search/", response_model=List[CandidateResponse], summary="Search Candidates")
async def search_candidates(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Tìm kiếm thí sinh theo từ khóa.
    
    Endpoint này tìm kiếm thí sinh dựa trên tên hoặc thông tin cá nhân.
    
    Args:
        q: Từ khóa tìm kiếm
        skip: Số bản ghi bỏ qua (dùng cho phân trang)
        limit: Số bản ghi tối đa trả về
        service: CandidateService (injected)
        
    Returns:
        List[CandidateResponse]: Danh sách thí sinh phù hợp với từ khóa
    """
    try:
        candidates = await service.search_candidates(q, skip, limit)
        return candidates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đã xảy ra lỗi khi tìm kiếm thí sinh: {str(e)}"
        )

@router.get("/{candidate_id}/education", response_model=List[EducationHistoryResponse], summary="Get Education History")
async def get_education_history(
    candidate_id: str,
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Lấy lịch sử học tập của thí sinh.
    
    Endpoint này trả về lịch sử học tập của thí sinh từ đồ thị tri thức Neo4j.
    
    Args:
        candidate_id: ID của thí sinh
        service: CandidateService (injected)
        
    Returns:
        List[EducationHistoryResponse]: Lịch sử học tập của thí sinh
    """
    try:
        history = await service.get_candidate_education_history(candidate_id)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đã xảy ra lỗi khi lấy lịch sử học tập: {str(e)}"
        )

@router.get("/{candidate_id}/exams", response_model=List[ExamHistoryResponse], summary="Get Exam History")
async def get_exam_history(
    candidate_id: str,
    service: CandidateService = Depends(get_candidate_service)
):
    """
    Lấy lịch sử thi của thí sinh.
    
    Endpoint này trả về lịch sử thi cử của thí sinh từ đồ thị tri thức Neo4j.
    
    Args:
        candidate_id: ID của thí sinh
        service: CandidateService (injected)
        
    Returns:
        List[ExamHistoryResponse]: Lịch sử thi của thí sinh
    """
    try:
        history = await service.get_candidate_exam_history(candidate_id)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đã xảy ra lỗi khi lấy lịch sử thi: {str(e)}"
        ) 