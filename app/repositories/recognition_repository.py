"""
Recognition repository module.

This module provides database access methods for the Recognition model,
including CRUD operations and queries for retrieving recognitions
with filtering options.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload
from typing import Optional, List, Dict, Any, Tuple
from app.domain.models.recognition import Recognition
from app.domain.models.candidate_exam import CandidateExam
from datetime import date
import logging
from app.services.id_service import generate_model_id

class RecognitionRepository:
    """Repository for Recognition database operations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize Recognition Repository
        
        Args:
            db: Database session
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Recognition], int]:
        """
        Get all recognitions with pagination and optional filtering
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Dictionary of filter conditions
                - candidate_exam_id: Filter by candidate exam ID
                - recognition_type: Filter by recognition type
                - issuing_organization: Filter by issuing organization
                - issue_date_from: Filter by minimum issue date
                - issue_date_to: Filter by maximum issue date
                
        Returns:
            Tuple of (list of Recognition objects, total count)
        """
        try:
            # Build query
            query = select(Recognition).options(
                joinedload(Recognition.candidate_exam)
            )
            
            # Apply filters
            if filters:
                conditions = []
                
                if 'candidate_exam_id' in filters:
                    conditions.append(Recognition.candidate_exam_id == filters['candidate_exam_id'])
                
                if 'recognition_type' in filters:
                    conditions.append(Recognition.recognition_type == filters['recognition_type'])
                
                if 'issuing_organization' in filters:
                    conditions.append(Recognition.issuing_organization == filters['issuing_organization'])
                
                if 'issue_date_from' in filters:
                    conditions.append(Recognition.issue_date >= filters['issue_date_from'])
                
                if 'issue_date_to' in filters:
                    conditions.append(Recognition.issue_date <= filters['issue_date_to'])
                
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Recognition.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            recognitions = result.scalars().unique().all()
            
            return recognitions, total
        
        except Exception as e:
            self.logger.error(f"Error in get_all: {e}")
            raise
    
    async def get_by_id(self, recognition_id: str) -> Optional[Recognition]:
        """
        Get a recognition by ID
        
        Args:
            recognition_id: ID of the recognition to retrieve
            
        Returns:
            Recognition object or None if not found
        """
        try:
            query = select(Recognition).where(
                Recognition.recognition_id == recognition_id
            ).options(
                joinedload(Recognition.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Recognition.candidate_exam)
                .joinedload(CandidateExam.exam)
            )
            
            result = await self.db.execute(query)
            return result.scalars().first()
        
        except Exception as e:
            self.logger.error(f"Error in get_by_id: {e}")
            raise
    
    async def get_by_candidate_exam(
        self, 
        candidate_exam_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Recognition], int]:
        """
        Get recognitions for a specific candidate exam
        
        Args:
            candidate_exam_id: ID of the candidate exam
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of Recognition objects, total count)
        """
        try:
            # Build query
            query = select(Recognition).where(
                Recognition.candidate_exam_id == candidate_exam_id
            ).options(
                joinedload(Recognition.candidate_exam)
            )
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Recognition.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            recognitions = result.scalars().unique().all()
            
            return recognitions, total
        
        except Exception as e:
            self.logger.error(f"Error in get_by_candidate_exam: {e}")
            raise
    
    async def get_by_issuing_organization(
        self,
        organization: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Recognition], int]:
        """
        Get recognitions issued by a specific organization
        
        Args:
            organization: Name of the issuing organization
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of Recognition objects, total count)
        """
        try:
            # Build query
            query = select(Recognition).where(
                Recognition.issuing_organization == organization
            ).options(
                joinedload(Recognition.candidate_exam)
            )
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Recognition.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            recognitions = result.scalars().unique().all()
            
            return recognitions, total
        
        except Exception as e:
            self.logger.error(f"Error in get_by_issuing_organization: {e}")
            raise
    
    async def create(self, recognition_data: Dict[str, Any]) -> Recognition:
        """
        Create a new recognition
        
        Args:
            recognition_data: Dictionary containing recognition data
            
        Returns:
            Created Recognition object
        """
        try:
            # Ensure recognition_id is set
            if 'recognition_id' not in recognition_data or not recognition_data['recognition_id']:
                recognition_data['recognition_id'] = generate_model_id("Recognition")
                self.logger.info(f"Generated new recognition ID: {recognition_data['recognition_id']}")
            
            self.logger.debug(f"Creating recognition with ID: {recognition_data['recognition_id']}")
            recognition = Recognition(**recognition_data)
            self.db.add(recognition)
            await self.db.flush()
            await self.db.refresh(recognition)
            self.logger.info(f"Successfully created recognition: {recognition.recognition_id}")
            
            # Return the fully loaded recognition with relationships
            return await self.get_by_id(recognition.recognition_id)
        
        except Exception as e:
            self.logger.error(f"Error in create: {e}")
            raise
    
    async def update(
        self, 
        recognition_id: str, 
        recognition_data: Dict[str, Any]
    ) -> Optional[Recognition]:
        """
        Update an existing recognition
        
        Args:
            recognition_id: ID of the recognition to update
            recognition_data: Dictionary containing updated data
            
        Returns:
            Updated Recognition object or None if not found
        """
        try:
            # Check if recognition exists
            query = select(Recognition).where(Recognition.recognition_id == recognition_id)
            result = await self.db.execute(query)
            recognition = result.scalars().first()
            
            if not recognition:
                return None
            
            # Update recognition
            query = update(Recognition).where(
                Recognition.recognition_id == recognition_id
            ).values(**recognition_data).returning(Recognition)
            
            result = await self.db.execute(query)
            await self.db.flush()
            
            # Get updated recognition
            updated_recognition = await self.get_by_id(recognition_id)
            return updated_recognition
        
        except Exception as e:
            self.logger.error(f"Error in update: {e}")
            raise
    
    async def delete(self, recognition_id: str) -> bool:
        """
        Delete a recognition
        
        Args:
            recognition_id: ID of the recognition to delete
            
        Returns:
            Boolean indicating if the recognition was deleted
        """
        try:
            # Check if recognition exists
            query = select(Recognition).where(Recognition.recognition_id == recognition_id)
            result = await self.db.execute(query)
            recognition = result.scalars().first()
            
            if not recognition:
                return False
            
            # Delete recognition
            query = delete(Recognition).where(Recognition.recognition_id == recognition_id)
            await self.db.execute(query)
            await self.db.flush()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error in delete: {e}")
            raise 