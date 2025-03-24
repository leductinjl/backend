"""
Base Sync Service Module.

This module provides the abstract BaseSyncService class that defines
the interface for synchronization services between PostgreSQL and Neo4j.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

# Type variables for generic repository types
T = TypeVar('T')  # SQL model type
N = TypeVar('N')  # Neo4j node type

logger = logging.getLogger(__name__)

class BaseSyncService(ABC):
    """
    Abstract base class for synchronization services.
    
    This class provides the common structure and utility methods for services
    that synchronize data between PostgreSQL and Neo4j, ensuring proper
    handling of ontology relationships.
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        neo4j_driver: AsyncDriver,
        sql_repository: Any = None,
        graph_repository: Any = None
    ):
        """
        Initialize the base sync service.
        
        Args:
            db_session: SQLAlchemy async session
            neo4j_driver: Neo4j async driver
            sql_repository: Optional SQL repository instance
            graph_repository: Optional Neo4j graph repository instance
        """
        self.db_session = db_session
        self.neo4j_driver = neo4j_driver
        self.sql_repository = sql_repository
        self.graph_repository = graph_repository
    
    @abstractmethod
    async def sync_by_id(self, entity_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a single entity by ID.
        
        Args:
            entity_id: ID of the entity to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all entities of a specific type.
        
        Args:
            limit: Optional maximum number of entities to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        pass
    
    @abstractmethod
    def _convert_to_node(self, sql_model: Any) -> Any:
        """
        Convert SQL model to Neo4j node.
        
        Args:
            sql_model: SQL model instance
            
        Returns:
            Graph node instance
        """
        pass
    
    @abstractmethod
    async def sync_relationships(self, entity_id: str) -> Dict[str, int]:
        """
        Synchronize all relationships for a specific entity.
        
        This is a default implementation that returns an empty result.
        Override this method in subclasses that need to synchronize relationships.
        
        Args:
            entity_id: ID of the entity to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logging.getLogger(__name__).info(f"No relationship synchronization implemented for entity ID: {entity_id}")
        return {}
    
    def _log_sync_result(self, entity_type: str, success_count: int, failure_count: int, total_count: int) -> None:
        """
        Log the results of a synchronization operation.
        
        Args:
            entity_type: Type of entity being synced (e.g., "Score", "Subject")
            success_count: Number of successfully synced entities
            failure_count: Number of failed synchronizations
            total_count: Total number of processed entities
        """
        logger.info(
            f"{entity_type} sync completed: {success_count} successful, "
            f"{failure_count} failed, {total_count} total"
        )
    
    async def execute_neo4j_query(self, query: str, params: Dict[str, Any] = None) -> List[Any]:
        """
        Execute a Cypher query in Neo4j.
        
        Args:
            query: The Cypher query to execute
            params: Parameters for the query
            
        Returns:
            Query results
            
        Raises:
            Exception: If the query execution fails
        """
        try:
            async with self.neo4j_driver.session() as session:
                result = await session.run(query, params or {})
                records = await result.values()
                return records
        except Exception as e:
            logger.error(f"Error executing Neo4j query: {str(e)}")
            raise 