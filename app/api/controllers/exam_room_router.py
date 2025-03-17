"""
Exam Room router module.

This module provides API endpoints for managing exam rooms.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.exam_room import (
    ExamRoomCreate,
    ExamRoomUpdate,
    ExamRoomResponse,
    ExamRoomDetailResponse,
    ExamRoomFullDetailResponse,
    ExamRoomListResponse
)
from app.repositories.exam_room_repository import ExamRoomRepository
from app.repositories.exam_location_repository import ExamLocationRepository
from app.services.exam_room_service import ExamRoomService

router = APIRouter(
    prefix="/exam-rooms",
    tags=["Exam Rooms"],
    responses={404: {"description": "Not found"}}
)

async def get_exam_room_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ExamRoomService.
    
    Args:
        db: Database session
        
    Returns:
        ExamRoomService: Service instance for exam room business logic
    """
    repository = ExamRoomRepository(db)
    location_repository = ExamLocationRepository(db)
    return ExamRoomService(repository, location_repository)

@router.get("/", response_model=ExamRoomListResponse, summary="List Exam Rooms")
async def get_exam_rooms(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    exam_id: Optional[str] = Query(None, description="Filter by exam ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    capacity_min: Optional[int] = Query(None, ge=1, description="Filter by minimum capacity"),
    capacity_max: Optional[int] = Query(None, ge=1, description="Filter by maximum capacity"),
    service: ExamRoomService = Depends(get_exam_room_service)
):
    """
    Retrieve a list of exam rooms with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        location_id: Optional filter by location ID
        exam_id: Optional filter by exam ID (exams the rooms are associated with)
        is_active: Optional filter by active status
        capacity_min: Optional filter by minimum capacity
        capacity_max: Optional filter by maximum capacity
        service: ExamRoomService instance
        
    Returns:
        List of exam rooms
    """
    rooms, total = await service.get_all_exam_rooms(
        skip=skip, 
        limit=limit, 
        location_id=location_id,
        exam_id=exam_id,
        is_active=is_active,
        capacity_min=capacity_min,
        capacity_max=capacity_max
    )
    
    # Transform the data for response - select first exam if available for backwards compatibility
    room_items = []
    for room in rooms:
        detail_room = {**room}
        # Handle the case where exams is now a list instead of direct fields
        if "exams" in detail_room and detail_room["exams"]:
            first_exam = detail_room["exams"][0]
            detail_room["exam_id"] = first_exam["exam_id"]
            detail_room["exam_name"] = first_exam["exam_name"]
        else:
            detail_room["exam_id"] = None
            detail_room["exam_name"] = None
        
        # Remove the exams list from the response to match the expected DTO
        if "exams" in detail_room:
            del detail_room["exams"]
            
        room_items.append(detail_room)
    
    return ExamRoomListResponse(
        items=room_items,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{room_id}", response_model=ExamRoomDetailResponse, summary="Get Exam Room")
async def get_exam_room(
    room_id: str = Path(..., description="The unique identifier of the exam room"),
    service: ExamRoomService = Depends(get_exam_room_service)
):
    """
    Retrieve a specific exam room by ID.
    
    Args:
        room_id: The unique identifier of the exam room
        service: ExamRoomService instance
        
    Returns:
        The exam room if found
        
    Raises:
        HTTPException: If the exam room is not found
    """
    room = await service.get_exam_room_by_id(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam room with ID {room_id} not found"
        )
    
    # Transform for response - select first exam if available for backwards compatibility
    detail_room = {**room}
    if "exams" in detail_room and detail_room["exams"]:
        first_exam = detail_room["exams"][0]
        detail_room["exam_id"] = first_exam["exam_id"]
        detail_room["exam_name"] = first_exam["exam_name"]
    else:
        detail_room["exam_id"] = None
        detail_room["exam_name"] = None
    
    # Remove the exams list from the response to match the expected DTO
    if "exams" in detail_room:
        del detail_room["exams"]
    
    return detail_room

@router.get("/{room_id}/full", response_model=ExamRoomFullDetailResponse, summary="Get Exam Room with All Linked Exams")
async def get_exam_room_full_details(
    room_id: str = Path(..., description="The unique identifier of the exam room"),
    service: ExamRoomService = Depends(get_exam_room_service)
):
    """
    Retrieve a specific exam room by ID with full details including all linked exams.
    
    Args:
        room_id: The unique identifier of the exam room
        service: ExamRoomService instance
        
    Returns:
        The exam room with all linked exams
        
    Raises:
        HTTPException: If the exam room is not found
    """
    room = await service.get_exam_room_by_id(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam room with ID {room_id} not found"
        )
    
    # For this endpoint, we return the full details including all linked exams
    return room

@router.get("/location/{location_id}", response_model=List[ExamRoomResponse], summary="Get Exam Rooms by Location ID")
async def get_exam_rooms_by_location(
    location_id: str = Path(..., description="The ID of the exam location"),
    service: ExamRoomService = Depends(get_exam_room_service)
):
    """
    Retrieve all exam rooms for a specific location.
    
    Args:
        location_id: The ID of the exam location
        service: ExamRoomService instance
        
    Returns:
        List of exam rooms for the specified location
    """
    rooms = await service.get_rooms_by_location_id(location_id)
    return rooms

@router.get("/exam/{exam_id}", response_model=List[ExamRoomResponse], summary="Get Exam Rooms by Exam ID")
async def get_exam_rooms_by_exam(
    exam_id: str = Path(..., description="The ID of the exam"),
    service: ExamRoomService = Depends(get_exam_room_service)
):
    """
    Retrieve all exam rooms for a specific exam.
    
    Args:
        exam_id: The ID of the exam
        service: ExamRoomService instance
        
    Returns:
        List of exam rooms for the specified exam
    """
    rooms = await service.get_rooms_by_exam_id(exam_id)
    return rooms

@router.post(
    "/", 
    response_model=ExamRoomResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam Room"
)
async def create_exam_room(
    room: ExamRoomCreate,
    service: ExamRoomService = Depends(get_exam_room_service)
):
    """
    Create a new exam room.
    
    Args:
        room: Exam room data
        service: ExamRoomService instance
        
    Returns:
        The created exam room
        
    Raises:
        HTTPException: If the exam location doesn't exist
    """
    new_room = await service.create_exam_room(room.model_dump())
    if not new_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create exam room. Exam location with ID {room.location_id} not found."
        )
    
    return new_room

@router.put("/{room_id}", response_model=ExamRoomResponse, summary="Update Exam Room")
async def update_exam_room(
    room_id: str = Path(..., description="The unique identifier of the exam room"),
    room: ExamRoomUpdate = None,
    service: ExamRoomService = Depends(get_exam_room_service)
):
    """
    Update an exam room.
    
    Args:
        room_id: The unique identifier of the exam room
        room: Updated exam room data
        service: ExamRoomService instance
        
    Returns:
        The updated exam room
        
    Raises:
        HTTPException: If the exam room is not found, or if the exam location doesn't exist
    """
    updated_room = await service.update_exam_room(
        room_id, 
        room.model_dump(exclude_unset=True) if room else {}
    )
    if not updated_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam room with ID {room_id} not found or update failed due to invalid location ID"
        )
    
    return updated_room

@router.patch("/{room_id}", response_model=ExamRoomResponse, summary="Partially Update Exam Room")
async def partially_update_exam_room(
    room_id: str = Path(..., description="The unique identifier of the exam room"),
    room: ExamRoomUpdate = None,
    service: ExamRoomService = Depends(get_exam_room_service)
):
    """
    Partially update an exam room.
    
    Args:
        room_id: The unique identifier of the exam room
        room: Partial exam room data
        service: ExamRoomService instance
        
    Returns:
        The updated exam room
        
    Raises:
        HTTPException: If the exam room is not found, or if the exam location doesn't exist
    """
    updated_room = await service.update_exam_room(
        room_id, 
        room.model_dump(exclude_unset=True, exclude_none=True) if room else {}
    )
    if not updated_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam room with ID {room_id} not found or update failed due to invalid location ID"
        )
    
    return updated_room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Exam Room")
async def delete_exam_room(
    room_id: str = Path(..., description="The unique identifier of the exam room"),
    service: ExamRoomService = Depends(get_exam_room_service)
):
    """
    Delete an exam room.
    
    Args:
        room_id: The unique identifier of the exam room
        service: ExamRoomService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the exam room is not found
    """
    deleted = await service.delete_exam_room(room_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam room with ID {room_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 