"""
Achievement Sync Service module.

This module provides the AchievementSyncService class for synchronizing Achievement data
between PostgreSQL and Neo4j.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

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
    
    async def sync_by_id(self, achievement_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific achievement by ID.
        
        Args:
            achievement_id: The ID of the achievement to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing achievement {achievement_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get achievement from SQL database
            achievement = await self.sql_repository.get_by_id(achievement_id)
            if not achievement:
                logger.error(f"Achievement {achievement_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(achievement)
            
            # Create or update node in Neo4j
            await self.graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(achievement_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing achievement {achievement_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all achievements.
        
        Args:
            limit: Optional limit on number of achievements to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all achievements (skip_relationships={skip_relationships})")
        
        try:
            # Get all achievements from SQL database
            achievements, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for achievement in achievements:
                try:
                    # Sync the achievement node - handle both ORM objects and dictionaries
                    achievement_id = achievement.achievement_id if hasattr(achievement, 'achievement_id') else achievement.get("achievement_id")
                    if not achievement_id:
                        logger.error(f"Missing achievement_id in achievement object: {achievement}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(achievement_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get achievement_id safely for logging
                    achievement_id = getattr(achievement, 'achievement_id', None) if hasattr(achievement, 'achievement_id') else achievement.get("achievement_id", "unknown")
                    logger.error(f"Error syncing achievement {achievement_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during achievement synchronization: {e}")
            return {"success": 0, "failed": 0}
    
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
            
    async def sync_relationships(self, achievement_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific achievement.
        
        Args:
            achievement_id: ID of the achievement to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for achievement {achievement_id}")
        
        relationship_counts = {
            "candidate": 0,
            "exam": 0
        }
        
        try:
            # Get achievement from SQL database with full details
            achievement = await self.sql_repository.get_by_id(achievement_id)
            if not achievement:
                logger.error(f"Achievement {achievement_id} not found in SQL database")
                return relationship_counts
            
            # Extract candidate_id and exam_id
            candidate_id = None
            exam_id = None
            
            if hasattr(achievement, 'candidate_exam') and achievement.candidate_exam:
                if hasattr(achievement.candidate_exam, 'candidate_id'):
                    candidate_id = achievement.candidate_exam.candidate_id
                
                if hasattr(achievement.candidate_exam, 'exam_id'):
                    exam_id = achievement.candidate_exam.exam_id
            
            # Sync EARNED_BY relationship (achievement-candidate)
            if candidate_id:
                success = await self.graph_repository.add_earned_by_relationship(achievement_id, candidate_id)
                if success:
                    relationship_counts["candidate"] += 1
            
            # Sync FOR_EXAM relationship (achievement-exam)
            if exam_id:
                success = await self.graph_repository.add_for_exam_relationship(achievement_id, exam_id)
                if success:
                    relationship_counts["exam"] += 1
            
            logger.info(f"Achievement relationship synchronization completed for {achievement_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for achievement {achievement_id}: {e}")
            return relationship_counts 