"""
Base synchronization service module.

This module provides the base class for synchronizing data between
PostgreSQL and Neo4j databases.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.ontology.neo4j_connection import neo4j_connection

logger = logging.getLogger(__name__)

class BaseSyncService:
    """
    Base service for synchronizing data between PostgreSQL and Neo4j.
    
    This service is responsible for providing common functionality
    for all sync services.
    """
    
    def __init__(self, neo4j_connection, db_session: AsyncSession):
        """Initialize with Neo4j connection and SQLAlchemy session."""
        self.neo4j = neo4j_connection
        self.db = db_session
        
    async def _log_sync_start(self, entity_type, entity_id=None):
        """Log the start of a synchronization operation."""
        if entity_id:
            logger.info(f"Syncing {entity_type} with ID {entity_id} to Neo4j")
        else:
            logger.info(f"Starting bulk sync of {entity_type}s to Neo4j")
    
    async def _log_sync_success(self, entity_type, entity_id=None, count=None):
        """Log the successful completion of a synchronization operation."""
        if entity_id:
            logger.info(f"Successfully synchronized {entity_type} with ID {entity_id} to Neo4j")
        elif count is not None:
            logger.info(f"Successfully synchronized {count} {entity_type}s to Neo4j")
        else:
            logger.info(f"Successfully completed bulk sync of {entity_type}s to Neo4j")
    
    async def _log_sync_error(self, entity_type, error, entity_id=None):
        """Log an error that occurred during synchronization."""
        if entity_id:
            logger.error(f"Error syncing {entity_type} with ID {entity_id} to Neo4j: {error}")
        else:
            logger.error(f"Error during bulk sync of {entity_type}s to Neo4j: {error}")
    
    async def _execute_neo4j_query(self, query, params=None):
        """Execute a Neo4j query and handle potential errors."""
        try:
            logger.debug(f"Executing Neo4j query: {query}")
            if params:
                logger.debug(f"Query parameters: {params}")
            return await self.neo4j.execute_query(query, params or {})
        except Exception as e:
            logger.error(f"Error executing Neo4j query: {e}")
            raise 