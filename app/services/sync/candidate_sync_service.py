"""
Candidate synchronization service module.

This module provides services for synchronizing candidate-related data between
PostgreSQL and Neo4j databases, including candidates and their relationships
with other entities.
"""

import logging
import json
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sync.base_sync_service import BaseSyncService
from app.domain.graph_models.candidate_node import CandidateNode
from app.graph_repositories.candidate_graph_repository import CandidateGraphRepository
from app.repositories.repository_factory import RepositoryFactory

logger = logging.getLogger(__name__)

class CandidateSyncService(BaseSyncService):
    """
    Service for synchronizing candidate-related data between PostgreSQL and Neo4j.
    
    This service handles synchronization of candidates and their relationships
    with other entities like exams, majors, etc.
    """
    
    def __init__(self, neo4j_connection, db_session: AsyncSession):
        """Initialize with Neo4j connection and SQLAlchemy session."""
        super().__init__(neo4j_connection, db_session)
        
        # Initialize candidate-related repositories
        self.candidate_graph_repo = CandidateGraphRepository(neo4j_connection)
        
    async def sync_candidate(self, candidate_model, personal_info_model=None):
        """
        Synchronize a candidate from PostgreSQL to Neo4j.
        
        Args:
            candidate_model: A Candidate SQLAlchemy model or dictionary
            personal_info_model: Optional personal info model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        candidate_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(candidate_model, dict):
                candidate_id = candidate_model.get("candidate_id")
                candidate_dict = candidate_model
                
                # Add personal info if provided
                if personal_info_model and isinstance(personal_info_model, dict):
                    candidate_dict.update(personal_info_model)
            else:
                candidate_id = candidate_model.candidate_id
                candidate_dict = {
                    "candidate_id": candidate_model.candidate_id,
                    "first_name": candidate_model.first_name,
                    "last_name": candidate_model.last_name,
                    "email": candidate_model.email,
                    "date_of_birth": candidate_model.date_of_birth,
                    "gender": candidate_model.gender,
                    "phone_number": candidate_model.phone_number,
                    "address": candidate_model.address,
                    "status": candidate_model.status,
                }
                
                # Add personal info if provided
                if personal_info_model:
                    if not isinstance(personal_info_model, dict):
                        # Convert SQLAlchemy model to dict
                        personal_info_dict = {
                            "national_id": getattr(personal_info_model, "national_id", None),
                            "nationality": getattr(personal_info_model, "nationality", None),
                            "marital_status": getattr(personal_info_model, "marital_status", None),
                            "blood_type": getattr(personal_info_model, "blood_type", None),
                            "ethnicity": getattr(personal_info_model, "ethnicity", None),
                            "religion": getattr(personal_info_model, "religion", None),
                        }
                        candidate_dict.update(personal_info_dict)
                    else:
                        candidate_dict.update(personal_info_model)
            
            await self._log_sync_start("candidate", candidate_id)
            
            # Create Neo4j node
            candidate_node = CandidateNode.from_dict(candidate_dict)
            
            # Create or update node in Neo4j
            query = candidate_node.create_query()
            logger.info(f"Executing Neo4j query for candidate {candidate_id}")
            await self._execute_neo4j_query(query, candidate_node.to_dict())
            
            # Create relationships if applicable
            if hasattr(candidate_node, "create_relationships_query") and callable(getattr(candidate_node, "create_relationships_query")):
                rel_query = candidate_node.create_relationships_query()
                if rel_query:
                    logger.info(f"Creating relationships for candidate {candidate_id}")
                    await self._execute_neo4j_query(rel_query, candidate_node.to_dict())
            
            await self._log_sync_success("candidate", candidate_id)
            return True
        except Exception as e:
            await self._log_sync_error("candidate", str(e), candidate_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_education_history(self, education_history_model):
        """
        Synchronize a candidate's education history from PostgreSQL to Neo4j.
        
        Args:
            education_history_model: An EducationHistory SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        history_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(education_history_model, dict):
                history_id = education_history_model.get("history_id")
                candidate_id = education_history_model.get("candidate_id")
                school_id = education_history_model.get("school_id")
            else:
                history_id = education_history_model.history_id
                candidate_id = education_history_model.candidate_id
                school_id = education_history_model.school_id
            
            await self._log_sync_start("education history", history_id)
            
            # Create relationship between candidate and school
            relationship_query = """
            MATCH (c:Candidate {candidate_id: $candidate_id})
            MATCH (s:School {school_id: $school_id})
            MERGE (c)-[r:STUDIED_AT]->(s)
            RETURN r
            """
            
            params = {
                "candidate_id": candidate_id,
                "school_id": school_id
            }
            
            logger.info(f"Creating education history relationship between candidate {candidate_id} and school {school_id}")
            await self._execute_neo4j_query(relationship_query, params)
            
            await self._log_sync_success("education history", history_id)
            return True
        except Exception as e:
            await self._log_sync_error("education history", str(e), history_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_candidate_exam_relationship(self, candidate_exam_model):
        """
        Synchronize a candidate-exam relationship from PostgreSQL to Neo4j.
        
        Args:
            candidate_exam_model: A CandidateExam SQLAlchemy model or dictionary
        
        Returns:
            bool: True if successful, False otherwise
        """
        candidate_exam_id = None
        try:
            # Handle both dictionary and SQLAlchemy model
            if isinstance(candidate_exam_model, dict):
                candidate_exam_id = candidate_exam_model.get("candidate_exam_id")
                candidate_id = candidate_exam_model.get("candidate_id")
                exam_id = candidate_exam_model.get("exam_id")
                registration_date = candidate_exam_model.get("registration_date")
                status = candidate_exam_model.get("status")
            else:
                candidate_exam_id = candidate_exam_model.candidate_exam_id
                candidate_id = candidate_exam_model.candidate_id
                exam_id = candidate_exam_model.exam_id
                registration_date = candidate_exam_model.registration_date
                status = candidate_exam_model.status
            
            await self._log_sync_start("candidate-exam relationship", candidate_exam_id)
            
            # Create relationship between candidate and exam
            relationship_query = """
            MATCH (c:Candidate {candidate_id: $candidate_id})
            MATCH (e:Exam {exam_id: $exam_id})
            MERGE (c)-[r:REGISTERED_FOR {
                candidate_exam_id: $candidate_exam_id,
                registration_date: $registration_date,
                status: $status
            }]->(e)
            RETURN r
            """
            
            params = {
                "candidate_id": candidate_id,
                "exam_id": exam_id,
                "candidate_exam_id": candidate_exam_id,
                "registration_date": registration_date,
                "status": status
            }
            
            logger.info(f"Creating relationship between candidate {candidate_id} and exam {exam_id}")
            await self._execute_neo4j_query(relationship_query, params)
            
            await self._log_sync_success("candidate-exam relationship", candidate_exam_id)
            return True
        except Exception as e:
            await self._log_sync_error("candidate-exam relationship", str(e), candidate_exam_id)
            logger.error(traceback.format_exc())
            return False
    
    async def sync_candidate_major_relationship(self, candidate_id, major_id):
        """
        Synchronize a candidate-major relationship to Neo4j.
        
        Args:
            candidate_id: The ID of the candidate
            major_id: The ID of the major
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self._log_sync_start("candidate-major relationship")
            
            # Create relationship between candidate and major
            relationship_query = """
            MATCH (c:Candidate {candidate_id: $candidate_id})
            MATCH (m:Major {major_id: $major_id})
            MERGE (c)-[r:STUDIES]->(m)
            RETURN r
            """
            
            params = {
                "candidate_id": candidate_id,
                "major_id": major_id
            }
            
            logger.info(f"Creating relationship between candidate {candidate_id} and major {major_id}")
            await self._execute_neo4j_query(relationship_query, params)
            
            await self._log_sync_success("candidate-major relationship")
            return True
        except Exception as e:
            await self._log_sync_error("candidate-major relationship", str(e))
            logger.error(traceback.format_exc())
            return False
            
    async def bulk_sync_candidates(self):
        """
        Synchronize all candidates from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized candidates
        """
        await self._log_sync_start("candidate")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            candidate_repo = await repo_factory.get_candidate_repository()
            personal_info_repo = await repo_factory.get_personal_info_repository()
            
            # Get all candidates
            candidates = await candidate_repo.get_all()
            logger.info(f"Found {len(candidates)} candidates to sync")
            
            # Sync each candidate
            success_count = 0
            for candidate in candidates:
                # Get personal info if available
                personal_info = None
                try:
                    personal_info = await personal_info_repo.get_by_candidate_id(candidate.candidate_id)
                except Exception as e:
                    logger.warning(f"Could not get personal info for candidate {candidate.candidate_id}: {str(e)}")
                
                if await self.sync_candidate(candidate, personal_info):
                    success_count += 1
            
            await self._log_sync_success("candidate", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("candidate", str(e))
            logger.error(traceback.format_exc())
            return 0
            
    async def bulk_sync_education_histories(self):
        """
        Synchronize all education histories from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized education histories
        """
        await self._log_sync_start("education history")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            history_repo = await repo_factory.get_education_history_repository()
            
            # Get all education histories
            histories = await history_repo.get_all()
            logger.info(f"Found {len(histories)} education histories to sync")
            
            # Sync each education history
            success_count = 0
            for history in histories:
                if await self.sync_education_history(history):
                    success_count += 1
            
            await self._log_sync_success("education history", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("education history", str(e))
            logger.error(traceback.format_exc())
            return 0
            
    async def bulk_sync_candidate_exam_relationships(self):
        """
        Synchronize all candidate-exam relationships from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized relationships
        """
        await self._log_sync_start("candidate-exam relationship")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            candidate_exam_repo = await repo_factory.get_candidate_exam_repository()
            
            # Get all candidate-exam relationships
            relationships = await candidate_exam_repo.get_all()
            logger.info(f"Found {len(relationships)} candidate-exam relationships to sync")
            
            # Sync each relationship
            success_count = 0
            for relationship in relationships:
                if await self.sync_candidate_exam_relationship(relationship):
                    success_count += 1
            
            await self._log_sync_success("candidate-exam relationship", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("candidate-exam relationship", str(e))
            logger.error(traceback.format_exc())
            return 0
            
    async def bulk_sync_candidate_major_relationships(self):
        """
        Synchronize all candidate-major relationships from PostgreSQL to Neo4j.
        
        Returns:
            int: Number of successfully synchronized relationships
        """
        await self._log_sync_start("candidate-major relationship")
        try:
            # Get repository factory
            repo_factory = RepositoryFactory(self.db)
            candidate_major_repo = await repo_factory.get_candidate_major_repository()
            
            # Get all candidate-major relationships
            relationships = await candidate_major_repo.get_all()
            logger.info(f"Found {len(relationships)} candidate-major relationships to sync")
            
            # Sync each relationship
            success_count = 0
            for relationship in relationships:
                if await self.sync_candidate_major_relationship(
                    relationship.candidate_id, relationship.major_id
                ):
                    success_count += 1
            
            await self._log_sync_success("candidate-major relationship", count=success_count)
            return success_count
        except Exception as e:
            await self._log_sync_error("candidate-major relationship", str(e))
            logger.error(traceback.format_exc())
            return 0 