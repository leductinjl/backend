"""
Degree repository module.

This module provides database access methods for the Degree model, including
CRUD operations and queries for retrieving degrees with filtering options.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload, selectinload
from app.domain.models.degree import Degree
from app.domain.models.major import Major
from app.domain.models.candidate import Candidate
from app.domain.models.education_history import EducationHistory
from app.domain.models.education_level import EducationLevel
from typing import List, Optional, Dict, Any, Tuple
import logging

class DegreeRepository:
    """
    Repository for interacting with the Degree table in PostgreSQL
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Dict[str, Any] = None
    ) -> Tuple[List[Degree], int]:
        """
        Get a list of degrees with pagination and optional filtering
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional filters to apply (e.g., major_id, start_year, end_year)
            
        Returns:
            Tuple containing list of degrees and total count
        """
        try:
            # Start with base Degree query with Major join
            query = select(Degree).join(Major, Degree.major_id == Major.major_id)
            
            # Apply filters if provided
            if filters:
                conditions = []
                if 'major_id' in filters and filters['major_id']:
                    conditions.append(Degree.major_id == filters['major_id'])
                
                if 'start_year' in filters and filters['start_year']:
                    # Convert integer year to date for filtering
                    from datetime import date
                    start_date = date(year=int(filters['start_year']), month=1, day=1)
                    conditions.append(Degree.start_year >= start_date)
                    
                if 'end_year' in filters and filters['end_year']:
                    # Convert integer year to date for filtering
                    from datetime import date
                    end_date = date(year=int(filters['end_year']), month=12, day=31)
                    conditions.append(Degree.end_year <= end_date)
                
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Execute base query to get degrees with major information
            # This avoids cartesian product issues
            query = query.options(joinedload(Degree.major))
            query = query.offset(skip).limit(limit)
            
            result = await self.db_session.execute(query)
            degrees = list(result.scalars().unique().all())
            
            # Count total records independently
            count_query = select(func.count()).select_from(select(Degree.degree_id).distinct())
            total_count = await self.db_session.scalar(count_query)
            
            # For each degree, find a matching candidate (if any)
            # This way we avoid the cartesian product problem
            for degree in degrees:
                # Find a candidate who has education history with matching major
                candidate_query = (
                    select(Candidate)
                    .join(EducationHistory, Candidate.candidate_id == EducationHistory.candidate_id)
                    .join(EducationLevel, EducationHistory.education_level_id == EducationLevel.education_level_id)
                    .where(
                        and_(
                            EducationLevel.code.in_(['UNIVERSITY', 'POSTGRADUATE']),
                            # Find a logical connection between degree and education history
                            # For example, matching by major and years
                            (EducationHistory.start_year <= degree.start_year) if degree.start_year else True,
                            (EducationHistory.end_year >= degree.end_year) if degree.end_year else True
                        )
                    )
                    .limit(1)  # Just get one candidate for this degree
                )
                
                candidate_result = await self.db_session.execute(candidate_query)
                candidate = candidate_result.scalars().first()
                
                if candidate:
                    # Attach the candidate to the degree
                    from types import SimpleNamespace
                    degree.candidate = SimpleNamespace(
                        candidate_id=candidate.candidate_id,
                        full_name=candidate.full_name
                    )
            
            return degrees, total_count
        except Exception as e:
            self.logger.error(f"Error getting all degrees: {e}")
            raise
    
    async def get_by_id(self, degree_id: str) -> Optional[Degree]:
        """
        Get a degree by its ID, including related major information
        
        Args:
            degree_id: ID of the degree to retrieve
            
        Returns:
            Degree object if found, None otherwise
        """
        try:
            query = select(Degree).options(
                joinedload(Degree.major)
            ).where(Degree.degree_id == degree_id)
            
            result = await self.db_session.execute(query)
            return result.scalars().first()
        except Exception as e:
            self.logger.error(f"Error getting degree by ID {degree_id}: {e}")
            raise
    
    async def get_by_major(self, major_id: str, skip: int = 0, limit: int = 100) -> List[Degree]:
        """
        Get all degrees for a specific major
        
        Args:
            major_id: ID of the major
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of degrees for the specified major
        """
        try:
            query = select(Degree).options(
                joinedload(Degree.major)
            ).where(
                Degree.major_id == major_id
            ).offset(skip).limit(limit)
            
            result = await self.db_session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Error getting degrees for major {major_id}: {e}")
            raise
    
    async def create(self, degree_data: Dict[str, Any]) -> Degree:
        """
        Create a new degree
        
        Args:
            degree_data: Dictionary containing degree data
            
        Returns:
            Created degree object
        """
        try:
            # Convert integer years to date objects
            if 'start_year' in degree_data and isinstance(degree_data['start_year'], int):
                from datetime import date
                degree_data['start_year'] = date(year=degree_data['start_year'], month=1, day=1)
                
            if 'end_year' in degree_data and isinstance(degree_data['end_year'], int):
                from datetime import date
                degree_data['end_year'] = date(year=degree_data['end_year'], month=1, day=1)
            
            # Ensure degree_id is provided or generate one
            if 'degree_id' not in degree_data or not degree_data['degree_id']:
                from app.services.id_service import generate_model_id
                degree_data['degree_id'] = generate_model_id("Degree")
                self.logger.info(f"Generated new degree ID: {degree_data['degree_id']}")
                
            degree = Degree(**degree_data)
            self.db_session.add(degree)
            await self.db_session.commit()
            await self.db_session.refresh(degree)
            
            # Get the degree with related major
            return await self.get_by_id(degree.degree_id)
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error creating degree: {e}")
            raise
    
    async def update(self, degree_id: str, degree_data: Dict[str, Any]) -> Optional[Degree]:
        """
        Update an existing degree
        
        Args:
            degree_id: ID of the degree to update
            degree_data: Dictionary containing updated data
            
        Returns:
            Updated degree object if found, None otherwise
        """
        try:
            # First check if the degree exists
            degree_check = await self.get_by_id(degree_id)
            if not degree_check:
                return None
            
            # Convert integer years to date objects
            if 'start_year' in degree_data and isinstance(degree_data['start_year'], int):
                from datetime import date
                degree_data['start_year'] = date(year=degree_data['start_year'], month=1, day=1)
                
            if 'end_year' in degree_data and isinstance(degree_data['end_year'], int):
                from datetime import date
                degree_data['end_year'] = date(year=degree_data['end_year'], month=1, day=1)
            
            # Update the degree
            query = update(Degree).where(
                Degree.degree_id == degree_id
            ).values(**degree_data)
            
            await self.db_session.execute(query)
            await self.db_session.commit()
            
            # Retrieve updated degree with related data
            return await self.get_by_id(degree_id)
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error updating degree {degree_id}: {e}")
            raise
    
    async def delete(self, degree_id: str) -> bool:
        """
        Delete a degree by ID
        
        Args:
            degree_id: ID of the degree to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            # Check if the degree exists
            degree_check = await self.get_by_id(degree_id)
            if not degree_check:
                return False
            
            query = delete(Degree).where(Degree.degree_id == degree_id)
            result = await self.db_session.execute(query)
            await self.db_session.commit()
            
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error deleting degree {degree_id}: {e}")
            raise 