"""
Certificate service module.

This module provides business logic for certificates, bridging
the API layer with the repository layer.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

from app.repositories.certificate_repository import CertificateRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.domain.models.certificate import Certificate

logger = logging.getLogger(__name__)

class CertificateService:
    """Service for handling certificate business logic."""
    
    def __init__(
        self, 
        repository: CertificateRepository,
        candidate_repository: Optional[CandidateRepository] = None,
        exam_repository: Optional[ExamRepository] = None,
        candidate_exam_repository: Optional[CandidateExamRepository] = None
    ):
        """
        Initialize the service with repositories.
        
        Args:
            repository: Repository for certificate data access
            candidate_repository: Repository for candidate data access
            exam_repository: Repository for exam data access
            candidate_exam_repository: Repository for candidate exam registration data access
        """
        self.repository = repository
        self.candidate_repository = candidate_repository
        self.exam_repository = exam_repository
        self.candidate_exam_repository = candidate_exam_repository
    
    async def get_all_certificates(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        candidate_exam_id: Optional[str] = None,
        issue_date_after: Optional[date] = None,
        issue_date_before: Optional[date] = None,
        sort_field: Optional[str] = None,
        sort_dir: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get all certificates with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            search: Optional search term for filtering
            candidate_exam_id: Optional filter by candidate exam ID
            issue_date_after: Optional filter by certificates issued after date
            issue_date_before: Optional filter by certificates issued before date
            sort_field: Optional field to sort by
            sort_dir: Optional sort direction ('asc' or 'desc')
            
        Returns:
            Tuple containing the list of certificates and total count
        """
        filters = {}
        if search:
            filters["search"] = search
        if candidate_exam_id:
            filters["candidate_exam_id"] = candidate_exam_id
        if issue_date_after:
            filters["issue_date_after"] = issue_date_after
        if issue_date_before:
            filters["issue_date_before"] = issue_date_before
        if sort_field:
            filters["sort_field"] = sort_field
        if sort_dir:
            filters["sort_dir"] = sort_dir
        
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def get_certificate_by_id(self, certificate_id: str) -> Optional[Dict]:
        """
        Get a certificate by its ID.
        
        Args:
            certificate_id: The unique identifier of the certificate
            
        Returns:
            The certificate if found, None otherwise
        """
        return await self.repository.get_by_id(certificate_id)
    
    async def get_certificates_by_candidate_exam_id(self, candidate_exam_id: str) -> List[Dict]:
        """
        Get all certificates for a specific candidate exam.
        
        Args:
            candidate_exam_id: The ID of the candidate exam
            
        Returns:
            List of certificates for the specified candidate exam
        """
        return await self.repository.get_by_candidate_exam_id(candidate_exam_id)
    
    async def get_certificates_by_candidate_id(self, candidate_id: str) -> List[Dict]:
        """
        Get all certificates for a specific candidate across all exams.
        
        Args:
            candidate_id: The ID of the candidate
            
        Returns:
            List of certificates for the specified candidate
        """
        # Verify that we have the required repository
        if not self.candidate_exam_repository:
            logger.error("Cannot get certificates by candidate ID: candidate_exam_repository not provided")
            return []
        
        # Get all candidate-exam registrations for this candidate
        candidate_exams = await self.candidate_exam_repository.get_by_candidate_id(candidate_id)
        
        # No registrations found
        if not candidate_exams:
            logger.info(f"No exam registrations found for candidate ID {candidate_id}")
            return []
        
        # Collect all certificates from all candidate-exam registrations
        all_certificates = []
        for candidate_exam in candidate_exams:
            certificates = await self.repository.get_by_candidate_exam_id(candidate_exam["candidate_exam_id"])
            for certificate in certificates:
                # Add exam name to the certificate for context
                certificate["exam_name"] = candidate_exam.get("exam_name", "Unknown Exam")
            all_certificates.extend(certificates)
        
        return all_certificates
    
    async def get_certificate_by_number(self, certificate_number: str) -> Optional[Dict]:
        """
        Get a certificate by its certificate number.
        
        Args:
            certificate_number: The unique certificate number
            
        Returns:
            The certificate if found, None otherwise
        """
        return await self.repository.get_by_certificate_number(certificate_number)
    
    async def create_certificate(self, certificate_data: Dict[str, Any]) -> Optional[Certificate]:
        """
        Create a new certificate after validating the candidate exam ID.
        
        Args:
            certificate_data: Dictionary containing the certificate data
            
        Returns:
            The created certificate if successful, None otherwise
        """
        # Validate that candidate exam exists if repository is provided
        if self.candidate_exam_repository:
            candidate_exam = await self.candidate_exam_repository.get_by_id(certificate_data["candidate_exam_id"])
            
            if not candidate_exam:
                logger.error(f"Candidate exam with ID {certificate_data['candidate_exam_id']} not found")
                return None
        
        # Check if certificate already exists for this candidate exam
        certificate_exists = await self.repository.check_certificate_exists(certificate_data["candidate_exam_id"])
        
        if certificate_exists:
            logger.error(f"Certificate already exists for candidate exam {certificate_data['candidate_exam_id']}")
            return None
        
        # Generate a unique certificate number if not provided
        if "certificate_number" not in certificate_data or not certificate_data["certificate_number"]:
            # Format: CERT-YEAR-SEQUENTIAL NUMBER
            current_year = datetime.now().year
            # Get count of certificates for this year to generate sequential number
            count = await self.repository.get_certificate_count_for_year(current_year)
            certificate_data["certificate_number"] = f"CERT-{current_year}-{count+1:04d}"
            logger.info(f"Generated certificate number: {certificate_data['certificate_number']}")
        
        # Create the certificate
        return await self.repository.create(certificate_data)
    
    async def update_certificate(self, certificate_id: str, certificate_data: Dict[str, Any]) -> Optional[Certificate]:
        """
        Update an existing certificate.
        
        Args:
            certificate_id: The unique identifier of the certificate
            certificate_data: Dictionary containing the updated certificate data
            
        Returns:
            The updated certificate if found, None otherwise
        """
        # Check if certificate exists
        existing_certificate = await self.repository.get_by_id(certificate_id)
        
        if not existing_certificate:
            logger.error(f"Certificate with ID {certificate_id} not found")
            return None
        
        # Update the certificate
        return await self.repository.update(certificate_id, certificate_data)
    
    async def delete_certificate(self, certificate_id: str) -> bool:
        """
        Delete a certificate.
        
        Args:
            certificate_id: The unique identifier of the certificate
            
        Returns:
            True if the certificate was deleted, False otherwise
        """
        return await self.repository.delete(certificate_id) 