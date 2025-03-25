"""
Main Sync Service module.

This module provides the MainSyncService class for orchestrating synchronization
of data between PostgreSQL and Neo4j across different entity types.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple, Literal

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.services.sync.base_sync_service import BaseSyncService
from app.services.sync.subject_sync_service import SubjectSyncService
from app.services.sync.score_sync_service import ScoreSyncService
from app.services.sync.score_review_sync_service import ScoreReviewSyncService
from app.services.sync.exam_sync_service import ExamSyncService
from app.services.sync.candidate_sync_service import CandidateSyncService
from app.services.sync.achievement_sync_service import AchievementSyncService
from app.services.sync.award_sync_service import AwardSyncService
from app.services.sync.certificate_sync_service import CertificateSyncService
from app.services.sync.credential_sync_service import CredentialSyncService
from app.services.sync.degree_sync_service import DegreeSyncService
from app.services.sync.exam_location_sync_service import ExamLocationSyncService
from app.services.sync.exam_room_sync_service import ExamRoomSyncService
from app.services.sync.exam_schedule_sync_service import ExamScheduleSyncService
from app.services.sync.major_sync_service import MajorSyncService
from app.services.sync.management_unit_sync_service import ManagementUnitSyncService
from app.services.sync.recognition_sync_service import RecognitionSyncService
from app.services.sync.school_sync_service import SchoolSyncService

logger = logging.getLogger(__name__)

EntityType = Literal["subject", "score", "score_review", "exam", "candidate", "achievement", "award", "certificate", "credential", "degree", "exam_location", "exam_room", "exam_schedule", "major", "management_unit", "recognition", "school"]

class MainSyncService:
    """
    Main synchronization service that coordinates individual sync services.
    
    This service provides methods to synchronize data between PostgreSQL and Neo4j
    for all entity types or specific entity types, with clear separation between
    node synchronization and relationship synchronization.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        subject_sync_service: Optional[SubjectSyncService] = None,
        score_sync_service: Optional[ScoreSyncService] = None,
        score_review_sync_service: Optional[ScoreReviewSyncService] = None,
        exam_sync_service: Optional[ExamSyncService] = None,
        candidate_sync_service: Optional[CandidateSyncService] = None,
        achievement_sync_service: Optional[AchievementSyncService] = None,
        award_sync_service: Optional[AwardSyncService] = None,
        certificate_sync_service: Optional[CertificateSyncService] = None,
        credential_sync_service: Optional[CredentialSyncService] = None,
        degree_sync_service: Optional[DegreeSyncService] = None,
        exam_location_sync_service: Optional[ExamLocationSyncService] = None,
        exam_room_sync_service: Optional[ExamRoomSyncService] = None,
        exam_schedule_sync_service: Optional[ExamScheduleSyncService] = None,
        major_sync_service: Optional[MajorSyncService] = None,
        management_unit_sync_service: Optional[ManagementUnitSyncService] = None,
        recognition_sync_service: Optional[RecognitionSyncService] = None,
        school_sync_service: Optional[SchoolSyncService] = None,
    ):
        """
        Initialize the MainSyncService with individual sync services.
        
        Args:
            session: The SQLAlchemy async session
            driver: The Neo4j async driver
            subject_sync_service: Optional SubjectSyncService instance
            score_sync_service: Optional ScoreSyncService instance
            score_review_sync_service: Optional ScoreReviewSyncService instance
            exam_sync_service: Optional ExamSyncService instance
            candidate_sync_service: Optional CandidateSyncService instance
            achievement_sync_service: Optional AchievementSyncService instance
            award_sync_service: Optional AwardSyncService instance
            certificate_sync_service: Optional CertificateSyncService instance
            credential_sync_service: Optional CredentialSyncService instance
            degree_sync_service: Optional DegreeSyncService instance
            exam_location_sync_service: Optional ExamLocationSyncService instance
            exam_room_sync_service: Optional ExamRoomSyncService instance
            exam_schedule_sync_service: Optional ExamScheduleSyncService instance
            major_sync_service: Optional MajorSyncService instance
            management_unit_sync_service: Optional ManagementUnitSyncService instance
            recognition_sync_service: Optional RecognitionSyncService instance
            school_sync_service: Optional SchoolSyncService instance
        """
        # Initialize individual sync services if not provided
        self.subject_sync_service = subject_sync_service or SubjectSyncService(session, driver)
        self.score_sync_service = score_sync_service or ScoreSyncService(session, driver)
        self.score_review_sync_service = score_review_sync_service or ScoreReviewSyncService(session, driver)
        self.exam_sync_service = exam_sync_service or ExamSyncService(session, driver)
        self.candidate_sync_service = candidate_sync_service or CandidateSyncService(session, driver)
        self.achievement_sync_service = achievement_sync_service or AchievementSyncService(session, driver)
        self.award_sync_service = award_sync_service or AwardSyncService(session, driver)
        self.certificate_sync_service = certificate_sync_service or CertificateSyncService(session, driver)
        self.credential_sync_service = credential_sync_service or CredentialSyncService(session, driver)
        self.degree_sync_service = degree_sync_service or DegreeSyncService(session, driver)
        self.exam_location_sync_service = exam_location_sync_service or ExamLocationSyncService(session, driver)
        self.exam_room_sync_service = exam_room_sync_service or ExamRoomSyncService(session, driver)
        self.exam_schedule_sync_service = exam_schedule_sync_service or ExamScheduleSyncService(session, driver)
        self.major_sync_service = major_sync_service or MajorSyncService(session, driver)
        self.management_unit_sync_service = management_unit_sync_service or ManagementUnitSyncService(session, driver)
        self.recognition_sync_service = recognition_sync_service or RecognitionSyncService(session, driver)
        self.school_sync_service = school_sync_service or SchoolSyncService(session, driver)
        
        # Map entity types to their sync services
        self.sync_services = {
            "subject": self.subject_sync_service,
            "score": self.score_sync_service,
            "score_review": self.score_review_sync_service,
            "exam": self.exam_sync_service,
            "candidate": self.candidate_sync_service,
            "achievement": self.achievement_sync_service,
            "award": self.award_sync_service,
            "certificate": self.certificate_sync_service,
            "credential": self.credential_sync_service,
            "degree": self.degree_sync_service,
            "exam_location": self.exam_location_sync_service,
            "exam_room": self.exam_room_sync_service,
            "exam_schedule": self.exam_schedule_sync_service,
            "major": self.major_sync_service,
            "management_unit": self.management_unit_sync_service,
            "recognition": self.recognition_sync_service,
            "school": self.school_sync_service
        }

    async def sync_all_nodes(self, limit: Optional[int] = None) -> Dict[str, Dict[str, int]]:
        """
        Synchronize all entity nodes between PostgreSQL and Neo4j without their relationships.
        
        Args:
            limit: Optional limit on the number of entities to sync for each type
        
        Returns:
            A dictionary containing the sync results for each entity type
        """
        logger.info("Starting synchronization of all entity nodes")
        
        # Sync in order of dependencies
        results: Dict[str, Dict[str, int]] = {}
        
        # First sync base entities
        logger.info("Synchronizing subjects")
        subject_result = await self.subject_sync_service.sync_all_nodes(limit=limit)
        if isinstance(subject_result, tuple) and len(subject_result) >= 2:
            results["subject"] = {"success": subject_result[0], "failed": subject_result[1]}
        elif isinstance(subject_result, dict):
            results["subject"] = subject_result
        else:
            results["subject"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing schools")
        school_result = await self.school_sync_service.sync_all_nodes(limit=limit)
        if isinstance(school_result, tuple) and len(school_result) >= 2:
            results["school"] = {"success": school_result[0], "failed": school_result[1]}
        elif isinstance(school_result, dict):
            results["school"] = school_result
        else:
            results["school"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing majors")
        major_result = await self.major_sync_service.sync_all_nodes(limit=limit)
        if isinstance(major_result, tuple) and len(major_result) >= 2:
            results["major"] = {"success": major_result[0], "failed": major_result[1]}
        elif isinstance(major_result, dict):
            results["major"] = major_result
        else:
            results["major"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing management units")
        management_unit_result = await self.management_unit_sync_service.sync_all_nodes(limit=limit)
        if isinstance(management_unit_result, tuple) and len(management_unit_result) >= 2:
            results["management_unit"] = {"success": management_unit_result[0], "failed": management_unit_result[1]}
        elif isinstance(management_unit_result, dict):
            results["management_unit"] = management_unit_result
        else:
            results["management_unit"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing exam locations")
        exam_location_result = await self.exam_location_sync_service.sync_all_nodes(limit=limit)
        if isinstance(exam_location_result, tuple) and len(exam_location_result) >= 2:
            results["exam_location"] = {"success": exam_location_result[0], "failed": exam_location_result[1]}
        elif isinstance(exam_location_result, dict):
            results["exam_location"] = exam_location_result
        else:
            results["exam_location"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing exam rooms")
        exam_room_result = await self.exam_room_sync_service.sync_all_nodes(limit=limit)
        if isinstance(exam_room_result, tuple) and len(exam_room_result) >= 2:
            results["exam_room"] = {"success": exam_room_result[0], "failed": exam_room_result[1]}
        elif isinstance(exam_room_result, dict):
            results["exam_room"] = exam_room_result
        else:
            results["exam_room"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing exams")
        exam_result = await self.exam_sync_service.sync_all_nodes(limit=limit)
        if isinstance(exam_result, tuple) and len(exam_result) >= 2:
            results["exam"] = {"success": exam_result[0], "failed": exam_result[1]}
        elif isinstance(exam_result, dict):
            results["exam"] = exam_result
        else:
            results["exam"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing candidates")
        candidate_result = await self.candidate_sync_service.sync_all_nodes(limit=limit)
        if isinstance(candidate_result, tuple) and len(candidate_result) >= 2:
            results["candidate"] = {"success": candidate_result[0], "failed": candidate_result[1]}
        elif isinstance(candidate_result, dict):
            results["candidate"] = candidate_result
        else:
            results["candidate"] = {"success": 0, "failed": 0}
        
        # Then sync entities that depend on base entities
        logger.info("Synchronizing exam schedules")
        exam_schedule_result = await self.exam_schedule_sync_service.sync_all_nodes(limit=limit)
        if isinstance(exam_schedule_result, tuple) and len(exam_schedule_result) >= 2:
            results["exam_schedule"] = {"success": exam_schedule_result[0], "failed": exam_schedule_result[1]}
        elif isinstance(exam_schedule_result, dict):
            results["exam_schedule"] = exam_schedule_result
        else:
            results["exam_schedule"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing scores")
        score_result = await self.score_sync_service.sync_all_nodes(limit=limit)
        if isinstance(score_result, tuple) and len(score_result) >= 2:
            results["score"] = {"success": score_result[0], "failed": score_result[1]}
        elif isinstance(score_result, dict):
            results["score"] = score_result
        else:
            results["score"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing score reviews")
        score_review_result = await self.score_review_sync_service.sync_all_nodes(limit=limit)
        if isinstance(score_review_result, tuple) and len(score_review_result) >= 2:
            results["score_review"] = {"success": score_review_result[0], "failed": score_review_result[1]}
        elif isinstance(score_review_result, dict):
            results["score_review"] = score_review_result
        else:
            results["score_review"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing achievements")
        achievement_result = await self.achievement_sync_service.sync_all_nodes(limit=limit)
        if isinstance(achievement_result, tuple) and len(achievement_result) >= 2:
            results["achievement"] = {"success": achievement_result[0], "failed": achievement_result[1]}
        elif isinstance(achievement_result, dict):
            results["achievement"] = achievement_result
        else:
            results["achievement"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing awards")
        award_result = await self.award_sync_service.sync_all_nodes(limit=limit)
        if isinstance(award_result, tuple) and len(award_result) >= 2:
            results["award"] = {"success": award_result[0], "failed": award_result[1]}
        elif isinstance(award_result, dict):
            results["award"] = award_result
        else:
            results["award"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing certificates")
        certificate_result = await self.certificate_sync_service.sync_all_nodes(limit=limit)
        if isinstance(certificate_result, tuple) and len(certificate_result) >= 2:
            results["certificate"] = {"success": certificate_result[0], "failed": certificate_result[1]}
        elif isinstance(certificate_result, dict):
            results["certificate"] = certificate_result
        else:
            results["certificate"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing credentials")
        credential_result = await self.credential_sync_service.sync_all_nodes(limit=limit)
        if isinstance(credential_result, tuple) and len(credential_result) >= 2:
            results["credential"] = {"success": credential_result[0], "failed": credential_result[1]}
        elif isinstance(credential_result, dict):
            results["credential"] = credential_result
        else:
            results["credential"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing degrees")
        degree_result = await self.degree_sync_service.sync_all_nodes(limit=limit)
        if isinstance(degree_result, tuple) and len(degree_result) >= 2:
            results["degree"] = {"success": degree_result[0], "failed": degree_result[1]}
        elif isinstance(degree_result, dict):
            results["degree"] = degree_result
        else:
            results["degree"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing recognitions")
        recognition_result = await self.recognition_sync_service.sync_all_nodes(limit=limit)
        if isinstance(recognition_result, tuple) and len(recognition_result) >= 2:
            results["recognition"] = {"success": recognition_result[0], "failed": recognition_result[1]}
        elif isinstance(recognition_result, dict):
            results["recognition"] = recognition_result
        else:
            results["recognition"] = {"success": 0, "failed": 0}
        
        # Log summary
        total_success = sum(result["success"] for result in results.values())
        total_failed = sum(result["failed"] for result in results.values())
        logger.info(f"Node synchronization complete. Total: {total_success + total_failed}, Success: {total_success}, Failed: {total_failed}")
        
        return results
    
    async def sync_all_relationships(self, entity_type: Optional[EntityType] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Sync relationships for all entities of a specific type or all entity types.
        
        This method synchronizes relationships between entities without re-creating
        the entity nodes themselves. Useful for repairing or updating the graph
        after structure changes.
        
        Args:
            entity_type: Optional entity type to sync relationships for.
                         If None, sync relationships for all supported entity types.
            limit: Optional maximum number of entities to process per type
            
        Returns:
            Dictionary with sync results by entity type
        """
        logger.info(f"Starting synchronization of relationships for {'all entity types' if entity_type is None else entity_type}")
        
        results = {}
        
        try:
            # If specific entity type is provided, only sync that type
            if entity_type is not None:
                if entity_type not in self.sync_services:
                    raise ValueError(f"Unknown entity type: {entity_type}")
                
                # Check if the entity type supports relationship synchronization
                if not hasattr(self.sync_services[entity_type], "sync_all_relationships"):
                    raise NotImplementedError(f"Entity type {entity_type} does not support sync_all_relationships")
                    
                # Call the service's sync_all_relationships method
                results[entity_type] = await self.sync_services[entity_type].sync_all_relationships(limit=limit)
            else:
                # Sync all entity types with relationship support
                for etype, service in self.sync_services.items():
                    if hasattr(service, "sync_all_relationships"):
                        logger.info(f"Synchronizing relationships for all {etype} entities")
                        results[etype] = await service.sync_all_relationships(limit=limit)
                
            logger.info(f"Relationship synchronization complete for {len(results)} entity types")
            return results
            
        except Exception as e:
            logger.error(f"Error during relationship synchronization: {str(e)}")
            return {
                "error": str(e)
            }
    
    async def sync_nodes_by_type(self, entity_type: EntityType, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all nodes of a specific entity type.
        
        Args:
            entity_type: The type of entity to synchronize
            limit: Optional limit on the number of entities to sync
        
        Returns:
            A tuple containing the count of successfully synced and failed entities
        """
        if entity_type not in self.sync_services:
            logger.error(f"Unknown entity type: {entity_type}")
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        logger.info(f"Synchronizing all {entity_type} nodes")
        
        # Sync the nodes
        result = await self.sync_services[entity_type].sync_all_nodes(limit=limit)
        
        # Handle different result formats (could be tuple or dict)
        success_count = 0
        failed_count = 0
        
        if isinstance(result, tuple) and len(result) >= 2:
            success_count, failed_count = result[0], result[1]
        elif isinstance(result, dict) and "success" in result and "failed" in result:
            success_count, failed_count = result["success"], result["failed"]
        
        logger.info(f"{entity_type} node synchronization complete. Success: {success_count}, Failed: {failed_count}")
        
        return (success_count, failed_count)
    
    async def sync_relationships_by_type(self, entity_type: EntityType, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Synchronize relationships for all entities of a specific type.
        
        Args:
            entity_type: The type of entity to synchronize relationships for
            limit: Optional limit on the number of entities to process
            
        Returns:
            Dictionary with sync results
        """
        if entity_type not in self.sync_services:
            logger.error(f"Unknown entity type: {entity_type}")
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Check if the entity type supports relationship synchronization
        if not hasattr(self.sync_services[entity_type], "sync_all_relationships"):
            error_msg = f"Entity type {entity_type} does not support sync_all_relationships"
            logger.error(error_msg)
            raise NotImplementedError(error_msg)
        
        logger.info(f"Synchronizing relationships for all {entity_type} entities")
        
        # Call the service's sync_all_relationships method
        result = await self.sync_services[entity_type].sync_all_relationships(limit=limit)
        
        logger.info(f"{entity_type} relationship synchronization complete")
        return result
    
    async def sync_node_by_id(self, entity_type: EntityType, entity_id: str) -> bool:
        """
        Synchronize a specific entity node by its ID.
        
        Args:
            entity_type: The type of entity to synchronize
            entity_id: The ID of the entity to synchronize
        
        Returns:
            True if synchronization was successful, False otherwise
        """
        if entity_type not in self.sync_services:
            logger.error(f"Unknown entity type: {entity_type}")
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        logger.info(f"Synchronizing {entity_type} node with ID {entity_id}")
        
        # Sync the node
        result = await self.sync_services[entity_type].sync_node_by_id(entity_id)
        
        if result:
            logger.info(f"Successfully synchronized {entity_type} node with ID {entity_id}")
        else:
            logger.warning(f"Failed to synchronize {entity_type} node with ID {entity_id}")
            
        return result
    
    async def sync_relationship_by_id(self, entity_type: EntityType, entity_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific entity by its ID.
        
        Args:
            entity_type: The type of entity to synchronize relationships for
            entity_id: The ID of the entity
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        if entity_type not in self.sync_services:
            logger.error(f"Unknown entity type: {entity_type}")
            raise ValueError(f"Unknown entity type: {entity_type}")
            
        if not hasattr(self.sync_services[entity_type], "sync_relationship_by_id"):
            error_msg = f"Entity type {entity_type} does not support relationship synchronization"
            logger.error(error_msg)
            raise NotImplementedError(error_msg)
        
        logger.info(f"Synchronizing relationships for {entity_type} with ID {entity_id}")
        results = await self.sync_services[entity_type].sync_relationship_by_id(entity_id)
        
        logger.info(f"Successfully synchronized relationships for {entity_type} {entity_id}")
        return results
    
    # For compatibility with legacy code - these methods forward to the new methods
    async def sync_all_entities(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Dict[str, Dict[str, int]]:
        """
        Synchronize all entities between PostgreSQL and Neo4j.
        
        This is a legacy method for compatibility. It calls sync_all_nodes() and optionally sync_all_relationships().
        
        Args:
            limit: Optional limit on the number of entities to sync for each type
            skip_relationships: If True, only sync nodes without their relationships
        
        Returns:
            A dictionary containing the sync results for each entity type
        """
        logger.info(f"Starting synchronization of all entities (skip_relationships={skip_relationships})")
        
        # First sync all nodes
        results = await self.sync_all_nodes(limit=limit)
        
        # Then sync relationships if not skipped
        if not skip_relationships:
            relationship_results = await self.sync_all_relationships(limit=limit)
            
            # Add relationship results to entity results if available
            for entity_type, rel_result in relationship_results.items():
                if entity_type in results and isinstance(rel_result, dict):
                    results[entity_type]["relationships"] = rel_result.get("relationships", {})
        
        return results
    
    async def sync_by_type(self, entity_type: EntityType, limit: Optional[int] = None, skip_relationships: bool = False) -> Tuple[int, int]:
        """
        Synchronize all entities of a specific type.
        
        This is a legacy method for compatibility. It calls sync_nodes_by_type() and optionally sync_relationships_by_type().
        
        Args:
            entity_type: The type of entity to synchronize
            limit: Optional limit on the number of entities to sync
            skip_relationships: If True, only sync nodes without their relationships
        
        Returns:
            A tuple containing the count of successfully synced and failed entities
        """
        # Sync the nodes
        success_count, failed_count = await self.sync_nodes_by_type(entity_type, limit=limit)
        
        # Then sync relationships if not skipped
        if not skip_relationships and hasattr(self.sync_services[entity_type], "sync_all_relationships"):
            await self.sync_relationships_by_type(entity_type, limit=limit)
        
        return (success_count, failed_count)
    
    async def sync_entity_by_id(self, entity_type: EntityType, entity_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific entity by its ID.
        
        This is a legacy method for compatibility. It calls sync_node_by_id() and optionally sync_relationship_by_id().
        
        Args:
            entity_type: The type of entity to synchronize
            entity_id: The ID of the entity to synchronize
            skip_relationships: If True, only sync nodes without their relationships
        
        Returns:
            True if node synchronization was successful, False otherwise
        """
        # Sync the node
        result = await self.sync_node_by_id(entity_type, entity_id)
        
        # If node sync succeeded and relationships should be synced
        if result and not skip_relationships and hasattr(self.sync_services[entity_type], "sync_relationship_by_id"):
            await self.sync_relationship_by_id(entity_type, entity_id)
        
        return result 