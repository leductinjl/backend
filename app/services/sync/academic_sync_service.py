"""
Academic synchronization service module.

This module provides services for synchronizing academic achievement data between
PostgreSQL and Neo4j databases, including certificates, achievements, recognitions,
and degrees.
"""

import logging
import json
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sync.base_sync_service import BaseSyncService
from app.domain.graph_models.certificate_node import CertificateNode
from app.domain.graph_models.achievement_node import AchievementNode
from app.domain.graph_models.recognition_node import RecognitionNode
from app.domain.graph_models.degree_node import DegreeNode
from app.domain.graph_models.credential_node import CredentialNode
from app.graph_repositories.certificate_graph_repository import CertificateGraphRepository
from app.graph_repositories.achievement_graph_repository import AchievementGraphRepository
from app.graph_repositories.recognition_graph_repository import RecognitionGraphRepository
from app.graph_repositories.degree_graph_repository import DegreeGraphRepository
from app.graph_repositories.credential_graph_repository import CredentialGraphRepository
from app.repositories.repository_factory import RepositoryFactory

logger = logging.getLogger(__name__)

class AcademicSyncService(BaseSyncService):
    """
    Service for synchronizing academic achievement data between PostgreSQL and Neo4j.
    
    This service handles synchronization of certificates, achievements, recognitions,
    and degrees.
    """
    
    def __init__(self, neo4j_connection, db_session: AsyncSession):
        """Initialize with Neo4j connection and SQLAlchemy session."""
        super().__init__(neo4j_connection, db_session)
        
        # Initialize academic-related repositories
        self.certificate_graph_repo = CertificateGraphRepository(neo4j_connection)
        self.achievement_graph_repo = AchievementGraphRepository(neo4j_connection)
        self.recognition_graph_repo = RecognitionGraphRepository(neo4j_connection)
        self.degree_graph_repo = DegreeGraphRepository(neo4j_connection)
        self.credential_graph_repo = CredentialGraphRepository(neo4j_connection)
    
    async def sync_certificate(self, certificate_model):
        """
        Synchronize a certificate from PostgreSQL to Neo4j.
        
        Args:
            certificate_model: A Certificate SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        certificate_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(certificate_model, dict):
                certificate_id = certificate_model.get("certificate_id")
                cert_dict = certificate_model
            else:
                certificate_id = certificate_model.certificate_id
                cert_dict = {
                    "certificate_id": certificate_model.certificate_id,
                    "certificate_name": certificate_model.certificate_name,
                    "issuing_organization": certificate_model.issuing_organization,
                    "issue_date": certificate_model.issue_date,
                    "expiry_date": certificate_model.expiry_date,
                    "description": certificate_model.description,
                    "status": certificate_model.status,
                }
            
            await self._log_sync_start("certificate", certificate_id)
            
            # Create Neo4j node
            certificate_node = CertificateNode.from_dict(cert_dict)
            
            # Retrieve candidate and exam IDs for relationship creation
            repo_factory = RepositoryFactory(self.db)
            candidate_exam_repo = await repo_factory.get_candidate_exam_repository()
            
            try:
                candidate_exam = await candidate_exam_repo.get_by_certificate_id(certificate_id)
                if candidate_exam:
                    certificate_node.candidate_id = candidate_exam.candidate_id
                    certificate_node.exam_id = candidate_exam.exam_id
            except Exception as e:
                logger.warning(f"Could not retrieve candidate and exam for certificate {certificate_id}: {str(e)}")
            
            # Create or update node in Neo4j
            query = certificate_node.create_query()
            logger.info(f"Executing Neo4j query for certificate {certificate_id}")
            await self._execute_neo4j_query(query, certificate_node.to_dict())
            
            # Create relationships with candidate and exam
            if hasattr(certificate_node, "create_relationships_query") and callable(getattr(certificate_node, "create_relationships_query")):
                rel_query = certificate_node.create_relationships_query()
                if rel_query:
                    rel_params = certificate_node.to_dict()
                    logger.info(f"Creating relationships for certificate {certificate_id} with candidate {certificate_node.candidate_id} and exam {certificate_node.exam_id}")
                    await self._execute_neo4j_query(rel_query, rel_params)
            
            await self._log_sync_success("certificate", certificate_id)
            return True
        except Exception as e:
            await self._log_sync_error("certificate", str(e), certificate_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_achievement(self, achievement_model):
        """
        Synchronize an achievement from PostgreSQL to Neo4j.
        
        Args:
            achievement_model: An Achievement SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        achievement_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(achievement_model, dict):
                achievement_id = achievement_model.get("achievement_id")
                achievement_dict = achievement_model
            else:
                achievement_id = achievement_model.achievement_id
                achievement_dict = {
                    "achievement_id": achievement_model.achievement_id,
                    "candidate_id": achievement_model.candidate_id,
                    "achievement_name": achievement_model.achievement_name,
                    "achievement_date": achievement_model.achievement_date,
                    "description": achievement_model.description,
                    "achievement_type": achievement_model.achievement_type,
                    "issuing_organization": achievement_model.issuing_organization,
                }
            
            await self._log_sync_start("achievement", achievement_id)
            
            # Create Neo4j node
            achievement_node = AchievementNode.from_dict(achievement_dict)
            
            # Create or update node in Neo4j
            query = achievement_node.create_query()
            logger.info(f"Executing Neo4j query for achievement {achievement_id}")
            await self._execute_neo4j_query(query, achievement_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(achievement_node, "create_relationships_query") and callable(getattr(achievement_node, "create_relationships_query")):
                rel_query = achievement_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for achievement {achievement_id}")
                    await self._execute_neo4j_query(rel_query, achievement_node.to_dict())
            
            await self._log_sync_success("achievement", achievement_id)
            return True
        except Exception as e:
            await self._log_sync_error("achievement", str(e), achievement_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_recognition(self, recognition_model):
        """
        Synchronize a recognition from PostgreSQL to Neo4j.
        
        Args:
            recognition_model: A Recognition SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        recognition_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(recognition_model, dict):
                recognition_id = recognition_model.get("recognition_id")
                recognition_dict = recognition_model
            else:
                recognition_id = recognition_model.recognition_id
                recognition_dict = {
                    "recognition_id": recognition_model.recognition_id,
                    "candidate_id": recognition_model.candidate_id,
                    "recognition_name": recognition_model.recognition_name,
                    "recognition_date": recognition_model.recognition_date,
                    "issuing_organization": recognition_model.issuing_organization,
                    "description": recognition_model.description,
                    "recognition_type": recognition_model.recognition_type,
                }
            
            await self._log_sync_start("recognition", recognition_id)
            
            # Create Neo4j node
            recognition_node = RecognitionNode.from_dict(recognition_dict)
            
            # Create or update node in Neo4j
            query = recognition_node.create_query()
            logger.info(f"Executing Neo4j query for recognition {recognition_id}")
            await self._execute_neo4j_query(query, recognition_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(recognition_node, "create_relationships_query") and callable(getattr(recognition_node, "create_relationships_query")):
                rel_query = recognition_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for recognition {recognition_id}")
                    await self._execute_neo4j_query(rel_query, recognition_node.to_dict())
            
            await self._log_sync_success("recognition", recognition_id)
            return True
        except Exception as e:
            await self._log_sync_error("recognition", str(e), recognition_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_degree(self, degree_model):
        """
        Synchronize a degree from PostgreSQL to Neo4j.
        
        Args:
            degree_model: A Degree SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        degree_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(degree_model, dict):
                degree_id = degree_model.get("degree_id")
                degree_dict = degree_model
            else:
                degree_id = degree_model.degree_id
                degree_dict = {
                    "degree_id": degree_model.degree_id,
                    "candidate_id": degree_model.candidate_id,
                    "degree_name": degree_model.degree_name,
                    "institution": degree_model.institution,
                    "major": degree_model.major,
                    "graduation_date": degree_model.graduation_date,
                    "degree_type": degree_model.degree_type,
                    "gpa": degree_model.gpa,
                }
            
            await self._log_sync_start("degree", degree_id)
            
            # Create Neo4j node
            degree_node = DegreeNode.from_dict(degree_dict)
            
            # Create or update node in Neo4j
            query = degree_node.create_query()
            logger.info(f"Executing Neo4j query for degree {degree_id}")
            await self._execute_neo4j_query(query, degree_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(degree_node, "create_relationships_query") and callable(getattr(degree_node, "create_relationships_query")):
                rel_query = degree_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for degree {degree_id}")
                    await self._execute_neo4j_query(rel_query, degree_node.to_dict())
            
            await self._log_sync_success("degree", degree_id)
            return True
        except Exception as e:
            await self._log_sync_error("degree", str(e), degree_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_credential(self, credential_model):
        """
        Synchronize a credential from PostgreSQL to Neo4j.
        
        Args:
            credential_model: A Credential SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        credential_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(credential_model, dict):
                credential_id = credential_model.get("credential_id")
                credential_dict = credential_model
            else:
                credential_id = credential_model.credential_id
                credential_dict = {
                    "credential_id": credential_model.credential_id,
                    "credential_name": credential_model.credential_name,
                    "credential_type": credential_model.credential_type,
                    "issuing_organization": credential_model.issuing_organization,
                    "description": credential_model.description,
                }
            
            await self._log_sync_start("credential", credential_id)
            
            # Create Neo4j node
            credential_node = CredentialNode.from_dict(credential_dict)
            
            # Create or update node in Neo4j
            query = credential_node.create_query()
            logger.info(f"Executing Neo4j query for credential {credential_id}")
            await self._execute_neo4j_query(query, credential_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(credential_node, "create_relationships_query") and callable(getattr(credential_node, "create_relationships_query")):
                rel_query = credential_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for credential {credential_id}")
                    await self._execute_neo4j_query(rel_query, credential_node.to_dict())
            
            await self._log_sync_success("credential", credential_id)
            return True
        except Exception as e:
            await self._log_sync_error("credential", str(e), credential_id)
            logger.error(traceback.format_exc())
            return False
    
    async def bulk_sync_certificates(self):
        """
        Synchronize all certificates from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized certificates
        """
        await self._log_sync_start("certificate")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            certificate_repo = await repo_factory.get_certificate_repository()
            
            # Get all certificates
            certificates = await certificate_repo.get_all()
            logger.info(f"Found {len(certificates)} certificates to sync")
            
            # Sync each certificate
            success_count = 0
            for certificate in certificates:
                if await self.sync_certificate(certificate):
                    success_count += 1
            
            await self._log_sync_success("certificate", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("certificate", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def bulk_sync_achievements(self):
        """
        Synchronize all achievements from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized achievements
        """
        await self._log_sync_start("achievement")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            achievement_repo = await repo_factory.get_achievement_repository()
            
            # Get all achievements
            achievements = await achievement_repo.get_all()
            logger.info(f"Found {len(achievements)} achievements to sync")
            
            # Sync each achievement
            success_count = 0
            for achievement in achievements:
                if await self.sync_achievement(achievement):
                    success_count += 1
            
            await self._log_sync_success("achievement", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("achievement", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def bulk_sync_recognitions(self):
        """
        Synchronize all recognitions from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized recognitions
        """
        await self._log_sync_start("recognition")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            recognition_repo = await repo_factory.get_recognition_repository()
            
            # Get all recognitions
            recognitions = await recognition_repo.get_all()
            logger.info(f"Found {len(recognitions)} recognitions to sync")
            
            # Sync each recognition
            success_count = 0
            for recognition in recognitions:
                if await self.sync_recognition(recognition):
                    success_count += 1
            
            await self._log_sync_success("recognition", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("recognition", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def bulk_sync_degrees(self):
        """
        Synchronize all degrees from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized degrees
        """
        await self._log_sync_start("degree")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            degree_repo = await repo_factory.get_degree_repository()
            
            # Get all degrees
            degrees = await degree_repo.get_all()
            logger.info(f"Found {len(degrees)} degrees to sync")
            
            # Sync each degree
            success_count = 0
            for degree in degrees:
                if await self.sync_degree(degree):
                    success_count += 1
            
            await self._log_sync_success("degree", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("degree", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def bulk_sync_credentials(self):
        """
        Synchronize all credentials from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized credentials
        """
        await self._log_sync_start("credential")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            credential_repo = await repo_factory.get_credential_repository()
            
            # Get all credentials
            credentials = await credential_repo.get_all()
            logger.info(f"Found {len(credentials)} credentials to sync")
            
            # Sync each credential
            success_count = 0
            for credential in credentials:
                if await self.sync_credential(credential):
                    success_count += 1
            
            await self._log_sync_success("credential", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("credential", str(e))
            logger.error(traceback.format_exc())
            return 0 