"""
Education History repository module.

This module provides database access methods for the EducationHistory model, including
CRUD operations and queries for retrieving education history entries with filtering options.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload
from app.domain.models.education_history import EducationHistory
from app.domain.models.candidate import Candidate
from app.domain.models.school import School
from app.domain.models.education_level import EducationLevel
from typing import List, Optional, Dict, Any, Tuple
import logging

class EducationHistoryRepository:
    """
    Repository for interacting with the EducationHistory table in PostgreSQL
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        candidate_id: Optional[str] = None,
        school_id: Optional[str] = None,
        education_level_id: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[List[EducationHistory], int]:
        """
        Retrieve education history entries with pagination and filtering.
        
        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            candidate_id: Filter by candidate ID
            school_id: Filter by school ID
            education_level_id: Filter by education level ID
            start_year: Filter by start year
            end_year: Filter by end year
            
        Returns:
            Tuple containing list of education history entries and total count
        """
        try:
            # Build query
            query = (
                select(EducationHistory)
                .options(
                    joinedload(EducationHistory.candidate),
                    joinedload(EducationHistory.school),
                    joinedload(EducationHistory.education_level)
                )
            )
            
            # Apply filters
            conditions = []
            if candidate_id:
                conditions.append(EducationHistory.candidate_id == candidate_id)
            if school_id:
                conditions.append(EducationHistory.school_id == school_id)
            if education_level_id:
                conditions.append(EducationHistory.education_level_id == education_level_id)
            if start_year:
                conditions.append(EducationHistory.start_year >= start_year)
            if end_year:
                conditions.append(EducationHistory.end_year <= end_year)
                
            if conditions:
                query = query.where(and_(*conditions))
                
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db_session.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db_session.execute(query)
            education_histories = result.scalars().unique().all()
            
            return education_histories, total
        except Exception as e:
            self.logger.error(f"Error retrieving education histories: {str(e)}")
            raise
    
    async def get_by_id(self, education_history_id: str) -> Optional[EducationHistory]:
        """
        Get an education history entry by ID.
        
        Args:
            education_history_id: ID of the education history to retrieve
            
        Returns:
            EducationHistory object or None if not found
        """
        try:
            query = (
                select(EducationHistory)
                .where(EducationHistory.education_history_id == education_history_id)
                .options(
                    joinedload(EducationHistory.candidate),
                    joinedload(EducationHistory.school),
                    joinedload(EducationHistory.education_level)
                )
            )
            result = await self.db_session.execute(query)
            return result.scalars().first()
        except Exception as e:
            self.logger.error(f"Error getting education history with ID {education_history_id}: {str(e)}")
            raise
    
    async def get_by_candidate(
        self, 
        candidate_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[EducationHistory], int]:
        """
        Get all education history entries for a specific candidate
        
        Args:
            candidate_id: ID of the candidate
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple containing list of education history entries and total count
        """
        try:
            # Count total records for this candidate
            count_query = select(func.count()).select_from(EducationHistory).where(
                EducationHistory.candidate_id == candidate_id
            )
            total_count = await self.db_session.scalar(count_query)
            
            # Query with pagination
            query = select(EducationHistory).options(
                joinedload(EducationHistory.school),
                joinedload(EducationHistory.candidate),
                joinedload(EducationHistory.education_level)
            ).where(
                EducationHistory.candidate_id == candidate_id
            ).offset(skip).limit(limit)
            
            result = await self.db_session.execute(query)
            return list(result.scalars().all()), total_count
        except Exception as e:
            self.logger.error(f"Error getting education history for candidate {candidate_id}: {e}")
            raise
    
    async def get_by_school(
        self, 
        school_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[EducationHistory], int]:
        """
        Get all education history entries for a specific school
        
        Args:
            school_id: ID of the school
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple containing list of education history entries and total count
        """
        try:
            # Count total records for this school
            count_query = select(func.count()).select_from(EducationHistory).where(
                EducationHistory.school_id == school_id
            )
            total_count = await self.db_session.scalar(count_query)
            
            # Query with pagination
            query = select(EducationHistory).options(
                joinedload(EducationHistory.candidate)
            ).where(
                EducationHistory.school_id == school_id
            ).offset(skip).limit(limit)
            
            result = await self.db_session.execute(query)
            return list(result.scalars().all()), total_count
        except Exception as e:
            self.logger.error(f"Error getting education history for school {school_id}: {e}")
            raise
    
    async def create(self, education_history_data: Dict[str, Any]) -> EducationHistory:
        """
        Create a new education history entry
        
        Args:
            education_history_data: Dictionary containing education history data
            
        Returns:
            Created education history object
        """
        try:
            # Convert integer years to date objects
            if 'start_year' in education_history_data and isinstance(education_history_data['start_year'], int):
                from datetime import date
                education_history_data['start_year'] = date(year=education_history_data['start_year'], month=1, day=1)
                
            if 'end_year' in education_history_data and isinstance(education_history_data['end_year'], int):
                from datetime import date
                education_history_data['end_year'] = date(year=education_history_data['end_year'], month=1, day=1)
            
            # If education_history_id is not provided, generate it
            if 'education_history_id' not in education_history_data or not education_history_data['education_history_id']:
                from app.services.id_service import generate_model_id
                education_history_data['education_history_id'] = generate_model_id("EducationHistory")
                self.logger.info(f"Generated new education history ID: {education_history_data['education_history_id']}")
                
            education_history = EducationHistory(**education_history_data)
            self.db_session.add(education_history)
            await self.db_session.commit()
            await self.db_session.refresh(education_history)
            
            # Get the education history with related entities
            return await self.get_by_id(education_history.education_history_id)
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error creating education history: {e}")
            raise
    
    async def update(
        self, 
        education_history_id: str, 
        education_history_data: Dict[str, Any]
    ) -> Optional[EducationHistory]:
        """
        Update an existing education history entry
        
        Args:
            education_history_id: ID of the education history entry to update
            education_history_data: Dictionary containing updated data
            
        Returns:
            Updated education history object if found, None otherwise
        """
        try:
            # First check if the education history exists
            education_history_check = await self.get_by_id(education_history_id)
            if not education_history_check:
                return None
            
            # Convert integer years to date objects
            if 'start_year' in education_history_data and isinstance(education_history_data['start_year'], int):
                from datetime import date
                education_history_data['start_year'] = date(year=education_history_data['start_year'], month=1, day=1)
                
            if 'end_year' in education_history_data and isinstance(education_history_data['end_year'], int):
                from datetime import date
                education_history_data['end_year'] = date(year=education_history_data['end_year'], month=1, day=1)
            
            # Update the education history
            query = update(EducationHistory).where(
                EducationHistory.education_history_id == education_history_id
            ).values(**education_history_data)
            
            await self.db_session.execute(query)
            await self.db_session.commit()
            
            # Retrieve updated education history with related data
            return await self.get_by_id(education_history_id)
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error updating education history {education_history_id}: {e}")
            raise
    
    async def delete(self, education_history_id: str) -> bool:
        """
        Delete an education history entry by ID
        
        Args:
            education_history_id: ID of the education history entry to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            # Check if the education history exists
            education_history_check = await self.get_by_id(education_history_id)
            if not education_history_check:
                return False
            
            query = delete(EducationHistory).where(EducationHistory.education_history_id == education_history_id)
            result = await self.db_session.execute(query)
            await self.db_session.commit()
            
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error deleting education history {education_history_id}: {e}")
            raise 