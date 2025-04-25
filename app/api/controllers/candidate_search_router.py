"""
Candidate Search Router Module.

Module này cung cấp các endpoints API để tìm kiếm thông tin thí sinh 
và truy vấn thông tin theo nhóm.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path, Body
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.infrastructure.database.connection import get_db
from app.infrastructure.ontology.neo4j_connection import get_neo4j
from app.api.dto.candidate_search import (
    CandidateBasicInfo,
    CandidateDetailedInfo,
    CandidateSearchResult,
    EducationInfo,
    ExamsInfo,
    AchievementsInfo,
    CandidateSearchRequest
)
from app.graph_repositories.search.candidate_search_repository import CandidateSearchRepository
from app.services.search.candidate_search_service import CandidateSearchService

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}}
)

async def get_candidate_search_service(
    db: AsyncSession = Depends(get_db),
    neo4j = Depends(get_neo4j)
):
    """
    Dependency injection for CandidateSearchService
    
    Args:
        db: Database session
        neo4j: Neo4j connection
        
    Returns:
        CandidateSearchService: Service instance
    """
    search_repo = CandidateSearchRepository(neo4j)
    return CandidateSearchService(search_repo)

@router.get("/candidates", response_model=CandidateSearchResult, summary="Tìm kiếm thí sinh")
async def search_candidates(
    candidate_id: Optional[str] = Query(None, description="Mã thí sinh"),
    id_number: Optional[str] = Query(None, description="Số căn cước/CMND/Định danh"),
    full_name: Optional[str] = Query(None, description="Họ và tên (chỉ dùng khi có mã thí sinh hoặc số căn cước)"),
    birth_date: Optional[date] = Query(None, description="Ngày sinh (YYYY-MM-DD)"),
    phone_number: Optional[str] = Query(None, description="Số điện thoại"),
    email: Optional[str] = Query(None, description="Địa chỉ email"),
    address: Optional[str] = Query(None, description="Địa chỉ (tìm trong cả địa chỉ chính và phụ)"),
    registration_number: Optional[str] = Query(None, description="Số báo danh trong kỳ thi"),
    exam_id: Optional[str] = Query(None, description="Mã kỳ thi"),
    school_id: Optional[str] = Query(None, description="Mã trường học"),
    case_sensitive: bool = Query(False, description="Có phân biệt chữ hoa/thường không"),
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(10, ge=1, le=100, description="Kích thước trang"),
    service: CandidateSearchService = Depends(get_candidate_search_service)
):
    """
    Tìm kiếm thí sinh theo nhiều tiêu chí khác nhau.
    
    Endpoint cho phép tìm kiếm thí sinh dựa trên nhiều tiêu chí như mã thí sinh, 
    số căn cước, họ tên, ngày sinh, v.v. Người dùng phải cung cấp ít nhất một thông tin định danh
    (mã thí sinh hoặc số căn cước) để thực hiện tìm kiếm.
    
    Returns:
        CandidateSearchResult: Kết quả tìm kiếm bao gồm danh sách thí sinh và thông tin phân trang
    """
    try:
        # Kiểm tra xem có ít nhất một thông tin định danh không
        if not candidate_id and not id_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "MISSING_IDENTIFICATION",
                    "message": "Vui lòng cung cấp ít nhất một thông tin định danh (mã thí sinh hoặc số căn cước)",
                    "details": "Không thể tìm kiếm chỉ bằng tên. Cần có mã thí sinh hoặc số căn cước để xác định thí sinh chính xác."
                }
            )
        
        # Tạo từ điển chứa các tiêu chí tìm kiếm
        search_criteria = {
            "candidate_id": candidate_id,
            "id_number": id_number,
            "full_name": full_name,
            "birth_date": birth_date,
            "phone_number": phone_number,
            "email": email,
            "address": address,
            "registration_number": registration_number,
            "exam_id": exam_id,
            "school_id": school_id,
            "case_sensitive": case_sensitive
        }
        
        # Lọc bỏ các tiêu chí có giá trị None
        search_criteria = {k: v for k, v in search_criteria.items() if v is not None}
        
        # Thực hiện tìm kiếm
        result = await service.search_candidates(search_criteria, page, page_size)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tìm kiếm thí sinh: {str(e)}"
        )

@router.post("/candidates", response_model=CandidateSearchResult, summary="Tìm kiếm thí sinh (POST)")
async def search_candidates_post(
    search_request: CandidateSearchRequest,
    service: CandidateSearchService = Depends(get_candidate_search_service)
):
    """
    Tìm kiếm thí sinh theo nhiều tiêu chí sử dụng POST request.
    
    Endpoint này tương tự với endpoint GET nhưng sử dụng POST để cho phép 
    gửi các tiêu chí tìm kiếm phức tạp hơn trong request body.
    
    Args:
        search_request: Object chứa các tiêu chí tìm kiếm
        
    Returns:
        CandidateSearchResult: Kết quả tìm kiếm bao gồm danh sách thí sinh và thông tin phân trang
    """
    try:
        # Kiểm tra xem có ít nhất một thông tin định danh không
        if not search_request.candidate_id and not search_request.id_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Yêu cầu ít nhất một thông tin định danh (mã thí sinh hoặc số căn cước)"
            )
        
        # Chuyển đổi search_request thành dictionary
        search_criteria = search_request.model_dump(exclude={"page", "page_size"})
        
        # Lọc bỏ các tiêu chí có giá trị None
        search_criteria = {k: v for k, v in search_criteria.items() if v is not None}
        
        # Thực hiện tìm kiếm
        result = await service.search_candidates(search_criteria, search_request.page, search_request.page_size)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tìm kiếm thí sinh: {str(e)}"
        )

@router.get("/candidates/{candidate_id}", response_model=CandidateDetailedInfo, summary="Xem thông tin thí sinh")
async def get_candidate_detailed_info(
    candidate_id: str = Path(..., description="Mã thí sinh"),
    include_education: bool = Query(False, description="Bao gồm thông tin học vấn"),
    include_exams: bool = Query(False, description="Bao gồm thông tin kỳ thi"),
    include_achievements: bool = Query(False, description="Bao gồm thông tin thành tích"),
    service: CandidateSearchService = Depends(get_candidate_search_service)
):
    """
    Lấy thông tin chi tiết của thí sinh theo ID, với các nhóm thông tin tùy chọn.
    
    Endpoint này cho phép xem thông tin chi tiết của thí sinh gồm thông tin cơ bản
    và tùy chọn bao gồm thêm các nhóm thông tin như học vấn, kỳ thi, và thành tích.
    
    Args:
        candidate_id: Mã thí sinh
        include_education: Có bao gồm thông tin học vấn không
        include_exams: Có bao gồm thông tin kỳ thi không
        include_achievements: Có bao gồm thông tin thành tích không
        
    Returns:
        CandidateDetailedInfo: Thông tin chi tiết của thí sinh theo các nhóm
    """
    try:
        result = await service.get_candidate_info(
            candidate_id, 
            include_education, 
            include_exams, 
            include_achievements
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy thí sinh với mã {candidate_id}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin thí sinh: {str(e)}"
        )

@router.get("/candidates/{candidate_id}/education", response_model=EducationInfo, summary="Xem thông tin học vấn")
async def get_candidate_education(
    candidate_id: str = Path(..., description="Mã thí sinh"),
    service: CandidateSearchService = Depends(get_candidate_search_service)
):
    """
    Lấy thông tin học vấn của thí sinh.
    
    Endpoint này trả về thông tin về trường học, ngành học, và bằng cấp của thí sinh.
    
    Args:
        candidate_id: Mã thí sinh
        
    Returns:
        EducationInfo: Thông tin học vấn của thí sinh
    """
    try:
        result = await service.get_candidate_education_info(candidate_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy thí sinh với mã {candidate_id}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin học vấn của thí sinh: {str(e)}"
        )

@router.get("/candidates/{candidate_id}/exams", response_model=ExamsInfo, summary="Xem thông tin kỳ thi")
async def get_candidate_exams(
    candidate_id: str = Path(..., description="Mã thí sinh"),
    service: CandidateSearchService = Depends(get_candidate_search_service)
):
    """
    Lấy thông tin kỳ thi của thí sinh.
    
    Endpoint này trả về thông tin về các kỳ thi, lịch thi, điểm số, và phúc khảo của thí sinh.
    
    Args:
        candidate_id: Mã thí sinh
        
    Returns:
        ExamsInfo: Thông tin kỳ thi của thí sinh
    """
    try:
        result = await service.get_candidate_exams_info(candidate_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy thí sinh với mã {candidate_id}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin kỳ thi của thí sinh: {str(e)}"
        )

@router.get("/candidates/{candidate_id}/achievements", response_model=AchievementsInfo, summary="Xem thông tin thành tích")
async def get_candidate_achievements(
    candidate_id: str = Path(..., description="Mã thí sinh"),
    service: CandidateSearchService = Depends(get_candidate_search_service)
):
    """
    Lấy thông tin thành tích và giấy tờ của thí sinh.
    
    Endpoint này trả về thông tin về chứng chỉ, giấy tờ xác thực, giải thưởng, 
    thành tích, và công nhận của thí sinh.
    
    Args:
        candidate_id: Mã thí sinh
        
    Returns:
        AchievementsInfo: Thông tin thành tích của thí sinh
    """
    try:
        result = await service.get_candidate_achievements_info(candidate_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy thí sinh với mã {candidate_id}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thông tin thành tích của thí sinh: {str(e)}"
        ) 