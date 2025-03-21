"""
Data synchronization service module.

This module provides services for synchronizing data between 
PostgreSQL and Neo4j databases.
"""

import logging
from app.domain.graph_models.exam_node import ExamNode
from app.domain.graph_models.candidate_node import CandidateNode
from app.domain.graph_models.school_node import SchoolNode
from app.domain.graph_models.subject_node import SubjectNode
from app.domain.graph_models.score_node import ScoreNode
from app.domain.graph_models.major_node import MajorNode
from app.domain.graph_models.award_node import AwardNode
from app.domain.graph_models.certificate_node import CertificateNode
from app.domain.graph_models.achievement_node import AchievementNode
from app.domain.graph_models.recognition_node import RecognitionNode
from app.domain.graph_models.degree_node import DegreeNode
from app.domain.graph_models.credential_node import CredentialNode
from app.domain.graph_models.exam_location_node import ExamLocationNode
from app.domain.graph_models.exam_room_node import ExamRoomNode
from app.domain.graph_models.exam_schedule_node import ExamScheduleNode
from app.domain.graph_models.exam_attempt_node import ExamAttemptNode
from app.domain.graph_models.score_review_node import ScoreReviewNode
from app.domain.graph_models.score_history_node import ScoreHistoryNode
from app.graph_repositories.exam_graph_repository import ExamGraphRepository
from app.graph_repositories.candidate_graph_repository import CandidateGraphRepository
from app.graph_repositories.school_graph_repository import SchoolGraphRepository
from app.graph_repositories.subject_graph_repository import SubjectGraphRepository
from app.graph_repositories.score_graph_repository import ScoreGraphRepository
from app.graph_repositories.major_graph_repository import MajorGraphRepository
from app.graph_repositories.award_graph_repository import AwardGraphRepository
from app.graph_repositories.certificate_graph_repository import CertificateGraphRepository
from app.graph_repositories.achievement_graph_repository import AchievementGraphRepository
from app.graph_repositories.recognition_graph_repository import RecognitionGraphRepository
from app.graph_repositories.degree_graph_repository import DegreeGraphRepository
from app.graph_repositories.credential_graph_repository import CredentialGraphRepository
from app.graph_repositories.exam_location_graph_repository import ExamLocationGraphRepository
from app.graph_repositories.exam_room_graph_repository import ExamRoomGraphRepository
from app.graph_repositories.exam_schedule_graph_repository import ExamScheduleGraphRepository
from app.graph_repositories.exam_attempt_graph_repository import ExamAttemptGraphRepository
from app.graph_repositories.score_review_graph_repository import ScoreReviewGraphRepository
from app.graph_repositories.score_history_graph_repository import ScoreHistoryGraphRepository
from app.infrastructure.ontology.neo4j_connection import neo4j_connection
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.exam_score_repository import ExamScoreRepository
from app.repositories.major_repository import MajorRepository
from app.repositories.award_repository import AwardRepository
from app.repositories.certificate_repository import CertificateRepository
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.recognition_repository import RecognitionRepository
from app.repositories.degree_repository import DegreeRepository
from app.repositories.candidate_credential_repository import CandidateCredentialRepository
from app.repositories.repository_factory import RepositoryFactory
from app.domain.graph_models.management_unit_node import ManagementUnitNode
from app.graph_repositories.management_unit_graph_repository import ManagementUnitGraphRepository
import json
import traceback

logger = logging.getLogger(__name__)

