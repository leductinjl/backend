from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from app.domain.models.candidate import Candidate
from app.domain.models.personal_info import PersonalInfo
from typing import List, Optional, Dict, Any
import logging
from app.services.id_service import generate_model_id

class CandidateRepository:
    """
    Repository để thao tác với bảng Candidate trong PostgreSQL
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Candidate]:
        """Lấy danh sách thí sinh với phân trang"""
        try:
            query = select(Candidate).offset(skip).limit(limit)
            result = await self.db_session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Error getting all candidates: {e}")
            raise
    
    async def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Lấy thông tin thí sinh theo ID"""
        try:
            query = select(Candidate).where(Candidate.candidate_id == candidate_id)
            result = await self.db_session.execute(query)
            return result.scalars().first()
        except Exception as e:
            self.logger.error(f"Error getting candidate by ID {candidate_id}: {e}")
            raise
    
    async def get_by_id_with_personal_info(self, candidate_id: str) -> Optional[Candidate]:
        """Lấy thông tin thí sinh kèm thông tin cá nhân"""
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
        """Tạo thí sinh mới"""
        try:
            candidate = Candidate(**candidate_data)
            self.db_session.add(candidate)
            await self.db_session.commit()
            await self.db_session.refresh(candidate)
            return candidate
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error creating candidate: {e}")
            raise
    
    async def update(self, candidate_id: str, candidate_data: Dict[str, Any]) -> Optional[Candidate]:
        """Cập nhật thông tin thí sinh"""
        try:
            query = update(Candidate).where(Candidate.candidate_id == candidate_id).values(**candidate_data)
            await self.db_session.execute(query)
            await self.db_session.commit()
            
            # Fetch updated candidate
            return await self.get_by_id(candidate_id)
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error updating candidate {candidate_id}: {e}")
            raise
    
    async def delete(self, candidate_id: str) -> bool:
        """Xóa thí sinh"""
        try:
            query = delete(Candidate).where(Candidate.candidate_id == candidate_id)
            result = await self.db_session.execute(query)
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Error deleting candidate {candidate_id}: {e}")
            raise
    
    async def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Candidate]:
        """Tìm kiếm thí sinh theo tên"""
        try:
            query = select(Candidate).where(
                Candidate.full_name.ilike(f"%{search_term}%")
            ).offset(skip).limit(limit)
            result = await self.db_session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Error searching candidates with term '{search_term}': {e}")
            raise

async def get_candidates(db: AsyncSession, skip: int = 0, limit: int = 100):
    """
    Get a list of candidates with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        list: List of Candidate objects
    """
    result = await db.execute(
        select(Candidate).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def get_candidate_by_id(db: AsyncSession, candidate_id: str):
    """
    Get a candidate by ID.
    
    Args:
        db: Database session
        candidate_id: Candidate ID to find
        
    Returns:
        Candidate: The found candidate or None
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id)
    )
    return result.scalars().first()

async def create_candidate(db: AsyncSession, full_name: str, candidate_id: str = None):
    """
    Create a new candidate.
    
    Args:
        db: Database session
        full_name: Full name of the candidate
        candidate_id: Optional ID for the candidate. If not provided, one will be generated.
        
    Returns:
        Candidate: The created candidate
    """
    # Generate ID if not provided
    if not candidate_id:
        candidate_id = generate_model_id("Candidate")
    
    # Create the candidate
    db_candidate = Candidate(
        candidate_id=candidate_id,
        full_name=full_name
    )
    
    db.add(db_candidate)
    await db.commit()
    await db.refresh(db_candidate)
    
    logger.info(f"Created candidate with ID: {candidate_id}")
    return db_candidate

async def update_candidate(db: AsyncSession, candidate_id: str, update_data: dict):
    """
    Update a candidate's information.
    
    Args:
        db: Database session
        candidate_id: Candidate ID to update
        update_data: Dictionary of fields to update
        
    Returns:
        Candidate: The updated candidate or None if not found
    """
    # First check if candidate exists
    db_candidate = await get_candidate_by_id(db, candidate_id)
    if not db_candidate:
        return None
    
    # Update the candidate
    await db.execute(
        update(Candidate)
        .where(Candidate.candidate_id == candidate_id)
        .values(**update_data)
    )
    
    await db.commit()
    await db.refresh(db_candidate)
    
    logger.info(f"Updated candidate with ID: {candidate_id}")
    return db_candidate

async def delete_candidate(db: AsyncSession, candidate_id: str):
    """
    Delete a candidate.
    
    Args:
        db: Database session
        candidate_id: Candidate ID to delete
        
    Returns:
        bool: True if candidate was deleted, False if not found
    """
    # First check if candidate exists
    db_candidate = await get_candidate_by_id(db, candidate_id)
    if not db_candidate:
        return False
    
    # Delete the candidate
    await db.execute(
        delete(Candidate)
        .where(Candidate.candidate_id == candidate_id)
    )
    
    await db.commit()
    
    logger.info(f"Deleted candidate with ID: {candidate_id}")
    return True

async def create_candidate_with_personal_info(
    db: AsyncSession, 
    full_name: str, 
    personal_info: dict
):
    """
    Create a new candidate with personal information.
    
    Args:
        db: Database session
        full_name: Full name of the candidate
        personal_info: Dictionary of personal information fields
        
    Returns:
        Candidate: The created candidate with personal info
    """
    # Generate ID for candidate
    candidate_id = generate_model_id("Candidate")
    
    # Create the candidate
    db_candidate = Candidate(
        candidate_id=candidate_id,
        full_name=full_name
    )
    
    db.add(db_candidate)
    
    # Create personal info
    db_personal_info = PersonalInfo(
        candidate_id=candidate_id,
        **personal_info
    )
    
    db.add(db_personal_info)
    
    # Commit both entities in a single transaction
    await db.commit()
    await db.refresh(db_candidate)
    
    logger.info(f"Created candidate with ID: {candidate_id} and personal info")
    return db_candidate 