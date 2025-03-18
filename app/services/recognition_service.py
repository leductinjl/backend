"""
Recognition service module.

This module contains business logic for handling recognition operations,
using the repository layer for data access.
"""

from app.repositories.recognition_repository import RecognitionRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
import logging

class RecognitionService:
    """
    Service for handling business logic related to recognitions
    """
    
    def __init__(
        self, 
        recognition_repo: RecognitionRepository,
        candidate_exam_repo: Optional[CandidateExamRepository] = None
    ):
        """
        Initialize Recognition Service
        
        Args:
            recognition_repo: Repository for interacting with recognition data
            candidate_exam_repo: Repository for interacting with candidate exam data
        """
        self.recognition_repo = recognition_repo
        self.candidate_exam_repo = candidate_exam_repo
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
    
    async def get_recognitions_by_candidate_id(
        self, 
        candidate_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get all recognitions for a specific candidate across all exams
        
        Args:
            candidate_id: ID of the candidate
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of recognitions and pagination metadata
        """
        try:
            # Verify that we have the required repository
            if not self.candidate_exam_repo:
                self.logger.error("Cannot get recognitions by candidate ID: candidate_exam_repo not provided")
                return {
                    "items": [],
                    "total": 0,
                    "page": 1,
                    "size": limit
                }
            
            # Get all candidate-exam registrations for this candidate
            candidate_exams = await self.candidate_exam_repo.get_by_candidate_id(candidate_id)
            
            # No registrations found
            if not candidate_exams:
                self.logger.info(f"No exam registrations found for candidate ID {candidate_id}")
                return {
                    "items": [],
                    "total": 0,
                    "page": 1,
                    "size": limit
                }
            
            # Collect all recognitions from all candidate-exam registrations
            all_recognitions = []
            total_count = 0
            
            for candidate_exam in candidate_exams:
                recognitions, count = await self.recognition_repo.get_by_candidate_exam(
                    candidate_exam["candidate_exam_id"], 0, 1000  # Get all recognitions
                )
                
                for recognition in recognitions:
                    # Add exam name to the recognition for context
                    serialized_recognition = self._serialize_recognition(recognition)
                    serialized_recognition["exam_name"] = candidate_exam.get("exam_name", "Unknown Exam")
                    all_recognitions.append(serialized_recognition)
                
                total_count += count
            
            # Apply pagination to the combined result
            start_idx = skip
            end_idx = min(skip + limit, len(all_recognitions))
            paginated_recognitions = all_recognitions[start_idx:end_idx] if start_idx < len(all_recognitions) else []
            
            return {
                "items": paginated_recognitions,
                "total": total_count,
                "page": skip // limit + 1 if limit > 0 else 1,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting recognitions for candidate {candidate_id}: {e}")
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
            # Debug log to check relationship structure
            self.logger.debug(f"Recognition: {recognition.recognition_id}")
            self.logger.debug(f"Has candidate_exam: {hasattr(recognition, 'candidate_exam')}")
            
            if hasattr(recognition, 'candidate_exam') and recognition.candidate_exam is not None:
                self.logger.debug(f"CandidateExam ID: {recognition.candidate_exam.candidate_exam_id}")
                self.logger.debug(f"Has candidate: {hasattr(recognition.candidate_exam, 'candidate')}")
                
                if hasattr(recognition.candidate_exam, 'candidate') and recognition.candidate_exam.candidate is not None:
                    candidate = recognition.candidate_exam.candidate
                    self.logger.debug(f"Candidate ID: {candidate.candidate_id}")
                    self.logger.debug(f"Has full_name: {hasattr(candidate, 'full_name')}")
                    
                    data["candidate_name"] = candidate.full_name
                
                if hasattr(recognition.candidate_exam, 'exam') and recognition.candidate_exam.exam is not None:
                    self.logger.debug(f"Has exam: {hasattr(recognition.candidate_exam, 'exam')}")
                    self.logger.debug(f"Exam ID: {recognition.candidate_exam.exam.exam_id}")
                    self.logger.debug(f"Has exam_name: {hasattr(recognition.candidate_exam.exam, 'exam_name')}")
                    
                    data["exam_name"] = recognition.candidate_exam.exam.exam_name
        except Exception as e:
            # Log but don't fail if there's an issue accessing relationships
            self.logger.warning(f"Error accessing relationships for recognition {recognition.recognition_id}: {e}")
        
        return data 