from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.school_repository import SchoolRepository
from typing import Dict, Any
import logging

class DashboardService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.candidate_repo = CandidateRepository(db_session)
        self.exam_repo = ExamRepository(db_session)
        self.school_repo = SchoolRepository(db_session)
        self.logger = logging.getLogger(__name__)

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get dashboard statistics including:
        - Total number of candidates
        - Total number of exams
        - Total number of schools
        """
        try:
            # Get total candidates using COUNT
            candidate_count = await self.candidate_repo.count()

            # Get total exams using COUNT
            exam_count = await self.exam_repo.count()

            # Get total schools using COUNT
            school_count = await self.school_repo.count()

            self.logger.info(f"Retrieved dashboard stats: {candidate_count} candidates, {exam_count} exams, {school_count} schools")
            
            return {
                "total_candidates": candidate_count,
                "total_exams": exam_count,
                "total_schools": school_count
            }
        except Exception as e:
            self.logger.error(f"Error getting dashboard stats: {e}")
            raise 