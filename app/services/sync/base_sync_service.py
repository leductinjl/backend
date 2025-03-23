"""
Base Sync Service module.

This module provides the BaseSyncService abstract class which serves as the foundation for all
synchronization services that transfer data between PostgreSQL and Neo4j.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic

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
    async def sync_by_id(self, entity_id: str) -> bool:
        """
        Synchronize a single entity by ID.
        
        Args:
            entity_id: ID of the entity to sync
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Dict[str, Any]:
        """
        Synchronize all entities of a specific type.
        
        Args:
            limit: Optional maximum number of entities to sync
            offset: Number of entities to skip from the beginning
            
        Returns:
            Dictionary with sync results
        """
        pass
    
    @abstractmethod
    def _convert_to_node(self, entity: Any) -> Any:
        """
        Convert SQL model to Neo4j node model.
        
        Args:
            entity: SQL model instance
            
        Returns:
            Neo4j node instance
        """
        pass
    
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