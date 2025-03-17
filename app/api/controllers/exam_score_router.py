"""
Exam Score router module.

This module provides API endpoints for managing exam scores.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path, Body
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.infrastructure.database.connection import get_db
from app.api.dto.exam_score import (
    ExamScoreCreate,
    ExamScoreUpdate,
    ExamScoreResponse,
    ExamScoreDetailResponse,
    ExamScoreListResponse,
    ScoreStatus
)
from app.repositories.exam_score_repository import ExamScoreRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.repositories.exam_subject_repository import ExamSubjectRepository
from app.services.exam_score_service import ExamScoreService

router = APIRouter(
    prefix="/exam-scores",
    tags=["Exam Scores"],
    responses={404: {"description": "Not found"}}
)

async def get_exam_score_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ExamScoreService.
    
    Args:
        db: Database session
        
    Returns:
        ExamScoreService: Service instance for exam score business logic
    """
    repository = ExamScoreRepository(db)
    candidate_exam_repository = CandidateExamRepository(db)
    exam_subject_repository = ExamSubjectRepository(db)
    return ExamScoreService(repository, candidate_exam_repository, exam_subject_repository)

@router.get("/", response_model=ExamScoreListResponse, summary="List Exam Scores")
async def get_exam_scores(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for candidate name/code, exam name, or subject name/code"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    status: Optional[ScoreStatus] = Query(None, description="Filter by score status"),
    min_score: Optional[float] = Query(None, ge=0, description="Filter by minimum score"),
    max_score: Optional[float] = Query(None, description="Filter by maximum score"),
    score_date: Optional[date] = Query(None, description="Filter by score date"),
    graded_by: Optional[str] = Query(None, description="Filter by grader ID"),
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Retrieve a list of exam scores with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        search: Search term for candidate name/code, exam name, or subject name/code
        candidate_id: Filter by candidate ID
        exam_id: Filter by exam ID
        subject_id: Filter by subject ID
        status: Filter by score status
        min_score: Filter by minimum score
        max_score: Filter by maximum score
        score_date: Filter by score date (YYYY-MM-DD)
        graded_by: Filter by grader ID
        service: ExamScoreService instance
        
    Returns:
        List of exam scores
    """
    scores, total = await service.get_all_scores(
        skip=skip, 
        limit=limit,
        search=search,
        candidate_id=candidate_id,
        exam_id=exam_id,
        subject_id=subject_id,
        status=status.value if status else None,
        min_score=min_score,
        max_score=max_score,
        score_date=score_date.isoformat() if score_date else None,
        graded_by=graded_by
    )
    
    return ExamScoreListResponse(
        items=scores,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{score_id}", response_model=ExamScoreDetailResponse, summary="Get Exam Score")
async def get_exam_score(
    score_id: str = Path(..., description="The unique identifier of the exam score"),
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Retrieve a specific exam score by ID.
    
    Args:
        score_id: The unique identifier of the exam score
        service: ExamScoreService instance
        
    Returns:
        The exam score if found
        
    Raises:
        HTTPException: If the exam score is not found
    """
    score = await service.get_score_by_id(score_id)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam score with ID {score_id} not found"
        )
    
    return score

