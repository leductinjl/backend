"""
Candidate Exam repository module.

This module provides database operations for candidate exam registrations,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, join, and_, or_
from sqlalchemy.sql import expression

from app.domain.models.candidate_exam import CandidateExam
from app.domain.models.candidate import Candidate
from app.domain.models.exam import Exam
from app.domain.models.exam_location import ExamLocation
from app.domain.models.exam_room import ExamRoom

logger = logging.getLogger(__name__)

class CandidateExamRepository:
    """Repository for managing CandidateExam entities in the database."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            db: An async SQLAlchemy session
        """
        self.db = db
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all candidate exam registrations with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of candidate exam registrations with details and total count
        """
        # Join query to get candidate and exam names
        query = (
            select(
                CandidateExam,
                Candidate.full_name.label("candidate_name"),
                Exam.exam_name
            )
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
        )
        
        # Apply filters if any
        if filters:
            filter_conditions = []
            
            for field, value in filters.items():
                if field == "search" and value:
                    # Search in candidate name or exam name
                    search_term = f"%{value}%"
                    filter_conditions.append(
                        or_(
                            Candidate.full_name.ilike(search_term),
                            Exam.exam_name.ilike(search_term)
                        )
                    )
                elif hasattr(CandidateExam, field) and value is not None:
                    if isinstance(value, list):
                        filter_conditions.append(getattr(CandidateExam, field).in_(value))
                    else:
                        filter_conditions.append(getattr(CandidateExam, field) == value)
            
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include related entity names
        registrations = []
        for reg, candidate_name, exam_name in result:
            reg_dict = {
                "candidate_exam_id": reg.candidate_exam_id,
                "candidate_id": reg.candidate_id,
                "exam_id": reg.exam_id,
                "registration_number": reg.registration_number,
                "registration_date": reg.registration_date,
                "status": reg.status,
                "attempt_number": reg.attempt_number,
                "created_at": reg.created_at,
                "updated_at": reg.updated_at,
                "candidate_name": candidate_name,
                "exam_name": exam_name
            }
            registrations.append(reg_dict)
        
        return registrations, total or 0
    
    async def get_by_id(self, candidate_exam_id: str) -> Optional[Dict]:
        """
        Get a candidate exam registration by its ID, including related entity names.
        
        Args:
            candidate_exam_id: The unique identifier of the candidate exam registration
            
        Returns:
            The candidate exam registration with related entity names if found, None otherwise
        """
        query = (
            select(
                CandidateExam,
                Candidate.full_name.label("candidate_name"),
                Exam.exam_name
            )
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
            .filter(CandidateExam.candidate_exam_id == candidate_exam_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        reg, candidate_name, exam_name = row
        return {
            "candidate_exam_id": reg.candidate_exam_id,
            "candidate_id": reg.candidate_id,
            "exam_id": reg.exam_id,
            "registration_number": reg.registration_number,
            "registration_date": reg.registration_date,
            "status": reg.status,
            "attempt_number": reg.attempt_number,
            "created_at": reg.created_at,
            "updated_at": reg.updated_at,
            "candidate_name": candidate_name,
            "exam_name": exam_name
        }
    
    async def get_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all exam registrations for a specific candidate.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of exam registrations for the specified candidate
        """
        query = (
            select(
                CandidateExam,
                Exam.exam_name
            )
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
            .filter(CandidateExam.candidate_id == candidate_id)
        )
        
        result = await self.db.execute(query)
        
        registrations = []
        for reg, exam_name in result:
            reg_dict = {
                "candidate_exam_id": reg.candidate_exam_id,
                "candidate_id": reg.candidate_id,
                "exam_id": reg.exam_id,
                "registration_number": reg.registration_number,
                "registration_date": reg.registration_date,
                "status": reg.status,
                "attempt_number": reg.attempt_number,
                "created_at": reg.created_at,
                "updated_at": reg.updated_at,
                "exam_name": exam_name
            }
            registrations.append(reg_dict)
        
        return registrations
    
    async def get_by_exam_id(self, exam_id: str) -> List[Dict]:
        """
        Get all candidate registrations for a specific exam.
        
        Args:
            exam_id: The ID of the exam
            
        Returns:
            List of candidate registrations for the specified exam
        """
        query = (
            select(
                CandidateExam,
                Candidate.full_name.label("candidate_name")
            )
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .filter(CandidateExam.exam_id == exam_id)
        )
        
        result = await self.db.execute(query)
        
        registrations = []
        for reg, candidate_name in result:
            reg_dict = {
                "candidate_exam_id": reg.candidate_exam_id,
                "candidate_id": reg.candidate_id,
                "exam_id": reg.exam_id,
                "registration_number": reg.registration_number,
                "registration_date": reg.registration_date,
                "status": reg.status,
                "attempt_number": reg.attempt_number,
                "created_at": reg.created_at,
                "updated_at": reg.updated_at,
                "candidate_name": candidate_name
            }
            registrations.append(reg_dict)
        
        return registrations
    
    async def get_by_candidate_and_exam(self, candidate_id: str, exam_id: str) -> Optional[CandidateExam]:
        """
        Get a candidate exam registration by candidate ID and exam ID.
        
        Args:
            candidate_id: The ID of the candidate
            exam_id: The ID of the exam
            
        Returns:
            The candidate exam registration if found, None otherwise
        """
        query = select(CandidateExam).filter(
            CandidateExam.candidate_id == candidate_id,
            CandidateExam.exam_id == exam_id
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_location_id(self, location_id: str) -> List[Dict]:
        """
        Get all candidate registrations for a specific exam location.
        
        Args:
            location_id: The ID of the exam location
            
        Returns:
            List of candidate registrations for the specified location
        """
        query = (
            select(
                CandidateExam,
                Candidate.full_name.label("candidate_name"),
                Candidate.candidate_code,
                Exam.exam_name,
                Exam.exam_date,
                ExamRoom.room_name
            )
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
            .outerjoin(ExamRoom, CandidateExam.exam_room_id == ExamRoom.room_id)
            .filter(CandidateExam.exam_location_id == location_id)
        )
        
        result = await self.db.execute(query)
        
        registrations = []
        for reg, candidate_name, candidate_code, exam_name, exam_date, room_name in result:
            reg_dict = {
                "candidate_exam_id": reg.candidate_exam_id,
                "candidate_id": reg.candidate_id,
                "exam_id": reg.exam_id,
                "registration_date": reg.registration_date,
                "status": reg.status,
                "payment_status": reg.payment_status,
                "payment_amount": reg.payment_amount,
                "exam_location_id": reg.exam_location_id,
                "exam_room_id": reg.exam_room_id,
                "attendance": reg.attendance,
                "attendance_time": reg.attendance_time,
                "notes": reg.notes,
                "metadata": reg.metadata,
                "created_at": reg.created_at,
                "updated_at": reg.updated_at,
                "candidate_name": candidate_name,
                "candidate_code": candidate_code,
                "exam_name": exam_name,
                "exam_date": exam_date,
                "room_name": room_name
            }
            registrations.append(reg_dict)
        
        return registrations
    
    async def get_by_room_id(self, room_id: str) -> List[Dict]:
        """
        Get all candidate registrations for a specific exam room.
        
        Args:
            room_id: The ID of the exam room
            
        Returns:
            List of candidate registrations for the specified room
        """
        query = (
            select(
                CandidateExam,
                Candidate.full_name.label("candidate_name"),
                Candidate.candidate_code,
                Exam.exam_name,
                Exam.exam_date,
                ExamLocation.location_name
            )
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
            .outerjoin(ExamLocation, CandidateExam.exam_location_id == ExamLocation.location_id)
            .filter(CandidateExam.exam_room_id == room_id)
        )
        
        result = await self.db.execute(query)
        
        registrations = []
        for reg, candidate_name, candidate_code, exam_name, exam_date, location_name in result:
            reg_dict = {
                "candidate_exam_id": reg.candidate_exam_id,
                "candidate_id": reg.candidate_id,
                "exam_id": reg.exam_id,
                "registration_date": reg.registration_date,
                "status": reg.status,
                "payment_status": reg.payment_status,
                "payment_amount": reg.payment_amount,
                "exam_location_id": reg.exam_location_id,
                "exam_room_id": reg.exam_room_id,
                "attendance": reg.attendance,
                "attendance_time": reg.attendance_time,
                "notes": reg.notes,
                "metadata": reg.metadata,
                "created_at": reg.created_at,
                "updated_at": reg.updated_at,
                "candidate_name": candidate_name,
                "candidate_code": candidate_code,
                "exam_name": exam_name,
                "exam_date": exam_date,
                "location_name": location_name
            }
            registrations.append(reg_dict)
        
        return registrations
    
    async def create(self, candidate_exam_data: Dict[str, Any]) -> CandidateExam:
        """
        Create a new candidate exam registration.
        
        Args:
            candidate_exam_data: Dictionary containing the candidate exam data
            
        Returns:
            The created candidate exam registration
        """
        # Auto-generate registration_number if not provided
        if 'registration_number' not in candidate_exam_data or not candidate_exam_data['registration_number']:
            # Get exam code (first 4 chars of exam_id)
            exam_id = candidate_exam_data['exam_id']
            exam_code = exam_id.split('_')[1][:4] if '_' in exam_id else exam_id[:4]
            
            # Get candidate ID suffix (last 5 chars)
            candidate_id = candidate_exam_data['candidate_id']
            candidate_suffix = candidate_id[-5:] if len(candidate_id) >= 5 else candidate_id.zfill(5)
            
            # Count existing registrations for this exam to generate sequence
            query = select(func.count()).select_from(CandidateExam).filter(
                CandidateExam.exam_id == candidate_exam_data['exam_id']
            )
            count = await self.db.scalar(query) or 0
            sequence = str(count + 1).zfill(3)
            
            # Format: EXAM_CODE + CANDIDATE_SUFFIX + SEQUENCE
            candidate_exam_data['registration_number'] = f"{exam_code}{candidate_suffix}{sequence}"
            logger.info(f"Generated registration number: {candidate_exam_data['registration_number']}")
        
        # Create a new candidate exam registration
        new_registration = CandidateExam(**candidate_exam_data)
        
        # Add to session and commit
        self.db.add(new_registration)
        await self.db.commit()
        await self.db.refresh(new_registration)
        
        logger.info(f"Created candidate exam registration with ID: {new_registration.candidate_exam_id}")
        return new_registration
    
    async def update(self, candidate_exam_id: str, candidate_exam_data: Dict[str, Any]) -> Optional[CandidateExam]:
        """
        Update a candidate exam registration.
        
        Args:
            candidate_exam_id: The unique identifier of the candidate exam registration
            candidate_exam_data: Dictionary containing the updated data
            
        Returns:
            The updated candidate exam registration if found, None otherwise
        """
        # Get the raw CandidateExam object first
        query = select(CandidateExam).filter(CandidateExam.candidate_exam_id == candidate_exam_id)
        result = await self.db.execute(query)
        existing_registration = result.scalar_one_or_none()
        
        if not existing_registration:
            return None
        
        # Update the candidate exam registration
        update_stmt = (
            update(CandidateExam)
            .where(CandidateExam.candidate_exam_id == candidate_exam_id)
            .values(**candidate_exam_data)
            .returning(CandidateExam)
        )
        result = await self.db.execute(update_stmt)
        await self.db.commit()
        
        updated_registration = result.scalar_one_or_none()
        if updated_registration:
            logger.info(f"Updated candidate exam registration with ID: {candidate_exam_id}")
        
        return updated_registration
    
    async def delete(self, candidate_exam_id: str) -> bool:
        """
        Delete a candidate exam registration.
        
        Args:
            candidate_exam_id: The unique identifier of the candidate exam registration
            
        Returns:
            True if the candidate exam registration was deleted, False otherwise
        """
        # Check if the candidate exam registration exists
        query = select(CandidateExam).filter(CandidateExam.candidate_exam_id == candidate_exam_id)
        result = await self.db.execute(query)
        existing_registration = result.scalar_one_or_none()
        
        if not existing_registration:
            return False
        
        # Delete the candidate exam registration
        delete_stmt = delete(CandidateExam).where(CandidateExam.candidate_exam_id == candidate_exam_id)
        await self.db.execute(delete_stmt)
        await self.db.commit()
        
        logger.info(f"Deleted candidate exam registration with ID: {candidate_exam_id}")
        return True
    
    async def get_all_raw(self) -> List[CandidateExam]:
        """
        Get all candidate exam registrations as raw CandidateExam objects without formatting.
        
        Returns:
            List of raw CandidateExam instances
        """
        query = select(CandidateExam)
        result = await self.db.execute(query)
        return result.scalars().all() 