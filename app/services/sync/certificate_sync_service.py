"""
Certificate Sync Service Module.

This module provides the CertificateSyncService class for synchronizing Certificate
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

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
    
    async def sync_by_id(self, certificate_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific certificate by ID.
        
        Args:
            certificate_id: The ID of the certificate to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing certificate {certificate_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get certificate from SQL database with details
            certificate = await self.certificate_repository.get_by_id(certificate_id)
            if not certificate:
                logger.error(f"Certificate {certificate_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            certificate_node = self._convert_to_node(certificate)
            await self.certificate_graph_repository.create_or_update(certificate_node)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(certificate_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing certificate {certificate_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all certificates.
        
        Args:
            limit: Optional limit on number of certificates to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all certificates (skip_relationships={skip_relationships})")
        
        try:
            # Get all certificates from SQL database with details
            certificates, _ = await self.certificate_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for certificate in certificates:
                try:
                    # Sync the certificate node
                    await self.sync_by_id(certificate["certificate_id"], skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error syncing certificate {certificate['certificate_id']}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during certificate synchronization: {e}")
            return {"success": 0, "failed": 0}
    
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
            
    async def sync_relationships(self, certificate_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific certificate.
        
        Args:
            certificate_id: ID of the certificate to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for certificate {certificate_id}")
        
        relationship_counts = {
            "candidate": 0,
            "exam": 0,
            "issuing_organization": 0
        }
        
        try:
            # Get certificate from SQL database with full details
            certificate = await self.certificate_repository.get_by_id(certificate_id)
            if not certificate:
                logger.error(f"Certificate {certificate_id} not found in SQL database")
                return relationship_counts
            
            # Extract candidate_id if available
            candidate_id = certificate.get("candidate_id")
            
            # Sync ISSUED_TO relationship (certificate-candidate)
            if candidate_id:
                success = await self.certificate_graph_repository.add_issued_to_relationship(certificate_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Extract exam_id if available
            exam_id = certificate.get("exam_id")
            
            # Sync FOR_EXAM relationship (certificate-exam)
            if exam_id:
                success = await self.certificate_graph_repository.add_for_exam_relationship(certificate_id, exam_id)
                if success:
                    relationship_counts["exam"] += 1
            
            logger.info(f"Certificate relationship synchronization completed for {certificate_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for certificate {certificate_id}: {e}")
            return relationship_counts 