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
        sql_repository: Optional[CertificateRepository] = None,
        graph_repository: Optional[CertificateGraphRepository] = None
    ):
        """
        Initialize the CertificateSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional CertificateRepository instance
            graph_repository: Optional CertificateGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.session = session
        self.driver = driver
        self.sql_repository = sql_repository or CertificateRepository(session)
        self.graph_repository = graph_repository or CertificateGraphRepository(driver)
    
    async def sync_node_by_id(self, certificate_id: str) -> bool:
        """
        Synchronize a specific certificate node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            certificate_id: The ID of the certificate to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing certificate node {certificate_id}")
        
        try:
            # Get certificate from SQL database with details
            certificate = await self.sql_repository.get_by_id(certificate_id)
            if not certificate:
                logger.error(f"Certificate {certificate_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            certificate_node = self._convert_to_node(certificate)
            result = await self.graph_repository.create_or_update(certificate_node)
            
            logger.info(f"Successfully synchronized certificate node {certificate_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing certificate node {certificate_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all certificate nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of certificates to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all certificate nodes (limit={limit})")
        
        try:
            # Get all certificates from SQL database with details
            certificates, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for certificate in certificates:
                try:
                    # Sync only the certificate node
                    if await self.sync_node_by_id(certificate["certificate_id"]):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error syncing certificate node {certificate['certificate_id']}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing certificate nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during certificate nodes synchronization: {e}")
            return (0, 0)
    
    async def sync_relationship_by_id(self, certificate_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific certificate.
        
        Args:
            certificate_id: ID of the certificate to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for certificate {certificate_id}")
        
        # Check if certificate node exists before syncing relationships
        certificate_node = await self.graph_repository.get_by_id(certificate_id)
        if not certificate_node:
            logger.warning(f"Certificate node {certificate_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Certificate node not found in Neo4j",
                "candidate": 0,
                "exam": 0,
                "issuing_organization": 0
            }
        
        relationship_counts = {
            "candidate": 0,
            "exam": 0,
            "issuing_organization": 0
        }
        
        try:
            # Get certificate from SQL database with full details
            certificate = await self.sql_repository.get_by_id(certificate_id)
            if not certificate:
                logger.error(f"Certificate {certificate_id} not found in SQL database")
                return relationship_counts
            
            # Extract candidate_id if available
            candidate_id = certificate.get("candidate_id")
            
            # Sync ISSUED_TO relationship (certificate-candidate)
            if candidate_id:
                success = await self.graph_repository.add_issued_to_relationship(certificate_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Extract exam_id if available
            exam_id = certificate.get("exam_id")
            
            # Sync FOR_EXAM relationship (certificate-exam)
            if exam_id:
                success = await self.graph_repository.add_for_exam_relationship(certificate_id, exam_id)
                if success:
                    relationship_counts["exam"] += 1
            
            logger.info(f"Certificate relationship synchronization completed for {certificate_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for certificate {certificate_id}: {e}")
            return relationship_counts
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all certificates.
        
        Args:
            limit: Optional maximum number of certificates to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all certificates (limit={limit})")
        
        try:
            # Get all certificates from SQL database
            certificates, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_certificates = len(certificates)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "candidate": 0,
                "exam": 0,
                "issuing_organization": 0
            }
            
            # For each certificate, sync relationships
            for certificate in certificates:
                try:
                    # Verify certificate exists in Neo4j
                    certificate_node = await self.graph_repository.get_by_id(certificate["certificate_id"])
                    if not certificate_node:
                        logger.warning(f"Certificate {certificate['certificate_id']} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this certificate
                    results = await self.sync_relationship_by_id(certificate["certificate_id"])
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error synchronizing relationships for certificate {certificate['certificate_id']}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_certificates": total_certificates,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all certificates: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during certificate relationships synchronization: {e}")
            return {
                "total_certificates": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            }
    
    def _convert_to_node(self, certificate: Dict[str, Any]) -> CertificateNode:
        """
        Convert a SQL Certificate model or dictionary to a CertificateNode.
        
        Args:
            certificate: SQL Certificate instance or dictionary with certificate data
            
        Returns:
            CertificateNode instance ready for Neo4j
        """
        try:
            # Tạo CertificateNode chỉ với thuộc tính cơ bản, không có thông tin relationship
            certificate_node = CertificateNode(
                certificate_id=certificate["certificate_id"],
                certificate_name=f"Certificate {certificate.get('certificate_number', '')}",
                certificate_number=certificate.get("certificate_number"),
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