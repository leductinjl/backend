"""
Exam Schedule router module.

This module defines API endpoints for managing exam schedules, 
including creating, retrieving, updating, and deleting schedules.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.services.exam_schedule_service import ExamScheduleService
from app.api.dto.exam_schedule import (
    ExamScheduleCreate,
    ExamScheduleUpdate,
    ExamScheduleResponse,
    ExamScheduleListResponse
)
from app.domain.models.user import User

router = APIRouter(
    prefix="/exam-schedules",
    tags=["Exam Schedules"],
    responses={404: {"description": "Not found"}}
)

async def get_exam_schedule_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ExamScheduleService.
    
    Args:
        db: Database session
        
    Returns:
        ExamScheduleService: Service instance for exam schedule business logic
    """
    return ExamScheduleService(db)

@router.get(
    "",
    response_model=ExamScheduleListResponse,
    summary="Get exam schedules with filtering and pagination",
    description="Retrieve a list of exam schedules with optional filtering by exam, subject, date range, and status."
)
async def get_exam_schedules(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    exam_subject_id: Optional[str] = Query(None, description="Filter by exam subject ID"),
    start_date: Optional[datetime] = Query(None, description="Filter schedules starting on or after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter schedules ending on or before this date"),
    status: Optional[str] = Query(None, description="Filter by schedule status"),
    service: ExamScheduleService = Depends(get_exam_schedule_service)
):
    """
    Retrieve a list of exam schedules with optional filtering and pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        exam_id: Optional filter by exam ID
        subject_id: Optional filter by subject ID
        exam_subject_id: Optional filter by exam subject ID
        start_date: Optional filter for schedules starting on or after this date
        end_date: Optional filter for schedules ending on or before this date
        status: Optional filter by schedule status
        service: ExamScheduleService instance
    """
    try:
        schedules, total = await service.get_exam_schedules(
            skip=skip,
            limit=limit,
            exam_id=exam_id,
            subject_id=subject_id,
            exam_subject_id=exam_subject_id,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        # Convert to response DTOs
        schedule_responses = [
            ExamScheduleResponse.from_orm(schedule)
            for schedule in schedules
        ]
        
        return ExamScheduleListResponse(
            items=schedule_responses,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving exam schedules: {str(e)}"
        )

@router.get(
    "/{exam_schedule_id}",
    response_model=ExamScheduleResponse,
    summary="Get exam schedule by ID",
    description="Retrieve a specific exam schedule by its ID."
)
async def get_exam_schedule(
    exam_schedule_id: str = Path(..., description="ID of the exam schedule to retrieve"),
    service: ExamScheduleService = Depends(get_exam_schedule_service)
):
    """
    Retrieve a specific exam schedule by its ID.
    
    Args:
        exam_schedule_id: ID of the exam schedule to retrieve
        service: ExamScheduleService instance
    """
    try:
        schedule = await service.get_exam_schedule_by_id(exam_schedule_id)
        
        return ExamScheduleResponse.from_orm(schedule)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving the exam schedule: {str(e)}"
        )

@router.get(
    "/exam-subject/{exam_subject_id}",
    response_model=ExamScheduleListResponse,
    summary="Get schedules for an exam subject",
    description="Retrieve all schedules for a specific exam subject."
)
async def get_schedules_by_exam_subject(
    exam_subject_id: str = Path(..., description="ID of the exam subject"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: ExamScheduleService = Depends(get_exam_schedule_service)
):
    """
    Retrieve all schedules for a specific exam subject with pagination.
    
    Args:
        exam_subject_id: ID of the exam subject
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: ExamScheduleService instance
    """
    try:
        schedules, total = await service.get_schedules_by_exam_subject(
            exam_subject_id=exam_subject_id,
            skip=skip,
            limit=limit
        )
        
        # Convert to response DTOs
        schedule_responses = [
            ExamScheduleResponse.from_orm(schedule)
            for schedule in schedules
        ]
        
        return ExamScheduleListResponse(
            items=schedule_responses,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving exam schedules: {str(e)}"
        )

@router.get(
    "/exam/{exam_id}",
    response_model=ExamScheduleListResponse,
    summary="Get schedules for an exam",
    description="Retrieve all schedules for a specific exam."
)
async def get_schedules_by_exam(
    exam_id: str = Path(..., description="ID of the exam"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: ExamScheduleService = Depends(get_exam_schedule_service)
):
    """
    Retrieve all schedules for a specific exam with pagination.
    
    Args:
        exam_id: ID of the exam
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        service: ExamScheduleService instance
    """
    try:
        schedules, total = await service.get_schedules_by_exam(
            exam_id=exam_id,
            skip=skip,
            limit=limit
        )
        
        # Convert to response DTOs
        schedule_responses = [
            ExamScheduleResponse.from_orm(schedule)
            for schedule in schedules
        ]
        
        return ExamScheduleListResponse(
            items=schedule_responses,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving exam schedules: {str(e)}"
        )

@router.post(
    "",
    response_model=ExamScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new exam schedule",
    description="Create a new exam schedule for an exam subject."
)
async def create_exam_schedule(
    schedule_data: ExamScheduleCreate,
    service: ExamScheduleService = Depends(get_exam_schedule_service)
):
    """
    Create a new exam schedule for an exam subject.
    
    Args:
        schedule_data: Data for creating the exam schedule
        service: ExamScheduleService instance
    """
    try:
        created_schedule = await service.create_exam_schedule(schedule_data)
        
        return ExamScheduleResponse.from_orm(created_schedule)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the exam schedule: {str(e)}"
        )

@router.put(
    "/{exam_schedule_id}",
    response_model=ExamScheduleResponse,
    summary="Update an exam schedule",
    description="Update an existing exam schedule."
)
async def update_exam_schedule(
    exam_schedule_id: str = Path(..., description="ID of the exam schedule to update"),
    schedule_data: ExamScheduleUpdate = ...,
    service: ExamScheduleService = Depends(get_exam_schedule_service)
):
    """
    Update an existing exam schedule.
    
    Args:
        exam_schedule_id: ID of the exam schedule to update
        schedule_data: Data for updating the exam schedule
        service: ExamScheduleService instance
    """
    try:
        updated_schedule = await service.update_exam_schedule(
            exam_schedule_id=exam_schedule_id,
            schedule_data=schedule_data
        )
        
        return ExamScheduleResponse.from_orm(updated_schedule)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the exam schedule: {str(e)}"
        )

@router.delete(
    "/{exam_schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an exam schedule",
    description="Delete an existing exam schedule."
)
async def delete_exam_schedule(
    exam_schedule_id: str = Path(..., description="ID of the exam schedule to delete"),
    service: ExamScheduleService = Depends(get_exam_schedule_service)
):
    """
    Delete an existing exam schedule.
    
    Args:
        exam_schedule_id: ID of the exam schedule to delete
        service: ExamScheduleService instance
    """
    try:
        await service.delete_exam_schedule(exam_schedule_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the exam schedule: {str(e)}"
        )