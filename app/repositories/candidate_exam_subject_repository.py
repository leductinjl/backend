"""
Candidate Exam Subject repository module.

This module provides database access methods for the CandidateExamSubject model,
including CRUD operations and queries for retrieving candidate exam subjects with various filters.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import logging

from app.domain.models.candidate_exam_subject import CandidateExamSubject
from app.domain.models.candidate_exam import CandidateExam
from app.domain.models.candidate import Candidate
from app.domain.models.exam import Exam
from app.domain.models.exam_subject import ExamSubject
from app.domain.models.subject import Subject
from app.domain.models.exam_schedule import ExamSchedule
from app.domain.models.exam_room import ExamRoom
from app.domain.models.exam_location import ExamLocation
from app.domain.models.exam_score import ExamScore

class CandidateExamSubjectRepository:
    """Repository for interacting with the CandidateExamSubject table."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with a database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def _enrich_candidate_exam_subject_data(self, candidate_exam_subject):
        """
        Enrich candidate exam subject with related data for API response.
        
        Args:
            candidate_exam_subject: CandidateExamSubject object with loaded relationships
            
        Returns:
            CandidateExamSubject with additional attributes for related entities
        """
        if candidate_exam_subject is None:
            return None
            
        # Add candidate info if available
        if candidate_exam_subject.candidate_exam and candidate_exam_subject.candidate_exam.candidate:
            candidate = candidate_exam_subject.candidate_exam.candidate
            candidate_exam_subject.candidate_id = candidate.candidate_id
            candidate_exam_subject.candidate_name = candidate.full_name
        
        # Add exam info if available through candidate_exam
        if candidate_exam_subject.candidate_exam and candidate_exam_subject.candidate_exam.exam:
            exam = candidate_exam_subject.candidate_exam.exam
            candidate_exam_subject.exam_id = exam.exam_id
            candidate_exam_subject.exam_name = exam.exam_name
        # If exam info not available through candidate_exam, try through exam_subject
        elif candidate_exam_subject.exam_subject and candidate_exam_subject.exam_subject.exam:
            exam = candidate_exam_subject.exam_subject.exam
            candidate_exam_subject.exam_id = exam.exam_id
            candidate_exam_subject.exam_name = exam.exam_name
        
        # Add subject info if available
        if candidate_exam_subject.exam_subject and candidate_exam_subject.exam_subject.subject:
            subject = candidate_exam_subject.exam_subject.subject
            candidate_exam_subject.subject_id = subject.subject_id
            candidate_exam_subject.subject_name = subject.subject_name
            
        return candidate_exam_subject
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        candidate_id: Optional[str] = None,
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        candidate_exam_id: Optional[str] = None,
        exam_subject_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[CandidateExamSubject], int]:
        """
        Retrieve candidate exam subjects with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            candidate_id: Filter by candidate ID
            exam_id: Filter by exam ID
            subject_id: Filter by subject ID
            candidate_exam_id: Filter by candidate exam ID
            exam_subject_id: Filter by exam subject ID
            status: Filter by status
            
        Returns:
            Tuple of (list of candidate exam subjects, total count)
        """
        try:
            # Build query with joins for related data
            query = (
                select(CandidateExamSubject)
                .options(
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.candidate),
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.exam),
                    joinedload(CandidateExamSubject.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(CandidateExamSubject.exam_subject)
                    .joinedload(ExamSubject.subject)
                )
            )
            
            # Apply filters
            conditions = []
            
            if candidate_exam_id:
                conditions.append(CandidateExamSubject.candidate_exam_id == candidate_exam_id)
                
            if exam_subject_id:
                conditions.append(CandidateExamSubject.exam_subject_id == exam_subject_id)
                
            if status:
                conditions.append(CandidateExamSubject.status == status)
            
            # Apply joins and conditions for related filters
            if candidate_id or exam_id:
                query = query.join(CandidateExam, CandidateExamSubject.candidate_exam_id == CandidateExam.candidate_exam_id)
                
                if candidate_id:
                    conditions.append(CandidateExam.candidate_id == candidate_id)
                    
                if exam_id:
                    conditions.append(CandidateExam.exam_id == exam_id)
            
            if subject_id:
                query = query.join(ExamSubject, CandidateExamSubject.exam_subject_id == ExamSubject.exam_subject_id)
                conditions.append(ExamSubject.subject_id == subject_id)
            
            # Apply conditions if any
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            candidate_exam_subjects = result.scalars().unique().all()
            
            # Enrich with related data
            enriched_results = [self._enrich_candidate_exam_subject_data(ces) for ces in candidate_exam_subjects]
            
            return enriched_results, total
            
        except Exception as e:
            self.logger.error(f"Error getting candidate exam subjects: {str(e)}")
            raise
    
    async def get_by_id(self, candidate_exam_subject_id: str) -> Optional[CandidateExamSubject]:
        """
        Get a candidate exam subject by ID.
        
        Args:
            candidate_exam_subject_id: ID of the candidate exam subject to retrieve
            
        Returns:
            CandidateExamSubject object or None if not found
        """
        try:
            query = (
                select(CandidateExamSubject)
                .options(
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.candidate),
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.exam),
                    joinedload(CandidateExamSubject.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(CandidateExamSubject.exam_subject)
                    .joinedload(ExamSubject.subject)
                )
                .where(CandidateExamSubject.candidate_exam_subject_id == candidate_exam_subject_id)
            )
            
            result = await self.db.execute(query)
            candidate_exam_subject = result.scalars().first()
            
            # Enrich with related data
            return self._enrich_candidate_exam_subject_data(candidate_exam_subject)
            
        except Exception as e:
            self.logger.error(f"Error getting candidate exam subject with ID {candidate_exam_subject_id}: {str(e)}")
            raise
    
    async def get_by_candidate(
        self, 
        candidate_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[CandidateExamSubject], int]:
        """
        Get all exam subjects registered by a specific candidate.
        
        Args:
            candidate_id: ID of the candidate
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of candidate exam subjects, total count)
        """
        try:
            # Build query with joins
            query = (
                select(CandidateExamSubject)
                .join(CandidateExam, CandidateExamSubject.candidate_exam_id == CandidateExam.candidate_exam_id)
                .options(
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.candidate),
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.exam),
                    joinedload(CandidateExamSubject.exam_subject)
                    .joinedload(ExamSubject.exam),
                    joinedload(CandidateExamSubject.exam_subject)
                    .joinedload(ExamSubject.subject)
                )
                .where(CandidateExam.candidate_id == candidate_id)
            )
            
            # Get total count
            count_query = (
                select(func.count())
                .select_from(
                    select(CandidateExamSubject)
                    .join(CandidateExam, CandidateExamSubject.candidate_exam_id == CandidateExam.candidate_exam_id)
                    .where(CandidateExam.candidate_id == candidate_id)
                    .subquery()
                )
            )
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            candidate_exam_subjects = result.scalars().unique().all()
            
            # Enrich with related data
            enriched_results = [self._enrich_candidate_exam_subject_data(ces) for ces in candidate_exam_subjects]
            
            return enriched_results, total
            
        except Exception as e:
            self.logger.error(f"Error getting candidate exam subjects for candidate {candidate_id}: {str(e)}")
            raise
    
    async def get_by_candidate_exam(
        self, 
        candidate_exam_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[CandidateExamSubject], int]:
        """
        Get all subjects registered for a specific candidate exam.
        
        Args:
            candidate_exam_id: ID of the candidate exam
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of candidate exam subjects, total count)
        """
        try:
            # Build query
            query = (
                select(CandidateExamSubject)
                .options(
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.candidate),
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.exam),
                    joinedload(CandidateExamSubject.exam_subject)
                    .joinedload(ExamSubject.subject)
                )
                .where(CandidateExamSubject.candidate_exam_id == candidate_exam_id)
            )
            
            # Get total count
            count_query = (
                select(func.count())
                .select_from(
                    select(CandidateExamSubject)
                    .where(CandidateExamSubject.candidate_exam_id == candidate_exam_id)
                    .subquery()
                )
            )
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            candidate_exam_subjects = result.scalars().unique().all()
            
            # Enrich with related data
            enriched_results = [self._enrich_candidate_exam_subject_data(ces) for ces in candidate_exam_subjects]
            
            return enriched_results, total
            
        except Exception as e:
            self.logger.error(f"Error getting candidate exam subjects for candidate exam {candidate_exam_id}: {str(e)}")
            raise
    
    async def get_by_exam_subject(
        self, 
        exam_subject_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[CandidateExamSubject], int]:
        """
        Get all candidates registered for a specific exam subject.
        
        Args:
            exam_subject_id: ID of the exam subject
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of candidate exam subjects, total count)
        """
        try:
            # Build query
            query = (
                select(CandidateExamSubject)
                .options(
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.candidate),
                    joinedload(CandidateExamSubject.candidate_exam)
                    .joinedload(CandidateExam.exam),
                    joinedload(CandidateExamSubject.exam_subject)
                )
                .where(CandidateExamSubject.exam_subject_id == exam_subject_id)
            )
            
            # Get total count
            count_query = (
                select(func.count())
                .select_from(
                    select(CandidateExamSubject)
                    .where(CandidateExamSubject.exam_subject_id == exam_subject_id)
                    .subquery()
                )
            )
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            candidate_exam_subjects = result.scalars().unique().all()
            
            # Enrich with related data
            enriched_results = [self._enrich_candidate_exam_subject_data(ces) for ces in candidate_exam_subjects]
            
            return enriched_results, total
            
        except Exception as e:
            self.logger.error(f"Error getting candidate exam subjects for exam subject {exam_subject_id}: {str(e)}")
            raise
    
    async def get_candidate_exam_schedule(self, candidate_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete exam schedule for a candidate with room and location details.
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            List of dictionaries with complete exam schedule information
        """
        try:
            # Build the complex query with all necessary joins
            query = (
                select(
                    CandidateExamSubject,
                    ExamSubject,
                    ExamSchedule,
                    ExamRoom,
                    ExamLocation,
                    Subject,
                    Exam
                )
                .join(CandidateExam, CandidateExamSubject.candidate_exam_id == CandidateExam.candidate_exam_id)
                .join(ExamSubject, CandidateExamSubject.exam_subject_id == ExamSubject.exam_subject_id)
                .join(Subject, ExamSubject.subject_id == Subject.subject_id)
                .join(Exam, ExamSubject.exam_id == Exam.exam_id)
                .join(ExamSchedule, ExamSubject.exam_subject_id == ExamSchedule.exam_subject_id)
                .join(ExamRoom, ExamSchedule.room_id == ExamRoom.room_id)
                .join(ExamLocation, ExamRoom.location_id == ExamLocation.location_id)
                .where(CandidateExam.candidate_id == candidate_id)
                .order_by(ExamSchedule.start_time)
            )
            
            # Execute query
            result = await self.db.execute(query)
            rows = result.fetchall()
            
            # Process results into a more useful format
            schedules = []
            for row in rows:
                ces, es, schedule, room, location, subject, exam = row
                
                schedule_info = {
                    "candidate_exam_subject_id": ces.candidate_exam_subject_id,
                    "registration_status": ces.status,
                    "is_required": ces.is_required,
                    "registration_date": ces.registration_date,
                    "notes": ces.notes,
                    
                    "exam_id": exam.exam_id,
                    "exam_name": exam.exam_name,
                    "subject_id": subject.subject_id, 
                    "subject_name": subject.subject_name,
                    "subject_code": subject.subject_code,
                    
                    "exam_schedule_id": schedule.exam_schedule_id,
                    "start_time": schedule.start_time,
                    "end_time": schedule.end_time,
                    "schedule_status": schedule.status,
                    
                    "room_id": room.room_id,
                    "room_name": room.room_name,
                    "room_number": room.room_number,
                    "floor": room.floor,
                    
                    "location_id": location.location_id,
                    "location_name": location.location_name,
                    "address": location.address,
                    "city": location.city,
                }
                
                schedules.append(schedule_info)
            
            return schedules
            
        except Exception as e:
            self.logger.error(f"Error getting exam schedule for candidate {candidate_id}: {str(e)}")
            raise
    
    async def get_candidate_exam_scores(
        self, 
        candidate_id: str, 
        exam_id: Optional[str] = None,
        subject_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all exam scores for a candidate with optional filtering by exam and subject.
        
        Args:
            candidate_id: ID of the candidate
            exam_id: Optional ID of the exam to filter by
            subject_id: Optional ID of the subject to filter by
            
        Returns:
            List of dictionaries with score information
        """
        try:
            # Build the complex query with all necessary joins
            query = (
                select(
                    CandidateExamSubject,
                    CandidateExam,
                    Exam,
                    ExamSubject,
                    Subject,
                    ExamScore
                )
                .join(CandidateExam, CandidateExamSubject.candidate_exam_id == CandidateExam.candidate_exam_id)
                .join(Exam, CandidateExam.exam_id == Exam.exam_id)
                .join(ExamSubject, CandidateExamSubject.exam_subject_id == ExamSubject.exam_subject_id)
                .join(Subject, ExamSubject.subject_id == Subject.subject_id)
                .join(ExamScore, CandidateExamSubject.candidate_exam_subject_id == ExamScore.candidate_exam_subject_id)
                .where(CandidateExam.candidate_id == candidate_id)
            )
            
            # Apply optional filters
            if exam_id:
                query = query.where(Exam.exam_id == exam_id)
            
            if subject_id:
                query = query.where(Subject.subject_id == subject_id)
            
            # Order by exam and subject
            query = query.order_by(Exam.exam_name, Subject.subject_name)
            
            # Execute query
            result = await self.db.execute(query)
            rows = result.fetchall()
            
            # Process results
            scores = []
            for row in rows:
                ces, ce, exam, es, subject, score = row
                
                score_info = {
                    "candidate_id": ce.candidate_id,
                    "candidate_exam_id": ce.candidate_exam_id,
                    "candidate_exam_subject_id": ces.candidate_exam_subject_id,
                    "exam_score_id": score.exam_score_id,
                    
                    "exam_id": exam.exam_id,
                    "exam_name": exam.exam_name,
                    "subject_id": subject.subject_id,
                    "subject_name": subject.subject_name,
                    "subject_code": subject.subject_code,
                    
                    "score": float(score.score) if score.score is not None else None,
                    "status": score.status,
                    "graded_by": score.graded_by,
                    "graded_at": score.graded_at,
                    "notes": score.notes,
                    
                    # Include registration status for the subject
                    "registration_status": ces.status,
                    "is_required": ces.is_required,
                    "registration_date": ces.registration_date
                }
                
                scores.append(score_info)
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Error getting exam scores for candidate {candidate_id}: {str(e)}")
            raise
    
    async def create(self, candidate_exam_subject_data: Dict[str, Any]) -> CandidateExamSubject:
        """
        Create a new candidate exam subject registration.
        
        Args:
            candidate_exam_subject_data: Dictionary with candidate exam subject data
            
        Returns:
            Created CandidateExamSubject object
        """
        try:
            # Generate ID if not provided
            if 'candidate_exam_subject_id' not in candidate_exam_subject_data:
                from app.services.id_service import generate_model_id
                candidate_exam_subject_data['candidate_exam_subject_id'] = generate_model_id("CandidateExamSubject")
            
            # Create new instance
            candidate_exam_subject = CandidateExamSubject(**candidate_exam_subject_data)
            self.db.add(candidate_exam_subject)
            await self.db.flush()
            
            # Get the created instance with related data
            created = await self.get_by_id(candidate_exam_subject.candidate_exam_subject_id)
            
            return created
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error creating candidate exam subject: {str(e)}")
            raise
    
    async def update(self, candidate_exam_subject_id: str, candidate_exam_subject_data: Dict[str, Any]) -> Optional[CandidateExamSubject]:
        """
        Update a candidate exam subject registration.
        
        Args:
            candidate_exam_subject_id: ID of the candidate exam subject to update
            candidate_exam_subject_data: Dictionary with updated data
            
        Returns:
            Updated CandidateExamSubject object or None if not found
        """
        try:
            # Check if exists
            candidate_exam_subject = await self.get_by_id(candidate_exam_subject_id)
            if not candidate_exam_subject:
                return None
            
            # Update
            stmt = (
                update(CandidateExamSubject)
                .where(CandidateExamSubject.candidate_exam_subject_id == candidate_exam_subject_id)
                .values(**candidate_exam_subject_data)
            )
            await self.db.execute(stmt)
            
            # Get updated object
            updated = await self.get_by_id(candidate_exam_subject_id)
            
            return updated
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error updating candidate exam subject {candidate_exam_subject_id}: {str(e)}")
            raise
    
    async def delete(self, candidate_exam_subject_id: str) -> bool:
        """
        Delete a candidate exam subject registration.
        
        Args:
            candidate_exam_subject_id: ID of the candidate exam subject to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            # Check if exists
            candidate_exam_subject = await self.get_by_id(candidate_exam_subject_id)
            if not candidate_exam_subject:
                return False
            
            # Delete
            stmt = delete(CandidateExamSubject).where(
                CandidateExamSubject.candidate_exam_subject_id == candidate_exam_subject_id
            )
            result = await self.db.execute(stmt)
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error deleting candidate exam subject {candidate_exam_subject_id}: {str(e)}")
            raise
