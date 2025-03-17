"""
Achievement repository module.

This module provides database access methods for the Achievement model,
including CRUD operations and queries for retrieving achievements
with filtering options.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload
from typing import Optional, List, Dict, Any, Tuple
from app.domain.models.achievement import Achievement
from app.domain.models.candidate_exam import CandidateExam
from datetime import date
import logging
from app.services.id_service import generate_model_id

class AchievementRepository:
    """Repository for Achievement database operations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize Achievement Repository
        
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
    ) -> Tuple[List[Achievement], int]:
        """
        Get all achievements with pagination and optional filtering
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Dictionary of filter conditions
                - candidate_exam_id: Filter by candidate exam ID
                - achievement_type: Filter by achievement type
                - organization: Filter by organization
                - education_level: Filter by education level
                - achievement_date_from: Filter by minimum achievement date
                - achievement_date_to: Filter by maximum achievement date
                
        Returns:
            Tuple of (list of Achievement objects, total count)
        """
        try:
            # Build query
            query = select(Achievement).options(
                joinedload(Achievement.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Achievement.candidate_exam)
                .joinedload(CandidateExam.exam)
            )
            
            # Apply filters
            if filters:
                conditions = []
                
                if 'candidate_exam_id' in filters:
                    conditions.append(Achievement.candidate_exam_id == filters['candidate_exam_id'])
                
                if 'achievement_type' in filters:
                    conditions.append(Achievement.achievement_type == filters['achievement_type'])
                
                if 'organization' in filters:
                    conditions.append(Achievement.organization == filters['organization'])
                
                if 'education_level' in filters:
                    conditions.append(Achievement.education_level == filters['education_level'])
                
                if 'achievement_date_from' in filters:
                    conditions.append(Achievement.achievement_date >= filters['achievement_date_from'])
                
                if 'achievement_date_to' in filters:
                    conditions.append(Achievement.achievement_date <= filters['achievement_date_to'])
                
                if 'search' in filters and filters['search']:
                    search_term = f"%{filters['search']}%"
                    conditions.append(Achievement.achievement_name.ilike(search_term))
                
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Achievement.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            achievements = result.scalars().unique().all()
            
            return achievements, total
        
        except Exception as e:
            self.logger.error(f"Error in get_all: {e}")
            raise
    
    async def get_by_id(self, achievement_id: str) -> Optional[Achievement]:
        """
        Get an achievement by ID
        
        Args:
            achievement_id: ID of the achievement to retrieve
            
        Returns:
            Achievement object or None if not found
        """
        try:
            query = select(Achievement).where(
                Achievement.achievement_id == achievement_id
            ).options(
                joinedload(Achievement.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Achievement.candidate_exam)
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
    ) -> Tuple[List[Achievement], int]:
        """
        Get achievements for a specific candidate exam
        
        Args:
            candidate_exam_id: ID of the candidate exam
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of Achievement objects, total count)
        """
        try:
            # Build query
            query = select(Achievement).where(
                Achievement.candidate_exam_id == candidate_exam_id
            ).options(
                joinedload(Achievement.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Achievement.candidate_exam)
                .joinedload(CandidateExam.exam)
            )
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Achievement.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            achievements = result.scalars().unique().all()
            
            return achievements, total
        
        except Exception as e:
            self.logger.error(f"Error in get_by_candidate_exam: {e}")
            raise
    
    async def get_by_achievement_type(
        self,
        achievement_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Achievement], int]:
        """
        Get achievements of a specific type
        
        Args:
            achievement_type: Type of the achievement (Research, Community Service, etc.)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of Achievement objects, total count)
        """
        try:
            # Build query
            query = select(Achievement).where(
                Achievement.achievement_type == achievement_type
            ).options(
                joinedload(Achievement.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Achievement.candidate_exam)
                .joinedload(CandidateExam.exam)
            )
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Achievement.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            achievements = result.scalars().unique().all()
            
            return achievements, total
        
        except Exception as e:
            self.logger.error(f"Error in get_by_achievement_type: {e}")
            raise
    
    async def get_by_organization(
        self,
        organization: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Achievement], int]:
        """
        Get achievements recognized by a specific organization
        
        Args:
            organization: Name of the organization
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of Achievement objects, total count)
        """
        try:
            # Build query
            query = select(Achievement).where(
                Achievement.organization == organization
            ).options(
                joinedload(Achievement.candidate_exam)
                .joinedload(CandidateExam.candidate),
                joinedload(Achievement.candidate_exam)
                .joinedload(CandidateExam.exam)
            )
            
            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(Achievement.created_at.desc())
            
            # Execute query
            result = await self.db.execute(query)
            achievements = result.scalars().unique().all()
            
            return achievements, total
        
        except Exception as e:
            self.logger.error(f"Error in get_by_organization: {e}")
            raise
    
    async def create(self, achievement_data: Dict[str, Any]) -> Achievement:
        """
        Create a new achievement
        
        Args:
            achievement_data: Dictionary containing achievement data
            
        Returns:
            Created Achievement object
        """
        try:
            # Ensure achievement_id is set
            if 'achievement_id' not in achievement_data or not achievement_data['achievement_id']:
                achievement_data['achievement_id'] = generate_model_id("Achievement")
                self.logger.info(f"Generated new achievement ID: {achievement_data['achievement_id']}")
            
            self.logger.debug(f"Creating achievement with ID: {achievement_data['achievement_id']}")
            achievement = Achievement(**achievement_data)
            self.db.add(achievement)
            await self.db.flush()
            await self.db.refresh(achievement)
            self.logger.info(f"Successfully created achievement: {achievement.achievement_id}")
            
            # Return the fully loaded achievement with relationships
            return await self.get_by_id(achievement.achievement_id)
        
        except Exception as e:
            self.logger.error(f"Error in create: {e}")
            raise
    
    async def update(
        self, 
        achievement_id: str, 
        achievement_data: Dict[str, Any]
    ) -> Optional[Achievement]:
        """
        Update an existing achievement
        
        Args:
            achievement_id: ID of the achievement to update
            achievement_data: Dictionary containing updated data
            
        Returns:
            Updated Achievement object or None if not found
        """
        try:
            # Check if achievement exists
            query = select(Achievement).where(Achievement.achievement_id == achievement_id)
            result = await self.db.execute(query)
            achievement = result.scalars().first()
            
            if not achievement:
                return None
            
            # Update achievement
            query = update(Achievement).where(
                Achievement.achievement_id == achievement_id
            ).values(**achievement_data).returning(Achievement)
            
            result = await self.db.execute(query)
            await self.db.flush()
            
            # Get updated achievement
            updated_achievement = await self.get_by_id(achievement_id)
            return updated_achievement
        
        except Exception as e:
            self.logger.error(f"Error in update: {e}")
            raise
    
    async def delete(self, achievement_id: str) -> bool:
        """
        Delete an achievement
        
        Args:
            achievement_id: ID of the achievement to delete
            
        Returns:
            Boolean indicating if the achievement was deleted
        """
        try:
            # Check if achievement exists
            query = select(Achievement).where(Achievement.achievement_id == achievement_id)
            result = await self.db.execute(query)
            achievement = result.scalars().first()
            
            if not achievement:
                return False
            
            # Delete achievement
            query = delete(Achievement).where(Achievement.achievement_id == achievement_id)
            await self.db.execute(query)
            await self.db.flush()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error in delete: {e}")
            raise 