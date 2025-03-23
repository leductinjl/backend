"""
Management Unit Sync Service Module.

This module provides the ManagementUnitSyncService class for synchronizing ManagementUnit
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.management_unit import ManagementUnit
from app.domain.graph_models.management_unit_node import ManagementUnitNode
from app.repositories.management_unit_repository import ManagementUnitRepository
from app.graph_repositories.management_unit_graph_repository import ManagementUnitGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class ManagementUnitSyncService(BaseSyncService):
    """
    Service for synchronizing ManagementUnit data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual management units by ID and synchronizing
    all management units in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        management_unit_repository: Optional[ManagementUnitRepository] = None,
        management_unit_graph_repository: Optional[ManagementUnitGraphRepository] = None
    ):
        """
        Initialize the ManagementUnitSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            management_unit_repository: Optional ManagementUnitRepository instance
            management_unit_graph_repository: Optional ManagementUnitGraphRepository instance
        """
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = management_unit_repository or ManagementUnitRepository(session)
        self.graph_repository = management_unit_graph_repository or ManagementUnitGraphRepository(driver)
    
    async def sync_by_id(self, unit_id: str) -> bool:
        """
        Synchronize a single management unit by ID.
        
        Args:
            unit_id: ID of the management unit to synchronize
            
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            # Get management unit from SQL database
            unit = await self.sql_repository.get_by_id(unit_id)
            if not unit:
                logger.warning(f"Management Unit with ID {unit_id} not found in SQL database")
                return False
            
            # Convert to Neo4j node and save
            unit_node = self._convert_to_node(unit)
            result = await self.graph_repository.create_or_update(unit_node)
            
            if result:
                logger.info(f"Successfully synchronized management unit {unit_id}")
                return True
            else:
                logger.error(f"Failed to synchronize management unit {unit_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error synchronizing management unit {unit_id}: {str(e)}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, offset: int = 0) -> Tuple[int, int]:
        """
        Synchronize all management units from PostgreSQL to Neo4j.
        
        Args:
            limit: Optional maximum number of management units to synchronize
            offset: Optional offset for pagination
            
        Returns:
            Tuple containing counts of (successful, failed) synchronizations
        """
        success_count = 0
        failure_count = 0
        
        try:
            # Get all management units from SQL database
            units, total = await self.sql_repository.get_all(skip=offset, limit=limit or 100)
            
            logger.info(f"Found {total} management units to synchronize")
            
            # Synchronize each management unit
            for unit in units:
                if await self.sync_by_id(unit.unit_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Management Unit synchronization complete. Success: {success_count}, Failed: {failure_count}")
            
        except Exception as e:
            logger.error(f"Error during management unit synchronization: {str(e)}")
        
        return success_count, failure_count
    
    def _convert_to_node(self, unit: ManagementUnit) -> ManagementUnitNode:
        """
        Convert a SQL ManagementUnit model to a ManagementUnitNode.
        
        Args:
            unit: SQL ManagementUnit model instance
            
        Returns:
            ManagementUnitNode instance ready for Neo4j
        """
        try:
            # Create the management unit node
            unit_node = ManagementUnitNode.from_sql_model(unit)
            return unit_node
            
        except Exception as e:
            logger.error(f"Error converting management unit to node: {str(e)}")
            # Return a basic node with just the ID as fallback
            return ManagementUnitNode(
                unit_id=unit.unit_id,
                unit_name=unit.unit_name,
                unit_type=unit.unit_type
            ) 