class SyncService:
    """
    Service for synchronizing data between PostgreSQL and Neo4j.
    
    This service is responsible for ensuring data consistency between
    the relational database and the knowledge graph.
    """
    
    def __init__(self, neo4j_connection, db_session):
        """Initialize with Neo4j connection and SQLAlchemy session."""
        self.neo4j = neo4j_connection
        self.db = db_session
        
        # Initialize repositories
        self.candidate_graph_repo = CandidateGraphRepository(neo4j_connection)
        self.school_graph_repo = SchoolGraphRepository(neo4j_connection)
        self.exam_graph_repo = ExamGraphRepository(neo4j_connection)
        self.subject_graph_repo = SubjectGraphRepository(neo4j_connection)
        self.score_graph_repo = ScoreGraphRepository(neo4j_connection)
        self.major_graph_repo = MajorGraphRepository(neo4j_connection)
        self.award_graph_repo = AwardGraphRepository(neo4j_connection)
        self.certificate_graph_repo = CertificateGraphRepository(neo4j_connection)
        self.achievement_graph_repo = AchievementGraphRepository(neo4j_connection)
        self.recognition_graph_repo = RecognitionGraphRepository(neo4j_connection)
        self.degree_graph_repo = DegreeGraphRepository(neo4j_connection)
        self.credential_graph_repo = CredentialGraphRepository(neo4j_connection)
        self.exam_location_graph_repository = ExamLocationGraphRepository(neo4j_connection)
        self.exam_room_graph_repository = ExamRoomGraphRepository(neo4j_connection)
        self.exam_schedule_graph_repository = ExamScheduleGraphRepository(neo4j_connection)
        self.exam_attempt_graph_repository = ExamAttemptGraphRepository(neo4j_connection)
        self.score_review_graph_repository = ScoreReviewGraphRepository(neo4j_connection)
        self.score_history_graph_repository = ScoreHistoryGraphRepository(neo4j_connection)
        self.management_unit_graph_repo = ManagementUnitGraphRepository(neo4j_connection)
        
        self.candidate_repo = CandidateRepository(db_session)
        self.school_repo = SchoolRepository(db_session)
        self.exam_repo = ExamRepository(db_session)
        self.subject_repo = SubjectRepository(db_session)
        self.score_repo = ExamScoreRepository(db_session)
        self.major_repo = MajorRepository(db_session)
        self.award_repo = AwardRepository(db_session)
        self.certificate_repo = CertificateRepository(db_session)
        self.achievement_repo = AchievementRepository(db_session)
        self.recognition_repo = RecognitionRepository(db_session)
        self.degree_repo = DegreeRepository(db_session)
        self.credential_repo = CandidateCredentialRepository(db_session)
        
        # Initialize repository factory for SQL repositories
        self.repository_factory = RepositoryFactory(db_session)
    
    async def sync_exam(self, exam_model):
        """
        Synchronize an Exam model from PostgreSQL to Neo4j.
        
        Args:
            exam_model: SQLAlchemy Exam model hoặc dictionary chứa dữ liệu exam
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        try:
            # Nếu exam_model là dictionary, chuyển đổi thành ExamNode trực tiếp
            if isinstance(exam_model, dict):
                exam_node = ExamNode(
                    exam_id=exam_model.get('exam_id'),
                    exam_name=exam_model.get('exam_name'),
                    exam_type=exam_model.get('type_id'),
                    start_date=exam_model.get('start_date'),
                    end_date=exam_model.get('end_date'),
                    scope=exam_model.get('scope')
                )
            else:
                # Nếu là ORM object, sử dụng phương thức from_sql_model
                exam_node = ExamNode.from_sql_model(exam_model)
            
            # Create or update the node in Neo4j
            success = await self.exam_graph_repo.create_or_update(exam_node)
            
            if success:
                exam_id = exam_model.get('exam_id') if isinstance(exam_model, dict) else exam_model.exam_id
                logger.info(f"Synchronized exam {exam_id} to Neo4j")
            else:
                exam_id = exam_model.get('exam_id') if isinstance(exam_model, dict) else exam_model.exam_id
                logger.error(f"Failed to synchronize exam {exam_id} to Neo4j")
            
            return success
        except Exception as e:
            exam_id = exam_model.get('exam_id') if isinstance(exam_model, dict) else getattr(exam_model, 'exam_id', 'unknown')
            logger.error(f"Error synchronizing exam {exam_id} to Neo4j: {e}")
            return False
    
    async def sync_school(self, school_model):
        """
        Synchronize a School model from PostgreSQL to Neo4j.
        
        Args:
            school_model: SQLAlchemy School model
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        try:
            # Sử dụng phương thức from_sql_model để chuyển đổi thành node
            school_node = SchoolNode.from_sql_model(school_model)
            
            # Create or update the node in Neo4j
            success = await self.school_graph_repo.create_or_update(school_node)
            
            if success:
                logger.info(f"Synchronized school {school_model.school_id} to Neo4j")
            else:
                logger.error(f"Failed to synchronize school {school_model.school_id} to Neo4j")
            
            return success
        except Exception as e:
            logger.error(f"Error synchronizing school to Neo4j: {e}")
            return False
    
    async def sync_candidate(self, candidate_model, personal_info_model=None):
        """
        Synchronize a Candidate model from PostgreSQL to Neo4j.
        
        Args:
            candidate_model: SQLAlchemy Candidate model
            personal_info_model: SQLAlchemy PersonalInfo model (optional)
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        try:
            logger.info(f"Starting sync for candidate {candidate_model.candidate_id}")
            
            # Get personal info from the model if not provided
            if not personal_info_model and hasattr(candidate_model, 'personal_info'):
                personal_info_model = candidate_model.personal_info
                logger.info(f"Found personal info for candidate {candidate_model.candidate_id}")
            
            # Create node from models
            candidate_node = CandidateNode.from_sql_model(
                candidate_model, 
                personal_info_model
            )
            
            if not candidate_node:
                logger.error(f"Failed to create node for candidate {candidate_model.candidate_id}")
                return False
            
            # Create or update the node in Neo4j
            success = await self.candidate_graph_repo.create_or_update(candidate_node)
            
            if success:
                logger.info(f"Successfully synchronized candidate {candidate_model.candidate_id} to Neo4j")
            else:
                logger.error(f"Failed to synchronize candidate {candidate_model.candidate_id} to Neo4j")
            
            return success
            
        except Exception as e:
            logger.error(f"Error synchronizing candidate {candidate_model.candidate_id} to Neo4j: {e}", exc_info=True)
            return False
    
    async def sync_education_history(self, education_history_model):
        """
        Synchronize an education history relationship between a candidate and a school.
        
        Args:
            education_history_model: SQLAlchemy EducationHistory model
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        try:
            # Prepare relationship data
            relationship_data = {
                "start_year": education_history_model.start_year,
                "end_year": education_history_model.end_year,
                "education_level": education_history_model.education_level_id
            }
            
            # Synchronize the relationship
            success = await self.candidate_graph_repo.add_studies_at_relationship(
                education_history_model.candidate_id,
                education_history_model.school_id,
                relationship_data
            )
            
            if success:
                logger.info(f"Synchronized education history for candidate {education_history_model.candidate_id} at school {education_history_model.school_id}")
            else:
                logger.error(f"Failed to synchronize education history for candidate {education_history_model.candidate_id} at school {education_history_model.school_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error synchronizing education history to Neo4j: {e}")
            return False
    
    async def sync_school_major(self, school_major_model):
        """
        Synchronize a school-major relationship.
        
        Args:
            school_major_model: SQLAlchemy SchoolMajor model
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        try:
            # Synchronize the relationship
            success = await self.school_graph_repo.add_offers_major_relationship(
                school_major_model.school_id,
                school_major_model.major_id,
                school_major_model.start_year
            )
            
            if success:
                logger.info(f"Synchronized relationship between school {school_major_model.school_id} and major {school_major_model.major_id}")
            else:
                logger.error(f"Failed to synchronize relationship between school {school_major_model.school_id} and major {school_major_model.major_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error synchronizing school-major relationship to Neo4j: {e}")
            return False
    
    async def sync_exam_subject_relationship(self, exam_subject_model):
        """
        Synchronize the relationship between an exam and a subject.
        
        Args:
            exam_subject_model: SQLAlchemy ExamSubject model
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        try:
            relationship_data = {
                "exam_date": exam_subject_model.exam_date,
                "duration_minutes": exam_subject_model.duration_minutes
            }
            
            success = await self.exam_graph_repo.add_includes_subject_relationship(
                exam_subject_model.exam_id,
                exam_subject_model.subject_id,
                relationship_data
            )
            
            if success:
                logger.info(f"Synchronized relationship between exam {exam_subject_model.exam_id} and subject {exam_subject_model.subject_id}")
            else:
                logger.error(f"Failed to synchronize relationship between exam {exam_subject_model.exam_id} and subject {exam_subject_model.subject_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error synchronizing exam-subject relationship to Neo4j: {e}")
            return False
    
    async def sync_candidate_exam_relationship(self, candidate_exam_model):
        """
        Synchronize the relationship between a candidate and an exam.
        
        Args:
            candidate_exam_model: SQLAlchemy CandidateExam model
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        try:
            relationship_data = {
                "registration_number": candidate_exam_model.registration_number,
                "registration_date": candidate_exam_model.registration_date,
                "status": candidate_exam_model.status
            }
            
            success = await self.candidate_graph_repo.add_attends_exam_relationship(
                candidate_exam_model.candidate_id,
                candidate_exam_model.exam_id,
                relationship_data
            )
            
            if success:
                logger.info(f"Synchronized relationship between candidate {candidate_exam_model.candidate_id} and exam {candidate_exam_model.exam_id}")
            else:
                logger.error(f"Failed to synchronize relationship between candidate {candidate_exam_model.candidate_id} and exam {candidate_exam_model.exam_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error synchronizing candidate-exam relationship to Neo4j: {e}")
            return False
            
    async def sync_subject(self, subject_model):
        """
        Synchronize a Subject model from PostgreSQL to Neo4j.
        
        Args:
            subject_model: SQLAlchemy Subject model
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        try:
            # Sử dụng phương thức from_sql_model để chuyển đổi thành node
            subject_node = SubjectNode.from_sql_model(subject_model)
            
            # Create or update the node in Neo4j
            success = await self.subject_graph_repo.create_or_update(subject_node)
            
            if success:
                logger.info(f"Synchronized subject {subject_model.subject_id} to Neo4j")
            else:
                logger.error(f"Failed to synchronize subject {subject_model.subject_id} to Neo4j")
            
            return success
        except Exception as e:
            logger.error(f"Error synchronizing subject to Neo4j: {e}")
            return False
    
    async def sync_score(self, score_model):
        """
        Synchronize a score from PostgreSQL to Neo4j.
        
        Args:
            score_model: PostgreSQL model or dictionary containing score data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug(f"Syncing score: {score_model}")
            
            # Extract exam_score_id based on whether it's a dict or SQLAlchemy model
            if isinstance(score_model, dict):
                exam_score_id = score_model.get('exam_score_id')
            else:
                exam_score_id = getattr(score_model, 'exam_score_id', None)
            
            # Create ScoreNode
            score_node = ScoreNode.from_sql_model(score_model)
            
            # Execute creation query
            create_query = score_node.create_query()
            query_params = score_node.to_dict()
            
            logger.debug(f"Executing Neo4j query: {create_query}")
            logger.debug(f"With parameters: {query_params}")
            
            result = await self.neo4j.execute_query(create_query, query_params)
            logger.debug(f"Result from Neo4j: {result}")
            
            # Create relationships
            relationships_query = score_node.create_relationships_query()
            
            if relationships_query:
                logger.debug(f"Executing relationships query: {relationships_query}")
                logger.debug(f"With parameters: {query_params}")
                
                rel_result = await self.neo4j.execute_query(relationships_query, query_params)
                logger.debug(f"Relationship result from Neo4j: {rel_result}")
            
            logger.info(f"Successfully synchronized score {exam_score_id} to Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing score to Neo4j: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    async def sync_subject_score(self, score_model):
        """
        Synchronize a subject score relationship between a candidate and a subject.
        
        Args:
            score_model: SQLAlchemy SubjectScore model
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        try:
            # Prepare relationship data
            relationship_data = {
                "score": score_model.score,
                "score_date": score_model.score_date
            }
            
            # Synchronize the relationship
            success = await self.candidate_graph_repo.add_scored_in_relationship(
                score_model.candidate_id,
                score_model.subject_id,
                relationship_data
            )
            
            if success:
                logger.info(f"Synchronized subject score for candidate {score_model.candidate_id} in subject {score_model.subject_id}")
            else:
                logger.error(f"Failed to synchronize subject score for candidate {score_model.candidate_id} in subject {score_model.subject_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error synchronizing subject score to Neo4j: {e}")
            return False
    
    async def sync_major(self, major_model):
        """
        Sync a major from PostgreSQL to Neo4j.
        
        Args:
            major_model: SQLAlchemy Major model instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            major_node = MajorNode.from_sql_model(major_model)
            success = await self.major_graph_repo.create_or_update(major_node)
            
            if success:
                logger.info(f"Successfully synced major {major_model.major_id} to Neo4j")
                return True
            else:
                logger.error(f"Failed to sync major {major_model.major_id} to Neo4j")
                return False
        except Exception as e:
            logger.error(f"Error syncing major {major_model.major_id}: {e}")
            return False
    
    async def sync_school_major_relationship(self, school_id, major_id, start_year):
        """
        Sync the relationship between a school and a major.
        
        Args:
            school_id: ID of the school
            major_id: ID of the major
            start_year: Year when the school started offering the major
        """
        try:
            success = await self.school_graph_repo.add_offers_major_relationship(
                school_id, major_id, start_year
            )
            
            if success:
                logger.info(f"Successfully synced school-major relationship: {school_id} -> {major_id}")
            else:
                logger.error(f"Failed to sync school-major relationship: {school_id} -> {major_id}")
        except Exception as e:
            logger.error(f"Error syncing school-major relationship: {e}")
    
    async def sync_candidate_major_relationship(self, candidate_id, major_id):
        """
        Sync the relationship between a candidate and a major.
        
        Args:
            candidate_id: ID of the candidate
            major_id: ID of the major
        """
        try:
            success = await self.candidate_graph_repo.add_studies_major_relationship(
                candidate_id, major_id
            )
            
            if success:
                logger.info(f"Successfully synced candidate-major relationship: {candidate_id} -> {major_id}")
            else:
                logger.error(f"Failed to sync candidate-major relationship: {candidate_id} -> {major_id}")
        except Exception as e:
            logger.error(f"Error syncing candidate-major relationship: {e}")
    
    async def sync_award(self, award_model):
        """
        Sync an award from PostgreSQL to Neo4j.
        
        Args:
            award_model: SQLAlchemy Award model instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Kiểm tra candidate_exam đã được eager loaded chưa
            exam_id = None
            if hasattr(award_model, 'candidate_exam') and award_model.candidate_exam:
                if hasattr(award_model.candidate_exam, 'exam_id'):
                    exam_id = award_model.candidate_exam.exam_id
                    logger.info(f"Award {award_model.award_id}: Found exam_id {exam_id} from candidate_exam")
            
            # Tạo node từ model SQL
            award_node = AwardNode.from_sql_model(award_model)
            
            # Đảm bảo exam_id được set đúng (thêm lại nếu from_sql_model bỏ qua)
            if exam_id and not hasattr(award_node, 'exam_id'):
                award_node.exam_id = exam_id
                logger.info(f"Added exam_id {exam_id} to award_node")
            
            # Tạo hoặc cập nhật node trong Neo4j
            success = await self.award_graph_repo.create_or_update(award_node)
            
            if success:
                logger.info(f"Successfully synced award {award_model.award_id} to Neo4j")
            else:
                logger.error(f"Failed to sync award {award_model.award_id} to Neo4j")
            
            return success
        except Exception as e:
            logger.error(f"Error syncing award {award_model.award_id}: {e}", exc_info=True)
            return False
    
    async def sync_certificate(self, certificate_model):
        """
        Synchronize a certificate from PostgreSQL to Neo4j.
        
        Args:
            certificate_model: SQLAlchemy certificate model or dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log input data
            logger.debug(f"Syncing certificate model: {certificate_model}")
            
            # Handle both dictionary and SQLAlchemy model inputs
            if isinstance(certificate_model, dict):
                certificate_id = certificate_model.get('certificate_id')
                candidate_exam_id = certificate_model.get('candidate_exam_id')
            else:
                certificate_id = getattr(certificate_model, 'certificate_id', None)
                candidate_exam_id = getattr(certificate_model, 'candidate_exam_id', None)
            
            logger.debug(f"Certificate ID: {certificate_id}, Candidate Exam ID: {candidate_exam_id}")
            
            # Initialize candidate_id and exam_id to None
            candidate_id = None
            exam_id = None
            
            # Get candidate_id and exam_id from candidate_exam_id if available
            if candidate_exam_id:
                candidate_exam_repo = self.repository_factory.get_candidate_exam_repository()
                candidate_exam = await candidate_exam_repo.get_by_id(candidate_exam_id)
                
                logger.debug(f"Retrieved candidate_exam: {candidate_exam}")
                
                if candidate_exam:
                    # Extract candidate_id and exam_id based on whether candidate_exam is a dict or model
                    if isinstance(candidate_exam, dict):
                        candidate_id = candidate_exam.get('candidate_id')
                        exam_id = candidate_exam.get('exam_id')
            else:
                    candidate_id = getattr(candidate_exam, 'candidate_id', None)
                    exam_id = getattr(candidate_exam, 'exam_id', None)
                        
                    logger.debug(f"Retrieved candidate_id: {candidate_id} and exam_id: {exam_id}")
                    
                    # Update the certificate_model with candidate_id and exam_id
                    if isinstance(certificate_model, dict):
                        certificate_model['candidate_id'] = candidate_id
                        certificate_model['exam_id'] = exam_id
                    else:
                        setattr(certificate_model, 'candidate_id', candidate_id)
                        setattr(certificate_model, 'exam_id', exam_id)
            
            # Create CertificateNode
            certificate_node = CertificateNode.from_sql_model(certificate_model)
            
            # Explicitly set candidate_id and exam_id on the node
            certificate_node.candidate_id = candidate_id
            certificate_node.exam_id = exam_id
            
            # Execute creation query
            create_query = certificate_node.create_query()
            query_params = certificate_node.to_dict()
            
            logger.debug(f"Executing Neo4j query: {create_query}")
            logger.debug(f"With parameters: {query_params}")
            
            result = await self.neo4j.execute_query(create_query, query_params)
            logger.debug(f"Result from Neo4j: {result}")
            
            # Create relationships if candidate_id and exam_id are available
            if candidate_id or exam_id:
                relationships_query = certificate_node.create_relationships_query()
                
                if relationships_query:
                    logger.debug(f"Executing relationships query: {relationships_query}")
                    logger.debug(f"With parameters for relationships: {query_params}")
                    
                    rel_result = await self.neo4j.execute_query(relationships_query, query_params)
                    logger.debug(f"Relationship result from Neo4j: {rel_result}")
            
            logger.info(f"Successfully synchronized certificate {certificate_id} to Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing certificate to Neo4j: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    async def sync_achievement(self, achievement_model):
        """
        Synchronize an achievement from PostgreSQL to Neo4j.
        
        Args:
            achievement_model: Achievement model from PostgreSQL
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create AchievementNode from model
            achievement_node = AchievementNode.from_sql_model(achievement_model)
            
            # Create/update in Neo4j
            success = await self.achievement_graph_repo.create_or_update(achievement_node)
            
            if success:
                logger.info(f"Successfully synced achievement {achievement_model.achievement_id}")
            else:
                logger.error(f"Failed to sync achievement {achievement_model.achievement_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error syncing achievement {achievement_model.achievement_id}: {e}")
            return False
    
    async def sync_recognition(self, recognition_model):
        """
        Synchronize a recognition from PostgreSQL to Neo4j.
        
        Args:
            recognition_model: Recognition model from PostgreSQL or dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Lấy recognition_id cho logging
            if isinstance(recognition_model, dict):
                recognition_id = recognition_model.get('recognition_id', 'unknown')
                candidate_exam_id = recognition_model.get('candidate_exam_id')
            else:
                recognition_id = getattr(recognition_model, 'recognition_id', 'unknown')
                candidate_exam_id = getattr(recognition_model, 'candidate_exam_id', None)
                
            # Thêm candidate_id và exam_id từ candidate_exam_id nếu có
            candidate_id = None
            exam_id = None
            
            if candidate_exam_id:
                try:
                    # Lấy repository
                    candidate_exam_repo = self.repository_factory.get_candidate_exam_repository()
                    
                    # Lấy thông tin candidate_exam
                    candidate_exam = await candidate_exam_repo.get_by_id(candidate_exam_id)
                    
                    if candidate_exam:
                        # Thêm thông tin vào dictionary hoặc model
                        if isinstance(recognition_model, dict):
                            recognition_model['candidate_id'] = candidate_exam.get('candidate_id')
                            recognition_model['exam_id'] = candidate_exam.get('exam_id')
                            candidate_id = candidate_exam.get('candidate_id')
                            exam_id = candidate_exam.get('exam_id')
                        else:
                            setattr(recognition_model, 'candidate_id', candidate_exam.get('candidate_id'))
                            setattr(recognition_model, 'exam_id', candidate_exam.get('exam_id'))
                            candidate_id = candidate_exam.get('candidate_id')
                            exam_id = candidate_exam.get('exam_id')
                            
                        logger.info(f"Retrieved candidate_id {candidate_id} and exam_id {exam_id} for recognition {recognition_id}")
                except Exception as e:
                    logger.error(f"Error getting candidate_exam data for recognition {recognition_id}: {e}")
            
            # Create RecognitionNode from model
            recognition_node = RecognitionNode.from_sql_model(recognition_model)
            
            # Set candidate_id and exam_id if they were retrieved
            if candidate_id and not recognition_node.candidate_id:
                recognition_node.candidate_id = candidate_id
            
            # Thêm exam_id vào recognition_node (vì RecognitionNode mặc định không có thuộc tính exam_id)
            if exam_id:
                recognition_node.exam_id = exam_id
            
            # Create/update in Neo4j
            success = await self.recognition_graph_repo.create_or_update(recognition_node)
            
            # Tạo mối quan hệ với candidate và exam
            if success and (hasattr(recognition_node, 'candidate_id') or hasattr(recognition_node, 'exam_id')):
                try:
                    # Tạo Cypher query cho mối quan hệ
                    relationship_params = {
                        "recognition_id": recognition_node.recognition_id,
                        "candidate_id": getattr(recognition_node, 'candidate_id', None),
                        "exam_id": getattr(recognition_node, 'exam_id', None)
                    }
                    
                    # Thực thi query
                    result = await self.neo4j.execute_query(
                        recognition_node.create_relationships_query(),
                        relationship_params
                    )
                    
                    if result:
                        logger.info(f"Created relationships for recognition {recognition_id}")
                except Exception as e:
                    logger.error(f"Error creating relationships for recognition {recognition_id}: {e}")
            
            if success:
                logger.info(f"Successfully synced recognition {recognition_id}")
            else:
                logger.error(f"Failed to sync recognition {recognition_id}")
            
            return success
        except Exception as e:
            if isinstance(recognition_model, dict):
                recognition_id = recognition_model.get('recognition_id', 'unknown')
            else:
                recognition_id = getattr(recognition_model, 'recognition_id', 'unknown')
            logger.error(f"Error syncing recognition {recognition_id}: {e}", exc_info=True)
            return False
    
    async def sync_degree(self, degree_model):
        """
        Synchronize a degree from PostgreSQL to Neo4j.
        
        Args:
            degree_model: Degree model from PostgreSQL
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create DegreeNode from model
            degree_node = DegreeNode.from_sql_model(degree_model)
            
            # Create/update in Neo4j
            success = await self.degree_graph_repo.create_or_update(degree_node)
            
            if success:
                logger.info(f"Successfully synced degree {degree_model.degree_id}")
            else:
                logger.error(f"Failed to sync degree {degree_model.degree_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error syncing degree {degree_model.degree_id}: {e}")
            return False
    
    async def sync_credential(self, credential_model):
        """
        Synchronize a credential from PostgreSQL to Neo4j.
        
        Args:
            credential_model: Credential model from PostgreSQL
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create CredentialNode from model
            credential_node = CredentialNode.from_sql_model(credential_model)
            
            # Create/update in Neo4j
            success = await self.credential_graph_repo.create_or_update(credential_node)
            
            if success:
                logger.info(f"Successfully synced credential {credential_model.credential_id}")
            else:
                logger.error(f"Failed to sync credential {credential_model.credential_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error syncing credential {credential_model.credential_id}: {e}")
            return False
    
    # ----- Bulk Synchronization Methods -----
    
    async def bulk_sync_candidates(self):
        """
        Synchronize all candidates from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of candidates synchronized
        """
        try:
            # Get candidate repository
            candidate_repo = self.repository_factory.get_candidate_repository()
            
            # Get all candidates with related personal info
            candidates = await candidate_repo.get_all(include_personal_info=True)
            
            logger.info(f"Retrieved {len(candidates)} candidates from PostgreSQL")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each candidate
            for candidate in candidates:
                logger.info(f"Syncing candidate {candidate.candidate_id}")
                if await self.sync_candidate(candidate):
                    success_count += 1
            
            logger.info(f"Successfully synchronized {success_count} candidates")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing candidates: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_schools(self):
        """
        Bulk sync schools from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of schools synchronized
        """
        try:
            # Get school repository
            school_repo = self.repository_factory.get_school_repository()
            
            # Get all schools
            schools_result = await school_repo.get_all()
            
            # Trích xuất danh sách schools
            schools_list = self.extract_items(schools_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(schools_list)} schools to synchronize")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each school
            for school in schools_list:
                try:
                    if await self.sync_school(school):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing school: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} schools")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk sync of schools: {e}")
            return 0
    
    def extract_items(self, result):
        """
        Trích xuất danh sách các mục từ kết quả trả về từ repository.
        
        Args:
            result: Kết quả trả về từ phương thức get_all() của repository
            
        Returns:
            list: Danh sách các items
        """
        items_list = []
        
        # Kiểm tra định dạng kết quả trả về
        if isinstance(result, tuple):
            # Kết quả thường là (items, count)
            if len(result) > 0:
                # Nếu phần tử đầu tiên là list hoặc object iterable (chủ yếu ORM objects)
                if isinstance(result[0], list):
                    items_list = result[0]
                elif hasattr(result[0], '__iter__') and not isinstance(result[0], (str, bytes, dict)):
                    items_list = list(result[0])
                # Nếu phần tử thứ nhất là số (count), phần tử thứ hai là list
                elif isinstance(result[0], (int, float)) and len(result) > 1:
                    if isinstance(result[1], list):
                        items_list = result[1]
                    elif hasattr(result[1], '__iter__') and not isinstance(result[1], (str, bytes, dict)):
                        items_list = list(result[1])
            
            # Debug log để kiểm tra
            logger.debug(f"extract_items: tuple result with length {len(result)}, extracted {len(items_list)} items")
        elif isinstance(result, list):
            # Nếu kết quả là list thì gán trực tiếp
            items_list = result
            logger.debug(f"extract_items: list result with {len(items_list)} items")
        else:
            # Trong trường hợp đó là một ORM object (không phải list hay tuple)
            # Ví dụ: một kết quả trả về từ scalars().all()
            if hasattr(result, '__iter__') and not isinstance(result, (str, bytes, dict)):
                items_list = list(result)
                logger.debug(f"extract_items: iterable result, extracted {len(items_list)} items")
        
        return items_list

    async def bulk_sync_exams(self):
        """
        Bulk sync exams from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of exams synchronized
        """
        try:
            # Get exam repository
            exam_repo = self.repository_factory.get_exam_repository()
            
            # Get all exams
            exams_result = await exam_repo.get_all()
            
            # Trích xuất danh sách exams
            exams_list = self.extract_items(exams_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(exams_list)} exams to synchronize")
            
            # Ghi log thêm thông tin về danh sách exams
            if len(exams_list) == 0:
                logger.warning("No exams found in the database to synchronize")
            else:
                exam_ids = [exam.get('exam_id', 'unknown_id') if isinstance(exam, dict) else 
                           getattr(exam, 'exam_id', 'unknown_id') for exam in exams_list[:5]]
                logger.info(f"First few exam IDs: {', '.join(exam_ids)}")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each exam
            for exam in exams_list:
                try:
                    exam_id = exam.get('exam_id', 'unknown_id') if isinstance(exam, dict) else getattr(exam, 'exam_id', 'unknown_id')
                    logger.info(f"Syncing exam {exam_id}")
                    if await self.sync_exam(exam):
                        success_count += 1
                    else:
                        logger.warning(f"Failed to sync exam {exam_id}")
                except Exception as e:
                    exam_id = exam.get('exam_id', 'unknown_id') if isinstance(exam, dict) else getattr(exam, 'exam_id', 'unknown_id')
                    logger.error(f"Error synchronizing exam {exam_id}: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} exams")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk sync of exams: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_subjects(self):
        """
        Bulk sync subjects from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of subjects synchronized
        """
        try:
            # Get subject repository
            subject_repo = self.repository_factory.get_subject_repository()
            
            # Get all subjects
            subjects_result = await subject_repo.get_all()
            
            # Trích xuất danh sách subjects
            subjects_list = self.extract_items(subjects_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(subjects_list)} subjects to synchronize")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each subject
            for subject in subjects_list:
                try:
                    if await self.sync_subject(subject):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing subject: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} subjects")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk sync of subjects: {e}")
            return 0
    
    async def bulk_sync_scores(self):
        """
        Bulk sync scores from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of scores synchronized
        """
        try:
            # Get score repository
            score_repo = self.repository_factory.get_score_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("Fetching scores from repository")
            
            # Get all scores
            scores_result = await score_repo.get_all()
            
            # Log raw result để debug
            logger.info(f"Raw result from score_repo.get_all(): {str(scores_result)[:100]}")
            
            # Trích xuất danh sách scores
            scores_list = self.extract_items(scores_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(scores_list)} scores to synchronize")
            
            # Log type of result
            if len(scores_list) > 0:
                first_item = scores_list[0]
                logger.info(f"First score item type: {type(first_item).__name__}")
                if hasattr(first_item, 'score_id'):
                    logger.info(f"First score ID: {first_item.score_id}")
                elif isinstance(first_item, dict) and 'score_id' in first_item:
                    logger.info(f"First score ID: {first_item['score_id']}")
            else:
                logger.warning("No scores found in database")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each score
            for score in scores_list:
                try:
                    if await self.sync_score(score):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing score: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} scores")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk sync of scores: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_majors(self):
        """
        Bulk sync majors from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of majors synchronized
        """
        try:
            # Get major repository
            major_repo = self.repository_factory.get_major_repository()
            
            # Get all majors
            majors_result = await major_repo.get_all()
            
            # Trích xuất danh sách majors
            majors_list = self.extract_items(majors_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(majors_list)} majors to synchronize")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each major
            for major in majors_list:
                try:
                    if await self.sync_major(major):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing major: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} majors")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk sync of majors: {e}")
            return 0
    
    async def bulk_sync_awards(self):
        """
        Bulk sync awards from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of awards synchronized
        """
        try:
            # Get award repository
            award_repo = self.repository_factory.get_award_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("==== DEBUGGING: bulk_sync_awards() ĐƯỢC GỌI ====")
            logger.info("Fetching awards from repository")
            print("Fetching awards from repository")
            
            # Get all awards (gọi repository với eager loading)
            # AwardRepository.get_all() đã có joinedload CandidateExam, Candidate, và Exam
            awards_result = await award_repo.get_all(limit=100)
            
            # Log raw result để debug chi tiết
            if awards_result:
                if isinstance(awards_result, tuple) and len(awards_result) >= 2:
                    logger.info(f"Raw result structure: tuple with {len(awards_result)} elements")
                    logger.info(f"First element type: {type(awards_result[0]).__name__}")
                    logger.info(f"Second element type: {type(awards_result[1]).__name__}")
                    logger.info(f"Total count: {awards_result[1]}")
                else:
                    logger.info(f"Raw result type: {type(awards_result).__name__}")
            
            # Trích xuất danh sách awards
            awards_list = self.extract_items(awards_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(awards_list)} awards to synchronize")
            print(f"Found {len(awards_list)} awards to synchronize")
            
            # Log type of result
            if len(awards_list) > 0:
                first_item = awards_list[0]
                logger.info(f"First award item type: {type(first_item).__name__}")
                
                if hasattr(first_item, 'award_id'):
                    logger.info(f"First award ID: {first_item.award_id}")
                    
                    # Kiểm tra xem candidate_exam có được nạp không
                    if hasattr(first_item, 'candidate_exam') and first_item.candidate_exam:
                        logger.info(f"candidate_exam is loaded: {first_item.candidate_exam.candidate_exam_id}")
                        
                        # Kiểm tra xem exam_id có trong candidate_exam không
                        if hasattr(first_item.candidate_exam, 'exam_id'):
                            logger.info(f"exam_id found: {first_item.candidate_exam.exam_id}")
                        else:
                            logger.warning("exam_id not found in candidate_exam")
                    else:
                        logger.warning("candidate_exam not loaded")
            else:
                logger.warning("No awards found in database")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each award
            for award in awards_list:
                try:
                    # Bỏ qua nếu không tồn tại candidate_exam
                    if not hasattr(award, 'candidate_exam') or not award.candidate_exam:
                        logger.warning(f"Skipping award {award.award_id} - missing candidate_exam relation")
                        continue
                        
                    if await self.sync_award(award):
                        success_count += 1
                        logger.info(f"Successfully synchronized award: {award.award_id}")
                    else:
                        logger.warning(f"Failed to sync award: {award.award_id}")
                except Exception as e:
                    logger.error(f"Error synchronizing award: {e}", exc_info=True)
                    continue
            
            logger.info(f"Successfully synchronized {success_count} awards")
            print(f"Successfully synchronized {success_count} awards")
            return success_count
        except Exception as e:
            error_msg = f"Error in bulk sync of awards: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(error_msg)
            import traceback
            print(traceback.format_exc())
            return 0
    
    async def bulk_sync_school_major_relationships(self):
        """
        Bulk sync school-major relationships from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of relationships synchronized
        """
        try:
            # This would need to be implemented based on how these relationships are stored
            # Example implementation would query a join table
            return 0
        except Exception as e:
            logger.error(f"Error in bulk synchronizing school-major relationships: {e}")
            return 0
    
    async def bulk_sync_candidate_major_relationships(self):
        """
        Bulk sync candidate-major relationships from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of relationships synchronized
        """
        try:
            # This would need to be implemented based on how these relationships are stored
            # Example implementation would query a join table
            return 0
        except Exception as e:
            logger.error(f"Error in bulk synchronizing candidate-major relationships: {e}")
            return 0
    
    async def bulk_sync_certificates(self):
        """
        Synchronize all certificates from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of certificates synchronized
        """
        try:
            # Get certificate repository
            certificate_repo = self.repository_factory.get_certificate_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("Fetching certificates from repository")
            
            # Get all certificates
            certificates_result = await certificate_repo.get_all()
            
            # Log raw result để debug
            logger.info(f"Raw result from certificate_repo.get_all(): {str(certificates_result)[:100]}")
            
            # Trích xuất danh sách certificates
            certificates_list = self.extract_items(certificates_result)
            
            # Log thông tin về kết quả
            total_certificates = len(certificates_list)
            logger.info(f"Found {total_certificates} certificates to synchronize")
            
            # Log type of result
            if total_certificates > 0:
                first_item = certificates_list[0]
                logger.info(f"First certificate item type: {type(first_item).__name__}")
                if hasattr(first_item, 'certificate_id'):
                    logger.info(f"First certificate ID: {first_item.certificate_id}")
                elif isinstance(first_item, dict) and 'certificate_id' in first_item:
                    logger.info(f"First certificate ID: {first_item['certificate_id']}")
            else:
                logger.warning("No certificates found in database")
                return 0
            
            # Track successful syncs
            success_count = 0
            
            # Sync each certificate
            for certificate in certificates_list:
                try:
                    cert_id = certificate.get('certificate_id') if isinstance(certificate, dict) else getattr(certificate, 'certificate_id', 'unknown')
                    
                    if await self.sync_certificate(certificate):
                        success_count += 1
                        logger.info(f"Successfully synchronized certificate {cert_id}")
                    else:
                        logger.warning(f"Failed to sync certificate with ID: {cert_id}")
                except Exception as e:
                    cert_id = certificate.get('certificate_id') if isinstance(certificate, dict) else getattr(certificate, 'certificate_id', 'unknown')
                    logger.error(f"Error synchronizing certificate with ID {cert_id}: {e}", exc_info=True)
                    continue
            
            logger.info(f"Successfully synchronized {success_count} out of {total_certificates} certificates")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing certificates: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_achievements(self):
        """
        Synchronize all achievements from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of achievements synchronized
        """
        try:
            # Get achievement repository
            achievement_repo = self.repository_factory.get_achievement_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("Fetching achievements from repository")
            
            # Get all achievements
            achievements_result = await achievement_repo.get_all()
            
            # Log raw result để debug
            logger.info(f"Raw result from achievement_repo.get_all(): {str(achievements_result)[:100]}")
            
            # Trích xuất danh sách achievements
            achievements_list = self.extract_items(achievements_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(achievements_list)} achievements to synchronize")
            
            # Log type of result
            if len(achievements_list) > 0:
                first_item = achievements_list[0]
                logger.info(f"First achievement item type: {type(first_item).__name__}")
                if hasattr(first_item, 'achievement_id'):
                    logger.info(f"First achievement ID: {first_item.achievement_id}")
                elif isinstance(first_item, dict) and 'achievement_id' in first_item:
                    logger.info(f"First achievement ID: {first_item['achievement_id']}")
            else:
                logger.warning("No achievements found in database")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each achievement
            for achievement in achievements_list:
                try:
                    if await self.sync_achievement(achievement):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing achievement: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} achievements")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing achievements: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_recognitions(self):
        """
        Synchronize all recognitions from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of recognitions synchronized
        """
        try:
            # Get recognition repository
            recognition_repo = self.repository_factory.get_recognition_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("Fetching recognitions from repository")
            
            # Get all recognitions
            recognitions_result = await recognition_repo.get_all()
            
            # Log raw result để debug
            logger.info(f"Raw result from recognition_repo.get_all(): {str(recognitions_result)[:100]}")
            
            # Trích xuất danh sách recognitions
            recognitions_list = self.extract_items(recognitions_result)
            
            # Log thông tin về kết quả
            total_recognitions = len(recognitions_list)
            logger.info(f"Found {total_recognitions} recognitions to synchronize")
            
            # Log type of result
            if total_recognitions > 0:
                first_item = recognitions_list[0]
                logger.info(f"First recognition item type: {type(first_item).__name__}")
                if hasattr(first_item, 'recognition_id'):
                    logger.info(f"First recognition ID: {first_item.recognition_id}")
                elif isinstance(first_item, dict) and 'recognition_id' in first_item:
                    logger.info(f"First recognition ID: {first_item['recognition_id']}")
            else:
                logger.warning("No recognitions found in database")
                return 0
            
            # Track successful syncs
            success_count = 0
            
            # Sync each recognition
            for recognition in recognitions_list:
                try:
                    rec_id = recognition.get('recognition_id') if isinstance(recognition, dict) else getattr(recognition, 'recognition_id', 'unknown')
                    
                    if await self.sync_recognition(recognition):
                        success_count += 1
                        logger.info(f"Successfully synchronized recognition with ID: {rec_id}")
                    else:
                        logger.warning(f"Failed to sync recognition with ID: {rec_id}")
                except Exception as e:
                    rec_id = recognition.get('recognition_id') if isinstance(recognition, dict) else getattr(recognition, 'recognition_id', 'unknown')
                    logger.error(f"Error synchronizing recognition with ID {rec_id}: {e}", exc_info=True)
                    continue
            
            logger.info(f"Successfully synchronized {success_count} out of {total_recognitions} recognitions")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing recognitions: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_degrees(self):
        """
        Synchronize all degrees from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of degrees synchronized
        """
        try:
            # Get degree repository
            degree_repo = self.repository_factory.get_degree_repository()
            
            # Get all degrees
            degrees_result = await degree_repo.get_all()
            
            # Trích xuất danh sách degrees
            degrees_list = self.extract_items(degrees_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(degrees_list)} degrees to synchronize")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each degree
            for degree in degrees_list:
                try:
                    if await self.sync_degree(degree):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing degree: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} degrees")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing degrees: {e}")
            return 0
    
    async def bulk_sync_credentials(self):
        """
        Synchronize all credentials from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of credentials synchronized
        """
        try:
            # Get credential repository
            credential_repo = self.repository_factory.get_credential_repository()
            
            # Get all credentials
            credentials_result = await credential_repo.get_all()
            
            # Trích xuất danh sách credentials
            credentials_list = self.extract_items(credentials_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(credentials_list)} credentials to synchronize")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each credential
            for credential in credentials_list:
                try:
                    if await self.sync_credential(credential):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing credential: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} credentials")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing credentials: {e}")
            return 0
    
    async def sync_ontology_relationships(self):
        """
        Synchronize INSTANCE_OF relationships for all existing nodes with their corresponding class nodes.
        """
        try:
            # Sync Candidate nodes
            query = """
            MATCH (instance:Candidate:OntologyInstance)
            MATCH (class:Candidate:OntologyClass {id: 'candidate-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            # Handle different possible result structures
            if result and len(result) > 0:
                # Check if result is a list of records/dictionaries
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                # Check if result[0] is a list or tuple
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                # If result[0] has count attribute
                elif hasattr(result[0], 'count'):
                    count = result[0].count
                else:
                    # Try to convert to string and log for debugging
                    logger.debug(f"Unexpected result structure: {str(result)}")
                    count = 0
            else:
                count = 0
            logger.info(f"Created {count} INSTANCE_OF relationships for Candidate nodes")

            # Sync School nodes
            query = """
            MATCH (instance:School:OntologyInstance)
            MATCH (class:School:OntologyClass {id: 'school-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            # Handle different possible result structures
            if result and len(result) > 0:
                # Check if result is a list of records/dictionaries
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                # Check if result[0] is a list or tuple
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                # If result[0] has count attribute
                elif hasattr(result[0], 'count'):
                    count = result[0].count
                else:
                    # Try to convert to string and log for debugging
                    logger.debug(f"Unexpected result structure: {str(result)}")
                    count = 0
            else:
                count = 0
            logger.info(f"Created {count} INSTANCE_OF relationships for School nodes")

            # Sync Exam nodes
            query = """
            MATCH (instance:Exam:OntologyInstance)
            MATCH (class:Exam:OntologyClass {id: 'exam-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            # Handle different possible result structures
            if result and len(result) > 0:
                # Check if result is a list of records/dictionaries
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                # Check if result[0] is a list or tuple
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                # If result[0] has count attribute
                elif hasattr(result[0], 'count'):
                    count = result[0].count
                else:
                    # Try to convert to string and log for debugging
                    logger.debug(f"Unexpected result structure: {str(result)}")
                    count = 0
            else:
                count = 0
            logger.info(f"Created {count} INSTANCE_OF relationships for Exam nodes")

            # Sync Subject nodes
            query = """
            MATCH (instance:Subject:OntologyInstance)
            MATCH (class:Subject:OntologyClass {id: 'subject-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            # Handle different possible result structures
            if result and len(result) > 0:
                # Check if result is a list of records/dictionaries
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                # Check if result[0] is a list or tuple
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                # If result[0] has count attribute
                elif hasattr(result[0], 'count'):
                    count = result[0].count
                else:
                    # Try to convert to string and log for debugging
                    logger.debug(f"Unexpected result structure: {str(result)}")
                    count = 0
            else:
                count = 0
            logger.info(f"Created {count} INSTANCE_OF relationships for Subject nodes")

            # Sync Credential nodes
            query = """
            MATCH (instance:Credential:OntologyInstance)
            MATCH (class:Credential:OntologyClass {id: 'credential-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            count = 0
            if result and len(result) > 0:
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                elif hasattr(result[0], 'count'):
                    count = result[0].count
            logger.info(f"Created {count} INSTANCE_OF relationships for Credential nodes")

            # Sync Degree nodes
            query = """
            MATCH (instance:Degree:OntologyInstance)
            MATCH (class:Degree:OntologyClass {id: 'degree-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            count = 0
            if result and len(result) > 0:
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                elif hasattr(result[0], 'count'):
                    count = result[0].count
            logger.info(f"Created {count} INSTANCE_OF relationships for Degree nodes")

            # Sync Major nodes
            query = """
            MATCH (instance:Major:OntologyInstance)
            MATCH (class:Major:OntologyClass {id: 'major-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            count = 0
            if result and len(result) > 0:
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                elif hasattr(result[0], 'count'):
                    count = result[0].count
            logger.info(f"Created {count} INSTANCE_OF relationships for Major nodes")

            # Sync ManagementUnit nodes
            query = """
            MATCH (instance:ManagementUnit:OntologyInstance)
            MATCH (class:ManagementUnit:OntologyClass {id: 'managementunit-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            count = 0
            if result and len(result) > 0:
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                elif hasattr(result[0], 'count'):
                    count = result[0].count
            logger.info(f"Created {count} INSTANCE_OF relationships for ManagementUnit nodes")

            # Sync Award nodes
            query = """
            MATCH (instance:Award:OntologyInstance)
            MATCH (class:Award:OntologyClass {id: 'award-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            count = 0
            if result and len(result) > 0:
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                elif hasattr(result[0], 'count'):
                    count = result[0].count
            logger.info(f"Created {count} INSTANCE_OF relationships for Award nodes")

            # Sync Certificate nodes
            query = """
            MATCH (instance:Certificate:OntologyInstance)
            MATCH (class:Certificate:OntologyClass {id: 'certificate-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            count = 0
            if result and len(result) > 0:
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                elif hasattr(result[0], 'count'):
                    count = result[0].count
            logger.info(f"Created {count} INSTANCE_OF relationships for Certificate nodes")

            # Sync Recognition nodes
            query = """
            MATCH (instance:Recognition:OntologyInstance)
            MATCH (class:Recognition:OntologyClass {id: 'recognition-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            count = 0
            if result and len(result) > 0:
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                elif hasattr(result[0], 'count'):
                    count = result[0].count
            logger.info(f"Created {count} INSTANCE_OF relationships for Recognition nodes")

            # Sync Achievement nodes
            query = """
            MATCH (instance:Achievement:OntologyInstance)
            MATCH (class:Achievement:OntologyClass {id: 'achievement-class'})
            MERGE (instance)-[r:INSTANCE_OF]->(class)
            RETURN count(r) as count
            """
            result = await self.neo4j.execute_query(query)
            count = 0
            if result and len(result) > 0:
                if hasattr(result[0], 'get'):
                    count = result[0].get('count', 0)
                elif isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    count = result[0][0]
                elif hasattr(result[0], 'count'):
                    count = result[0].count
            logger.info(f"Created {count} INSTANCE_OF relationships for Achievement nodes")

        except Exception as e:
            logger.error(f"Error syncing ontology relationships: {e}")
            raise

    async def bulk_sync_all(self, resync_ontology=True):
        """
        Đồng bộ tất cả dữ liệu từ PostgreSQL sang Neo4j.
        
        Args:
            resync_ontology (bool): Nếu True, sẽ tạo lại các mối quan hệ INSTANCE_OF 
                                  cho tất cả các node hiện có với class node tương ứng.
        
        Returns:
            dict: Kết quả đồng bộ với số lượng entity được đồng bộ cho mỗi loại
        """
        try:
            results = {}
            
            # Đồng bộ các entity
            results["candidates"] = await self.bulk_sync_candidates()
            results["schools"] = await self.bulk_sync_schools()
            results["exams"] = await self.bulk_sync_exams()
            results["subjects"] = await self.bulk_sync_subjects()
            results["majors"] = await self.bulk_sync_majors()
            results["exam_locations"] = await self.bulk_sync_exam_locations()
            results["exam_rooms"] = await self.bulk_sync_exam_rooms()
            results["exam_schedules"] = await self.bulk_sync_exam_schedules()
            results["exam_attempts"] = await self.bulk_sync_exam_attempts()
            results["scores"] = await self.bulk_sync_scores()
            results["score_reviews"] = await self.bulk_sync_score_reviews()
            results["score_histories"] = await self.bulk_sync_score_histories()
            results["certificates"] = await self.bulk_sync_certificates()
            results["awards"] = await self.bulk_sync_awards()
            results["achievements"] = await self.bulk_sync_achievements()
            results["recognitions"] = await self.bulk_sync_recognitions()
            results["degrees"] = await self.bulk_sync_degrees()
            results["credentials"] = await self.bulk_sync_credentials()
            results["management_units"] = await self.bulk_sync_management_units()
            
            # Đồng bộ các mối quan hệ
            results["candidate_exam_relationships"] = await self.bulk_sync_candidate_exam_relationships()
            
            # Đồng bộ lại các mối quan hệ ontology nếu được yêu cầu
            if resync_ontology:
                await self.sync_ontology_relationships()
                logger.info("Completed ontology relationship synchronization")
            
            logger.info(f"Completed bulk sync with results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error during bulk sync: {e}", exc_info=True)
            raise
    
    async def sync_score_history(self, history_model):
        """
        Đồng bộ một bản ghi lịch sử điểm từ PostgreSQL sang Neo4j.
        
        Args:
            history_model: SQLAlchemy ScoreHistory model
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            # Tạo node từ model SQL
            history_node = ScoreHistoryNode.from_sql_model(history_model)
            
            # Sử dụng repository để tạo/cập nhật trong Neo4j
            success = await self.score_history_graph_repository.create_or_update(history_node)
            
            if success:
                logger.info(f"Successfully synchronized score history {history_model.history_id}")
            else:
                logger.warning(f"Failed to synchronize score history {history_model.history_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error synchronizing score history {history_model.history_id}: {e}")
            return False
            
    async def sync_management_unit(self, unit_model):
        """
        Đồng bộ một đơn vị quản lý từ PostgreSQL sang Neo4j.
        
        Args:
            unit_model: SQLAlchemy ManagementUnit model
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Tạo node từ model
            unit_node = ManagementUnitNode.from_sql_model(unit_model)
            
            # Sử dụng repository để tạo/cập nhật trong Neo4j
            result = await self.management_unit_graph_repo.create_or_update(unit_node)
            
            if result:
                logger.info(f"Successfully synchronized management unit {unit_model.unit_id}")
                return True
            else:
                logger.warning(f"Failed to synchronize management unit {unit_model.unit_id}")
                return False
        except Exception as e:
            logger.error(f"Error synchronizing management unit {unit_model.unit_id}: {e}")
            return False
    
    async def bulk_sync_exam_locations(self):
        """
        Synchronize all exam locations from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized exam locations
        """
        try:
            logger.info("Starting bulk synchronization of exam locations")
            
            # Get exam location repository
            location_repo = self.repository_factory.get_exam_location_repository()
            
            # Get exam location mapping repository to establish relationships
            exam_mapping_repo = self.repository_factory.get_exam_location_mapping_repository()
            
            # Get all locations
            locations_result = await location_repo.get_all_raw()
            
            # Log structure of the result for debugging
            logger.debug(f"Location result type: {type(locations_result)}")
            if hasattr(locations_result, 'keys'):
                logger.debug(f"Location result keys: {locations_result.keys()}")
            
            # Extract list of locations
            locations = locations_result.get('results', []) if isinstance(locations_result, dict) else locations_result
            
            logger.info(f"Found {len(locations)} exam locations to synchronize")
            if locations:
                logger.debug(f"First location type: {type(locations[0])}")
            
            # Initialize success counter
            success_count = 0
            
            # Synchronize each location
            for location in locations:
                try:
                    # Sync the location to Neo4j
                    success = await self.sync_exam_location(location)
                    
                    if success:
                        # Get location ID
                        location_id = location.get('exam_location_id') if isinstance(location, dict) else getattr(location, 'exam_location_id', None)
                        
                        # Find exams associated with this location
                        exam_mappings = await exam_mapping_repo.get_exams_by_location_id(location_id)
                        
                        # Log number of mappings found
                        logger.debug(f"Found {len(exam_mappings) if exam_mappings else 0} exam mappings for location {location_id}")
                        
                        # For each mapping, create a relationship in Neo4j
                        if exam_mappings:
                            for mapping in exam_mappings:
                                # Get exam ID from mapping
                                exam_id = mapping.get('exam_id') if isinstance(mapping, dict) else getattr(mapping, 'exam_id', None)
                                
                                if exam_id:
                                    # Create relationship query
                                    relationship_query = """
                                    MATCH (l:ExamLocation {location_id: $location_id})
                                    MATCH (e:Exam {exam_id: $exam_id})
                                    MERGE (l)-[:HOSTS]->(e)
                                    """
                                    
                                    # Execute relationship query
                                    try:
                                        logger.debug(f"Creating relationship between location {location_id} and exam {exam_id}")
                                        await self.neo4j.execute_query(
                                            relationship_query, 
                                            {"location_id": location_id, "exam_id": exam_id}
                                        )
                                        logger.debug(f"Successfully created relationship between location {location_id} and exam {exam_id}")
                                    except Exception as e:
                                        logger.error(f"Error creating relationship between location {location_id} and exam {exam_id}: {str(e)}")
                        
                        # Increment success counter
                        success_count += 1
                        logger.info(f"Successfully synchronized exam location {location_id} to Neo4j")
                    else:
                        location_id = location.get('exam_location_id') if isinstance(location, dict) else getattr(location, 'exam_location_id', None)
                        logger.warning(f"Failed to synchronize exam location {location_id} to Neo4j")
                except Exception as e:
                    location_id = location.get('exam_location_id') if isinstance(location, dict) else getattr(location, 'exam_location_id', None)
                    logger.error(f"Error synchronizing exam location {location_id} to Neo4j: {str(e)}")
                    logger.error(traceback.format_exc())
            
            logger.info(f"Successfully synchronized {success_count} out of {len(locations)} exam locations")
            return success_count
        except Exception as e:
            logger.error(f"Error during bulk synchronization of exam locations: {str(e)}")
            logger.error(traceback.format_exc())
            return 0
    
    async def bulk_sync_exam_rooms(self):
        """
        Synchronize all exam rooms from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of exam rooms synchronized
        """
        try:
            # Get exam room repository
            room_repo = self.repository_factory.get_exam_room_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("Fetching exam rooms from repository")
            
            # Get all exam rooms 
            rooms_result = await room_repo.get_all()
            
            # Log raw result để debug
            logger.info(f"Raw result from room_repo.get_all(): {str(rooms_result)[:100]}")
            
            # Trích xuất danh sách rooms
            rooms_list = self.extract_items(rooms_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(rooms_list)} exam rooms to synchronize")
            
            # Log type of result
            if len(rooms_list) > 0:
                first_item = rooms_list[0]
                logger.info(f"First room item type: {type(first_item).__name__}")
                if hasattr(first_item, 'room_id'):
                    logger.info(f"First room ID: {first_item.room_id}")
                elif isinstance(first_item, dict) and 'room_id' in first_item:
                    logger.info(f"First room ID: {first_item['room_id']}")
            else:
                logger.warning("No exam rooms found in database")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each room
            for room in rooms_list:
                try:
                    if await self.sync_exam_room(room):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing exam room: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} exam rooms")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing exam rooms: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_exam_schedules(self):
        """
        Synchronize all exam schedules from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of exam schedules synchronized
        """
        try:
            # Get exam schedule repository
            schedule_repo = self.repository_factory.get_exam_schedule_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("Fetching exam schedules from repository")
            
            # Get all exam schedules
            schedules_result = await schedule_repo.get_all()
            
            # Log raw result để debug
            logger.info(f"Raw result from schedule_repo.get_all(): {str(schedules_result)[:100]}")
            
            # Trích xuất danh sách schedules
            schedules_list = self.extract_items(schedules_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(schedules_list)} exam schedules to synchronize")
            
            # Log type of result
            if len(schedules_list) > 0:
                first_item = schedules_list[0]
                logger.info(f"First schedule item type: {type(first_item).__name__}")
                if hasattr(first_item, 'schedule_id'):
                    logger.info(f"First schedule ID: {first_item.schedule_id}")
                elif isinstance(first_item, dict) and 'schedule_id' in first_item:
                    logger.info(f"First schedule ID: {first_item['schedule_id']}")
            else:
                logger.warning("No exam schedules found in database")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each schedule
            for schedule in schedules_list:
                try:
                    if await self.sync_exam_schedule(schedule):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing exam schedule: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} exam schedules")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing exam schedules: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_exam_attempts(self):
        """
        Synchronize all exam attempts from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of exam attempts synchronized
        """
        try:
            # Get exam attempt repository
            attempt_repo = self.repository_factory.get_exam_attempt_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("Fetching exam attempts from repository")
            
            # Get all exam attempts
            attempts_result = await attempt_repo.get_all()
            
            # Log raw result để debug
            logger.info(f"Raw result from attempt_repo.get_all(): {str(attempts_result)[:100]}")
            
            # Trích xuất danh sách attempts
            attempts_list = self.extract_items(attempts_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(attempts_list)} exam attempts to synchronize")
            
            # Log type of result
            if len(attempts_list) > 0:
                first_item = attempts_list[0]
                logger.info(f"First attempt item type: {type(first_item).__name__}")
                if hasattr(first_item, 'attempt_id'):
                    logger.info(f"First attempt ID: {first_item.attempt_id}")
                elif isinstance(first_item, dict) and 'attempt_id' in first_item:
                    logger.info(f"First attempt ID: {first_item['attempt_id']}")
            else:
                logger.warning("No exam attempts found in database")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each attempt
            for attempt in attempts_list:
                try:
                    if await self.sync_exam_attempt(attempt):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing exam attempt: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} exam attempts")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing exam attempts: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_score_reviews(self):
        """
        Synchronize all score reviews from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of score reviews synchronized
        """
        try:
            # Get score review repository
            review_repo = self.repository_factory.get_score_review_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("Fetching score reviews from repository")
            
            # Get all score reviews
            reviews_result = await review_repo.get_all()
            
            # Log raw result để debug
            logger.info(f"Raw result from review_repo.get_all(): {str(reviews_result)[:100]}")
            
            # Trích xuất danh sách reviews
            reviews_list = self.extract_items(reviews_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(reviews_list)} score reviews to synchronize")
            
            # Log type of result
            if len(reviews_list) > 0:
                first_item = reviews_list[0]
                logger.info(f"First score review item type: {type(first_item).__name__}")
                if hasattr(first_item, 'review_id'):
                    logger.info(f"First score review ID: {first_item.review_id}")
                elif isinstance(first_item, dict) and 'review_id' in first_item:
                    logger.info(f"First score review ID: {first_item['review_id']}")
            else:
                logger.warning("No score reviews found in database")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each review
            for review in reviews_list:
                try:
                    if isinstance(review, dict) and 'review_id' in review:
                        if await self.sync_score_review(review):
                            success_count += 1
                    else:
                        logger.warning(f"Skipping invalid review record: {review}")
                except Exception as e:
                    logger.error(f"Error synchronizing score review: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} score reviews")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing score reviews: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_score_histories(self):
        """
        Synchronize all score histories from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of score histories synchronized
        """
        try:
            # Get score history repository
            history_repo = self.repository_factory.get_score_history_repository()
            
            # Log trước khi gọi get_all để debug
            logger.info("Fetching score histories from repository")
            
            # Get all score histories
            histories_result = await history_repo.get_all()
            
            # Log raw result để debug
            logger.info(f"Raw result from history_repo.get_all(): {str(histories_result)[:100]}")
            
            # Trích xuất danh sách histories
            histories_list = self.extract_items(histories_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(histories_list)} score histories to synchronize")
            
            # Log type of result
            if len(histories_list) > 0:
                first_item = histories_list[0]
                logger.info(f"First history item type: {type(first_item).__name__}")
                if hasattr(first_item, 'history_id'):
                    logger.info(f"First history ID: {first_item.history_id}")
                elif isinstance(first_item, dict) and 'history_id' in first_item:
                    logger.info(f"First history ID: {first_item['history_id']}")
            else:
                logger.warning("No score histories found in database")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each history
            for history in histories_list:
                try:
                    if isinstance(history, dict) and 'history_id' in history:
                        if await self.sync_score_history(history):
                            success_count += 1
                    else:
                        logger.warning(f"Skipping invalid history record: {history}")
                except Exception as e:
                    logger.error(f"Error synchronizing score history: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} score histories")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk synchronizing score histories: {e}", exc_info=True)
            return 0
    
    async def bulk_sync_management_units(self):
        """
        Bulk sync management units from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of units synchronized
        """
        try:
            # Get management unit repository
            unit_repo = self.repository_factory.get_management_unit_repository()
            
            # Get all management units
            units_result = await unit_repo.get_all()
            
            # Trích xuất danh sách management units
            units_list = self.extract_items(units_result)
            
            # Log thông tin về kết quả
            logger.info(f"Found {len(units_list)} management units to synchronize")
            
            # Track successful syncs
            success_count = 0
            
            # Sync each unit
            for unit in units_list:
                try:
                    if await self.sync_management_unit(unit):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing management unit: {e}")
                    continue
            
            logger.info(f"Successfully synchronized {success_count} management units")
            return success_count
        except Exception as e:
            logger.error(f"Error in bulk sync of management units: {e}")
            return 0

    async def sync_exam_location(self, exam_location_model):
        """
        Synchronize an exam location from PostgreSQL to Neo4j.
        
        Args:
            exam_location_model: PostgreSQL model or dictionary containing exam location data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug(f"Syncing exam location: {exam_location_model}")
            
            # Extract exam_location_id based on whether it's a dict or SQLAlchemy model
            if isinstance(exam_location_model, dict):
                exam_location_id = exam_location_model.get('exam_location_id')
                contact_info = exam_location_model.get('contact_info')
                additional_info = exam_location_model.get('additional_info')
            else:
                exam_location_id = getattr(exam_location_model, 'exam_location_id', None)
                contact_info = getattr(exam_location_model, 'contact_info', None)
                additional_info = getattr(exam_location_model, 'additional_info', None)
            
            # Convert complex nested objects to JSON strings to avoid Neo4j serialization issues
            if contact_info and not isinstance(contact_info, str):
                if isinstance(exam_location_model, dict):
                    exam_location_model['contact_info'] = json.dumps(contact_info, ensure_ascii=False)
                else:
                    setattr(exam_location_model, 'contact_info', json.dumps(contact_info, ensure_ascii=False))
            
            if additional_info and not isinstance(additional_info, str):
                if isinstance(exam_location_model, dict):
                    exam_location_model['additional_info'] = json.dumps(additional_info, ensure_ascii=False)
            else:
                    setattr(exam_location_model, 'additional_info', json.dumps(additional_info, ensure_ascii=False))
            
            # Create ExamLocationNode
            location_node = ExamLocationNode.from_sql_model(exam_location_model)
            
            # Execute creation query
            create_query = location_node.create_query()
            query_params = location_node.to_dict()
            
            logger.debug(f"Executing Neo4j query: {create_query}")
            logger.debug(f"With parameters: {query_params}")
            
            result = await self.neo4j.execute_query(create_query, query_params)
            logger.debug(f"Result from Neo4j: {result}")
            
            # Create relationships
            relationships_query = location_node.create_relationships_query()
            
            if relationships_query:
                logger.debug(f"Executing relationships query: {relationships_query}")
                logger.debug(f"With parameters: {query_params}")
                
                rel_result = await self.neo4j.execute_query(relationships_query, query_params)
                logger.debug(f"Relationship result from Neo4j: {rel_result}")
            
            logger.info(f"Successfully synchronized exam location {exam_location_id} to Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing exam location to Neo4j: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    async def sync_exam_room(self, exam_room_model):
        """
        Synchronize an exam room from PostgreSQL to Neo4j.
        
        Args:
            exam_room_model: PostgreSQL model or dictionary containing exam room data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug(f"Syncing exam room: {exam_room_model}")
            
            # Extract exam_room_id based on whether it's a dict or SQLAlchemy model
            if isinstance(exam_room_model, dict):
                exam_room_id = exam_room_model.get('exam_room_id')
                room_facilities = exam_room_model.get('room_facilities')
                additional_info = exam_room_model.get('additional_info')
            else:
                exam_room_id = getattr(exam_room_model, 'exam_room_id', None)
                room_facilities = getattr(exam_room_model, 'room_facilities', None)
                additional_info = getattr(exam_room_model, 'additional_info', None)
            
            # Convert complex nested objects to JSON strings to avoid Neo4j serialization issues
            if room_facilities and not isinstance(room_facilities, str):
                if isinstance(exam_room_model, dict):
                    exam_room_model['room_facilities'] = json.dumps(room_facilities, ensure_ascii=False)
                else:
                    setattr(exam_room_model, 'room_facilities', json.dumps(room_facilities, ensure_ascii=False))
            
            if additional_info and not isinstance(additional_info, str):
                if isinstance(exam_room_model, dict):
                    exam_room_model['additional_info'] = json.dumps(additional_info, ensure_ascii=False)
                else:
                    setattr(exam_room_model, 'additional_info', json.dumps(additional_info, ensure_ascii=False))
            
            # Create ExamRoomNode
            room_node = ExamRoomNode.from_sql_model(exam_room_model)
            
            # Execute creation query
            create_query = room_node.create_query()
            query_params = room_node.to_dict()
            
            logger.debug(f"Executing Neo4j query: {create_query}")
            logger.debug(f"With parameters: {query_params}")
            
            result = await self.neo4j.execute_query(create_query, query_params)
            logger.debug(f"Result from Neo4j: {result}")
            
            # Create relationships
            relationships_query = room_node.create_relationships_query()
            
            if relationships_query:
                logger.debug(f"Executing relationships query: {relationships_query}")
                logger.debug(f"With parameters: {query_params}")
                
                rel_result = await self.neo4j.execute_query(relationships_query, query_params)
                logger.debug(f"Relationship result from Neo4j: {rel_result}")
            
            logger.info(f"Successfully synchronized exam room {exam_room_id} to Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing exam room to Neo4j: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    async def sync_exam_schedule(self, exam_schedule_model):
        """
        Synchronize an exam schedule from PostgreSQL to Neo4j.
        
        Args:
            exam_schedule_model: PostgreSQL model or dictionary containing exam schedule data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug(f"Syncing exam schedule: {exam_schedule_model}")
            
            # Extract exam_schedule_id based on whether it's a dict or SQLAlchemy model
            if isinstance(exam_schedule_model, dict):
                exam_schedule_id = exam_schedule_model.get('exam_schedule_id')
            else:
                exam_schedule_id = getattr(exam_schedule_model, 'exam_schedule_id', None)
            
            # Create ExamScheduleNode
            schedule_node = ExamScheduleNode.from_sql_model(exam_schedule_model)
            
            # Execute creation query
            create_query = schedule_node.create_query()
            query_params = schedule_node.to_dict()
            
            logger.debug(f"Executing Neo4j query: {create_query}")
            logger.debug(f"With parameters: {query_params}")
            
            result = await self.neo4j.execute_query(create_query, query_params)
            logger.debug(f"Result from Neo4j: {result}")
            
            # Create relationships
            relationships_query = schedule_node.create_relationships_query()
            
            if relationships_query:
                logger.debug(f"Executing relationships query: {relationships_query}")
                logger.debug(f"With parameters: {query_params}")
                
                rel_result = await self.neo4j.execute_query(relationships_query, query_params)
                logger.debug(f"Relationship result from Neo4j: {rel_result}")
            
            logger.info(f"Successfully synchronized exam schedule {exam_schedule_id} to Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing exam schedule to Neo4j: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    async def sync_exam_attempt(self, attempt_model):
        """
        Synchronize an exam attempt from PostgreSQL to Neo4j.
        
        Args:
            attempt_model: SQLAlchemy ExamAttempt model
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create an attempt node from the model
            attempt_node = ExamAttemptNode.from_sql_model(attempt_model)
            
            # Create or update the node in Neo4j
            success = await self.exam_attempt_graph_repository.create_or_update(attempt_node)
            
            if success:
                logger.info(f"Synchronized exam attempt: {attempt_model.attempt_id}")
            else:
                logger.warning(f"Failed to synchronize exam attempt: {attempt_model.attempt_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error synchronizing exam attempt {attempt_model.attempt_id}: {e}")
            return False

    async def sync_score_review(self, review_model):
        """
        Synchronize a score review from PostgreSQL to Neo4j.
        
        Args:
            review_model: SQLAlchemy ScoreReview model
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a review node from the model
            review_node = ScoreReviewNode.from_sql_model(review_model)
            
            # Create or update the node in Neo4j
            success = await self.score_review_graph_repository.create_or_update(review_node)
            
            if success:
                logger.info(f"Synchronized score review: {review_model.review_id}")
            else:
                logger.warning(f"Failed to synchronize score review: {review_model.review_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error synchronizing score review {review_model.review_id}: {e}")
            return False 

    async def bulk_sync_candidate_exam_relationships(self):
        """
        Đồng bộ tất cả các mối quan hệ giữa thí sinh và kỳ thi từ PostgreSQL sang Neo4j.
        Tạo mối quan hệ (Candidate)-[:ATTENDS_EXAM]->(Exam) với các thuộc tính như
        registration_number, registration_date, và status.
        
        Returns:
            int: Số lượng mối quan hệ được đồng bộ thành công
        """
        try:
            logger.info("Starting bulk synchronization of candidate-exam relationships")
            # Get candidate exam repository
            candidate_exam_repo = self.repository_factory.get_candidate_exam_repository()
            
            # Get all candidate exams
            candidate_exams = await candidate_exam_repo.get_all_raw()
            logger.info(f"Found {len(candidate_exams)} candidate-exam relationships to synchronize")
            
            success_count = 0
            for candidate_exam in candidate_exams:
                try:
                    # Đồng bộ từng mối quan hệ
                    if await self.sync_candidate_exam_relationship(candidate_exam):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error synchronizing candidate-exam relationship {candidate_exam.candidate_exam_id}: {e}")
            
            logger.info(f"Successfully synchronized {success_count} out of {len(candidate_exams)} candidate-exam relationships")
            return success_count
        except Exception as e:
            logger.error(f"Error during bulk synchronization of candidate-exam relationships: {e}", exc_info=True)
            return 0