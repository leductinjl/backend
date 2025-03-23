"""
Achievement Sync Service module.

This module provides the AchievementSyncService class for synchronizing Achievement data
between PostgreSQL and Neo4j.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.services.sync.base_sync_service import BaseSyncService
from app.repositories.achievement_repository import AchievementRepository
from app.graph_repositories.achievement_graph_repository import AchievementGraphRepository
from app.domain.graph_models.achievement_node import AchievementNode
from app.domain.models.achievement import Achievement

logger = logging.getLogger(__name__)

class AchievementSyncService(BaseSyncService):
    """
    Service for synchronizing Achievement data between PostgreSQL and Neo4j.
    
    This service retrieves Achievement data from a PostgreSQL database
    and creates or updates corresponding nodes in a Neo4j graph database,
    ensuring the proper ontology relationships are established.
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        neo4j_driver: AsyncDriver,
        sql_repository: Optional[AchievementRepository] = None,
        graph_repository: Optional[AchievementGraphRepository] = None
    ):
        """
        Initialize the Achievement sync service.
        
        Args:
            db_session: SQLAlchemy async session
            neo4j_driver: Neo4j async driver
            sql_repository: Optional AchievementRepository instance
            graph_repository: Optional AchievementGraphRepository instance
        """
        super().__init__(db_session, neo4j_driver, sql_repository, graph_repository)
        
        # Initialize repositories if not provided
        self.sql_repository = sql_repository or AchievementRepository(db_session)
        self.graph_repository = graph_repository or AchievementGraphRepository(neo4j_driver)
    
    async def sync_by_id(self, achievement_id: str) -> bool:
        """
        Synchronize a single achievement by ID.
        
        Args:
            achievement_id: ID of the achievement to sync
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            # Get achievement from SQL database with relationships
            achievement = await self.sql_repository.get_by_id(achievement_id)
            
            if not achievement:
                logger.warning(f"Achievement with ID {achievement_id} not found in SQL database")
                return False
            
            # Convert to node
            achievement_node = self._convert_to_node(achievement)
            
            # Create or update in Neo4j
            result = await self.graph_repository.create_or_update(achievement_node)
            
            if result:
                logger.info(f"Successfully synchronized achievement {achievement_id}")
                return True
            else:
                logger.error(f"Failed to synchronize achievement {achievement_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error synchronizing achievement {achievement_id}: {str(e)}", exc_info=True)
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Dict[str, Any]:
        """
        Synchronize all achievements from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of achievements to sync
            offset: Number of achievements to skip from the beginning
            
        Returns:
            Dictionary with sync results
        """
        total_count = 0
        success_count = 0
        failure_count = 0
        
        try:
            # Get all achievements from SQL database
            achievements, total = await self.sql_repository.get_all(skip=offset, limit=limit)
            total_count = len(achievements)
            
            # Sync each achievement
            for achievement in achievements:
                if await self.sync_by_id(achievement.achievement_id):
                    success_count += 1
                else:
                    failure_count += 1
            
            # Log results
            self._log_sync_result("Achievement", success_count, failure_count, total_count)
            
            return {
                "total": total_count,
                "success": success_count,
                "failed": failure_count
            }
        except Exception as e:
            logger.error(f"Error synchronizing achievements: {str(e)}", exc_info=True)
            return {
                "total": total_count,
                "success": success_count,
                "failed": failure_count,
                "error": str(e)
            }
    
    def _convert_to_node(self, achievement: Achievement) -> AchievementNode:
        """
        Convert SQL Achievement model to AchievementNode.
        
        Args:
            achievement: SQL Achievement model instance
            
        Returns:
            AchievementNode instance
        """
        try:
            # Create node using the from_sql_model method
            achievement_node = AchievementNode.from_sql_model(achievement)
            
            if not achievement_node:
                # If conversion failed, create a basic node with just the ID and name
                logger.warning(f"Failed to convert using from_sql_model for {achievement.achievement_id}, creating basic node")
                achievement_node = AchievementNode(
                    achievement_id=achievement.achievement_id,
                    achievement_name=achievement.achievement_name
                )
            
            # Ensure relationships are established - extract candidate_id and exam_id
            if hasattr(achievement, 'candidate_exam') and achievement.candidate_exam:
                if hasattr(achievement.candidate_exam, 'candidate_id'):
                    achievement_node.candidate_id = achievement.candidate_exam.candidate_id
                
                if hasattr(achievement.candidate_exam, 'exam_id'):
                    achievement_node.exam_id = achievement.candidate_exam.exam_id
            
            return achievement_node
            
        except Exception as e:
            logger.error(f"Error converting achievement to node: {str(e)}", exc_info=True)
            # Return a basic node with just the ID and name as fallback
            return AchievementNode(
                achievement_id=achievement.achievement_id,
                achievement_name=achievement.achievement_name
            ) 