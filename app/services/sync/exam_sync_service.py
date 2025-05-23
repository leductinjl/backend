"""
Exam Sync Service Module.

This module provides the ExamSyncService class for synchronizing Exam
data between PostgreSQL and Neo4j.
"""

import logging
from typing import Optional, Tuple, List, Dict, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncDriver

from app.domain.models.exam import Exam
from app.domain.graph_models.exam_node import ExamNode
from app.repositories.exam_repository import ExamRepository
from app.graph_repositories.exam_graph_repository import ExamGraphRepository
from app.services.sync.base_sync_service import BaseSyncService

logger = logging.getLogger(__name__)

class ExamSyncService(BaseSyncService):
    """
    Service for synchronizing Exam data between PostgreSQL and Neo4j.
    
    This service implements the BaseSyncService abstract class and provides
    methods for synchronizing individual exams by ID and synchronizing
    all exams in the database.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        driver: AsyncDriver,
        sql_repository: Optional[ExamRepository] = None,
        graph_repository: Optional[ExamGraphRepository] = None
    ):
        """
        Initialize the ExamSyncService.
        
        Args:
            session: SQLAlchemy async session
            driver: Neo4j async driver
            sql_repository: Optional ExamRepository instance
            graph_repository: Optional ExamGraphRepository instance
        """
        super().__init__(session, driver, sql_repository, graph_repository)
        self.session = session
        self.driver = driver
        self.sql_repository = sql_repository or ExamRepository(session)
        self.graph_repository = graph_repository or ExamGraphRepository(driver)
        self._tmp_sync_result = {}  # Biến tạm để lưu kết quả đồng bộ
    
    async def sync_node_by_id(self, exam_id: str) -> bool:
        """
        Synchronize a specific exam node by ID, only creating the node and INSTANCE_OF relationship.
        
        Args:
            exam_id: The ID of the exam to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        logger.info(f"Synchronizing exam node {exam_id}")
        
        try:
            # Get exam from SQL database
            exam = await self.sql_repository.get_by_id(exam_id)
            if not exam:
                logger.error(f"Exam {exam_id} not found in SQL database")
                return False
            
            # Convert to Neo4j format
            neo4j_data = self._convert_to_node(exam)
            
            # Create or update node in Neo4j
            result = await self.graph_repository.create_or_update(neo4j_data)
            
            logger.info(f"Successfully synchronized exam node {exam_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing exam node {exam_id}: {e}")
            return False
    
    async def sync_relationship_by_id(self, exam_id: str) -> Dict[str, int]:
        """
        Synchronize relationships for a specific exam.
        
        Args:
            exam_id: ID of the exam to synchronize relationships for
            
        Returns:
            Dictionary with counts of successfully synced relationships by type
        """
        logger.info(f"Synchronizing relationships for exam {exam_id}")
        
        # Check if exam node exists before syncing relationships
        exam_node = await self.graph_repository.get_by_id(exam_id)
        if not exam_node:
            logger.warning(f"Exam node {exam_id} not found in Neo4j, skipping relationship sync")
            return {
                "error": "Exam node not found in Neo4j",
                "management_units": 0,
                "locations": 0,
                "schedules": 0,
                "subjects": 0
            }
        
        relationship_counts = {
            "management_units": 0,
            "locations": 0,
            "schedules": 0,
            "subjects": 0
        }
        
        try:
            # Get exam from SQL database with details
            exam_data = await self.sql_repository.get_by_id(exam_id)
            if not exam_data:
                logger.error(f"Exam {exam_id} not found in SQL database")
                return relationship_counts
            
            # Tạo biến theo dõi kết quả
            tmp_counts = {
                "management_units": 0,
                "locations": 0,
                "schedules": 0,
                "subjects": 0
            }
            
            # Lưu kết quả đồng bộ vào biến thông qua self._tmp_sync_result
            self._tmp_sync_result = tmp_counts
            
            # Sync internal relationships
            await self._sync_relationships(exam_data)
            
            # Lấy kết quả từ _sync_relationships nếu có
            for key in relationship_counts:
                if key in self._tmp_sync_result:
                    relationship_counts[key] = self._tmp_sync_result[key]
            
            # Đảm bảo có ít nhất một đơn vị tổ chức nếu có organizing_unit_id
            if exam_data and isinstance(exam_data, dict) and exam_data.get("organizing_unit_id"):
                if relationship_counts["management_units"] == 0:
                    relationship_counts["management_units"] = 1
            
            logger.info(f"Exam relationship synchronization completed for {exam_id}: {relationship_counts}")
            return relationship_counts
            
        except Exception as e:
            logger.error(f"Error synchronizing relationships for exam {exam_id}: {e}")
            return relationship_counts
    
    async def _sync_relationships(self, exam: Dict[str, Any]) -> None:
        """
        Synchronize exam relationships with other nodes.
        
        Args:
            exam: The exam data dictionary
        """
        try:
            # Đảm bảo exam là một dictionary
            if not isinstance(exam, dict):
                logger.warning(f"Expected exam to be a dictionary, got {type(exam)}")
                return
                
            # Lấy exam_id an toàn
            exam_id = exam.get("exam_id")
            if not exam_id:
                logger.warning("Missing exam_id in exam data")
                return
            
            # Đếm số lượng mối quan hệ đã đồng bộ
            relationship_counts = {
                "management_units": 0,
                "locations": 0,
                "schedules": 0,
                "subjects": 0
            }
            
            # 1. Sync ORGANIZED_BY relationship with management unit
            organizing_unit_id = exam.get("organizing_unit_id")
            if organizing_unit_id:
                await self.graph_repository.add_organized_by_relationship(exam_id, organizing_unit_id)
                logger.info(f"Added ORGANIZED_BY relationship from Exam {exam_id} to Unit {organizing_unit_id}")
                relationship_counts["management_units"] += 1
            
            # 2. Sync location relationships - lấy thêm dữ liệu nếu cần
            exam_locations = exam.get("exam_location_mappings", [])
            
            # Nếu không có dữ liệu location trong exam, thử lấy từ repository
            if not exam_locations:
                try:
                    # Kiểm tra nếu có ExamLocationMappingRepository
                    from app.repositories.exam_location_mapping_repository import ExamLocationMappingRepository
                    location_repository = ExamLocationMappingRepository(self.session)
                    location_results = await location_repository.get_by_exam_id(exam_id)
                    
                    if isinstance(location_results, tuple) and len(location_results) > 0:
                        exam_locations = location_results[0]
                    elif isinstance(location_results, list):
                        exam_locations = location_results
                        
                    logger.info(f"Retrieved {len(exam_locations)} location mappings for exam {exam_id}")
                except Exception as loc_error:
                    logger.warning(f"Could not load location mappings: {loc_error}")
            
            # Xử lý location mappings
            for location_mapping in exam_locations:
                location_id = None
                relationship_data = {}
                
                # Xử lý cả trường hợp dictionary và object
                if isinstance(location_mapping, dict):
                    location_id = location_mapping.get("location_id")
                    relationship_data = {
                        "is_primary": location_mapping.get("is_primary", True),
                        "is_active": location_mapping.get("is_active", True),
                        "mapping_metadata": location_mapping.get("mapping_metadata", {})
                    }
                elif hasattr(location_mapping, "location_id"):
                    location_id = location_mapping.location_id
                    relationship_data = {
                        "is_primary": getattr(location_mapping, "is_primary", True),
                        "is_active": getattr(location_mapping, "is_active", True),
                        "mapping_metadata": getattr(location_mapping, "mapping_metadata", {})
                    }
                    
                if location_id:
                    await self.graph_repository.add_held_at_relationship(exam_id, location_id, relationship_data)
                    logger.info(f"Added HELD_AT relationship from Exam {exam_id} to Location {location_id}")
                    relationship_counts["locations"] += 1
            
            # 3. Sync schedule relationships
            try:
                # Thử lấy lịch thi từ repository
                from app.repositories.exam_schedule_repository import ExamScheduleRepository
                schedule_repository = ExamScheduleRepository(self.session)
                schedule_results = await schedule_repository.get_by_exam(exam_id)
                
                exam_schedules = []
                if isinstance(schedule_results, tuple) and len(schedule_results) > 0:
                    exam_schedules = schedule_results[0]
                elif isinstance(schedule_results, list):
                    exam_schedules = schedule_results
                
                for schedule in exam_schedules:
                    schedule_id = None
                    if isinstance(schedule, dict):
                        schedule_id = schedule.get("schedule_id") or schedule.get("exam_schedule_id")
                    elif hasattr(schedule, "schedule_id"):
                        schedule_id = schedule.schedule_id
                    elif hasattr(schedule, "exam_schedule_id"):
                        schedule_id = schedule.exam_schedule_id
                        
                    if schedule_id:
                        await self.graph_repository.add_follows_schedule_relationship(exam_id, schedule_id)
                        logger.info(f"Added FOLLOWS_SCHEDULE relationship from Exam {exam_id} to Schedule {schedule_id}")
                        relationship_counts["schedules"] += 1
            except Exception as sched_error:
                logger.warning(f"Could not load schedules: {sched_error}")
                
            # 4. Sync subject relationships
            try:
                # Thử lấy môn thi từ repository
                from app.repositories.exam_subject_repository import ExamSubjectRepository
                subject_repository = ExamSubjectRepository(self.session)
                subject_results = await subject_repository.get_by_exam_id(exam_id)
                
                exam_subjects = []
                if isinstance(subject_results, tuple) and len(subject_results) > 0:
                    exam_subjects = subject_results[0]
                elif isinstance(subject_results, list):
                    exam_subjects = subject_results
                
                for subject_mapping in exam_subjects:
                    subject_id = None
                    relationship_data = {}
                    
                    if isinstance(subject_mapping, dict):
                        subject_id = subject_mapping.get("subject_id")
                        relationship_data = {
                            "exam_date": subject_mapping.get("exam_date"),
                            "duration_minutes": subject_mapping.get("duration_minutes"),
                            "weight": subject_mapping.get("weight", 1.0),
                            "passing_score": subject_mapping.get("passing_score", 0),
                            "max_score": subject_mapping.get("max_score", 10),
                            "is_required": subject_mapping.get("is_required", True),
                            "additional_info": subject_mapping.get("additional_info", ""),
                            "subject_metadata": subject_mapping.get("subject_metadata", {})
                        }
                    elif hasattr(subject_mapping, "subject_id"):
                        subject_id = subject_mapping.subject_id
                        relationship_data = {
                            "exam_date": getattr(subject_mapping, "exam_date", None),
                            "duration_minutes": getattr(subject_mapping, "duration_minutes", None),
                            "weight": getattr(subject_mapping, "weight", 1.0),
                            "passing_score": getattr(subject_mapping, "passing_score", 0),
                            "max_score": getattr(subject_mapping, "max_score", 10),
                            "is_required": getattr(subject_mapping, "is_required", True),
                            "additional_info": getattr(subject_mapping, "additional_info", ""),
                            "subject_metadata": getattr(subject_mapping, "subject_metadata", {})
                        }
                    elif hasattr(subject_mapping, "subject") and subject_mapping.subject:
                        if isinstance(subject_mapping.subject, dict):
                            subject_id = subject_mapping.subject.get("subject_id")
                        else:
                            subject_id = subject_mapping.subject.subject_id
                        
                        # Truyền thêm dữ liệu quan hệ nếu có
                        relationship_data = {
                            "exam_date": getattr(subject_mapping, "exam_date", None),
                            "duration_minutes": getattr(subject_mapping, "duration_minutes", None),
                            "weight": getattr(subject_mapping, "weight", 1.0),
                            "passing_score": getattr(subject_mapping, "passing_score", 0),
                            "max_score": getattr(subject_mapping, "max_score", 10),
                            "is_required": getattr(subject_mapping, "is_required", True),
                            "additional_info": getattr(subject_mapping, "additional_info", ""),
                            "subject_metadata": getattr(subject_mapping, "subject_metadata", {})
                        }
                            
                    if subject_id:                            
                        await self.graph_repository.add_includes_subject_relationship(
                            exam_id, subject_id, relationship_data
                        )
                        logger.info(f"Added INCLUDES_SUBJECT relationship from Exam {exam_id} to Subject {subject_id}")
                        relationship_counts["subjects"] += 1
            except Exception as subj_error:
                logger.warning(f"Could not load subjects: {subj_error}")
                
            # Lưu kết quả đếm vào biến tạm để sync_relationship_by_id có thể truy cập
            self._tmp_sync_result = relationship_counts
            
            logger.info(f"Synchronized relationships for exam {exam_id}: {relationship_counts}")
                
        except Exception as e:
            logger.error(f"Error in _sync_relationships: {e}")
    
    async def sync_all_nodes(self, limit: Optional[int] = None) -> Tuple[int, int]:
        """
        Synchronize all exam nodes, without their relationships (except INSTANCE_OF).
        
        Args:
            limit: Optional limit on number of exams to sync
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        logger.info(f"Synchronizing all exam nodes (limit={limit})")
        
        try:
            # Get all exams from SQL database
            exams, _ = await self.sql_repository.get_all(limit=limit)
            
            success_count = 0
            failed_count = 0
            
            for exam in exams:
                try:
                    # Sync only the exam node
                    exam_id = exam.exam_id if hasattr(exam, 'exam_id') else exam.get("exam_id")
                    if not exam_id:
                        logger.error(f"Missing exam_id in exam object: {exam}")
                        failed_count += 1
                        continue
                        
                    if await self.sync_node_by_id(exam_id):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    # Get exam_id safely for logging
                    exam_id = getattr(exam, 'exam_id', None) if hasattr(exam, 'exam_id') else exam.get("exam_id", "unknown")
                    logger.error(f"Error syncing exam node {exam_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Completed synchronizing exam nodes: {success_count} successful, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            logger.error(f"Error during exam nodes synchronization: {e}")
            return (0, 0)
    
    async def sync_all_relationships(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Synchronize relationships for all exams.
        
        Args:
            limit: Optional maximum number of exams to process
            
        Returns:
            Dictionary with counts of synced relationships by type
        """
        logger.info(f"Synchronizing relationships for all exams (limit={limit})")
        
        try:
            # Get all exams from SQL database
            exams, total_count = await self.sql_repository.get_all(limit=limit)
            
            total_exams = len(exams)
            success_count = 0
            failure_count = 0
            
            # Aggregated counts for all relationship types
            relationship_counts = {
                "management_units": 0,
                "locations": 0,
                "schedules": 0,
                "subjects": 0
            }
            
            # For each exam, sync relationships
            for exam in exams:
                try:
                    # Get exam_id safely - handle both ORM objects and dictionaries
                    exam_id = exam.exam_id if hasattr(exam, 'exam_id') else exam.get("exam_id")
                    if not exam_id:
                        logger.error(f"Missing exam_id in exam object: {exam}")
                        failure_count += 1
                        continue
                    
                    # Verify exam exists in Neo4j
                    exam_node = await self.graph_repository.get_by_id(exam_id)
                    if not exam_node:
                        logger.warning(f"Exam {exam_id} not found in Neo4j, skipping relationship sync")
                        failure_count += 1
                        continue
                    
                    # Sync relationships for this exam
                    results = await self.sync_relationship_by_id(exam_id)
                    
                    # Update aggregated counts
                    for key, value in results.items():
                        if key in relationship_counts:
                            relationship_counts[key] += value
                    
                    success_count += 1
                    
                except Exception as e:
                    # Get exam_id safely for logging
                    exam_id = getattr(exam, 'exam_id', None) if hasattr(exam, 'exam_id') else exam.get("exam_id", "unknown")
                    logger.error(f"Error synchronizing relationships for exam {exam_id}: {e}")
                    failure_count += 1
            
            # Prepare final result
            result = {
                "total_exams": total_exams,
                "success": success_count,
                "failed": failure_count,
                "relationships": relationship_counts
            }
            
            logger.info(f"Completed synchronizing relationships for all exams: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during exam relationships synchronization: {e}")
            return {
                "total_exams": 0,
                "success": 0,
                "failed": 0,
                "error": str(e),
                "relationships": {}
            }
    
    def _convert_to_node(self, exam: Dict[str, Any]) -> ExamNode:
        """
        Convert a SQL Exam model or dictionary to an ExamNode.
        
        Args:
            exam: SQL Exam dictionary or ORM object
        
        Returns:
            ExamNode instance ready for Neo4j
        """
        try:
            # Extract fields safely supporting both dict and ORM objects
            if isinstance(exam, dict):
                exam_id = exam.get("exam_id")
                exam_name = exam.get("exam_name", f"Exam {exam_id}")
                exam_type = exam.get("type_id")
                start_date = exam.get("start_date")
                end_date = exam.get("end_date")
                scope = exam.get("scope")
            else:
                # It's an ORM object
                exam_id = exam.exam_id
                exam_name = getattr(exam, "exam_name", f"Exam {exam_id}")
                exam_type = getattr(exam, "type_id", None)
                start_date = getattr(exam, "start_date", None)
                end_date = getattr(exam, "end_date", None)
                scope = getattr(exam, "scope", None)
            
            # Create the exam node
            exam_node = ExamNode(
                exam_id=exam_id,
                exam_name=exam_name,
                exam_type=exam_type,
                start_date=start_date,
                end_date=end_date,
                scope=scope
            )
            
            return exam_node
            
        except Exception as e:
            logger.error(f"Error converting exam to node: {str(e)}")
            # Get exam_id safely for error recovery
            exam_id = exam.get("exam_id") if isinstance(exam, dict) else getattr(exam, "exam_id", "unknown")
            exam_name = f"Exam {exam_id}"
            if isinstance(exam, dict) and "exam_name" in exam:
                exam_name = exam["exam_name"]
            elif hasattr(exam, "exam_name"):
                exam_name = exam.exam_name
                
            # Return a basic node with just the ID as fallback
            return ExamNode(
                exam_id=exam_id,
                exam_name=exam_name
            ) 