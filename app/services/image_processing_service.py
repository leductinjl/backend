"""
Image Processing Service module.

This module provides services for processing images and generating face embeddings
for candidate identification and search.
"""

import logging
import numpy as np
import cv2
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import json
import base64
from io import BytesIO
from PIL import Image
import insightface
from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)

class ImageProcessingService:
    """
    Service for processing images and generating face embeddings.
    
    This service handles:
    1. Face detection and alignment
    2. Face embedding generation
    3. Face comparison and similarity calculation
    4. Image preprocessing and validation
    """
    
    def __init__(self, model_name: str = "insightface"):
        """
        Initialize the image processing service.
        
        Args:
            model_name: Name of the face recognition model to use
        """
        self.model_name = model_name
        self.face_analyzer = FaceAnalysis(
            name="buffalo_l",  # Using buffalo_l model for better accuracy
            providers=['CPUExecutionProvider']
        )
        self.face_analyzer.prepare(ctx_id=0, det_size=(640, 640))
        logger.info(f"Initialized ImageProcessingService with model: {model_name}")
    
    def process_image(self, image_data: bytes, source: str) -> Dict[str, Any]:
        """
        Process an image to detect faces and generate embeddings.
        
        Args:
            image_data: Binary image data
            source: Source of the image (id_card, candidate_card, direct_face)
            
        Returns:
            Dictionary containing face embedding and metadata
        """
        try:
            # Convert binary data to numpy array
            image = self._bytes_to_image(image_data)
            if image is None:
                return {"error": "Invalid image data"}
            
            # Detect faces and get embeddings
            faces = self.face_analyzer.get(image)
            if not faces:
                return {"error": "No face detected in the image"}
            
            # Use the first face found
            face = faces[0]
            face_embedding = face.embedding
            
            # Convert numpy array to list for JSON serialization
            embedding_list = face_embedding.tolist()
            
            # Create result dictionary
            result = {
                "face_embedding": embedding_list,
                "face_embedding_model": self.model_name,
                "face_embedding_date": datetime.now().isoformat(),
                "face_embedding_source": source,
                "face_count": len(faces),
                "image_size": image.shape[:2],
                "success": True
            }
            
            logger.info(f"Successfully processed image from source: {source}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            return {"error": f"Error processing image: {str(e)}", "success": False}
    
    def compare_faces(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compare two face embeddings and return similarity score.
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            
        Returns:
            Similarity score between 0 and 1 (1 being identical)
        """
        try:
            # Convert lists to numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            logger.info(f"Face comparison completed with similarity: {similarity:.4f}")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error comparing faces: {str(e)}", exc_info=True)
            return 0.0
    
    def find_matches(self, query_embedding: List[float], candidates: List[Dict[str, Any]], 
                    threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Find candidate matches based on face embedding similarity.
        
        Args:
            query_embedding: Face embedding to compare against
            candidates: List of candidates with face embeddings
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            List of matches with similarity scores
        """
        matches = []
        
        for candidate in candidates:
            if "face_embedding" not in candidate:
                continue
                
            similarity = self.compare_faces(query_embedding, candidate["face_embedding"])
            
            if similarity >= threshold:
                match = {
                    "candidate_id": candidate.get("candidate_id"),
                    "full_name": candidate.get("full_name"),
                    "similarity": similarity,
                    "face_embedding_source": candidate.get("face_embedding_source"),
                    "face_embedding_date": candidate.get("face_embedding_date")
                }
                matches.append(match)
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        logger.info(f"Found {len(matches)} matches above threshold {threshold}")
        return matches
    
    def _bytes_to_image(self, image_data: bytes) -> Optional[np.ndarray]:
        """
        Convert binary image data to numpy array.
        
        Args:
            image_data: Binary image data
            
        Returns:
            Numpy array representing the image, or None if conversion fails
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Convert to numpy array
            return np.array(image)
            
        except Exception as e:
            logger.error(f"Error converting image data: {str(e)}", exc_info=True)
            return None
    
    def encode_embedding(self, embedding: List[float]) -> str:
        """
        Encode face embedding to base64 string for storage.
        
        Args:
            embedding: Face embedding as list of floats
            
        Returns:
            Base64 encoded string
        """
        try:
            # Convert to JSON string
            json_str = json.dumps(embedding)
            
            # Encode to base64
            encoded = base64.b64encode(json_str.encode()).decode()
            
            return encoded
            
        except Exception as e:
            logger.error(f"Error encoding embedding: {str(e)}", exc_info=True)
            return ""
    
    def decode_embedding(self, encoded: Any) -> Optional[List[float]]:
        """
        Decode face embedding from base64 string or list.
        
        Args:
            encoded: Base64 encoded string or list of floats
            
        Returns:
            Face embedding as list of floats, or None if decoding fails
        """
        try:
            # If already a list, return it directly
            if isinstance(encoded, list):
                return encoded
                
            # If string, decode from base64
            if isinstance(encoded, str):
                json_str = base64.b64decode(encoded.encode()).decode()
                embedding = json.loads(json_str)
                return embedding
                
            # If not a list or string, return None
            logger.error(f"Invalid embedding format: {type(encoded)}")
            return None
            
        except Exception as e:
            logger.error(f"Error decoding embedding: {str(e)}", exc_info=True)
            return None 