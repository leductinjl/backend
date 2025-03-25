"""
Candidate Sync Service module.

This module provides the CandidateSyncService class for synchronizing Candidate data
between PostgreSQL and Neo4j.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.services.sync.base_sync_service import BaseSyncService
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_exam_repository import CandidateExamRepository
from app.repositories.education_history_repository import EducationHistoryRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.candidate_credential_repository import CandidateCredentialRepository
from app.repositories.degree_repository import DegreeRepository
from app.repositories.award_repository import AwardRepository
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.recognition_repository import RecognitionRepository
from app.repositories.candidate_exam_subject_repository import CandidateExamSubjectRepository
from app.repositories.exam_schedule_repository import ExamScheduleRepository
from app.graph_repositories.candidate_graph_repository import CandidateGraphRepository
from app.domain.graph_models.candidate_node import CandidateNode
from app.domain.models.candidate import Candidate

logger = logging.getLogger(__name__)

class CandidateSyncService(BaseSyncService):
    """
    Service for synchronizing Candidate data between PostgreSQL and Neo4j.
    
    This service retrieves Candidate data from a PostgreSQL database
    and creates or updates corresponding nodes in a Neo4j graph database,
    ensuring the proper ontology relationships are established.
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        neo4j_driver: AsyncDriver,
        sql_repository: Optional[CandidateRepository] = None,
        graph_repository: Optional[CandidateGraphRepository] = None
    ):
        """
        Initialize the Candidate sync service.
        
        Args:
            db_session: SQLAlchemy async session
            neo4j_driver: Neo4j async driver
            sql_repository: Optional CandidateRepository instance
            graph_repository: Optional CandidateGraphRepository instance
        """
        super().__init__(db_session, neo4j_driver, sql_repository, graph_repository)
        
        # Initialize repositories if not provided
        self.sql_repository = sql_repository or CandidateRepository(db_session)
        self.graph_repository = graph_repository or CandidateGraphRepository(neo4j_driver)
    
        # Additional repositories for relationships
        self.candidate_exam_repository = CandidateExamRepository(db_session)
        self.education_history_repository = EducationHistoryRepository(db_session)
        self.exam_score_repository = ExamScoreRepository(db_session)
        self.certificate_repository = None  # Will be lazily initialized if needed
        self.credential_repository = None   # Will be lazily initialized if needed
        self.degree_repository = None       # Will be lazily initialized if needed
        self.award_repository = None        # Will be lazily initialized if needed
        self.achievement_repository = None  # Will be lazily initialized if needed
        self.recognition_repository = None  # Will be lazily initialized if needed
        self.candidate_exam_subject_repository = None  # Will be lazily initialized if needed
        self.exam_schedule_repository = None  # Will be lazily initialized if needed
    
    async def sync_node_by_id(self, candidate_id: str) -> bool:
        """
        Synchronize a specific candidate node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            candidate_id: The ID of the candidate to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing candidate node {candidate_id}")
        
        try:
            # Get candidate from SQL database with personal info
            candidate = await self.sql_repository.get_by_id_with_personal_info(candidate_id)
            if not candidate:
                logger.error(f"Candidate {candidate_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(candidate)
            
            # Create or update node in Neo4j (this automatically creates the INSTANCE_OF relationship)
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized candidate node {candidate_id}")
            return result
                
        except Exception as e:
            logger.error(f"Error syncing candidate node {candidate_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all candidate nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of candidates to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all candidate nodes (limit={limit})")
        
        try:
            # Get all candidates from SQL database with personal info
            candidates = await self.sql_repository.get_all(limit=limit, include_personal_info=True)
            if isinstance(candidates, tuple) and len(candidates) == 2:
                candidates, _ = candidates
            
            success_count = 0
            failed_count = 0
            
            for candidate in candidates:
                try:
                    # Sync only the candidate node
                    if await self.sync_node_by_id(candidate.candidate_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error syncing candidate node {candidate.candidate_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing candidate nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during candidate nodes synchronization: {e}")
            return (0, 0)
    
    async def sync_relationship_by_id(self, candidate_id: str) -> Dict[str, int]:
        """
        Synchronize all relationships for a specific candidate.
        
        This method establishes connections between a candidate and:
        1. Credentials, certificates, awards, achievements, recognitions
        2. Majors, schools, degrees
        3. Exams
        4. Exam schedules, scores, subjects
        
        Args:
            candidate_id: ID of the candidate
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for candidate {candidate_id}")
        
        # Check if candidate node exists before syncing relationships
        candidate_node = await self.graph_repository.get_by_id(candidate_id)
        if not candidate_node:
            logger.warning(f"Candidate node {candidate_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Candidate node not found in Neo4j",
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
            
        results = {
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
        
        try:
            # 1. Sync education histories (schools and majors)
            education_histories, _ = await self.education_history_repository.get_by_candidate(candidate_id)
            for history in education_histories:
                # Add STUDIES_AT relationship to school
                school_rel_data = {
                    "start_year": history.start_year,
                    "end_year": history.end_year,
                    "education_level": history.education_level.name if history.education_level else None,
                    "academic_performance": history.academic_performance,
                    "additional_info": history.additional_info
                }
                if await self.graph_repository.add_studies_at_relationship(
                    candidate_id, history.school_id, school_rel_data
                ):
                    results["schools"] += 1
                
                # Sync major relationships if available
                if hasattr(history, "school") and hasattr(history.school, "majors"):
                    for major in history.school.majors:
                        major_rel_data = {
                            "start_year": history.start_year,
                            "end_year": history.end_year,
                            "education_level": history.education_level.name if history.education_level else None,
                            "academic_performance": history.academic_performance,
                            "additional_info": history.additional_info,
                            "school_id": history.school_id,
                            "school_name": history.school.school_name if history.school else None
                        }
                        if await self.graph_repository.add_studies_major_relationship(
                            candidate_id, major.major_id, major_rel_data
                        ):
                            results["majors"] += 1
            
            # 2. Sync degrees
            if not self.degree_repository:
                from app.repositories.degree_repository import DegreeRepository
                self.degree_repository = DegreeRepository(self.db_session)
                
            degrees, total_degrees = await self.degree_repository.get_by_candidate(candidate_id)
            for degree in degrees:
                # Add relationship to degree
                if await self.graph_repository.add_holds_degree_relationship(
                    candidate_id, degree.degree_id
                ):
                    results["degrees"] += 1
                
                # If degree has a major, add relationship to that major too
                if hasattr(degree, "major") and degree.major:
                    major_rel_data = {
                        "degree_id": degree.degree_id,
                        "degree_name": degree.degree_name if hasattr(degree, "degree_name") else None,
                        "school_id": degree.school_id if hasattr(degree, "school_id") else None,
                        "school_name": degree.school_name if hasattr(degree, "school_name") else None
                    }
                    if await self.graph_repository.add_studies_major_relationship(
                        candidate_id, degree.major.major_id, major_rel_data
                    ):
                        results["majors"] += 1
            
            # 3. Sync exam relationships
            exam_registrations = await self.candidate_exam_repository.get_by_candidate_id(candidate_id)
            for registration in exam_registrations:
                # Add ATTENDS_EXAM relationship
                exam_rel_data = {
                    "registration_number": registration["registration_number"],
                    "registration_date": registration["registration_date"],
                    "status": registration["status"]
                }
                if await self.graph_repository.add_attends_exam_relationship(
                    candidate_id, registration["exam_id"], exam_rel_data
                ):
                    results["exams"] += 1
            
            # 4. Sync scores
            scores = await self.exam_score_repository.get_by_candidate_id(candidate_id)
            for score in scores:
                score_rel_data = {
                    "exam_id": score["exam_id"],
                    "exam_name": score["exam_name"],
                    "subject_id": score["subject_id"],
                    "subject_name": score["subject_name"],
                    "registration_status": "REGISTERED",
                    "is_required": True
                }
                if await self.graph_repository.add_receives_score_relationship(
                    candidate_id, score["exam_score_id"], score_rel_data
                ):
                    results["scores"] += 1
            
            # 5. Sync exam schedules
            if not self.exam_schedule_repository:
                from app.repositories.exam_schedule_repository import ExamScheduleRepository
                self.exam_schedule_repository = ExamScheduleRepository(self.db_session)
                
            schedules = await self.exam_schedule_repository.get_by_candidate_id(candidate_id)
            for schedule in schedules:
                # Sử dụng các property đã được định nghĩa trong ExamSchedule
                schedule_rel_data = {
                    "exam_id": schedule.exam_id,
                    "exam_name": schedule.exam_name,
                    "subject_id": schedule.subject_id,
                    "subject_name": schedule.subject_name,
                    "room_id": schedule.room_id,
                    "room_name": schedule.exam_room.room_name if schedule.exam_room else None,
                    "registration_status": "REGISTERED",  # Giá trị mặc định
                    "is_required": getattr(schedule.exam_subject, 'is_required', None) if schedule.exam_subject else None
                }
                if await self.graph_repository.add_has_exam_schedule_relationship(
                    candidate_id, schedule.exam_schedule_id, schedule_rel_data
                ):
                    results["schedules"] += 1
            
            # Get all candidate exams for this candidate (used by multiple relationship types)
            candidate_exams = await self.candidate_exam_repository.get_by_candidate_id(candidate_id)
            if not candidate_exams:
                logger.warning(f"No exam registrations found for candidate ID {candidate_id}")
                candidate_exams = []

            # 6. Sync certificates
            if not self.certificate_repository:
                from app.repositories.certificate_repository import CertificateRepository
                self.certificate_repository = CertificateRepository(self.db_session)
                
            # Get all certificates for each candidate exam
            for exam in candidate_exams:
                certificates = await self.certificate_repository.get_by_candidate_exam_id(exam["candidate_exam_id"])
                for certificate in certificates:
                    if await self.graph_repository.add_earns_certificate_relationship(
                        candidate_id, certificate["certificate_id"]
                    ):
                        results["certificates"] += 1
            
            # 7. Sync credentials
            if not self.credential_repository:
                self.credential_repository = CandidateCredentialRepository(self.db_session)
                
            credentials, _ = await self.credential_repository.get_by_candidate(candidate_id)
            for credential in credentials:
                if await self.graph_repository.add_provides_credential_relationship(
                    candidate_id, credential.credential_id
                ):
                    results["credentials"] += 1
            
            # 8. Sync awards
            if not self.award_repository:
                from app.repositories.award_repository import AwardRepository
                self.award_repository = AwardRepository(self.db_session)
                
            # Process awards for each candidate exam
            for exam in candidate_exams:
                awards, _ = await self.award_repository.get_by_candidate_exam(exam["candidate_exam_id"])
                for award in awards:
                    if await self.graph_repository.add_earns_award_relationship(
                        candidate_id, award.award_id
                    ):
                        results["awards"] += 1
            
            # 9. Sync achievements
            if not self.achievement_repository:
                from app.repositories.achievement_repository import AchievementRepository
                self.achievement_repository = AchievementRepository(self.db_session)
                
            # Process achievements for each candidate exam
            for exam in candidate_exams:
                achievements, _ = await self.achievement_repository.get_by_candidate_exam(exam["candidate_exam_id"])
                for achievement in achievements:
                    if await self.graph_repository.add_achieves_relationship(
                        candidate_id, achievement.achievement_id
                    ):
                        results["achievements"] += 1
            
            # 10. Sync recognitions
            if not self.recognition_repository:
                from app.repositories.recognition_repository import RecognitionRepository
                self.recognition_repository = RecognitionRepository(self.db_session)
                
            # Process recognitions for each candidate exam
            for exam in candidate_exams:
                recognitions, _ = await self.recognition_repository.get_by_candidate_exam(exam["candidate_exam_id"])
                for recognition in recognitions:
                    if await self.graph_repository.add_receives_recognition_relationship(
                        candidate_id, recognition.recognition_id
                    ):
                        results["recognitions"] += 1
                    
            logger.info(f"Synchronized all relationships for candidate {candidate_id}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for candidate {candidate_id}: {str(e)}", exc_info=True)
            return results
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all candidates.
        
        Args:
            limit: Optional maximum number of candidates to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all candidates (limit={limit})")
        
        try:
            # Get all candidate IDs from database
            candidates = await self.sql_repository.get_all(limit=limit)
            if isinstance(candidates, tuple) and len(candidates) == 2:
                candidates, _ = candidates
                
            total_candidates = len(candidates)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
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
            
            # For each candidate, sync relationships
            for candidate in candidates:
                try:
                    # Verify candidate exists in Neo4j
                    candidate_node = await self.graph_repository.get_by_id(candidate.candidate_id)
                    if not candidate_node:
                        logger.warning(f"Candidate {candidate.candidate_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                        
                    # Sync relationships for this candidate
                    results = await self.sync_relationship_by_id(candidate.candidate_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error synchronizing relationships for candidate {candidate.candidate_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_candidates": total_candidates,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all candidates: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during candidate relationships synchronization: {e}")
            return {
                "total_candidates": 0,
                "success": 0, 
                "failed": 0,
                "error": str(e),
                "relationships": {}
            }
    
    def _convert_to_node(self, candidate: Candidate) -> CandidateNode:
        """
        Convert SQL Candidate model to CandidateNode.
        
        Args:
            candidate: SQL Candidate model instance
            
        Returns:
            CandidateNode instance
        """
        try:
            # Create a basic node with the available data
            # Avoid accessing lazy-loaded relationships that would trigger database queries
            candidate_node = CandidateNode(
                candidate_id=candidate.candidate_id,
                full_name=candidate.full_name
            )
            
            # Xử lý personal_info nếu được tải như một dictionary
            if isinstance(candidate, dict) and "personal_info" in candidate:
                personal_info = candidate["personal_info"]
                if personal_info:
                    candidate_node.birth_date = personal_info.get("birth_date")
                    candidate_node.id_number = personal_info.get("id_number")
                    candidate_node.phone_number = personal_info.get("phone_number")
                    candidate_node.email = personal_info.get("email")
                    candidate_node.address = personal_info.get("primary_address")
                    candidate_node.id_card_image_url = personal_info.get("id_card_image_url")
                    candidate_node.candidate_card_image_url = personal_info.get("candidate_card_image_url")
                    candidate_node.face_recognition_data_url = personal_info.get("face_recognition_data_url")
            # Xử lý personal_info khi nó là một relationship đã được eager load
            elif hasattr(candidate, "personal_info") and candidate.personal_info is not None:
                # Đã tải personal_info thông qua eager loading
                personal_info = candidate.personal_info
                candidate_node.birth_date = personal_info.birth_date
                candidate_node.id_number = personal_info.id_number
                candidate_node.phone_number = personal_info.phone_number
                candidate_node.email = personal_info.email
                candidate_node.address = personal_info.primary_address
                candidate_node.id_card_image_url = personal_info.id_card_image_url
                candidate_node.candidate_card_image_url = personal_info.candidate_card_image_url
                candidate_node.face_recognition_data_url = personal_info.face_recognition_data_url
            
            return candidate_node
            
        except Exception as e:
            logger.error(f"Error converting candidate to node: {str(e)}", exc_info=True)
            # Return a basic node with just the ID and name as fallback
            return CandidateNode(
                candidate_id=candidate.candidate_id,
                full_name=candidate.full_name
            ) 