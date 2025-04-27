"""
Image Storage Service module.

This module provides services for storing and managing candidate images.
"""

import os
import logging
import uuid
from datetime import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.personal_info import PersonalInfo
from app.services.image_processing_service import ImageProcessingService
from app.config import settings

logger = logging.getLogger(__name__)

class ImageStorageService:
    """Service for handling image storage operations."""
    
    def __init__(self, db: AsyncSession, image_processor: ImageProcessingService):
        """
        Initialize the image storage service.
        
        Args:
            db: Database session
            image_processor: Image processing service instance
        """
        self.db = db
        self.image_processor = image_processor
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        self._ensure_upload_dir()
    
    def _get_full_url(self, path: str) -> str:
        """Convert a relative path to a full URL."""
        if not path:
            return None
        # Use the API URL from environment or default to localhost:8000
        base_url = os.getenv("API_URL", "http://localhost:8000")
        return f"{base_url}{path}"
    
    def _ensure_upload_dir(self):
        """Ensure the upload directory exists."""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    async def save_image(
        self,
        candidate_id: str,
        image: UploadFile,
        image_type: str,
        source: str
    ) -> dict:
        """
        Save an uploaded image and update the candidate's personal info.
        
        Args:
            candidate_id: ID of the candidate
            image: Uploaded image file
            image_type: Type of image (id_card, candidate_card, direct_face)
            source: Source of the image (upload, camera, etc.)
            
        Returns:
            dict: Information about the saved image
            
        Raises:
            HTTPException: If saving fails
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{candidate_id}_{image_type}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(self.upload_dir, filename)
            
            # Save the file
            with open(filepath, "wb") as f:
                content = await image.read()
                f.write(content)
            
            # Process image to get face embedding
            result = self.image_processor.process_image(content, source)
            
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])
            
            # Update personal info
            personal_info = await self.db.get(PersonalInfo, candidate_id)
            if not personal_info:
                raise HTTPException(status_code=404, detail="Candidate not found")
            
            # Update image URL and face embedding
            relative_url = f"/uploads/{filename}"
            if image_type == "id_card":
                personal_info.id_card_image_url = relative_url
            elif image_type == "candidate_card":
                personal_info.candidate_card_image_url = relative_url
            elif image_type == "direct_face":
                personal_info.face_recognition_data_url = relative_url
            
            personal_info.face_embedding = result["face_embedding"]
            personal_info.face_embedding_model = result["face_embedding_model"]
            personal_info.face_embedding_date = datetime.now()
            personal_info.face_embedding_source = source
            
            await self.db.commit()
            
            return {
                "message": "Image saved successfully",
                "image_url": self._get_full_url(relative_url),
                "image_type": image_type,
                "source": source
            }
            
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_image_url(self, candidate_id: str, image_type: str) -> str:
        """
        Get the URL of a candidate's image.
        
        Args:
            candidate_id: ID of the candidate
            image_type: Type of image (id_card, candidate_card, direct_face)
            
        Returns:
            str: URL of the image or None if not found
            
        Raises:
            HTTPException: If candidate not found
        """
        personal_info = await self.db.get(PersonalInfo, candidate_id)
        if not personal_info:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        if image_type == "id_card":
            url = personal_info.id_card_image_url
        elif image_type == "candidate_card":
            url = personal_info.candidate_card_image_url
        elif image_type == "direct_face":
            url = personal_info.face_recognition_data_url
        else:
            raise HTTPException(status_code=400, detail="Invalid image type")
        
        return self._get_full_url(url) 