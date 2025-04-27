"""
Image Search Router module.

This module provides API endpoints for face-based image search functionality.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.database import get_db
from app.services.image_processing_service import ImageProcessingService
from app.repositories.image_search_repository import ImageSearchRepository
from app.api.dto.candidate_search import CandidateSearchResponse
from app.api.dependencies.image_processing import get_image_processor

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/image-search",
    tags=["image-search"]
)

async def get_image_search_repository(
    db: AsyncSession = Depends(get_db),
    image_processor: ImageProcessingService = Depends(get_image_processor)
):
    """Dependency to get image search repository instance."""
    return ImageSearchRepository(db, image_processor)

@router.post("/search", response_model=List[CandidateSearchResponse])
async def search_by_face(
    image: UploadFile = File(...),
    threshold: float = Form(0.65),
    repository: ImageSearchRepository = Depends(get_image_search_repository)
):
    """
    Search for candidates by face image.
    
    Args:
        image: Face image file
        threshold: Minimum similarity threshold (0-1), default is 0.65 (65%)
        
    Returns:
        List of candidate matches with similarity scores
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Process image to get face embedding
        result = repository.image_processor.process_image(image_data, "direct_face")
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Search for matches
        matches = await repository.search_by_face(
            result["face_embedding"],
            threshold=threshold
        )
        
        return matches
        
    except Exception as e:
        logger.error(f"Error in search_by_face: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-embedding/{candidate_id}")
async def update_face_embedding(
    candidate_id: str,
    image: UploadFile = File(...),
    source: str = Form(...),
    repository: ImageSearchRepository = Depends(get_image_search_repository)
):
    """
    Update face embedding for a candidate.
    
    Args:
        candidate_id: Candidate ID
        image: Face image file
        source: Source of the image (id_card, candidate_card, direct_face)
        
    Returns:
        Success message
    """
    try:
        # Read image data
        image_data = await image.read()
        
        # Process image to get face embedding
        result = repository.image_processor.process_image(image_data, source)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Update embedding
        success = await repository.update_face_embedding(
            candidate_id,
            result["face_embedding"],
            result["face_embedding_model"],
            source
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update face embedding")
        
        return {"message": "Face embedding updated successfully"}
        
    except Exception as e:
        logger.error(f"Error in update_face_embedding: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/embedding/{candidate_id}")
async def get_face_embedding(
    candidate_id: str,
    repository: ImageSearchRepository = Depends(get_image_search_repository)
):
    """
    Get face embedding for a candidate.
    
    Args:
        candidate_id: Candidate ID
        
    Returns:
        Face embedding information
    """
    try:
        # Get embedding
        embedding = await repository.get_face_embedding(candidate_id)
        
        if embedding is None:
            raise HTTPException(status_code=404, detail="Face embedding not found")
        
        return {
            "candidate_id": candidate_id,
            "face_embedding": embedding
        }
        
    except Exception as e:
        logger.error(f"Error in get_face_embedding: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 