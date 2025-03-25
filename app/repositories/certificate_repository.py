"""
Certificate repository module.

This module provides database operations for certificates,
including CRUD operations and queries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.orm import joinedload

from app.domain.models.certificate import Certificate
from app.domain.models.candidate import Candidate
from app.domain.models.exam import Exam
from app.domain.models.exam_type import ExamType
from app.domain.models.user import User
from app.domain.models.exam_score import ExamScore
from app.domain.models.candidate_exam import CandidateExam
from app.domain.models.exam_subject import ExamSubject
from app.domain.models.subject import Subject

logger = logging.getLogger(__name__)

class CertificateRepository:
    """Repository for managing Certificate entities in the database."""
    
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
        Get all certificates with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria
            
        Returns:
            Tuple containing the list of certificates with details and total count
        """
        # Base query with all necessary joins
        query = (
            select(
                Certificate,
                CandidateExam,
                Candidate.full_name.label("candidate_name"),
                Exam.exam_name
            )
            .join(CandidateExam, Certificate.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
        )
        
        # Apply search filter
        if filters and "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Candidate.full_name.ilike(search_term),
                    Exam.exam_name.ilike(search_term),
                    Certificate.certificate_number.ilike(search_term)
                )
            )
        
        # Apply candidate_exam_id filter
        if filters and "candidate_exam_id" in filters and filters["candidate_exam_id"]:
            query = query.filter(Certificate.candidate_exam_id == filters["candidate_exam_id"])
        
        # Apply issue_date range filters
        if filters and "issue_date_after" in filters and filters["issue_date_after"]:
            query = query.filter(Certificate.issue_date >= filters["issue_date_after"])
        
        if filters and "issue_date_before" in filters and filters["issue_date_before"]:
            query = query.filter(Certificate.issue_date <= filters["issue_date_before"])
        
        # Apply sorting
        sort_field = filters.get("sort_field", "created_at") if filters else "created_at"
        sort_dir = filters.get("sort_dir", "desc") if filters else "desc"
        
        if hasattr(Certificate, sort_field):
            sort_attr = getattr(Certificate, sort_field)
            if sort_dir.lower() == "asc":
                query = query.order_by(asc(sort_attr))
            else:
                query = query.order_by(desc(sort_attr))
        else:
            # Default sort by created_at desc
            query = query.order_by(desc(Certificate.created_at))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        
        # Process results to include related entity details
        certificates = []
        for cert, candidate_exam, candidate_name, exam_name in result:
            certificate_dict = {
                "certificate_id": cert.certificate_id,
                "candidate_exam_id": cert.candidate_exam_id,
                "certificate_number": cert.certificate_number,
                "issue_date": cert.issue_date,
                "score": cert.score,
                "expiry_date": cert.expiry_date,
                "certificate_image_url": cert.certificate_image_url,
                "additional_info": cert.additional_info,
                "created_at": cert.created_at,
                "updated_at": cert.updated_at,
                "candidate_name": candidate_name,
                "exam_name": exam_name
            }
            certificates.append(certificate_dict)
        
        return certificates, total
    
    async def get_by_id(self, certificate_id: str) -> Optional[Dict]:
        """
        Get a certificate by its ID, including related entity details.
        
        Args:
            certificate_id: The unique identifier of the certificate
            
        Returns:
            The certificate with related entity details if found, None otherwise
        """
        query = (
            select(
                Certificate,
                CandidateExam,
                Candidate.full_name.label("candidate_name"),
                Exam.exam_name
            )
            .join(CandidateExam, Certificate.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
            .filter(Certificate.certificate_id == certificate_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        cert, candidate_exam, candidate_name, exam_name = row
        return {
            "certificate_id": cert.certificate_id,
            "candidate_exam_id": cert.candidate_exam_id,
            "certificate_number": cert.certificate_number,
            "issue_date": cert.issue_date,
            "score": cert.score,
            "expiry_date": cert.expiry_date,
            "certificate_image_url": cert.certificate_image_url,
            "additional_info": cert.additional_info,
            "created_at": cert.created_at,
            "updated_at": cert.updated_at,
            "candidate_name": candidate_name,
            "exam_name": exam_name,
            "candidate_id": candidate_exam.candidate_id,
            "exam_id": candidate_exam.exam_id
        }
    
    async def get_by_candidate_exam_id(self, candidate_exam_id: str) -> List[Dict]:
        """
        Get all certificates for a specific candidate exam.
        
        Args:
            candidate_exam_id: The ID of the candidate exam
            
        Returns:
            List of certificates for the specified candidate exam
        """
        filters = {"candidate_exam_id": candidate_exam_id}
        certificates, _ = await self.get_all(filters=filters)
        return certificates
    
    async def get_by_certificate_number(self, certificate_number: str) -> Optional[Dict]:
        """
        Get a certificate by its certificate number.
        
        Args:
            certificate_number: The unique certificate number
            
        Returns:
            The certificate if found, None otherwise
        """
        query = (
            select(
                Certificate,
                CandidateExam,
                Candidate.full_name.label("candidate_name"),
                Exam.exam_name
            )
            .join(CandidateExam, Certificate.candidate_exam_id == CandidateExam.candidate_exam_id)
            .join(Candidate, CandidateExam.candidate_id == Candidate.candidate_id)
            .join(Exam, CandidateExam.exam_id == Exam.exam_id)
            .filter(Certificate.certificate_number == certificate_number)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        cert, candidate_exam, candidate_name, exam_name = row
        return {
            "certificate_id": cert.certificate_id,
            "candidate_exam_id": cert.candidate_exam_id,
            "certificate_number": cert.certificate_number,
            "issue_date": cert.issue_date,
            "score": cert.score,
            "expiry_date": cert.expiry_date,
            "certificate_image_url": cert.certificate_image_url,
            "additional_info": cert.additional_info,
            "created_at": cert.created_at,
            "updated_at": cert.updated_at,
            "candidate_name": candidate_name,
            "exam_name": exam_name
        }
    
    async def check_certificate_exists(self, candidate_exam_id: str) -> bool:
        """
        Check if a certificate already exists for the candidate exam.
        
        Args:
            candidate_exam_id: The ID of the candidate exam
            
        Returns:
            True if a certificate exists, False otherwise
        """
        query = (
            select(Certificate)
            .filter(Certificate.candidate_exam_id == candidate_exam_id)
        )
        
        result = await self.db.execute(query)
        return result.first() is not None
    
    async def get_certificate_count_for_year(self, year: int) -> int:
        """
        Get the count of certificates issued in a specific year.
        
        Args:
            year: The year to count certificates for
            
        Returns:
            Count of certificates issued in the year
        """
        # Count certificates where certificate_number starts with CERT-{year}
        prefix = f"CERT-{year}"
        query = (
            select(func.count())
            .select_from(Certificate)
            .filter(Certificate.certificate_number.like(f"{prefix}%"))
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def create(self, certificate_data: Dict[str, Any]) -> Certificate:
        """
        Create a new certificate.
        
        Args:
            certificate_data: Dictionary containing the certificate data
            
        Returns:
            The created certificate
        """
        # Ensure certificate_id is set
        if 'certificate_id' not in certificate_data or not certificate_data['certificate_id']:
            from app.services.id_service import generate_model_id
            certificate_data['certificate_id'] = generate_model_id("Certificate")
            logger.info(f"Generated new certificate ID: {certificate_data['certificate_id']}")
        
        # Create a new certificate
        new_certificate = Certificate(**certificate_data)
        
        # Add to session and commit
        self.db.add(new_certificate)
        await self.db.commit()
        await self.db.refresh(new_certificate)
        
        logger.info(f"Created certificate with ID: {new_certificate.certificate_id}")
        return new_certificate
    
    async def update(self, certificate_id: str, certificate_data: Dict[str, Any]) -> Optional[Certificate]:
        """
        Update an existing certificate.
        
        Args:
            certificate_id: The unique identifier of the certificate
            certificate_data: Dictionary containing the updated certificate data
            
        Returns:
            The updated certificate if found, None otherwise
        """
        # Add updated_at timestamp
        certificate_data["updated_at"] = datetime.utcnow()
        
        # Update the certificate
        query = (
            update(Certificate)
            .where(Certificate.certificate_id == certificate_id)
            .values(**certificate_data)
            .returning(Certificate)
        )
        
        result = await self.db.execute(query)
        updated_certificate = result.scalar_one_or_none()
        
        if not updated_certificate:
            logger.warning(f"Certificate with ID {certificate_id} not found for update")
            return None
        
        await self.db.commit()
        logger.info(f"Updated certificate with ID: {certificate_id}")
        return updated_certificate
    
    async def delete(self, certificate_id: str) -> bool:
        """
        Delete a certificate.
        
        Args:
            certificate_id: The unique identifier of the certificate
            
        Returns:
            True if the certificate was deleted, False otherwise
        """
        # Delete the certificate
        query = (
            delete(Certificate)
            .where(Certificate.certificate_id == certificate_id)
            .returning(Certificate.certificate_id)
        )
        
        result = await self.db.execute(query)
        deleted_id = result.scalar_one_or_none()
        
        if not deleted_id:
            logger.warning(f"Certificate with ID {certificate_id} not found for deletion")
            return False
        
        await self.db.commit()
        logger.info(f"Deleted certificate with ID: {certificate_id}")
        return True
    
    async def _get_subject_scores(self, candidate_id: str, exam_id: str) -> List[Dict[str, Any]]:
        """
        Get the subject scores for a candidate in an exam.
        
        Args:
            candidate_id: The ID of the candidate
            exam_id: The ID of the exam
            
        Returns:
            List of subject scores with details
        """
        # First, get the candidate_exam_id
        candidate_exam_query = (
            select(CandidateExam.candidate_exam_id)
            .filter(
                CandidateExam.candidate_id == candidate_id,
                CandidateExam.exam_id == exam_id
            )
        )
        
        candidate_exam_result = await self.db.execute(candidate_exam_query)
        candidate_exam_id = candidate_exam_result.scalar_one_or_none()
        
        if not candidate_exam_id:
            return []
        
        # Get the exam_subject_ids for the exam
        exam_subject_query = (
            select(ExamSubject.exam_subject_id, Subject.subject_name, Subject.subject_code)
            .join(Subject, ExamSubject.subject_id == Subject.subject_id)
            .filter(ExamSubject.exam_id == exam_id)
        )
        
        exam_subject_result = await self.db.execute(exam_subject_query)
        exam_subjects = exam_subject_result.fetchall()
        
        # Get the scores for each exam_subject
        subject_scores = []
        
        for exam_subject_id, subject_name, subject_code in exam_subjects:
            score_query = (
                select(ExamScore.score_value, ExamScore.status)
                .filter(
                    ExamScore.candidate_exam_id == candidate_exam_id,
                    ExamScore.exam_subject_id == exam_subject_id
                )
            )
            
            score_result = await self.db.execute(score_query)
            score_row = score_result.first()
            
            if score_row:
                score_value, status = score_row
                subject_scores.append({
                    "subject_name": subject_name,
                    "subject_code": subject_code,
                    "score": score_value,
                    "status": status
                })
        
        return subject_scores 