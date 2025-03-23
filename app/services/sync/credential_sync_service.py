"""
Credential Sync Service Module.

This module provides the CredentialSyncService class for synchronizing Candidate Credential
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from neo4j import AsyncDriver

from app.domain.models.candidate_credential import CandidateCredential
from app.domain.graph_models.credential_node import CredentialNode
from app.repositories.candidate_credential_repository import CandidateCredentialRepository
from app.graph_repositories.credential_graph_repository import CredentialGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class CredentialSyncService(BaseSyncService):
    """
    Service for synchronizing Candidate Credential data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual credentials by ID and synchronizing
    all credentials in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        credential_repository: Optional[CandidateCredentialRepository] = None,
        credential_graph_repository: Optional[CredentialGraphRepository] = None
    ):
        """
        Initialize the CredentialSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            credential_repository: Optional CandidateCredentialRepository instance
            credential_graph_repository: Optional CredentialGraphRepository instance
        """
        self.session = session
        self.driver = driver
        self.credential_repository = credential_repository or CandidateCredentialRepository(session)
        self.credential_graph_repository = credential_graph_repository or CredentialGraphRepository(driver)
    
    async def sync_by_id(self, credential_id: str) -> bool:
        """
        Synchronize a single credential by ID.
        
        Args:
            credential_id: ID of the credential to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get credential from SQL database with details
            credential = await self.credential_repository.get_by_id(credential_id)
            if not credential:
                logger.warning(f"Credential with ID {credential_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            credential_node = self._convert_to_node(credential)
            result = await self.credential_graph_repository.create_or_update(credential_node)
            
            if result:
                logger.info(f"Successfully synchronized credential {credential_id}")
                return True
            else:
                logger.error(f"Failed to synchronize credential {credential_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing credential {credential_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all credentials from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of credentials to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all credentials from SQL database with details
            credentials, total = await self.credential_repository.get_all(skip=offset, limit=limit)
            
            logger.info(f"Found {total} credentials to synchronize")
            
            # Synchronize each credential
            for credential in credentials:
                if await self.sync_by_id(credential.credential_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Credential synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during credential synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, credential: CandidateCredential) -> CredentialNode:
        """
        Convert a SQL CandidateCredential model to a CredentialNode.
        
        Args:
            credential: SQL CandidateCredential instance
            
        Returns:
            CredentialNode instance ready for Neo4j
        """
        try:
            # Use the from_sql_model method from CredentialNode
            credential_node = CredentialNode.from_sql_model(credential)
            return credential_node
            
        except Exception as e:
            logger.error(f"Error converting credential to node: {str(e)}")
            # Return a basic node with just the ID and title as fallback
            return CredentialNode(
                credential_id=credential.credential_id,
                title=credential.title or f"Credential {credential.credential_id}",
                candidate_id=credential.candidate_id
            ) 