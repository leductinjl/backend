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
        sql_repository: Optional[ManagementUnitRepository] = None,
        graph_repository: Optional[ManagementUnitGraphRepository] = None
    ):
        """
        Initialize the ManagementUnitSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional ManagementUnitRepository instance
            graph_repository: Optional ManagementUnitGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.db_session = session
        self.neo4j_driver = driver
        self.sql_repository = sql_repository or ManagementUnitRepository(session)
        self.graph_repository = graph_repository or ManagementUnitGraphRepository(driver)
    
    async def sync_node_by_id(self, unit_id: str) -> bool:
        """
        Synchronize a specific management unit node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            unit_id: The ID of the management unit to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing management unit node {unit_id}")
        
        try:
            # Get management unit from SQL database
            unit = await self.sql_repository.get_by_id(unit_id)
            if not unit:
                logger.error(f"Management unit {unit_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(unit)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized management unit node {unit_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing management unit node {unit_id}: {e}")
            return False
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all management unit nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of management units to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all management unit nodes (limit={limit})")
        
        try:
            # Get all management units from SQL database
            units, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for unit in units:
                try:
                    # Sync only the management unit node - handle both ORM objects and dictionaries
                    unit_id = unit.unit_id if hasattr(unit, 'unit_id') else unit.get("unit_id")
                    if not unit_id:
                        logger.error(f"Missing unit_id in management unit object: {unit}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(unit_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get unit_id safely for logging
                    unit_id = getattr(unit, 'unit_id', None) if hasattr(unit, 'unit_id') else unit.get("unit_id", "unknown")
                    logger.error(f"Error syncing management unit node {unit_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing management unit nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during management unit nodes synchronization: {e}")
            return (0, 0)
    
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
            
    async def sync_relationship_by_id(self, unit_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific management unit.
        
        Args:
            unit_id: ID of the management unit to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for management unit {unit_id}")
        
        # Check if management unit node exists before syncing relationships
        unit_node = await self.graph_repository.get_by_id(unit_id)
        if not unit_node:
            logger.warning(f"Management unit node {unit_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Management unit node not found in Neo4j",
                "exams": 0,
                "parent_unit": 0,
                "child_units": 0
            }
        
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
            
            logger.info(f"Management unit relationship synchronization completed for {unit_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for management unit {unit_id}: {e}")
            return relationship_counts
            
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all management units.
        
        Args:
            limit: Optional maximum number of management units to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all management units (limit={limit})")
        
        try:
            # Get all management units from SQL database
            units, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_units = len(units)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "exams": 0,
                "parent_unit": 0,
                "child_units": 0
            }
            
            # For each management unit, sync relationships
            for unit in units:
                try:
                    # Get unit_id safely - handle both ORM objects and dictionaries
                    unit_id = unit.unit_id if hasattr(unit, 'unit_id') else unit.get("unit_id")
                    if not unit_id:
                        logger.error(f"Missing unit_id in management unit object: {unit}")
                        failure_count += 1
                        continue
                    
                    # Verify management unit exists in Neo4j
                    unit_node = await self.graph_repository.get_by_id(unit_id)
                    if not unit_node:
                        logger.warning(f"Management unit {unit_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this management unit
                    results = await self.sync_relationship_by_id(unit_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get unit_id safely for logging
                    unit_id = getattr(unit, 'unit_id', None) if hasattr(unit, 'unit_id') else unit.get("unit_id", "unknown")
                    logger.error(f"Error synchronizing relationships for management unit {unit_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_units": total_units,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all management units: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during management unit relationships synchronization: {e}")
            return {
                "total_units": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            } 