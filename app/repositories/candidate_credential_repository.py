"""
Candidate Credential repository module.

This module provides database access methods for the CandidateCredential model,
including CRUD operations and queries for external credentials.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload
from datetime import date
from typing import List, Optional, Dict, Any, Tuple
import logging

from app.domain.models.candidate_credential import CandidateCredential, CredentialType
from app.domain.models.candidate import Candidate
from app.services.id_service import generate_model_id

class CandidateCredentialRepository:
    """Repository for interacting with the CandidateCredential table."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with a database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def get_all(
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
        Retrieve candidate credentials with pagination and filtering.
        
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
            # Build query with joins for related data
            query = (
                select(CandidateCredential)
                .options(
                    joinedload(CandidateCredential.candidate)
                )
            )
            
            # Apply filters
            conditions = []
            
            if candidate_id:
                conditions.append(CandidateCredential.candidate_id == candidate_id)
            
            if credential_type:
                if credential_type in [t.value for t in CredentialType]:
                    conditions.append(CandidateCredential.credential_type == credential_type)
                else:
                    self.logger.warning(f"Invalid credential type filter: {credential_type}")
            
            if issuing_organization:
                conditions.append(CandidateCredential.issuing_organization.ilike(f"%{issuing_organization}%"))
            
            if issue_date_from:
                conditions.append(CandidateCredential.issue_date >= issue_date_from)
                
            if issue_date_to:
                conditions.append(CandidateCredential.issue_date <= issue_date_to)
            
            # Apply conditions if any
            if conditions:
                query = query.where(and_(*conditions))
            
            # Order by issue date, then title
            query = query.order_by(
                CandidateCredential.issue_date.desc(), 
                CandidateCredential.title
            )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            credentials = result.scalars().unique().all()
            
            return credentials, total
            
        except Exception as e:
            self.logger.error(f"Error getting candidate credentials: {str(e)}")
            raise
    
    async def get_by_id(self, credential_id: str) -> Optional[CandidateCredential]:
        """
        Get a candidate credential by ID.
        
        Args:
            credential_id: ID of the credential to retrieve
            
        Returns:
            CandidateCredential object or None if not found
        """
        try:
            query = (
                select(CandidateCredential)
                .options(
                    joinedload(CandidateCredential.candidate)
                )
                .where(CandidateCredential.credential_id == credential_id)
            )
            
            result = await self.db.execute(query)
            return result.scalars().first()
            
        except Exception as e:
            self.logger.error(f"Error getting credential with ID {credential_id}: {str(e)}")
            raise
    
    async def get_by_candidate(
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
        """
        try:
            # Build base query
            query = (
                select(CandidateCredential)
                .options(
                    joinedload(CandidateCredential.candidate)
                )
                .where(CandidateCredential.candidate_id == candidate_id)
            )
            
            # Apply credential type filter if provided
            if credential_type:
                if credential_type in [t.value for t in CredentialType]:
                    query = query.where(CandidateCredential.credential_type == credential_type)
                else:
                    self.logger.warning(f"Invalid credential type filter: {credential_type}")
            
            # Order by issue date, then title
            query = query.order_by(
                CandidateCredential.issue_date.desc(), 
                CandidateCredential.title
            )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            credentials = result.scalars().unique().all()
            
            return credentials, total
            
        except Exception as e:
            self.logger.error(f"Error getting credentials for candidate {candidate_id}: {str(e)}")
            raise
    
    async def create(self, credential_data: Dict[str, Any]) -> CandidateCredential:
        """
        Create a new candidate credential.
        
        Args:
            credential_data: Dictionary with credential data
            
        Returns:
            Created CandidateCredential object
        """
        try:
            # Ensure credential_id is set
            if 'credential_id' not in credential_data or not credential_data['credential_id']:
                credential_data['credential_id'] = generate_model_id("CandidateCredential")
                self.logger.info(f"Generated credential ID: {credential_data['credential_id']}")
            
            # Create new credential
            credential = CandidateCredential(**credential_data)
            self.db.add(credential)
            await self.db.flush()
            await self.db.commit()  # Commit transaction
            
            # Get the created credential with related data
            created_credential = await self.get_by_id(credential.credential_id)
            
            return created_credential
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error creating candidate credential: {str(e)}")
            raise
    
    async def update(
        self,
        credential_id: str,
        credential_data: Dict[str, Any]
    ) -> Optional[CandidateCredential]:
        """
        Update a candidate credential.
        
        Args:
            credential_id: ID of the credential to update
            credential_data: Dictionary with updated data
            
        Returns:
            Updated CandidateCredential object or None if not found
        """
        try:
            # Check if the credential exists
            credential = await self.get_by_id(credential_id)
            if not credential:
                return None
            
            # Update the credential
            stmt = (
                update(CandidateCredential)
                .where(CandidateCredential.credential_id == credential_id)
                .values(**credential_data)
            )
            await self.db.execute(stmt)
            await self.db.flush()
            
            # Get the updated credential
            updated_credential = await self.get_by_id(credential_id)
            
            return updated_credential
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error updating credential {credential_id}: {str(e)}")
            raise
    
    async def delete(self, credential_id: str) -> bool:
        """
        Delete a candidate credential.
        
        Args:
            credential_id: ID of the credential to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            # Check if the credential exists
            credential = await self.get_by_id(credential_id)
            if not credential:
                return False
            
            # Delete the credential
            stmt = delete(CandidateCredential).where(CandidateCredential.credential_id == credential_id)
            result = await self.db.execute(stmt)
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error deleting credential {credential_id}: {str(e)}")
            raise 