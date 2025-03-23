"""
Certificate Sync Service Module.

This module provides the CertificateSyncService class for synchronizing Certificate
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from neo4j import AsyncDriver

from app.domain.models.certificate import Certificate
from app.domain.graph_models.certificate_node import CertificateNode
from app.repositories.certificate_repository import CertificateRepository
from app.graph_repositories.certificate_graph_repository import CertificateGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class CertificateSyncService(BaseSyncService):
    """
    Service for synchronizing Certificate data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual certificates by ID and synchronizing
    all certificates in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        certificate_repository: Optional[CertificateRepository] = None,
        certificate_graph_repository: Optional[CertificateGraphRepository] = None
    ):
        """
        Initialize the CertificateSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            certificate_repository: Optional CertificateRepository instance
            certificate_graph_repository: Optional CertificateGraphRepository instance
        """
        self.session = session
        self.driver = driver
        self.certificate_repository = certificate_repository or CertificateRepository(session)
        self.certificate_graph_repository = certificate_graph_repository or CertificateGraphRepository(driver)
    
    async def sync_by_id(self, certificate_id: str) -> bool:
        """
        Synchronize a single certificate by ID.
        
        Args:
            certificate_id: ID of the certificate to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get certificate from SQL database with details
            certificate = await self.certificate_repository.get_by_id(certificate_id)
            if not certificate:
                logger.warning(f"Certificate with ID {certificate_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            certificate_node = self._convert_to_node(certificate)
            result = await self.certificate_graph_repository.create_or_update(certificate_node)
            
            if result:
                logger.info(f"Successfully synchronized certificate {certificate_id}")
                return True
            else:
                logger.error(f"Failed to synchronize certificate {certificate_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing certificate {certificate_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all certificates from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of certificates to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all certificates from SQL database with details
            certificates, total = await self.certificate_repository.get_all(skip=offset, limit=limit)
            
            logger.info(f"Found {total} certificates to synchronize")
            
            # Synchronize each certificate
            for certificate in certificates:
                if await self.sync_by_id(certificate["certificate_id"]):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Certificate synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during certificate synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, certificate: Dict[str, Any]) -> CertificateNode:
        """
        Convert a SQL Certificate model or dictionary to a CertificateNode.
        
        Args:
            certificate: SQL Certificate instance or dictionary with certificate data
            
        Returns:
            CertificateNode instance ready for Neo4j
        """
        try:
            # Extract candidate_id and exam_id from candidate_exam if needed
            candidate_id = None
            exam_id = None
            
            # Create the Neo4j node with relationships
            certificate_node = CertificateNode(
                certificate_id=certificate["certificate_id"],
                certificate_name=f"Certificate {certificate.get('certificate_number', '')}",
                certificate_number=certificate.get("certificate_number"),
                candidate_id=candidate_id,
                exam_id=exam_id,
                issue_date=certificate.get("issue_date"),
                expiry_date=certificate.get("expiry_date"),
                issuing_organization=None,  # Not in model, could be added if needed
                status=None,  # Not in model, could be added if needed
                additional_info=certificate.get("additional_info"),
                certificate_image_url=certificate.get("certificate_image_url")
            )
            
            return certificate_node
            
        except Exception as e:
            logger.error(f"Error converting certificate to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return CertificateNode(
                certificate_id=certificate["certificate_id"],
                certificate_name=f"Certificate {certificate.get('certificate_id')}"
            ) 