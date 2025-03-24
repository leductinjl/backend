"""
Credential Sync Service Module.

This module provides the CredentialSyncService class for synchronizing Candidate Credential
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

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
    
    async def sync_by_id(self, credential_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific credential by ID.
        
        Args:
            credential_id: The ID of the credential to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing credential {credential_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get credential from SQL database
            credential = await self.credential_repository.get_by_id(credential_id)
            if not credential:
                logger.error(f"Credential {credential_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(credential)
            
            # Create or update node in Neo4j
            await self.credential_graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(credential_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing credential {credential_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all credentials.
        
        Args:
            limit: Optional limit on number of credentials to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all credentials (skip_relationships={skip_relationships})")
        
        try:
            # Get all credentials from SQL database
            credentials, _ = await self.credential_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for credential in credentials:
                try:
                    # Sync the credential node - handle both ORM objects and dictionaries
                    credential_id = credential.credential_id if hasattr(credential, 'credential_id') else credential.get("credential_id")
                    if not credential_id:
                        logger.error(f"Missing credential_id in credential object: {credential}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(credential_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get credential_id safely for logging
                    credential_id = getattr(credential, 'credential_id', None) if hasattr(credential, 'credential_id') else credential.get("credential_id", "unknown")
                    logger.error(f"Error syncing credential {credential_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during credential synchronization: {e}")
            return {"success": 0, "failed": 0}
    
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
            
    async def sync_relationships(self, credential_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific credential.
        
        Args:
            credential_id: ID of the credential to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for credential {credential_id}")
        
        relationship_counts = {
            "candidate": 0,
            "issuing_organization": 0
        }
        
        try:
            # Get credential from SQL database with full details
            credential = await self.credential_repository.get_by_id(credential_id)
            if not credential:
                logger.error(f"Credential {credential_id} not found in SQL database")
                return relationship_counts
            
            # Extract candidate_id if available
            candidate_id = credential.candidate_id
            
            # Sync BELONGS_TO relationship (credential-candidate)
            if candidate_id:
                success = await self.credential_graph_repository.add_belongs_to_relationship(credential_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Extract issuing_organization if available
            issuing_org = getattr(credential, 'issuing_organization', None)
            if issuing_org:
                # In a real implementation, we would add relationship to organization
                # This is a placeholder for future implementation
                relationship_counts["issuing_organization"] += 0
            
            logger.info(f"Credential relationship synchronization completed for {credential_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for credential {credential_id}: {e}")
            return relationship_counts 