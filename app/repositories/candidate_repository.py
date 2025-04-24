from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import joinedload
from app.domain.models.candidate import Candidate
from app.domain.models.personal_info import PersonalInfo
from typing import List, Optional, Dict, Any
import logging
from app.services.id_service import generate_model_id
from sqlalchemy.future import select

class CandidateRepository:
    """
    Repository for interacting with the Candidate table in PostgreSQL
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
    
    async def get_all(self, skip: int = 0, limit: int = 100, include_personal_info: bool = False) -> List[Candidate]:
        """
        Get list of candidates with pagination and optional personal info
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_personal_info: Whether to include personal info in the query
            
        Returns:
            List of candidates
        """
        try:
            # Build base query
            query = select(Candidate)
            
            # Add personal info if requested
            if include_personal_info:
                query = query.options(joinedload(Candidate.personal_info))
            
            # Add pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db_session.execute(query)
            candidates = list(result.scalars().unique().all())
            
            self.logger.info(f"Retrieved {len(candidates)} candidates from database")
            return candidates
            
        except Exception as e:
            self.logger.error(f"Error getting all candidates: {e}")
            raise
    
    async def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Get candidate information by ID"""
        try:
            query = select(Candidate).where(Candidate.candidate_id == candidate_id)
            result = await self.db_session.execute(query)
            return result.scalars().first()
        except Exception as e:
            self.logger.error(f"Error getting candidate by ID {candidate_id}: {e}")
            raise
    
    async def get_by_id_with_personal_info(self, candidate_id: str) -> Optional[Candidate]:
        """Get candidate information with personal information"""
        try:
            query = select(Candidate).options(
                joinedload(Candidate.personal_info)
            ).where(Candidate.candidate_id == candidate_id)
            result = await self.db_session.execute(query)
            return result.scalars().first()
        except Exception as e:
            self.logger.error(f"Error getting candidate with personal info by ID {candidate_id}: {e}")
            raise
    
    async def create(self, candidate_data: Dict[str, Any]) -> Candidate:
        """
        Create a new candidate
        
        Args:
            candidate_data: Data to create the candidate
            
        Returns:
            Created candidate with personal information
        """
        try:
            # Convert candidate_data to dict if it's a Pydantic model
            if hasattr(candidate_data, 'dict'):
                candidate_data = candidate_data.dict(exclude_unset=True)
            
            # Handle personal_info separately
            personal_info = candidate_data.pop('personal_info', None)
            
            # Generate candidate_id if not provided
            if 'candidate_id' not in candidate_data:
                candidate_data['candidate_id'] = generate_model_id("Candidate")
            
            # Create candidate
            candidate = Candidate(**candidate_data)
            self.db_session.add(candidate)
            
            # Create personal_info if provided
            if personal_info:
                personal_info['candidate_id'] = candidate.candidate_id
                personal_info_obj = PersonalInfo(**personal_info)
                self.db_session.add(personal_info_obj)
            
            await self.db_session.commit()
            await self.db_session.refresh(candidate)
            
            # Get created candidate with personal info
            return await self.get_by_id_with_personal_info(candidate.candidate_id)
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error creating candidate: {e}")
            raise
    
    async def update(self, candidate_id: str, candidate_data: Dict[str, Any]) -> Optional[Candidate]:
        """
        Update a candidate's information
        
        Args:
            candidate_id: ID of the candidate to update
            candidate_data: Data to update
            
        Returns:
            Updated candidate or None if not found
        """
        try:
            # Convert candidate_data to dict if it's a Pydantic model
            if hasattr(candidate_data, 'dict'):
                candidate_data = candidate_data.dict(exclude_unset=True)
            
            # Handle personal_info separately
            personal_info = candidate_data.pop('personal_info', None)
            
            # Update candidate
                query = update(Candidate).where(Candidate.candidate_id == candidate_id).values(**candidate_data)
                await self.db_session.execute(query)
            
            if personal_info:
            # Update personal_info if provided
                personal_info_query = update(PersonalInfo).where(
                        PersonalInfo.candidate_id == candidate_id
                ).values(**personal_info)
                await self.db_session.execute(personal_info_query)
            
            await self.db_session.commit()
            
            # Get updated candidate with personal info
            return await self.get_by_id_with_personal_info(candidate_id)
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error updating candidate {candidate_id}: {e}")
            raise
            
    async def update_personal_info(self, candidate_id: str, personal_info_data: Dict[str, Any]) -> Optional[Candidate]:
        """
        Update only the personal information of a candidate
        
        Args:
            candidate_id: ID of the candidate whose personal info to update
            personal_info_data: Dictionary containing updated personal info data
            
        Returns:
            Updated candidate with personal info or None if candidate not found
        """
        try:
            # First, check if candidate exists
            candidate = await self.get_by_id(candidate_id)
            if not candidate:
                return None
                
            # Check if personal_info already exists
            personal_info_query = select(PersonalInfo).where(PersonalInfo.candidate_id == candidate_id)
            personal_info_result = await self.db_session.execute(personal_info_query)
            personal_info = personal_info_result.scalars().first()
            
            if personal_info:
                # Update existing personal_info
                # Remove None values to avoid overwriting with NULL
                update_data = {k: v for k, v in personal_info_data.items() if v is not None}
                if update_data:
                    personal_info_update = update(PersonalInfo).where(
                        PersonalInfo.candidate_id == candidate_id
                    ).values(**update_data)
                    await self.db_session.execute(personal_info_update)
            else:
                # Create new personal_info if it doesn't exist
                new_personal_info = PersonalInfo(
                    candidate_id=candidate_id,
                    **personal_info_data
                )
                self.db_session.add(new_personal_info)
            
            await self.db_session.commit()
            
            # Fetch updated candidate with personal info
            return await self.get_by_id_with_personal_info(candidate_id)
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error updating personal info for candidate {candidate_id}: {e}")
            raise
    
    async def delete(self, candidate_id: str) -> bool:
        """Delete a candidate"""
        try:
            # Delete personal_info first (if exists)
            personal_info_query = delete(PersonalInfo).where(PersonalInfo.candidate_id == candidate_id)
            await self.db_session.execute(personal_info_query)
            
            # Delete candidate after
            query = delete(Candidate).where(Candidate.candidate_id == candidate_id)
            result = await self.db_session.execute(query)
            
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error deleting candidate {candidate_id}: {e}")
            raise
    
    async def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Candidate]:
        """Search candidates by name"""
        try:
            query = select(Candidate).where(
                Candidate.full_name.ilike(f"%{search_term}%")
            ).offset(skip).limit(limit)
            result = await self.db_session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Error searching candidates with term '{search_term}': {e}")
            raise 
    
    async def get_all_with_personal_info(self, skip: int = 0, limit: int = 100) -> List[Candidate]:
        """
        Get list of candidates with personal information
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of candidates with personal information
        """
        try:
            query = select(Candidate).options(
                joinedload(Candidate.personal_info)
            ).offset(skip).limit(limit)
            
            result = await self.db_session.execute(query)
            candidates = list(result.scalars().unique().all())
            
            self.logger.info(f"Retrieved {len(candidates)} candidates with personal info from database")
            return candidates
            
        except Exception as e:
            self.logger.error(f"Error getting all candidates with personal info: {e}")
            raise
    
    async def count(self) -> int:
        query = select(func.count()).select_from(Candidate)
        result = await self.db_session.execute(query)
        return result.scalar_one() 