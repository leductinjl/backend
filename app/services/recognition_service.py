"""
Recognition service module.

This module contains business logic for handling recognition operations,
using the repository layer for data access.
"""

from app.repositories.recognition_repository import RecognitionRepository
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
import logging

class RecognitionService:
    """
    Service for handling business logic related to recognitions
    """
    
    def __init__(self, recognition_repo: RecognitionRepository):
        """
        Initialize Recognition Service
        
        Args:
            recognition_repo: Repository for interacting with recognition data
        """
        self.recognition_repo = recognition_repo
        self.logger = logging.getLogger(__name__)
    
    async def get_all_recognitions(
        self, 
        skip: int = 0, 
        limit: int = 100,
        candidate_exam_id: Optional[str] = None,
        recognition_type: Optional[str] = None,
        issuing_organization: Optional[str] = None,
        issue_date_from: Optional[date] = None,
        issue_date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get list of recognitions with pagination and filtering
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            candidate_exam_id: Filter by candidate exam ID
            recognition_type: Filter by recognition type
            issuing_organization: Filter by issuing organization
            issue_date_from: Filter by minimum issue date
            issue_date_to: Filter by maximum issue date
            
        Returns:
            Dictionary containing list of recognitions and pagination metadata
        """
        try:
            # Construct filters dictionary
            filters = {}
            if candidate_exam_id:
                filters['candidate_exam_id'] = candidate_exam_id
            if recognition_type:
                filters['recognition_type'] = recognition_type
            if issuing_organization:
                filters['issuing_organization'] = issuing_organization
            if issue_date_from:
                filters['issue_date_from'] = issue_date_from
            if issue_date_to:
                filters['issue_date_to'] = issue_date_to
                
            recognitions, total = await self.recognition_repo.get_all(skip, limit, filters)
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_recognition(recognition) for recognition in recognitions],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting all recognitions: {e}")
            raise
    
    async def get_recognition_by_id(self, recognition_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a recognition by its ID
        
        Args:
            recognition_id: ID of the recognition to retrieve
            
        Returns:
            Dictionary containing recognition details or None if not found
        """
        try:
            recognition = await self.recognition_repo.get_by_id(recognition_id)
            if not recognition:
                return None
            
            return self._serialize_recognition(recognition)
        except Exception as e:
            self.logger.error(f"Error getting recognition {recognition_id}: {e}")
            raise
    
    async def get_recognitions_by_candidate_exam(
        self, 
        candidate_exam_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all recognitions for a specific candidate exam
        
        Args:
            candidate_exam_id: ID of the candidate exam
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of recognitions and pagination metadata
        """
        try:
            recognitions, total = await self.recognition_repo.get_by_candidate_exam(
                candidate_exam_id, skip, limit
            )
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_recognition(recognition) for recognition in recognitions],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting recognitions for candidate exam {candidate_exam_id}: {e}")
            raise
    
    async def get_recognitions_by_issuing_organization(
        self, 
        organization: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all recognitions issued by a specific organization
        
        Args:
            organization: Name of the issuing organization
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of recognitions and pagination metadata
        """
        try:
            recognitions, total = await self.recognition_repo.get_by_issuing_organization(
                organization, skip, limit
            )
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_recognition(recognition) for recognition in recognitions],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting recognitions for organization {organization}: {e}")
            raise
    
    async def create_recognition(self, recognition_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new recognition
        
        Args:
            recognition_data: Dictionary containing recognition data
            
        Returns:
            Dictionary containing created recognition details
        """
        try:
            # Don't set recognition_id here, let the repository handle it
            if 'recognition_id' in recognition_data and not recognition_data['recognition_id']:
                del recognition_data['recognition_id']
                
            self.logger.info(f"Creating recognition for candidate_exam_id: {recognition_data.get('candidate_exam_id')}")
            recognition = await self.recognition_repo.create(recognition_data)
            self.logger.info(f"Successfully created recognition with ID: {recognition.recognition_id}")
            
            # Return basic recognition data to avoid potential relationship loading issues
            return {
                "recognition_id": recognition.recognition_id,
                "title": recognition.title,
                "issuing_organization": recognition.issuing_organization,
                "issue_date": recognition.issue_date,
                "recognition_type": recognition.recognition_type,
                "candidate_exam_id": recognition.candidate_exam_id,
                "recognition_image_url": recognition.recognition_image_url,
                "description": recognition.description,
                "additional_info": recognition.additional_info,
                "created_at": recognition.created_at,
                "updated_at": recognition.updated_at,
                "candidate_name": None,
                "exam_name": None
            }
        except Exception as e:
            self.logger.error(f"Error creating recognition: {e}")
            raise
    
    async def update_recognition(
        self, 
        recognition_id: str, 
        recognition_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing recognition
        
        Args:
            recognition_id: ID of the recognition to update
            recognition_data: Dictionary containing updated data
            
        Returns:
            Dictionary containing updated recognition details or None if not found
        """
        try:
            recognition = await self.recognition_repo.update(
                recognition_id, 
                recognition_data
            )
            if not recognition:
                return None
            
            return self._serialize_recognition(recognition)
        except Exception as e:
            self.logger.error(f"Error updating recognition {recognition_id}: {e}")
            raise
    
    async def delete_recognition(self, recognition_id: str) -> bool:
        """
        Delete a recognition
        
        Args:
            recognition_id: ID of the recognition to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            return await self.recognition_repo.delete(recognition_id)
        except Exception as e:
            self.logger.error(f"Error deleting recognition {recognition_id}: {e}")
            raise
    
    def _serialize_recognition(self, recognition) -> Dict[str, Any]:
        """
        Convert recognition model to dictionary with detailed information
        
        Args:
            recognition: Recognition model object
            
        Returns:
            Dictionary containing recognition information
        """
        data = {
            "recognition_id": recognition.recognition_id,
            "title": recognition.title,
            "issuing_organization": recognition.issuing_organization,
            "issue_date": recognition.issue_date,
            "recognition_type": recognition.recognition_type,
            "candidate_exam_id": recognition.candidate_exam_id,
            "recognition_image_url": recognition.recognition_image_url,
            "description": recognition.description,
            "additional_info": recognition.additional_info,
            "created_at": recognition.created_at,
            "updated_at": recognition.updated_at,
            # Set default values for related information
            "candidate_name": None,
            "exam_name": None
        }
        
        # Safely add candidate name and exam name if available
        try:
            if hasattr(recognition, 'candidate_exam') and recognition.candidate_exam:
                if hasattr(recognition.candidate_exam, 'candidate') and recognition.candidate_exam.candidate:
                    data["candidate_name"] = recognition.candidate_exam.candidate.full_name
                
                if hasattr(recognition.candidate_exam, 'exam') and recognition.candidate_exam.exam:
                    data["exam_name"] = recognition.candidate_exam.exam.exam_name
        except Exception as e:
            # Log but don't fail if there's an issue accessing relationships
            self.logger.warning(f"Error accessing relationships for recognition {recognition.recognition_id}: {e}")
        
        return data 