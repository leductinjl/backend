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
    for all entity types or specific entity types.
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

    async def sync_all_entities(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Dict[str, Dict[str, int]]:
        """
        Synchronize all entities between PostgreSQL and Neo4j.
        
        Args:
            limit: Optional limit on the number of entities to sync for each type
            skip_relationships: If True, only sync nodes without their relationships
        
        Returns:
            A dictionary containing the sync results for each entity type
        """
        logger.info(f"Starting synchronization of all entities (skip_relationships={skip_relationships})")
        
        # Sync in order of dependencies
        results: Dict[str, Dict[str, int]] = {}
        
        # First sync base entities
        logger.info("Synchronizing subjects")
        subject_result = await self.subject_sync_service.sync_all(limit=limit)
        if isinstance(subject_result, tuple) and len(subject_result) >= 2:
            results["subject"] = {"success": subject_result[0], "failed": subject_result[1]}
        elif isinstance(subject_result, dict):
            results["subject"] = subject_result
        else:
            results["subject"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing schools")
        school_result = await self.school_sync_service.sync_all(limit=limit)
        if isinstance(school_result, tuple) and len(school_result) >= 2:
            results["school"] = {"success": school_result[0], "failed": school_result[1]}
        elif isinstance(school_result, dict):
            results["school"] = school_result
        else:
            results["school"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing majors")
        major_result = await self.major_sync_service.sync_all(limit=limit)
        if isinstance(major_result, tuple) and len(major_result) >= 2:
            results["major"] = {"success": major_result[0], "failed": major_result[1]}
        elif isinstance(major_result, dict):
            results["major"] = major_result
        else:
            results["major"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing management units")
        management_unit_result = await self.management_unit_sync_service.sync_all(limit=limit)
        if isinstance(management_unit_result, tuple) and len(management_unit_result) >= 2:
            results["management_unit"] = {"success": management_unit_result[0], "failed": management_unit_result[1]}
        elif isinstance(management_unit_result, dict):
            results["management_unit"] = management_unit_result
        else:
            results["management_unit"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing exam locations")
        exam_location_result = await self.exam_location_sync_service.sync_all(limit=limit)
        if isinstance(exam_location_result, tuple) and len(exam_location_result) >= 2:
            results["exam_location"] = {"success": exam_location_result[0], "failed": exam_location_result[1]}
        elif isinstance(exam_location_result, dict):
            results["exam_location"] = exam_location_result
        else:
            results["exam_location"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing exam rooms")
        exam_room_result = await self.exam_room_sync_service.sync_all(limit=limit)
        if isinstance(exam_room_result, tuple) and len(exam_room_result) >= 2:
            results["exam_room"] = {"success": exam_room_result[0], "failed": exam_room_result[1]}
        elif isinstance(exam_room_result, dict):
            results["exam_room"] = exam_room_result
        else:
            results["exam_room"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing exams")
        exam_result = await self.exam_sync_service.sync_all(limit=limit)
        if isinstance(exam_result, tuple) and len(exam_result) >= 2:
            results["exam"] = {"success": exam_result[0], "failed": exam_result[1]}
        elif isinstance(exam_result, dict):
            results["exam"] = exam_result
        else:
            results["exam"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing candidates")
        candidate_result = await self.candidate_sync_service.sync_all(limit=limit)
        if isinstance(candidate_result, tuple) and len(candidate_result) >= 2:
            results["candidate"] = {"success": candidate_result[0], "failed": candidate_result[1]}
        elif isinstance(candidate_result, dict):
            results["candidate"] = candidate_result
        else:
            results["candidate"] = {"success": 0, "failed": 0}
        
        # Then sync entities that depend on base entities
        logger.info("Synchronizing exam schedules")
        exam_schedule_result = await self.exam_schedule_sync_service.sync_all(limit=limit)
        if isinstance(exam_schedule_result, tuple) and len(exam_schedule_result) >= 2:
            results["exam_schedule"] = {"success": exam_schedule_result[0], "failed": exam_schedule_result[1]}
        elif isinstance(exam_schedule_result, dict):
            results["exam_schedule"] = exam_schedule_result
        else:
            results["exam_schedule"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing scores")
        score_result = await self.score_sync_service.sync_all(limit=limit)
        if isinstance(score_result, tuple) and len(score_result) >= 2:
            results["score"] = {"success": score_result[0], "failed": score_result[1]}
        elif isinstance(score_result, dict):
            results["score"] = score_result
        else:
            results["score"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing score reviews")
        score_review_result = await self.score_review_sync_service.sync_all(limit=limit)
        if isinstance(score_review_result, tuple) and len(score_review_result) >= 2:
            results["score_review"] = {"success": score_review_result[0], "failed": score_review_result[1]}
        elif isinstance(score_review_result, dict):
            results["score_review"] = score_review_result
        else:
            results["score_review"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing achievements")
        achievement_result = await self.achievement_sync_service.sync_all(limit=limit)
        if isinstance(achievement_result, tuple) and len(achievement_result) >= 2:
            results["achievement"] = {"success": achievement_result[0], "failed": achievement_result[1]}
        elif isinstance(achievement_result, dict):
            results["achievement"] = achievement_result
        else:
            results["achievement"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing awards")
        award_result = await self.award_sync_service.sync_all(limit=limit)
        if isinstance(award_result, tuple) and len(award_result) >= 2:
            results["award"] = {"success": award_result[0], "failed": award_result[1]}
        elif isinstance(award_result, dict):
            results["award"] = award_result
        else:
            results["award"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing certificates")
        certificate_result = await self.certificate_sync_service.sync_all(limit=limit)
        if isinstance(certificate_result, tuple) and len(certificate_result) >= 2:
            results["certificate"] = {"success": certificate_result[0], "failed": certificate_result[1]}
        elif isinstance(certificate_result, dict):
            results["certificate"] = certificate_result
        else:
            results["certificate"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing credentials")
        credential_result = await self.credential_sync_service.sync_all(limit=limit)
        if isinstance(credential_result, tuple) and len(credential_result) >= 2:
            results["credential"] = {"success": credential_result[0], "failed": credential_result[1]}
        elif isinstance(credential_result, dict):
            results["credential"] = credential_result
        else:
            results["credential"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing degrees")
        degree_result = await self.degree_sync_service.sync_all(limit=limit)
        if isinstance(degree_result, tuple) and len(degree_result) >= 2:
            results["degree"] = {"success": degree_result[0], "failed": degree_result[1]}
        elif isinstance(degree_result, dict):
            results["degree"] = degree_result
        else:
            results["degree"] = {"success": 0, "failed": 0}
        
        logger.info("Synchronizing recognitions")
        recognition_result = await self.recognition_sync_service.sync_all(limit=limit)
        if isinstance(recognition_result, tuple) and len(recognition_result) >= 2:
            results["recognition"] = {"success": recognition_result[0], "failed": recognition_result[1]}
        elif isinstance(recognition_result, dict):
            results["recognition"] = recognition_result
        else:
            results["recognition"] = {"success": 0, "failed": 0}
        
        # Sync school-major relationships now that both schools and majors are synchronized
        if not skip_relationships:
            logger.info("Synchronizing school-major relationships")
            school_results, _ = await self.school_sync_service.sql_repository.get_all(limit=limit)
            for school in school_results:
                await self.school_sync_service.sync_school_majors(school.school_id)
        else:
            logger.info("Skipping school-major relationships as requested")
        
        # Log summary
        total_success = sum(result["success"] for result in results.values())
        total_failed = sum(result["failed"] for result in results.values())
        logger.info(f"Synchronization complete. Total: {total_success + total_failed}, Success: {total_success}, Failed: {total_failed}")
        
        return results
    
    async def sync_by_type(self, entity_type: EntityType, limit: Optional[int] = None, skip_relationships: bool = False) -> Tuple[int, int]:
        """
        Synchronize all entities of a specific type.
        
        Args:
            entity_type: The type of entity to synchronize
            limit: Optional limit on the number of entities to sync
            skip_relationships: If True, only sync nodes without their relationships
        
        Returns:
            A tuple containing the count of successfully synced and failed entities
        """
        if entity_type not in self.sync_services:
            logger.error(f"Unknown entity type: {entity_type}")
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        logger.info(f"Synchronizing all {entity_type} entities (skip_relationships={skip_relationships})")
        
        # First sync the nodes
        result = await self.sync_services[entity_type].sync_all(limit=limit, skip_relationships=skip_relationships)
        
        # Handle different result formats (could be tuple or dict)
        success_count = 0
        failed_count = 0
        
        if isinstance(result, tuple) and len(result) >= 2:
            success_count, failed_count = result[0], result[1]
        elif isinstance(result, dict) and "success" in result and "failed" in result:
            success_count, failed_count = result["success"], result["failed"]
        
        # Then sync relationships if needed
        if not skip_relationships and hasattr(self.sync_services[entity_type], "sync_relationships"):
            logger.info(f"Synchronizing {entity_type} relationships")
            # Since we're syncing by type, only entities of this type should have been created
            # We get all of them from the SQL database and sync their relationships
            if entity_type == "school":
                # Special handling for school-major relationships
                school_results, _ = await self.school_sync_service.sql_repository.get_all(limit=limit)
                for school in school_results:
                    await self.school_sync_service.sync_school_majors(school.school_id)
            elif entity_type == "candidate":
                # For candidates, use the dedicated method
                await self.sync_all_candidate_relationships(limit=limit)
        
        logger.info(f"{entity_type} synchronization complete. Success: {success_count}, Failed: {failed_count}")
        
        return (success_count, failed_count)
    
    async def sync_entity_by_id(self, entity_type: EntityType, entity_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific entity by its ID.
        
        Args:
            entity_type: The type of entity to synchronize
            entity_id: The ID of the entity to synchronize
            skip_relationships: If True, only sync node without its relationships
        
        Returns:
            True if synchronization was successful, False otherwise
        """
        if entity_type not in self.sync_services:
            logger.error(f"Unknown entity type: {entity_type}")
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        logger.info(f"Synchronizing {entity_type} with ID {entity_id} (skip_relationships={skip_relationships})")
        result = await self.sync_services[entity_type].sync_by_id(entity_id, skip_relationships=skip_relationships)
        
        if result:
            logger.info(f"Successfully synchronized {entity_type} with ID {entity_id}")
        else:
            logger.warning(f"Failed to synchronize {entity_type} with ID {entity_id}")
            
        return result
    
    async def sync_all_candidate_relationships(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Sync relationships for all candidates that already exist in Neo4j.
        
        This method synchronizes relationships between candidates and related entities
        without re-creating the candidate nodes themselves. Useful for repairing or
        updating the graph after structure changes.
        
        Args:
            limit: Optional maximum number of candidates to process
            
        Returns:
            Dictionary with sync results
        """
        logger.info("Starting synchronization of relationships for all candidates")
        
        try:
            # Get candidate IDs from the database
            candidate_ids = []
            
            # Get all candidates with pagination
            candidates, _ = await self.candidate_sync_service.sql_repository.get_all(
                limit=limit or 100
            )
            
            for candidate in candidates:
                candidate_ids.append(candidate.candidate_id)
            
            logger.info(f"Found {len(candidate_ids)} candidates to sync relationships for")
            
            # For each candidate, sync relationships
            success_count = 0
            failure_count = 0
            relationship_counts = {
                "schools": 0,
                "majors": 0,
                "degrees": 0,
                "exams": 0,
                "scores": 0,
                "schedules": 0,
                "certificates": 0,
                "credentials": 0,
                "awards": 0,
                "achievements": 0,
                "recognitions": 0
            }
            
            for candidate_id in candidate_ids:
                try:
                    # Verify candidate exists in Neo4j
                    candidate_node = await self.candidate_sync_service.graph_repository.get_by_id(candidate_id)
                    if not candidate_node:
                        logger.warning(f"Candidate {candidate_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships
                    results = await self.candidate_sync_service.sync_relationships(candidate_id)
                    
                    # Update counters
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    logger.info(f"Successfully synchronized relationships for candidate {candidate_id}")
                    
                except Exception as e:
                    logger.error(f"Error synchronizing relationships for candidate {candidate_id}: {e}")
                    failure_count += 1
            
            results = {
                "total_candidates": len(candidate_ids),
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Candidate relationship synchronization complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error during candidate relationship synchronization: {str(e)}")
            return {
                "success": 0, 
                "failed": 0,
                "error": str(e)
            }

    async def sync_entity_relationships(self, entity_type: EntityType, entity_id: str) -> Dict[str, int]:
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
            
        if not hasattr(self.sync_services[entity_type], "sync_relationships"):
            logger.error(f"Entity type {entity_type} does not support relationship synchronization")
            raise NotImplementedError(f"Entity type {entity_type} does not support relationship synchronization")
        
        logger.info(f"Synchronizing relationships for {entity_type} with ID {entity_id}")
        results = await self.sync_services[entity_type].sync_relationships(entity_id)
        
        logger.info(f"Successfully synchronized relationships for {entity_type} {entity_id}")
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
                if not hasattr(self.sync_services[entity_type], "sync_relationships"):
                    raise NotImplementedError(f"Entity type {entity_type} does not support relationship synchronization")
                    
                entity_types_to_sync = [entity_type]
            else:
                # Sync all entity types with relationship support
                entity_types_to_sync = []
                for etype, service in self.sync_services.items():
                    if hasattr(service, "sync_relationships"):
                        entity_types_to_sync.append(etype)
            
            # Process each entity type
            for etype in entity_types_to_sync:
                if etype == "candidate":
                    candidate_results = await self.sync_all_candidate_relationships(limit)
                    results["candidate"] = candidate_results
                # Add other entity types here as they are implemented
                # The pattern would be similar: call a specialized sync_all_{entity_type}_relationships method
                
            logger.info(f"Relationship synchronization complete for {len(results)} entity types")
            return results
            
        except Exception as e:
            logger.error(f"Error during relationship synchronization: {str(e)}")
            return {
                "error": str(e)
            } 