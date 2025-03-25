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
        sql_repository: Optional[CandidateCredentialRepository] = None,
        graph_repository: Optional[CredentialGraphRepository] = None
    ):
        """
        Initialize the CredentialSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional CandidateCredentialRepository instance
            graph_repository: Optional CredentialGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.session = session
        self.driver = driver
        self.sql_repository = sql_repository or CandidateCredentialRepository(session)
        self.graph_repository = graph_repository or CredentialGraphRepository(driver)
    
    async def sync_node_by_id(self, credential_id: str) -> bool:
        """
        Synchronize a specific credential node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            credential_id: The ID of the credential to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing credential node {credential_id}")
        
        try:
            # Get credential from SQL database
            credential = await self.sql_repository.get_by_id(credential_id)
            if not credential:
                logger.error(f"Credential {credential_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(credential)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized credential node {credential_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing credential node {credential_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all credential nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of credentials to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all credential nodes (limit={limit})")
        
        try:
            # Get all credentials from SQL database
            credentials, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for credential in credentials:
                try:
                    # Sync only the credential node - handle both ORM objects and dictionaries
                    credential_id = credential.credential_id if hasattr(credential, 'credential_id') else credential.get("credential_id")
                    if not credential_id:
                        logger.error(f"Missing credential_id in credential object: {credential}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(credential_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get credential_id safely for logging
                    credential_id = getattr(credential, 'credential_id', None) if hasattr(credential, 'credential_id') else credential.get("credential_id", "unknown")
                    logger.error(f"Error syncing credential node {credential_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing credential nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during credential nodes synchronization: {e}")
            return (0, 0)
    
    async def sync_relationship_by_id(self, credential_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific credential.
        
        Args:
            credential_id: ID of the credential to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for credential {credential_id}")
        
        # Check if credential node exists before syncing relationships
        credential_node = await self.graph_repository.get_by_id(credential_id)
        if not credential_node:
            logger.warning(f"Credential node {credential_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Credential node not found in Neo4j",
                "candidate": 0,
                "issuing_organization": 0
            }
        
        relationship_counts = {
            "candidate": 0,
            "issuing_organization": 0
        }
        
        try:
            # Get credential from SQL database with full details
            credential = await self.sql_repository.get_by_id(credential_id)
            if not credential:
                logger.error(f"Credential {credential_id} not found in SQL database")
                return relationship_counts
            
            # Extract candidate_id if available
            candidate_id = credential.candidate_id
            
            # Sync BELONGS_TO relationship (credential-candidate)
            if candidate_id:
                success = await self.graph_repository.add_belongs_to_relationship(credential_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Extract issuing_organization if available
            issuing_org = getattr(credential, 'issuing_organization', None)
            if issuing_org:
                # In a real implementation, we would add relationship to organization
                # This is a placeholder for future implementation
                relationship_counts["issuing_organization"] += 0
            
            logger.info(f"Credential relationship synchronization completed for {credential_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for credential {credential_id}: {e}")
            return relationship_counts
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all credentials.
        
        Args:
            limit: Optional maximum number of credentials to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all credentials (limit={limit})")
        
        try:
            # Get all credentials from SQL database
            credentials, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_credentials = len(credentials)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "candidate": 0,
                "issuing_organization": 0
            }
            
            # For each credential, sync relationships
            for credential in credentials:
                try:
                    # Get credential_id safely - handle both ORM objects and dictionaries
                    credential_id = credential.credential_id if hasattr(credential, 'credential_id') else credential.get("credential_id")
                    if not credential_id:
                        logger.error(f"Missing credential_id in credential object: {credential}")
                        failure_count += 1
                        continue
                    
                    # Verify credential exists in Neo4j
                    credential_node = await self.graph_repository.get_by_id(credential_id)
                    if not credential_node:
                        logger.warning(f"Credential {credential_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this credential
                    results = await self.sync_relationship_by_id(credential_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get credential_id safely for logging
                    credential_id = getattr(credential, 'credential_id', None) if hasattr(credential, 'credential_id') else credential.get("credential_id", "unknown")
                    logger.error(f"Error synchronizing relationships for credential {credential_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_credentials": total_credentials,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all credentials: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during credential relationships synchronization: {e}")
            return {
                "total_credentials": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            }
    
    def _convert_to_node(self, credential: CandidateCredential) -> CredentialNode:
        """
        Convert a SQL CandidateCredential model to a CredentialNode.
        
        Args:
            credential: SQL CandidateCredential instance
            
        Returns:
            CredentialNode instance ready for Neo4j
        """
        try:
            # Tạo CredentialNode trực tiếp với chỉ thuộc tính node, không có thông tin relationship
            return CredentialNode(
                credential_id=credential.credential_id,
                title=credential.title or f"Credential {credential.credential_id}",
                credential_type=getattr(credential, 'credential_type', None),
                issuing_organization=getattr(credential, 'issuing_organization', None),
                issue_date=getattr(credential, 'issue_date', None),
                expiry_date=getattr(credential, 'expiry_date', None),
                credential_url=getattr(credential, 'credential_url', None),
                verification_code=getattr(credential, 'verification_code', None),
                description=getattr(credential, 'description', None),
                status=getattr(credential, 'status', None),
                additional_info=getattr(credential, 'additional_info', None),
                credential_image_url=getattr(credential, 'credential_image_url', None)
            )
            
        except Exception as e:
            logger.error(f"Error converting credential to node: {str(e)}")
            # Return a basic node with just the ID and title as fallback
            return CredentialNode(
                credential_id=credential.credential_id,
                title=credential.title or f"Credential {credential.credential_id}"
            )