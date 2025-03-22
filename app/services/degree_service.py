"""
Degree service module.

This module contains business logic for handling degree operations,
using the repository layer for data access.
"""

from app.repositories.degree_repository import DegreeRepository
from typing import List, Dict, Any, Optional, Tuple
import logging

class DegreeService:
    """
    Service for handling business logic related to degrees
    """
    
    def __init__(self, degree_repo: DegreeRepository):
        """
        Initialize Degree Service
        
        Args:
            degree_repo: Repository for interacting with degree data
        """
        self.degree_repo = degree_repo
        self.logger = logging.getLogger(__name__)
    
    async def get_all_degrees(
        self, 
        skip: int = 0, 
        limit: int = 100,
        major_id: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get list of degrees with pagination and filtering
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            major_id: Filter by major ID
            start_year: Filter by minimum start year
            end_year: Filter by maximum end year
            
        Returns:
            Dictionary containing list of degrees and pagination metadata
        """
        try:
            # Construct filters dictionary
            filters = {}
            if major_id:
                filters['major_id'] = major_id
            if start_year:
                filters['start_year'] = start_year
            if end_year:
                filters['end_year'] = end_year
                
            degrees, total = await self.degree_repo.get_all(skip, limit, filters)
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Convert to serialized response
            return {
                "items": [self._serialize_degree(degree) for degree in degrees],
                "total": total,
                "page": page,
                "size": limit
            }
        except Exception as e:
            self.logger.error(f"Error getting all degrees: {e}")
            raise
    
    async def get_degree_by_id(self, degree_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a degree by its ID
        
        Args:
            degree_id: ID of the degree to retrieve
            
        Returns:
            Dictionary containing degree details or None if not found
        """
        try:
            degree = await self.degree_repo.get_by_id(degree_id)
            if not degree:
                return None
            
            return self._serialize_degree(degree)
        except Exception as e:
            self.logger.error(f"Error getting degree {degree_id}: {e}")
            raise
    
    async def get_degrees_by_major(self, major_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all degrees for a specific major
        
        Args:
            major_id: ID of the major
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of dictionaries containing degree details
        """
        try:
            degrees = await self.degree_repo.get_by_major(major_id, skip, limit)
            return [self._serialize_degree(degree) for degree in degrees]
        except Exception as e:
            self.logger.error(f"Error getting degrees for major {major_id}: {e}")
            raise
    
    async def get_degrees_by_candidate(self, candidate_id: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get all degrees for a specific candidate
        
        Args:
            candidate_id: ID of the candidate
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Dictionary containing list of degree details and pagination metadata
        """
        try:
            degrees, total = await self.degree_repo.get_by_candidate(candidate_id, skip, limit)
            
            # Calculate pagination metadata
            page = skip // limit + 1 if limit else 1
            
            # Get candidate name if degrees were found
            candidate_name = None
            if degrees and len(degrees) > 0:
                # Query the candidate name if needed
                from sqlalchemy import select
                from app.domain.models.candidate import Candidate
                
                query = select(Candidate.full_name).where(Candidate.candidate_id == candidate_id)
                result = await self.degree_repo.db_session.execute(query)
                candidate_name = result.scalar()
            
            # Serialize degrees and add candidate name
            serialized_degrees = []
            for degree in degrees:
                degree_dict = self._serialize_degree(degree)
                # Set candidate name if needed and not already set
                if candidate_name and (not "candidate_name" in degree_dict or not degree_dict["candidate_name"]):
                    degree_dict["candidate_name"] = candidate_name
                    
                serialized_degrees.append(degree_dict)
            
            # Return with pagination data
            return {
                "items": serialized_degrees,
                "total": total,
                "page": page,
                "size": limit,
                "candidate_id": candidate_id,
                "candidate_name": candidate_name
            }
        except Exception as e:
            self.logger.error(f"Error getting degrees for candidate {candidate_id}: {e}")
            raise
    
    async def create_degree(self, degree_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new degree
        
        Args:
            degree_data: Dictionary containing degree data
            
        Returns:
            Dictionary containing created degree details
        """
        try:
            degree = await self.degree_repo.create(degree_data)
            return self._serialize_degree(degree)
        except Exception as e:
            self.logger.error(f"Error creating degree: {e}")
            raise
    
    async def update_degree(self, degree_id: str, degree_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing degree
        
        Args:
            degree_id: ID of the degree to update
            degree_data: Dictionary containing updated data
            
        Returns:
            Dictionary containing updated degree details or None if not found
        """
        try:
            degree = await self.degree_repo.update(degree_id, degree_data)
            if not degree:
                return None
            
            return self._serialize_degree(degree)
        except Exception as e:
            self.logger.error(f"Error updating degree {degree_id}: {e}")
            raise
    
    async def delete_degree(self, degree_id: str) -> bool:
        """
        Delete a degree
        
        Args:
            degree_id: ID of the degree to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            return await self.degree_repo.delete(degree_id)
        except Exception as e:
            self.logger.error(f"Error deleting degree {degree_id}: {e}")
            raise
    
    def _serialize_degree(self, degree) -> Dict[str, Any]:
        """
        Convert degree model to dictionary with detailed information
        
        Args:
            degree: Degree model object
            
        Returns:
            Dictionary containing degree information
        """
        # Convert date objects to integers for year fields
        start_year = degree.start_year.year if degree.start_year else None
        end_year = degree.end_year.year if degree.end_year else None
        
        data = {
            "degree_id": degree.degree_id,
            "major_id": degree.major_id,
            "education_history_id": degree.education_history_id,
            "start_year": start_year,
            "end_year": end_year,
            "academic_performance": degree.academic_performance,
            "degree_image_url": degree.degree_image_url,
            "additional_info": degree.additional_info,
            "created_at": degree.created_at,
            "updated_at": degree.updated_at
        }
        
        # Add major name if available - use safe access pattern
        if hasattr(degree, 'major') and degree.major is not None:
            data["major_name"] = degree.major.major_name
        
        # Add candidate information if education history was loaded
        if degree.education_history_id and hasattr(degree, 'education_history') and degree.education_history is not None:
            data["candidate_id"] = degree.education_history.candidate_id
            
            # Safely access the candidate if it was loaded
            if hasattr(degree.education_history, 'candidate') and degree.education_history.candidate is not None:
                data["candidate_name"] = degree.education_history.candidate.full_name
        
        return data 