@router.get("/candidate-exam/{candidate_exam_id}", response_model=List[ExamScoreResponse], summary="Get Scores by Candidate Exam")
async def get_scores_by_candidate_exam(
    candidate_exam_id: str = Path(..., description="The ID of the candidate exam registration"),
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Retrieve all scores for a specific candidate exam registration.
    
    Args:
        candidate_exam_id: The ID of the candidate exam registration
        service: ExamScoreService instance
        
    Returns:
        List of scores for the specified candidate exam registration
    """
    scores = await service.get_scores_by_candidate_exam_id(candidate_exam_id)
    return scores

@router.get("/exam-subject/{exam_subject_id}", response_model=List[ExamScoreResponse], summary="Get Scores by Exam Subject")
async def get_scores_by_exam_subject(
    exam_subject_id: str = Path(..., description="The ID of the exam subject"),
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Retrieve all scores for a specific exam subject.
    
    Args:
        exam_subject_id: The ID of the exam subject
        service: ExamScoreService instance
        
    Returns:
        List of scores for the specified exam subject
    """
    scores = await service.get_scores_by_exam_subject_id(exam_subject_id)
    return scores

@router.post(
    "/",
    response_model=ExamScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam Score"
)
async def create_exam_score(
    score: ExamScoreCreate,
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Create a new exam score.
    
    Args:
        score: Exam score data
        service: ExamScoreService instance
        
    Returns:
        The created exam score
        
    Raises:
        HTTPException: If the exam subject doesn't exist
    """
    new_score = await service.create_score(score.model_dump())
    if not new_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create exam score. Exam subject may not exist."
        )
    
    return new_score

@router.put("/{score_id}", response_model=ExamScoreResponse, summary="Update Exam Score")
async def update_exam_score(
    score_id: str = Path(..., description="The unique identifier of the exam score"),
    score: ExamScoreUpdate = None,
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Update an exam score.
    
    Args:
        score_id: The unique identifier of the exam score
        score: Updated exam score data
        service: ExamScoreService instance
        
    Returns:
        The updated exam score
        
    Raises:
        HTTPException: If the exam score is not found
    """
    updated_score = await service.update_score(
        score_id, 
        score.model_dump(exclude_unset=True) if score else {}
    )
    if not updated_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam score with ID {score_id} not found"
        )
    
    return updated_score

@router.patch("/{score_id}", response_model=ExamScoreResponse, summary="Partially Update Exam Score")
async def partially_update_exam_score(
    score_id: str = Path(..., description="The unique identifier of the exam score"),
    score: ExamScoreUpdate = None,
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Partially update an exam score.
    
    Args:
        score_id: The unique identifier of the exam score
        score: Partial exam score data
        service: ExamScoreService instance
        
    Returns:
        The updated exam score
        
    Raises:
        HTTPException: If the exam score is not found
    """
    updated_score = await service.update_score(
        score_id, 
        score.model_dump(exclude_unset=True, exclude_none=True) if score else {}
    )
    if not updated_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam score with ID {score_id} not found"
        )
    
    return updated_score

@router.delete("/{score_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Exam Score")
async def delete_exam_score(
    score_id: str = Path(..., description="The unique identifier of the exam score"),
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Delete an exam score.
    
    Args:
        score_id: The unique identifier of the exam score
        service: ExamScoreService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the exam score is not found
    """
    deleted = await service.delete_score(score_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam score with ID {score_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{score_id}/grade", response_model=ExamScoreResponse, summary="Grade Exam Score")
async def grade_exam_score(
    score_id: str = Path(..., description="The unique identifier of the exam score"),
    score_value: float = Body(..., ge=0, embed=True, description="The score value"),
    graded_by: Optional[str] = Body(None, embed=True, description="ID of the user who graded the exam"),
    notes: Optional[str] = Body(None, embed=True, description="Notes about the grading"),
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Grade an exam score.
    
    Args:
        score_id: The unique identifier of the exam score
        score_value: The score value
        graded_by: ID of the user who graded the exam
        notes: Notes about the grading
        service: ExamScoreService instance
        
    Returns:
        The updated exam score
        
    Raises:
        HTTPException: If the exam score is not found
    """
    updated_score = await service.grade_score(score_id, score_value, graded_by, notes)
    if not updated_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam score with ID {score_id} not found"
        )
    
    return updated_score

@router.patch("/{score_id}/status", response_model=ExamScoreResponse, summary="Update Score Status")
async def update_exam_score_status(
    score_id: str = Path(..., description="The unique identifier of the exam score"),
    status: ScoreStatus = Body(..., embed=True, description="The new status"),
    notes: Optional[str] = Body(None, embed=True, description="Notes about the status change"),
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Update the status of an exam score.
    
    Args:
        score_id: The unique identifier of the exam score
        status: The new status
        notes: Notes about the status change
        service: ExamScoreService instance
        
    Returns:
        The updated exam score
        
    Raises:
        HTTPException: If the exam score is not found
    """
    updated_score = await service.update_score_status(score_id, status.value, notes)
    if not updated_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam score with ID {score_id} not found"
        )
    
    return updated_score

@router.get("/candidate-exam/{candidate_exam_id}/total", response_model=Dict[str, Optional[float]], summary="Calculate Total Score")
async def calculate_total_score(
    candidate_exam_id: str = Path(..., description="The ID of the candidate exam registration"),
    service: ExamScoreService = Depends(get_exam_score_service)
):
    """
    Calculate the total score for a candidate in an exam.
    
    Args:
        candidate_exam_id: The ID of the candidate exam registration
        service: ExamScoreService instance
        
    Returns:
        The total score if scores exist, None otherwise
    """
    total_score = await service.calculate_total_score(candidate_exam_id)
    return {"total_score": total_score} 