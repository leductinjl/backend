"""
Award repository module.

This module provides database access methods for the Award model,
including CRUD operations and queries for retrieving awards
with filtering options.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload
from typing import Optional, List, Dict, Any, Tuple
from app.domain.models.award import Award
from app.domain.models.candidate_exam import CandidateExam
from datetime import date
import logging
from app.services.id_service import generate_model_id

class AwardRepository:
    """Repository for Award database operations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize Award Repository
        
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
    ) -> Tuple[List[Award], int]:
        """
        Get all awards with pagination and optional filtering
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Dictionary of filter conditions
                - candidate_exam_id: Filter by candidate exam ID
                - award_type: Filter by award type
                - education_level: Filter by education level
                - award_date_from: Filter by minimum award date
                - award_date_to: Filter by maximum award date
                
        Returns:
            Tuple of (list of Award objects, total count)
        """
        try:
            # Build query
            query = select(Award).options(
                joinedload(Award.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Award.candidate_exam)
                .joinedload(CandidateExam.exam)
            )
            
            # Apply filters
            if filters:
                conditions = []
                
                if 'candidate_exam_id' in filters:
                    conditions.append(Award.candidate_exam_id == filters['candidate_exam_id'])
                
                if 'award_type' in filters:
                    conditions.append(Award.award_type == filters['award_type'])
                
                if 'education_level' in filters:
                    conditions.append(Award.education_level == filters['education_level'])
                
                if 'award_date_from' in filters:
                    conditions.append(Award.award_date >= filters['award_date_from'])
                
                if 'award_date_to' in filters:
                    conditions.append(Award.award_date <= filters['award_date_to'])
                
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Award.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            awards = result.scalars().unique().all()
            
            return awards, total
        
        except Exception as e:
            self.logger.error(f"Error in get_all: {e}")
            raise
    
    async def get_by_id(self, award_id: str) -> Optional[Award]:
        """
        Get an award by ID
        
        Args:
            award_id: ID of the award to retrieve
            
        Returns:
            Award object or None if not found
        """
        try:
            query = select(Award).where(
                Award.award_id == award_id
            ).options(
                joinedload(Award.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Award.candidate_exam)
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
    ) -> Tuple[List[Award], int]:
        """
        Get awards for a specific candidate exam
        
        Args:
            candidate_exam_id: ID of the candidate exam
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of Award objects, total count)
        """
        try:
            # Build query
            query = select(Award).where(
                Award.candidate_exam_id == candidate_exam_id
            ).options(
                joinedload(Award.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Award.candidate_exam)
                .joinedload(CandidateExam.exam)
            )
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Award.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            awards = result.scalars().unique().all()
            
            return awards, total
        
        except Exception as e:
            self.logger.error(f"Error in get_by_candidate_exam: {e}")
            raise
    
    async def get_by_award_type(
        self,
        award_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Award], int]:
        """
        Get awards of a specific type
        
        Args:
            award_type: Type of the award (First, Second, Third, etc.)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of Award objects, total count)
        """
        try:
            # Build query
            query = select(Award).where(
                Award.award_type == award_type
            ).options(
                joinedload(Award.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Award.candidate_exam)
                .joinedload(CandidateExam.exam)
            )
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Award.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            awards = result.scalars().unique().all()
            
            return awards, total
        
        except Exception as e:
            self.logger.error(f"Error in get_by_award_type: {e}")
            raise
    
    async def create(self, award_data: Dict[str, Any]) -> Award:
        """
        Create a new award
        
        Args:
            award_data: Dictionary containing award data
            
        Returns:
            Created Award object
        """
        try:
            # Ensure award_id is set
            if 'award_id' not in award_data or not award_data['award_id']:
                award_data['award_id'] = generate_model_id("Award")
                self.logger.info(f"Generated new award ID: {award_data['award_id']}")
            
            award = Award(**award_data)
            self.db.add(award)
            await self.db.flush()
            await self.db.refresh(award)
            return award
        
        except Exception as e:
            self.logger.error(f"Error in create: {e}")
            raise
    
    async def update(
        self, 
        award_id: str, 
        award_data: Dict[str, Any]
    ) -> Optional[Award]:
        """
        Update an existing award
        
        Args:
            award_id: ID of the award to update
            award_data: Dictionary containing updated data
            
        Returns:
            Updated Award object or None if not found
        """
        try:
            # Check if award exists
            query = select(Award).where(Award.award_id == award_id)
            result = await self.db.execute(query)
            award = result.scalars().first()
            
            if not award:
                return None
            
            # Update award
            query = update(Award).where(
                Award.award_id == award_id
            ).values(**award_data).returning(Award)
            
            result = await self.db.execute(query)
            await self.db.flush()
            
            # Get updated award
            updated_award = await self.get_by_id(award_id)
            return updated_award
        
        except Exception as e:
            self.logger.error(f"Error in update: {e}")
            raise
    
    async def delete(self, award_id: str) -> bool:
        """
        Delete an award
        
        Args:
            award_id: ID of the award to delete
            
        Returns:
            Boolean indicating if the award was deleted
        """
        try:
            # Check if award exists
            query = select(Award).where(Award.award_id == award_id)
            result = await self.db.execute(query)
            award = result.scalars().first()
            
            if not award:
                return False
            
            # Delete award
            query = delete(Award).where(Award.award_id == award_id)
            await self.db.execute(query)
            await self.db.flush()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error in delete: {e}")
            raise 