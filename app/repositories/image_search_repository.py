"""
Image Search Repository module.

This module provides data access methods for face embedding storage and retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload
from app.domain.models.personal_info import PersonalInfo
from app.domain.models.candidate import Candidate
from app.services.image_processing_service import ImageProcessingService

logger = logging.getLogger(__name__)

class ImageSearchRepository:
    """
    Repository for face embedding storage and retrieval.
    
    This repository handles:
    1. Storing face embeddings in the database
    2. Retrieving candidates with face embeddings
    3. Searching for candidates by face similarity
    """
    
    def __init__(self, db: AsyncSession, image_processor: ImageProcessingService):
        """
        Initialize the repository.
        
        Args:
            db: Database session
            image_processor: Image processing service instance
        """
        self.db = db
        self.image_processor = image_processor
        logger.info("Initialized ImageSearchRepository")
    
    async def update_face_embedding(self, candidate_id: str, face_embedding: List[float], 
                            model: str, source: str) -> bool:
        """
        Update face embedding for a candidate.
        
        Args:
            candidate_id: Candidate ID
            face_embedding: Face embedding vector
            model: Model used to generate the embedding
            source: Source of the image
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Encode embedding for storage
            encoded_embedding = self.image_processor.encode_embedding(face_embedding)
            if not encoded_embedding:
                logger.error(f"Failed to encode embedding for candidate {candidate_id}")
                return False
            
            # Update personal info record
            stmt = select(PersonalInfo).where(PersonalInfo.candidate_id == candidate_id)
            result = await self.db.execute(stmt)
            personal_info = result.scalar_one_or_none()
            
            if not personal_info:
                logger.error(f"Personal info not found for candidate {candidate_id}")
                return False
            
            # Update face embedding fields
            personal_info.face_embedding = encoded_embedding
            personal_info.face_embedding_model = model
            personal_info.face_embedding_date = text("CURRENT_TIMESTAMP")
            personal_info.face_embedding_source = source
            
            # Commit changes
            await self.db.commit()
            
            logger.info(f"Updated face embedding for candidate {candidate_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating face embedding: {str(e)}", exc_info=True)
            return False
    
    async def get_candidates_with_embeddings(self) -> List[Dict[str, Any]]:
        """
        Get all candidates with face embeddings.
        
        Returns:
            List of candidates with face embeddings
        """
        try:
            # Query candidates with face embeddings
            stmt = select(
                Candidate.candidate_id,
                Candidate.full_name,
                PersonalInfo.face_embedding,
                PersonalInfo.face_embedding_model,
                PersonalInfo.face_embedding_date,
                PersonalInfo.face_embedding_source
            ).join(
                PersonalInfo, 
                Candidate.candidate_id == PersonalInfo.candidate_id, 
                isouter=True
            ).where(
                PersonalInfo.face_embedding.isnot(None)
            )
            
            result = await self.db.execute(stmt)
            rows = result.fetchall()
            
            # Format results
            candidates = []
            for row in rows:
                if row.face_embedding:
                    # Decode embedding
                    embedding = self.image_processor.decode_embedding(row.face_embedding)
                    if embedding:
                        candidates.append({
                            "candidate_id": row.candidate_id,
                            "full_name": row.full_name,
                            "face_embedding": embedding,
                            "model": row.face_embedding_model,
                            "date": row.face_embedding_date,
                            "source": row.face_embedding_source
                        })
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error retrieving candidates with embeddings: {str(e)}", exc_info=True)
            return []
    
    async def search_by_face(self, face_embedding: List[float], threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Search for candidates by face embedding.
        
        Args:
            face_embedding: Face embedding to search for
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of candidates with similarity scores
        """
        try:
            # Get all candidates with embeddings
            candidates = await self.get_candidates_with_embeddings()
            
            # Calculate similarity scores
            results = []
            for candidate in candidates:
                if not candidate.get("face_embedding"):
                    continue
                    
                # Decode embedding
                candidate_embedding = self.image_processor.decode_embedding(candidate["face_embedding"])
                if not candidate_embedding:
                    continue
                    
                # Calculate similarity using compare_faces
                similarity = self.image_processor.compare_faces(face_embedding, candidate_embedding)
                
                if similarity >= threshold:
                    results.append({
                        "candidate_id": candidate["candidate_id"],
                        "full_name": candidate["full_name"],
                        "similarity": similarity,
                        "face_embedding_source": candidate["source"],
                        "face_embedding_date": candidate["date"] if candidate["date"] else None
                    })
            
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching by face: {str(e)}", exc_info=True)
            raise
    
    async def get_face_embedding(self, candidate_id: str) -> Optional[List[float]]:
        """
        Get face embedding for a candidate.
        
        Args:
            candidate_id: Candidate ID
            
        Returns:
            Face embedding vector or None if not found
        """
        try:
            stmt = select(PersonalInfo.face_embedding).where(
                PersonalInfo.candidate_id == candidate_id
            )
            result = await self.db.execute(stmt)
            row = result.scalar_one_or_none()
            
            if not row or not row.face_embedding:
                return None
            
            # Decode embedding
            return self.image_processor.decode_embedding(row.face_embedding)
            
        except Exception as e:
            logger.error(f"Error getting face embedding: {str(e)}", exc_info=True)
            return None 