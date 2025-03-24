"""
Management Unit Sync Service Module.

This module provides the ManagementUnitSyncService class for synchronizing ManagementUnit
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

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
    
    async def sync_by_id(self, unit_id: str, skip_relationships: bool = False) -> bool:
        """
        Synchronize a specific management unit by ID.
        
        Args:
            unit_id: The ID of the management unit to sync
            skip_relationships: If True, only sync node without its relationships
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing management unit {unit_id} (skip_relationships={skip_relationships})")
        
        try:
            # Get management unit from SQL database
            unit = await self.sql_repository.get_by_id(unit_id)
            if not unit:
                logger.error(f"Management unit {unit_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(unit)
            
            # Create or update node in Neo4j
            await self.graph_repository.create_or_update(neo4j_data)
            
            # Sync relationships if needed
            if not skip_relationships:
                await self.sync_relationships(unit_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing management unit {unit_id}: {e}")
            return False
    
    async def sync_all(self, limit: Optional[int] = None, skip_relationships: bool = False) -> Union[Tuple[int, int], Dict[str, int]]:
        """
        Synchronize all management units.
        
        Args:
            limit: Optional limit on number of management units to sync
            skip_relationships: If True, only sync nodes without their relationships
            
        Returns:
            Tuple of (success_count, failed_count) or dict with success/failed counts
        """
        logger.info(f"Synchronizing all management units (skip_relationships={skip_relationships})")
        
        try:
            # Get all management units from SQL database
            units, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for unit in units:
                try:
                    # Sync the management unit node - handle both ORM objects and dictionaries
                    unit_id = unit.unit_id if hasattr(unit, 'unit_id') else unit.get("unit_id")
                    if not unit_id:
                        logger.error(f"Missing unit_id in management unit object: {unit}")
                        failed_count += 1
                        continue
                        
                    await self.sync_by_id(unit_id, skip_relationships=skip_relationships)
                    success_count += 1
                except Exception as e:
                    # Get unit_id safely for logging
                    unit_id = getattr(unit, 'unit_id', None) if hasattr(unit, 'unit_id') else unit.get("unit_id", "unknown")
                    logger.error(f"Error syncing management unit {unit_id}: {e}")
                    failed_count += 1
            
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during management unit synchronization: {e}")
            return {"success": 0, "failed": 0}
    
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
            
    async def sync_relationships(self, unit_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific management unit.
        
        Args:
            unit_id: ID of the management unit to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for management unit {unit_id}")
        
        relationship_counts = {
            "exams": 0,
            "parent_unit": 0,
            "child_units": 0
        }
        
        try:
            # Get management unit from SQL database with full details
            unit = await self.sql_repository.get_by_id(unit_id)
            if not unit:
                logger.error(f"Management unit {unit_id} not found in SQL database")
                return relationship_counts
            
            # Sync ORGANIZES relationships (management_unit-exam)
            if hasattr(unit, 'exams') and unit.exams:
                for exam in unit.exams:
                    if hasattr(exam, 'exam_id') and exam.exam_id:
                        success = await self.graph_repository.add_organizes_relationship(unit_id, exam.exam_id)
                        if success:
                            relationship_counts["exams"] += 1
            
            # Sync PARENT_OF relationships (parent_unit-child_unit)
            if hasattr(unit, 'child_units') and unit.child_units:
                for child_unit in unit.child_units:
                    if hasattr(child_unit, 'unit_id') and child_unit.unit_id:
                        success = await self.graph_repository.add_parent_of_relationship(unit_id, child_unit.unit_id)
                        if success:
                            relationship_counts["child_units"] += 1
            
            # Sync CHILD_OF relationship (child_unit-parent_unit)
            if hasattr(unit, 'parent_unit_id') and unit.parent_unit_id:
                success = await self.graph_repository.add_child_of_relationship(unit_id, unit.parent_unit_id)
                if success:
                    relationship_counts["parent_unit"] += 1
            
            logger.info(f"Management unit relationship synchronization completed for {unit_id}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for management unit {unit_id}: {e}")
            return relationship_counts 