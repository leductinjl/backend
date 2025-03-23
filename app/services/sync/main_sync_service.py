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

    async def sync_all_entities(self, limit: Optional[int] = None) -> Dict[str, Dict[str, int]]:
        """
        Synchronize all entities between PostgreSQL and Neo4j.
        
        Args:
            limit: Optional limit on the number of entities to sync for each type
        
        Returns:
            A dictionary containing the sync results for each entity type
        """
        logger.info("Starting synchronization of all entities")
        
        # Sync in order of dependencies
        results: Dict[str, Dict[str, int]] = {}
        
        # First sync base entities
        logger.info("Synchronizing subjects")
        subject_result = await self.subject_sync_service.sync_all(limit=limit)
        results["subject"] = {"success": subject_result[0], "failed": subject_result[1]}
        
        logger.info("Synchronizing schools")
        school_result = await self.school_sync_service.sync_all(limit=limit)
        results["school"] = {"success": school_result[0], "failed": school_result[1]}
        
        logger.info("Synchronizing majors")
        major_result = await self.major_sync_service.sync_all(limit=limit)
        results["major"] = {"success": major_result[0], "failed": major_result[1]}
        
        logger.info("Synchronizing management units")
        management_unit_result = await self.management_unit_sync_service.sync_all(limit=limit)
        results["management_unit"] = {"success": management_unit_result[0], "failed": management_unit_result[1]}
        
        logger.info("Synchronizing exam locations")
        exam_location_result = await self.exam_location_sync_service.sync_all(limit=limit)
        results["exam_location"] = {"success": exam_location_result[0], "failed": exam_location_result[1]}
        
        logger.info("Synchronizing exam rooms")
        exam_room_result = await self.exam_room_sync_service.sync_all(limit=limit)
        results["exam_room"] = {"success": exam_room_result[0], "failed": exam_room_result[1]}
        
        logger.info("Synchronizing exams")
        exam_result = await self.exam_sync_service.sync_all(limit=limit)
        results["exam"] = {"success": exam_result[0], "failed": exam_result[1]}
        
        logger.info("Synchronizing candidates")
        candidate_result = await self.candidate_sync_service.sync_all(limit=limit)
        results["candidate"] = {"success": candidate_result[0], "failed": candidate_result[1]}
        
        # Then sync entities that depend on base entities
        logger.info("Synchronizing exam schedules")
        exam_schedule_result = await self.exam_schedule_sync_service.sync_all(limit=limit)
        results["exam_schedule"] = {"success": exam_schedule_result[0], "failed": exam_schedule_result[1]}
        
        logger.info("Synchronizing scores")
        score_result = await self.score_sync_service.sync_all(limit=limit)
        results["score"] = {"success": score_result[0], "failed": score_result[1]}
        
        logger.info("Synchronizing score reviews")
        score_review_result = await self.score_review_sync_service.sync_all(limit=limit)
        results["score_review"] = {"success": score_review_result[0], "failed": score_review_result[1]}
        
        logger.info("Synchronizing achievements")
        achievement_result = await self.achievement_sync_service.sync_all(limit=limit)
        results["achievement"] = {"success": achievement_result[0], "failed": achievement_result[1]}
        
        logger.info("Synchronizing awards")
        award_result = await self.award_sync_service.sync_all(limit=limit)
        results["award"] = {"success": award_result[0], "failed": award_result[1]}
        
        logger.info("Synchronizing certificates")
        certificate_result = await self.certificate_sync_service.sync_all(limit=limit)
        results["certificate"] = {"success": certificate_result[0], "failed": certificate_result[1]}
        
        logger.info("Synchronizing credentials")
        credential_result = await self.credential_sync_service.sync_all(limit=limit)
        results["credential"] = {"success": credential_result[0], "failed": credential_result[1]}
        
        logger.info("Synchronizing degrees")
        degree_result = await self.degree_sync_service.sync_all(limit=limit)
        results["degree"] = {"success": degree_result[0], "failed": degree_result[1]}
        
        logger.info("Synchronizing recognitions")
        recognition_result = await self.recognition_sync_service.sync_all(limit=limit)
        results["recognition"] = {"success": recognition_result[0], "failed": recognition_result[1]}
        
        # Sync school-major relationships now that both schools and majors are synchronized
        logger.info("Synchronizing school-major relationships")
        for school, _ in await self.school_sync_service.sql_repository.get_all(limit=limit):
            await self.school_sync_service.sync_school_majors(school.school_id)
        
        # Log summary
        total_success = sum(result["success"] for result in results.values())
        total_failed = sum(result["failed"] for result in results.values())
        logger.info(f"Synchronization complete. Total: {total_success + total_failed}, Success: {total_success}, Failed: {total_failed}")
        
        return results
    
    async def sync_by_type(self, entity_type: EntityType, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all entities of a specific type.
        
        Args:
            entity_type: The type of entity to synchronize
            limit: Optional limit on the number of entities to sync
        
        Returns:
            A tuple containing the count of successfully synced and failed entities
        """
        if entity_type not in self.sync_services:
            logger.error(f"Unknown entity type: {entity_type}")
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        logger.info(f"Synchronizing all {entity_type} entities")
        result = await self.sync_services[entity_type].sync_all(limit=limit)
        logger.info(f"{entity_type} synchronization complete. Success: {result[0]}, Failed: {result[1]}")
        
        return result
    
    async def sync_entity_by_id(self, entity_type: EntityType, entity_id: str) -> bool:
        """
        Synchronize a specific entity by its ID.
        
        Args:
            entity_type: The type of entity to synchronize
            entity_id: The ID of the entity to synchronize
        
        Returns:
            True if synchronization was successful, False otherwise
        """
        if entity_type not in self.sync_services:
            logger.error(f"Unknown entity type: {entity_type}")
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        logger.info(f"Synchronizing {entity_type} with ID {entity_id}")
        result = await self.sync_services[entity_type].sync_by_id(entity_id)
        
        if result:
            logger.info(f"Successfully synchronized {entity_type} with ID {entity_id}")
        else:
            logger.warning(f"Failed to synchronize {entity_type} with ID {entity_id}")
            
        return result 