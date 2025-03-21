"""
Main synchronization service module.

This module provides the main service for orchestrating data synchronization
between PostgreSQL and Neo4j databases using specialized sync services.
"""

import logging
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.ontology.neo4j_connection import neo4j_connection
from app.services.sync.base_sync_service import BaseSyncService
from app.services.sync.exam_sync_service import ExamSyncService
from app.services.sync.candidate_sync_service import CandidateSyncService
from app.services.sync.academic_sync_service import AcademicSyncService
from app.services.sync.score_sync_service import ScoreSyncService
from app.repositories.repository_factory import RepositoryFactory

logger = logging.getLogger(__name__)

class MainSyncService(BaseSyncService):
    """
    Main service for orchestrating data synchronization between PostgreSQL and Neo4j.
    
    This service is responsible for coordinating the various specialized sync
    services and providing a unified interface for data synchronization.
    """
    
    def __init__(self, neo4j_connection, db_session: AsyncSession):
        """Initialize with Neo4j connection and SQLAlchemy session."""
        super().__init__(neo4j_connection, db_session)
        
        # Initialize specialized sync services
        self.exam_sync_service = ExamSyncService(neo4j_connection, db_session)
        self.candidate_sync_service = CandidateSyncService(neo4j_connection, db_session)
        self.academic_sync_service = AcademicSyncService(neo4j_connection, db_session)
        self.score_sync_service = ScoreSyncService(neo4j_connection, db_session)
        
    async def sync_ontology_relationships(self):
        """
        Synchronize ontology relationships in Neo4j.
        
        This method creates relationships between entity types based on the
        ontology model.
        
        Returns:
            bool: True if successful, False otherwise
        """
        await self._log_sync_start("ontology relationships")
        try:
            # Create ontology relationships
            ontology_query = """
            // Create ontology relationships
            MERGE (candidate:EntityType {name: "Candidate"})
            MERGE (exam:EntityType {name: "Exam"})
            MERGE (school:EntityType {name: "School"})
            MERGE (subject:EntityType {name: "Subject"})
            MERGE (score:EntityType {name: "Score"})
            MERGE (major:EntityType {name: "Major"})
            MERGE (award:EntityType {name: "Award"})
            MERGE (certificate:EntityType {name: "Certificate"})
            MERGE (achievement:EntityType {name: "Achievement"})
            MERGE (recognition:EntityType {name: "Recognition"})
            MERGE (degree:EntityType {name: "Degree"})
            MERGE (credential:EntityType {name: "Credential"})
            MERGE (location:EntityType {name: "ExamLocation"})
            MERGE (room:EntityType {name: "ExamRoom"})
            MERGE (schedule:EntityType {name: "ExamSchedule"})
            MERGE (attempt:EntityType {name: "ExamAttempt"})
            MERGE (review:EntityType {name: "ScoreReview"})
            MERGE (history:EntityType {name: "ScoreHistory"})
            MERGE (unit:EntityType {name: "ManagementUnit"})
            
            // Define relationships
            MERGE (candidate)-[:CAN_HAVE]->(score)
            MERGE (candidate)-[:CAN_REGISTER_FOR]->(exam)
            MERGE (candidate)-[:CAN_RECEIVE]->(certificate)
            MERGE (candidate)-[:CAN_EARN]->(achievement)
            MERGE (candidate)-[:CAN_EARN]->(recognition)
            MERGE (candidate)-[:CAN_OBTAIN]->(degree)
            MERGE (candidate)-[:CAN_HAVE]->(credential)
            MERGE (candidate)-[:CAN_STUDY_AT]->(school)
            MERGE (candidate)-[:CAN_STUDY]->(major)
            MERGE (candidate)-[:CAN_REQUEST]->(review)
            
            MERGE (exam)-[:CAN_HAVE]->(subject)
            MERGE (exam)-[:CAN_BE_CONDUCTED_AT]->(location)
            MERGE (exam)-[:CAN_ISSUE]->(certificate)
            MERGE (exam)-[:CAN_BE_ADMINISTERED_BY]->(unit)
            
            MERGE (location)-[:CAN_HAVE]->(room)
            MERGE (room)-[:CAN_HOST]->(schedule)
            
            MERGE (score)-[:CAN_HAVE]->(history)
            MERGE (score)-[:CAN_HAVE]->(review)
            
            MERGE (school)-[:CAN_OFFER]->(major)
            
            RETURN count(*) as relationships
            """
            
            logger.info("Creating ontology relationships in Neo4j")
            result = await self._execute_neo4j_query(ontology_query)
            
            await self._log_sync_success("ontology relationships")
            return True
        except Exception as e:
            await self._log_sync_error("ontology relationships", str(e))
            logger.error(traceback.format_exc())
            return False
            
    async def bulk_sync_all(self, resync_ontology=True):
        """
        Synchronize all data from PostgreSQL to Neo4j.
        
        Args:
            resync_ontology: Whether to synchronize ontology relationships
        
        Returns:
            dict: Dictionary with sync results for each entity type
        """
        await self._log_sync_start("all entities")
        
        results = {}
        
        try:
            # Sync schools and candidates first
            logger.info("Syncing schools...")
            results["schools"] = await self.bulk_sync_schools()
            
            logger.info("Syncing candidates...")
            results["candidates"] = await self.candidate_sync_service.bulk_sync_candidates()
            
            # Sync majors and their relationships
            logger.info("Syncing majors...")
            results["majors"] = await self.bulk_sync_majors()
            
            logger.info("Syncing school-major relationships...")
            results["school_major_relationships"] = await self.bulk_sync_school_major_relationships()
            
            logger.info("Syncing candidate-major relationships...")
            results["candidate_major_relationships"] = await self.candidate_sync_service.bulk_sync_candidate_major_relationships()
            
            # Sync education histories
            logger.info("Syncing education histories...")
            results["education_histories"] = await self.candidate_sync_service.bulk_sync_education_histories()
            
            # Sync exams and related entities
            logger.info("Syncing exams...")
            results["exams"] = await self.exam_sync_service.bulk_sync_exams()
            
            logger.info("Syncing exam locations...")
            results["exam_locations"] = await self.exam_sync_service.bulk_sync_exam_locations()
            
            logger.info("Syncing exam rooms...")
            results["exam_rooms"] = await self.exam_sync_service.bulk_sync_exam_rooms()
            
            logger.info("Syncing exam schedules...")
            results["exam_schedules"] = await self.exam_sync_service.bulk_sync_exam_schedules()
            
            logger.info("Syncing exam attempts...")
            results["exam_attempts"] = await self.exam_sync_service.bulk_sync_exam_attempts()
            
            # Sync subjects and candidate-exam relationships
            logger.info("Syncing subjects...")
            results["subjects"] = await self.bulk_sync_subjects()
            
            logger.info("Syncing candidate-exam relationships...")
            results["candidate_exam_relationships"] = await self.candidate_sync_service.bulk_sync_candidate_exam_relationships()
            
            # Sync scores and related entities
            logger.info("Syncing scores...")
            results["scores"] = await self.score_sync_service.bulk_sync_scores()
            
            logger.info("Syncing score histories...")
            results["score_histories"] = await self.score_sync_service.bulk_sync_score_histories()
            
            logger.info("Syncing score reviews...")
            results["score_reviews"] = await self.score_sync_service.bulk_sync_score_reviews()
            
            # Sync academic achievements
            logger.info("Syncing certificates...")
            results["certificates"] = await self.academic_sync_service.bulk_sync_certificates()
            
            logger.info("Syncing achievements...")
            results["achievements"] = await self.academic_sync_service.bulk_sync_achievements()
            
            logger.info("Syncing recognitions...")
            results["recognitions"] = await self.academic_sync_service.bulk_sync_recognitions()
            
            logger.info("Syncing degrees...")
            results["degrees"] = await self.academic_sync_service.bulk_sync_degrees()
            
            logger.info("Syncing credentials...")
            results["credentials"] = await self.academic_sync_service.bulk_sync_credentials()
            
            logger.info("Syncing awards...")
            results["awards"] = await self.bulk_sync_awards()
            
            # Sync management units
            logger.info("Syncing management units...")
            results["management_units"] = await self.bulk_sync_management_units()
            
            # Sync ontology relationships if requested
            if resync_ontology:
                logger.info("Syncing ontology relationships...")
                await self.sync_ontology_relationships()
            
            await self._log_sync_success("all entities")
            
            # Calculate total number of synchronized entities
            total_synced = sum(results.values())
            logger.info(f"Total entities synchronized: {total_synced}")
            
            return results
        except Exception as e:
            await self._log_sync_error("all entities", str(e))
            logger.error(traceback.format_exc())
            return results
            
    # The following methods could be moved to specialized classes in a future refactoring
    
    async def bulk_sync_schools(self):
        """
        Synchronize all schools from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized schools
        """
        await self._log_sync_start("school")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            school_repo = await repo_factory.get_school_repository()
            
            # Get all schools
            schools = await school_repo.get_all()
            logger.info(f"Found {len(schools)} schools to sync")
            
            # Sync each school
            success_count = 0
            for school in schools:
                if await self.sync_school(school):
                    success_count += 1
            
            await self._log_sync_success("school", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("school", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def sync_school(self, school_model):
        """
        Synchronize a school from PostgreSQL to Neo4j.
        
        Args:
            school_model: A School SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        from app.domain.graph_models.school_node import SchoolNode
        from app.graph_repositories.school_graph_repository import SchoolGraphRepository
        
        school_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(school_model, dict):
                school_id = school_model.get("school_id")
                school_dict = school_model
            else:
                school_id = school_model.school_id
                school_dict = {
                    "school_id": school_model.school_id,
                    "school_name": school_model.school_name,
                    "address": school_model.address,
                    "city": school_model.city,
                    "state": school_model.state,
                    "country": school_model.country,
                    "postal_code": school_model.postal_code,
                    "phone": school_model.phone,
                    "email": school_model.email,
                    "website": school_model.website,
                    "school_type": school_model.school_type,
                    "founded_date": school_model.founded_date,
                    "status": school_model.status,
                }
            
            await self._log_sync_start("school", school_id)
            
            # Create Neo4j node
            school_node = SchoolNode.from_dict(school_dict)
            
            # Initialize repository
            school_graph_repo = SchoolGraphRepository(self.neo4j)
            
            # Create or update node in Neo4j
            await school_graph_repo.create_or_update(school_node)
            
            await self._log_sync_success("school", school_id)
            return True
        except Exception as e:
            await self._log_sync_error("school", str(e), school_id)
            logger.error(traceback.format_exc())
            return False
            
    async def bulk_sync_subjects(self):
        """
        Synchronize all subjects from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized subjects
        """
        await self._log_sync_start("subject")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            subject_repo = await repo_factory.get_subject_repository()
            
            # Get all subjects
            subjects = await subject_repo.get_all()
            logger.info(f"Found {len(subjects)} subjects to sync")
            
            # Sync each subject
            success_count = 0
            for subject in subjects:
                if await self.sync_subject(subject):
                    success_count += 1
            
            # Sync exam-subject relationships
            exam_subject_repo = await repo_factory.get_exam_subject_repository()
            exam_subjects = await exam_subject_repo.get_all()
            logger.info(f"Found {len(exam_subjects)} exam-subject relationships to sync")
            
            for exam_subject in exam_subjects:
                await self.sync_exam_subject_relationship(exam_subject)
            
            await self._log_sync_success("subject", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("subject", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def sync_subject(self, subject_model):
        """
        Synchronize a subject from PostgreSQL to Neo4j.
        
        Args:
            subject_model: A Subject SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        from app.domain.graph_models.subject_node import SubjectNode
        from app.graph_repositories.subject_graph_repository import SubjectGraphRepository
        
        subject_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(subject_model, dict):
                subject_id = subject_model.get("subject_id")
                subject_dict = subject_model
            else:
                subject_id = subject_model.subject_id
                subject_dict = {
                    "subject_id": subject_model.subject_id,
                    "subject_name": subject_model.subject_name,
                    "subject_code": subject_model.subject_code,
                    "description": subject_model.description,
                    "credit_hours": subject_model.credit_hours,
                    "subject_type": subject_model.subject_type,
                    "status": subject_model.status,
                }
            
            await self._log_sync_start("subject", subject_id)
            
            # Create Neo4j node
            subject_node = SubjectNode.from_dict(subject_dict)
            
            # Initialize repository
            subject_graph_repo = SubjectGraphRepository(self.neo4j)
            
            # Create or update node in Neo4j
            await subject_graph_repo.create_or_update(subject_node)
            
            await self._log_sync_success("subject", subject_id)
            return True
        except Exception as e:
            await self._log_sync_error("subject", str(e), subject_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_exam_subject_relationship(self, exam_subject_model):
        """
        Synchronize an exam-subject relationship from PostgreSQL to Neo4j.
        
        Args:
            exam_subject_model: An ExamSubject SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        exam_subject_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(exam_subject_model, dict):
                exam_subject_id = exam_subject_model.get("exam_subject_id")
                exam_id = exam_subject_model.get("exam_id")
                subject_id = exam_subject_model.get("subject_id")
            else:
                exam_subject_id = exam_subject_model.exam_subject_id
                exam_id = exam_subject_model.exam_id
                subject_id = exam_subject_model.subject_id
            
            await self._log_sync_start("exam-subject relationship", exam_subject_id)
            
            # Create relationship between exam and subject
            relationship_query = """
            MATCH (e:Exam {exam_id: $exam_id})
            MATCH (s:Subject {subject_id: $subject_id})
            MERGE (e)-[r:INCLUDES_SUBJECT]->(s)
            RETURN r
            """
            
            params = {
                "exam_id": exam_id,
                "subject_id": subject_id
            }
            
            logger.info(f"Creating relationship between exam {exam_id} and subject {subject_id}")
            await self._execute_neo4j_query(relationship_query, params)
            
            await self._log_sync_success("exam-subject relationship", exam_subject_id)
            return True
        except Exception as e:
            await self._log_sync_error("exam-subject relationship", str(e), exam_subject_id)
            logger.error(traceback.format_exc())
            return False
            
    async def bulk_sync_majors(self):
        """
        Synchronize all majors from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized majors
        """
        await self._log_sync_start("major")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            major_repo = await repo_factory.get_major_repository()
            
            # Get all majors
            majors = await major_repo.get_all()
            logger.info(f"Found {len(majors)} majors to sync")
            
            # Sync each major
            success_count = 0
            for major in majors:
                if await self.sync_major(major):
                    success_count += 1
            
            await self._log_sync_success("major", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("major", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def sync_major(self, major_model):
        """
        Synchronize a major from PostgreSQL to Neo4j.
        
        Args:
            major_model: A Major SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        from app.domain.graph_models.major_node import MajorNode
        from app.graph_repositories.major_graph_repository import MajorGraphRepository
        
        major_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(major_model, dict):
                major_id = major_model.get("major_id")
                major_dict = major_model
            else:
                major_id = major_model.major_id
                major_dict = {
                    "major_id": major_model.major_id,
                    "major_name": major_model.major_name,
                    "major_code": major_model.major_code,
                    "description": major_model.description,
                    "department": major_model.department,
                    "major_type": major_model.major_type,
                    "status": major_model.status,
                }
            
            await self._log_sync_start("major", major_id)
            
            # Create Neo4j node
            major_node = MajorNode.from_dict(major_dict)
            
            # Initialize repository
            major_graph_repo = MajorGraphRepository(self.neo4j)
            
            # Create or update node in Neo4j
            await major_graph_repo.create_or_update(major_node)
            
            await self._log_sync_success("major", major_id)
            return True
        except Exception as e:
            await self._log_sync_error("major", str(e), major_id)
            logger.error(traceback.format_exc())
            return False
            
    async def bulk_sync_school_major_relationships(self):
        """
        Synchronize all school-major relationships from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized relationships
        """
        await self._log_sync_start("school-major relationship")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            school_major_repo = await repo_factory.get_school_major_repository()
            
            # Get all school-major relationships
            relationships = await school_major_repo.get_all()
            logger.info(f"Found {len(relationships)} school-major relationships to sync")
            
            # Sync each relationship
            success_count = 0
            for relationship in relationships:
                if await self.sync_school_major_relationship(
                    relationship.school_id, relationship.major_id, relationship.start_year
                ):
                    success_count += 1
            
            await self._log_sync_success("school-major relationship", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("school-major relationship", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def sync_school_major_relationship(self, school_id, major_id, start_year):
        """
        Synchronize a school-major relationship to Neo4j.
        
        Args:
            school_id: The ID of the school
            major_id: The ID of the major
            start_year: The year the major started at the school
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self._log_sync_start("school-major relationship")
            
            # Create relationship between school and major
            relationship_query = """
            MATCH (s:School {school_id: $school_id})
            MATCH (m:Major {major_id: $major_id})
            MERGE (s)-[r:OFFERS_MAJOR {start_year: $start_year}]->(m)
            RETURN r
            """
            
            params = {
                "school_id": school_id,
                "major_id": major_id,
                "start_year": start_year
            }
            
            logger.info(f"Creating relationship between school {school_id} and major {major_id}")
            await self._execute_neo4j_query(relationship_query, params)
            
            await self._log_sync_success("school-major relationship")
            return True
        except Exception as e:
            await self._log_sync_error("school-major relationship", str(e))
            logger.error(traceback.format_exc())
            return False
            
    async def bulk_sync_awards(self):
        """
        Synchronize all awards from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized awards
        """
        await self._log_sync_start("award")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            award_repo = await repo_factory.get_award_repository()
            
            # Get all awards
            awards = await award_repo.get_all()
            logger.info(f"Found {len(awards)} awards to sync")
            
            # Sync each award
            success_count = 0
            for award in awards:
                if await self.sync_award(award):
                    success_count += 1
            
            await self._log_sync_success("award", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("award", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def sync_award(self, award_model):
        """
        Synchronize an award from PostgreSQL to Neo4j.
        
        Args:
            award_model: An Award SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        from app.domain.graph_models.award_node import AwardNode
        from app.graph_repositories.award_graph_repository import AwardGraphRepository
        
        award_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(award_model, dict):
                award_id = award_model.get("award_id")
                award_dict = award_model
            else:
                award_id = award_model.award_id
                award_dict = {
                    "award_id": award_model.award_id,
                    "candidate_id": award_model.candidate_id,
                    "award_name": award_model.award_name,
                    "award_date": award_model.award_date,
                    "description": award_model.description,
                    "award_type": award_model.award_type,
                    "issuing_organization": award_model.issuing_organization,
                }
            
            await self._log_sync_start("award", award_id)
            
            # Create Neo4j node
            award_node = AwardNode.from_dict(award_dict)
            
            # Initialize repository
            award_graph_repo = AwardGraphRepository(self.neo4j)
            
            # Create or update node in Neo4j
            await award_graph_repo.create_or_update(award_node)
            
            await self._log_sync_success("award", award_id)
            return True
        except Exception as e:
            await self._log_sync_error("award", str(e), award_id)
            logger.error(traceback.format_exc())
            return False
            
    async def bulk_sync_management_units(self):
        """
        Synchronize all management units from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized management units
        """
        await self._log_sync_start("management unit")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            unit_repo = await repo_factory.get_management_unit_repository()
            
            # Get all management units
            units = await unit_repo.get_all()
            logger.info(f"Found {len(units)} management units to sync")
            
            # Sync each management unit
            success_count = 0
            for unit in units:
                if await self.sync_management_unit(unit):
                    success_count += 1
            
            await self._log_sync_success("management unit", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("management unit", str(e))
            logger.error(traceback.format_exc())
            return 0
    
    async def sync_management_unit(self, unit_model):
        """
        Synchronize a management unit from PostgreSQL to Neo4j.
        
        Args:
            unit_model: A ManagementUnit SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        from app.domain.graph_models.management_unit_node import ManagementUnitNode
        from app.graph_repositories.management_unit_graph_repository import ManagementUnitGraphRepository
        
        unit_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(unit_model, dict):
                unit_id = unit_model.get("unit_id")
                unit_dict = unit_model
            else:
                unit_id = unit_model.unit_id
                unit_dict = {
                    "unit_id": unit_model.unit_id,
                    "unit_name": unit_model.unit_name,
                    "parent_unit_id": unit_model.parent_unit_id,
                    "unit_type": unit_model.unit_type,
                    "address": unit_model.address,
                    "city": unit_model.city,
                    "state": unit_model.state,
                    "country": unit_model.country,
                    "postal_code": unit_model.postal_code,
                    "phone": unit_model.phone,
                    "email": unit_model.email,
                    "website": unit_model.website,
                    "status": unit_model.status,
                }
            
            await self._log_sync_start("management unit", unit_id)
            
            # Create Neo4j node
            unit_node = ManagementUnitNode.from_dict(unit_dict)
            
            # Initialize repository
            unit_graph_repo = ManagementUnitGraphRepository(self.neo4j)
            
            # Create or update node in Neo4j
            await unit_graph_repo.create_or_update(unit_node)
            
            # Create parent-child relationship if parent exists
            if unit_dict.get("parent_unit_id"):
                parent_id = unit_dict["parent_unit_id"]
                relationship_query = """
                MATCH (parent:ManagementUnit {unit_id: $parent_id})
                MATCH (child:ManagementUnit {unit_id: $child_id})
                MERGE (parent)-[r:HAS_CHILD]->(child)
                RETURN r
                """
                
                params = {
                    "parent_id": parent_id,
                    "child_id": unit_id
                }
                
                logger.info(f"Creating parent-child relationship between units {parent_id} and {unit_id}")
                await self._execute_neo4j_query(relationship_query, params)
            
            await self._log_sync_success("management unit", unit_id)
            return True
        except Exception as e:
            await self._log_sync_error("management unit", str(e), unit_id)
            logger.error(traceback.format_exc())
            return False 