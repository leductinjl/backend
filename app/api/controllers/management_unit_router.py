"""
Management Unit router module.

This module provides API endpoints for managing management units.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db
from app.api.dto.management_unit import (
    ManagementUnitCreate,
    ManagementUnitUpdate,
    ManagementUnitResponse,
    ManagementUnitListResponse
)
from app.repositories.management_unit_repository import ManagementUnitRepository
from app.services.management_unit_service import ManagementUnitService

router = APIRouter(
    prefix="/management-units",
    tags=["Management Units"],
    responses={404: {"description": "Not found"}}
)

async def get_management_unit_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency injection for ManagementUnitService.
    
    Args:
        db: Database session
        
    Returns:
        ManagementUnitService: Service instance for management unit business logic
    """
    repository = ManagementUnitRepository(db)
    return ManagementUnitService(repository)

@router.get("/", response_model=ManagementUnitListResponse, summary="List Management Units")
async def get_management_units(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    unit_type: Optional[str] = Query(None, description="Filter by unit type"),
    service: ManagementUnitService = Depends(get_management_unit_service)
):
    """
    Retrieve a list of management units with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        unit_type: Optional filter by unit type
        service: ManagementUnitService instance
        
    Returns:
        List of management units
    """
    units, total = await service.get_all_units(skip=skip, limit=limit, unit_type=unit_type)
    
    return ManagementUnitListResponse(
        items=units,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{unit_id}", response_model=ManagementUnitResponse, summary="Get Management Unit")
async def get_management_unit(
    unit_id: str,
    service: ManagementUnitService = Depends(get_management_unit_service)
):
    """
    Retrieve a specific management unit by ID.
    
    Args:
        unit_id: The unique identifier of the management unit
        service: ManagementUnitService instance
        
    Returns:
        The management unit if found
        
    Raises:
        HTTPException: If the management unit is not found
    """
    unit = await service.get_unit_by_id(unit_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Management unit with ID {unit_id} not found"
        )
    
    return unit

@router.post(
    "/", 
    response_model=ManagementUnitResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Management Unit"
)
async def create_management_unit(
    unit: ManagementUnitCreate,
    service: ManagementUnitService = Depends(get_management_unit_service)
):
    """
    Create a new management unit.
    
    Args:
        unit: Management unit data
        service: ManagementUnitService instance
        
    Returns:
        The created management unit
    """
    return await service.create_unit(unit.model_dump())

@router.put("/{unit_id}", response_model=ManagementUnitResponse, summary="Update Management Unit")
async def update_management_unit(
    unit_id: str,
    unit: ManagementUnitUpdate,
    service: ManagementUnitService = Depends(get_management_unit_service)
):
    """
    Update a management unit.
    
    Args:
        unit_id: The unique identifier of the management unit
        unit: Updated management unit data
        service: ManagementUnitService instance
        
    Returns:
        The updated management unit
        
    Raises:
        HTTPException: If the management unit is not found
    """
    updated_unit = await service.update_unit(unit_id, unit.model_dump(exclude_unset=True))
    if not updated_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Management unit with ID {unit_id} not found"
        )
    
    return updated_unit

@router.patch("/{unit_id}", response_model=ManagementUnitResponse, summary="Partially Update Management Unit")
async def partially_update_management_unit(
    unit_id: str,
    unit: ManagementUnitUpdate,
    service: ManagementUnitService = Depends(get_management_unit_service)
):
    """
    Partially update a management unit.
    
    Args:
        unit_id: The unique identifier of the management unit
        unit: Partial management unit data
        service: ManagementUnitService instance
        
    Returns:
        The updated management unit
        
    Raises:
        HTTPException: If the management unit is not found
    """
    updated_unit = await service.update_unit(unit_id, unit.model_dump(exclude_unset=True, exclude_none=True))
    if not updated_unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Management unit with ID {unit_id} not found"
        )
    
    return updated_unit

@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Management Unit")
async def delete_management_unit(
    unit_id: str,
    service: ManagementUnitService = Depends(get_management_unit_service)
):
    """
    Delete a management unit.
    
    Args:
        unit_id: The unique identifier of the management unit
        service: ManagementUnitService instance
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the management unit is not found
    """
    deleted = await service.delete_unit(unit_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Management unit with ID {unit_id} not found"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 