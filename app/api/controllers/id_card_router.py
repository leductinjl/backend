"""
ID Card Router module.

This module provides endpoints for processing ID card images and extracting
information from them.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import logging
import os
import tempfile
import asyncio

from app.infrastructure.database.connection import get_db
from app.services.id_card_service import IdCardService
from app.api.dto.id_card import IdCardResponse, IdCardCreate, IdCardUpdate
from app.api.controllers.admin_router import get_image_storage_service
from app.services.image_storage_service import ImageStorageService
from app.services.image_processing_service import ImageProcessingService
from app.api.dependencies.image_processing import get_image_processor

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/id-cards",
    tags=["ID Cards"],
    responses={404: {"description": "Not found"}},
)

# Tạm thời bỏ qua xác thực admin
async def get_current_admin():
    """Tạm thời bỏ qua xác thực admin"""
    return None

async def get_id_card_service(
    db: AsyncSession = Depends(get_db)
) -> IdCardService:
    """Dependency to get ID card service instance."""
    return IdCardService()  # Không truyền db vào constructor

@router.post("/", response_model=IdCardResponse, status_code=status.HTTP_201_CREATED)
async def create_id_card(
    id_card: IdCardCreate,
    admin: dict = Depends(get_current_admin),
    id_card_service: IdCardService = Depends(get_id_card_service)
):
    """
    Create a new ID card record.
    """
    try:
        return await id_card_service.create_id_card(id_card)
    except Exception as e:
        logger.error(f"Error creating ID card: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ID card: {str(e)}"
        )

@router.get("/{id_card_id}", response_model=IdCardResponse)
async def get_id_card(
    id_card_id: str,
    admin: dict = Depends(get_current_admin),
    id_card_service: IdCardService = Depends(get_id_card_service)
):
    """
    Get an ID card by ID.
    """
    try:
        id_card = await id_card_service.get_id_card(id_card_id)
        if not id_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID card with ID {id_card_id} not found"
            )
        return id_card
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ID card: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting ID card: {str(e)}"
        )

@router.put("/{id_card_id}", response_model=IdCardResponse)
async def update_id_card(
    id_card_id: str,
    id_card: IdCardUpdate,
    admin: dict = Depends(get_current_admin),
    id_card_service: IdCardService = Depends(get_id_card_service)
):
    """
    Update an ID card.
    """
    try:
        updated_id_card = await id_card_service.update_id_card(id_card_id, id_card)
        if not updated_id_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID card with ID {id_card_id} not found"
            )
        return updated_id_card
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ID card: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating ID card: {str(e)}"
        )

@router.delete("/{id_card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_id_card(
    id_card_id: str,
    admin: dict = Depends(get_current_admin),
    id_card_service: IdCardService = Depends(get_id_card_service)
):
    """
    Delete an ID card.
    """
    try:
        success = await id_card_service.delete_id_card(id_card_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID card with ID {id_card_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ID card: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting ID card: {str(e)}"
        )

@router.post("/{id_card_id}/image", response_model=Dict[str, Any])
async def upload_id_card_image(
    id_card_id: str,
    image: UploadFile = File(...),
    admin: dict = Depends(get_current_admin),
    storage_service: ImageStorageService = Depends(get_image_storage_service)
):
    """
    Upload an image for an ID card.
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
            
        # Add timeout for the operation
        result = await asyncio.wait_for(
            storage_service.save_image(
                id_card_id,
                image,
                "id_card",
                "upload"
            ),
            timeout=60.0  # 60 seconds timeout for image processing
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
        return result
        
    except asyncio.TimeoutError:
        logger.error("Image processing timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Image processing timed out. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {str(e)}"
        )

@router.get("/{id_card_id}/image", response_model=Dict[str, Any])
async def get_id_card_image(
    id_card_id: str,
    admin: dict = Depends(get_current_admin),
    storage_service: ImageStorageService = Depends(get_image_storage_service)
):
    """
    Get the URL of an ID card's image.
    """
    try:
        url = await storage_service.get_image_url(id_card_id, "id_card")
        if not url:
            return {
                "image_url": None,
                "message": f"No image found for ID card {id_card_id}"
            }
        return {"image_url": url}
    except Exception as e:
        logger.error(f"Error getting image URL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting image URL: {str(e)}"
        )

@router.post("/ocr/extract", response_model=Dict[str, Any])
async def extract_info_from_ocr(
    image: UploadFile = File(...),
    admin: dict = Depends(get_current_admin),
    id_card_service: IdCardService = Depends(get_id_card_service)
):
    """
    Extract information from ID card image using OCR.
    
    This endpoint processes an ID card image and extracts text information
    using OCR technology.
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
            
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            
        try:
            # Extract info using OCR
            result = await id_card_service._extract_info_from_ocr(temp_file_path)
            return result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error extracting info from OCR: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting info from OCR: {str(e)}"
        )

@router.post("/qr/extract", response_model=Dict[str, Any])
async def extract_info_from_qr(
    image: UploadFile = File(...),
    admin: dict = Depends(get_current_admin),
    id_card_service: IdCardService = Depends(get_id_card_service)
):
    """
    Extract information from ID card QR code.
    
    This endpoint processes an ID card image and extracts information
    from the QR code if present.
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
            
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            
        try:
            # Extract info from QR code
            result = await id_card_service.qr_service.extract_info(temp_file_path)
            return result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error extracting info from QR code: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting info from QR code: {str(e)}"
        )

@router.post("/auto-extract", response_model=Dict[str, Any])
async def auto_extract_info(
    image: UploadFile = File(...),
    admin: dict = Depends(get_current_admin),
    id_card_service: IdCardService = Depends(get_id_card_service)
):
    """
    Automatically extract information from ID card image.
    
    This endpoint tries to extract information using both QR code and OCR.
    If QR code extraction fails, it falls back to OCR.
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
            
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            
        try:
            # Try QR code first, fall back to OCR if needed
            result = await id_card_service.extract_info(temp_file_path)
            return result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error auto-extracting info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error auto-extracting info: {str(e)}"
        ) 