"""
Candidate Sync Service module.

This module provides the CandidateSyncService class for synchronizing Candidate data
between PostgreSQL and Neo4j.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.services.sync.base_sync_service import BaseSyncService
from app.repositories.candidate_repository import CandidateRepository
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
    
    async def sync_by_id(self, candidate_id: str) -> bool:
        """
        Synchronize a single candidate by ID.
        
        Args:
            candidate_id: ID of the candidate to sync
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            # Get candidate from SQL database with personal info
            candidate = await self.sql_repository.get_by_id_with_personal_info(candidate_id)
            
            if not candidate:
                logger.warning(f"Candidate with ID {candidate_id} not found in SQL database")
                return False
            
            # Convert to node
            candidate_node = self._convert_to_node(candidate)
            
            # Create or update in Neo4j
            result = await self.graph_repository.create_or_update(candidate_node)
            
            if result:
                logger.info(f"Successfully synchronized candidate {candidate_id}")
                return True
            else:
                logger.error(f"Failed to synchronize candidate {candidate_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error synchronizing candidate {candidate_id}: {str(e)}", exc_info=True)
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Dict[str, Any]:
        """
        Synchronize all candidates from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of candidates to sync
            offset: Number of candidates to skip from the beginning
            
        Returns:
            Dictionary with sync results
        """
        total_count = 0
        success_count = 0
        failure_count = 0
        
        try:
            # Get all candidates from SQL database with personal info
            candidates = await self.sql_repository.get_all(skip=offset, limit=limit, include_personal_info=True)
            total_count = len(candidates)
            
            # Sync each candidate
            for candidate in candidates:
                if await self.sync_by_id(candidate.candidate_id):
                    success_count += 1
                else:
                    failure_count += 1
            
            # Log results
            self._log_sync_result("Candidate", success_count, failure_count, total_count)
            
            return {
                "total": total_count,
                "success": success_count,
                "failed": failure_count
            }
        except Exception as e:
            logger.error(f"Error synchronizing candidates: {str(e)}", exc_info=True)
            return {
                "total": total_count,
                "success": success_count,
                "failed": failure_count,
                "error": str(e)
            }
    
    def _convert_to_node(self, candidate: Candidate) -> CandidateNode:
        """
        Convert SQL Candidate model to CandidateNode.
        
        Args:
            candidate: SQL Candidate model instance with personal_info
            
        Returns:
            CandidateNode instance
        """
        try:
            # Create node using the from_sql_model method
            personal_info = getattr(candidate, "personal_info", None)
            
            candidate_node = CandidateNode.from_sql_model(
                candidate_model=candidate,
                personal_info_model=personal_info
            )
            
            if not candidate_node:
                # If conversion failed, create a basic node with just the ID and name
                logger.warning(f"Failed to convert using from_sql_model for {candidate.candidate_id}, creating basic node")
                candidate_node = CandidateNode(
                    candidate_id=candidate.candidate_id,
                    full_name=candidate.full_name
                )
            
            return candidate_node
            
        except Exception as e:
            logger.error(f"Error converting candidate to node: {str(e)}", exc_info=True)
            # Return a basic node with just the ID and name as fallback
            return CandidateNode(
                candidate_id=candidate.candidate_id,
                full_name=candidate.full_name
            ) 