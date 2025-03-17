"""
Candidate Credential service module.

This module provides business logic for managing external credentials of candidates,
including validations and complex operations that may involve multiple repositories.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import date
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories.candidate_credential_repository import CandidateCredentialRepository
from app.repositories.candidate_repository import CandidateRepository
from app.domain.models.candidate_credential import CandidateCredential, CredentialType
from app.api.dto.candidate_credential import (
    CandidateCredentialCreate,
    CandidateCredentialUpdate
)

class CandidateCredentialService:
    """Service for managing candidate credentials."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with a database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.credential_repository = CandidateCredentialRepository(db)
        self.candidate_repository = CandidateRepository(db)
    
    async def get_credentials(
        self,
        skip: int = 0,
        limit: int = 100,
        candidate_id: Optional[str] = None,
        credential_type: Optional[str] = None,
        issuing_organization: Optional[str] = None,
        issue_date_from: Optional[date] = None,
        issue_date_to: Optional[date] = None
    ) -> Tuple[List[CandidateCredential], int]:
        """
        Get candidate credentials with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            candidate_id: Filter by candidate ID
            credential_type: Filter by credential type
            issuing_organization: Filter by issuing organization
            issue_date_from: Filter by minimum issue date
            issue_date_to: Filter by maximum issue date
            
        Returns:
            Tuple of (list of candidate credentials, total count)
        """
        try:
            # Validate credential type if provided
            if credential_type and credential_type not in [t.value for t in CredentialType]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid credential type. Valid values are: {', '.join([t.value for t in CredentialType])}"
                )
            
            # Get credentials with filters
            credentials, total = await self.credential_repository.get_all(
                skip=skip,
                limit=limit,
                candidate_id=candidate_id,
                credential_type=credential_type,
                issuing_organization=issuing_organization,
                issue_date_from=issue_date_from,
                issue_date_to=issue_date_to
            )
            
            return credentials, total
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting candidate credentials: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving candidate credentials"
            )
    
    async def get_credential_by_id(self, credential_id: str) -> CandidateCredential:
        """
        Get a candidate credential by ID.
        
        Args:
            credential_id: ID of the credential to retrieve
            
        Returns:
            CandidateCredential object
            
        Raises:
            HTTPException: If the credential is not found
        """
        try:
            # Get the credential
            credential = await self.credential_repository.get_by_id(credential_id)
            
            # Raise exception if not found
            if not credential:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Credential with ID {credential_id} not found"
                )
            
            return credential
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting credential with ID {credential_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving the credential"
            )
    
    async def get_credentials_by_candidate(
        self,
        candidate_id: str,
        credential_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[CandidateCredential], int]:
        """
        Get credentials for a specific candidate.
        
        Args:
            candidate_id: ID of the candidate
            credential_type: Optional filter by credential type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of credentials, total count)
            
        Raises:
            HTTPException: If the candidate is not found
        """
        try:
            # Verify the candidate exists
            candidate = await self.candidate_repository.get_by_id(candidate_id)
            if not candidate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Candidate with ID {candidate_id} not found"
                )
            
            # Validate credential type if provided
            if credential_type and credential_type not in [t.value for t in CredentialType]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid credential type. Valid values are: {', '.join([t.value for t in CredentialType])}"
                )
            
            # Get credentials for the candidate
            credentials, total = await self.credential_repository.get_by_candidate(
                candidate_id=candidate_id,
                credential_type=credential_type,
                skip=skip,
                limit=limit
            )
            
            return credentials, total
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting credentials for candidate {candidate_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving candidate credentials"
            )
    
    async def create_credential(self, credential_data: CandidateCredentialCreate) -> CandidateCredential:
        """
        Create a new candidate credential.
        
        Args:
            credential_data: Data for creating the credential
            
        Returns:
            Created CandidateCredential object
            
        Raises:
            HTTPException: If validation fails or an error occurs during creation
        """
        try:
            # Verify the candidate exists
            candidate = await self.candidate_repository.get_by_id(credential_data.candidate_id)
            if not candidate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Candidate with ID {credential_data.candidate_id} not found"
                )
            
            # Validate credential type
            if credential_data.credential_type not in [t.value for t in CredentialType]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid credential type. Valid values are: {', '.join([t.value for t in CredentialType])}"
                )
            
            # Prepare data for creation
            credential_dict = credential_data.model_dump()
            
            # Create the credential
            created_credential = await self.credential_repository.create(credential_dict)
            
            return created_credential
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error creating candidate credential: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while creating the candidate credential"
            )
    
    async def update_credential(
        self,
        credential_id: str,
        credential_data: CandidateCredentialUpdate
    ) -> CandidateCredential:
        """
        Update a candidate credential.
        
        Args:
            credential_id: ID of the credential to update
            credential_data: Data for updating the credential
            
        Returns:
            Updated CandidateCredential object
            
        Raises:
            HTTPException: If validation fails or an error occurs during update
        """
        try:
            # Get the existing credential
            existing_credential = await self.get_credential_by_id(credential_id)
            
            # Prepare update data
            update_dict = {k: v for k, v in credential_data.model_dump(exclude_unset=True).items() if v is not None}
            
            # Validate credential type if being updated
            if 'credential_type' in update_dict and update_dict['credential_type'] not in [t.value for t in CredentialType]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid credential type. Valid values are: {', '.join([t.value for t in CredentialType])}"
                )
            
            # Update the credential
            updated_credential = await self.credential_repository.update(
                credential_id=credential_id,
                credential_data=update_dict
            )
            
            if not updated_credential:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Credential with ID {credential_id} not found"
                )
            
            return updated_credential
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating credential {credential_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the credential"
            )
    
    async def delete_credential(self, credential_id: str) -> bool:
        """
        Delete a candidate credential.
        
        Args:
            credential_id: ID of the credential to delete
            
        Returns:
            Boolean indicating success
            
        Raises:
            HTTPException: If the credential is not found or an error occurs during deletion
        """
        try:
            # Verify the credential exists
            credential = await self.get_credential_by_id(credential_id)
            
            # Delete the credential
            deleted = await self.credential_repository.delete(credential_id)
            
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Credential with ID {credential_id} not found"
                )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting credential {credential_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting the credential"
            ) 