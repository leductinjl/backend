"""
API routes configuration module.

This module handles the registration of all API routers with the FastAPI application,
organizing them by domain and ensuring consistent URL prefixes.
"""

from fastapi import FastAPI
from app.config import settings
import logging

# Explicit imports for clarity and to avoid importing any unintended routers
from app.api.controllers.candidate_router import router as candidate_router
from app.api.controllers.admin_router import router as admin_router
from app.api.controllers.health_router import router as health_router
from app.api.controllers.management_unit_router import router as management_unit_router
from app.api.controllers.school_router import router as school_router
from app.api.controllers.major_router import router as major_router
from app.api.controllers.subject_router import router as subject_router
from app.api.controllers.exam_type_router import router as exam_type_router
from app.api.controllers.school_major_router import router as school_major_router
from app.api.controllers.exam_router import router as exam_router
from app.api.controllers.exam_location_router import router as exam_location_router
from app.api.controllers.exam_room_router import router as exam_room_router
from app.api.controllers.exam_location_mapping_router import router as exam_location_mapping_router
from app.api.controllers.exam_subject_router import router as exam_subject_router
from app.api.controllers.exam_schedule_router import router as exam_schedule_router
from app.api.controllers.candidate_exam_router import router as candidate_exam_router
from app.api.controllers.candidate_exam_subject_router import router as candidate_exam_subject_router
from app.api.controllers.candidate_credential_router import router as candidate_credential_router
from app.api.controllers.exam_score_router import router as exam_score_router
from app.api.controllers.score_review_router import router as score_review_router
from app.api.controllers.exam_score_history_router import router as exam_score_history_router
from app.api.controllers.certificate_router import router as certificate_router
from app.api.controllers.exam_attempt_history_router import router as exam_attempt_history_router
from app.api.controllers.degree_router import router as degree_router
from app.api.controllers.education_history_router import router as education_history_router
from app.api.controllers.education_level_router import router as education_level_router
from app.api.controllers.recognition_router import router as recognition_router
from app.api.controllers.award_router import router as award_router
from app.api.controllers.achievement_router import router as achievement_router
from app.api.controllers.knowledge_graph_controller import router as knowledge_graph_router

logger = logging.getLogger("api")

def register_router(app, router, tag_name):
    """
    Helper function to register router with consistent prefix.
    
    Args:
        app: The FastAPI application instance
        router: The router to register
        tag_name: The tag name for OpenAPI documentation
    """
    logger.info(f"Registering router with tag: {tag_name}")
    app.include_router(
        router,
        prefix=f"{settings.API_PREFIX}",
        tags=[tag_name]
    )

def setup_routes(app: FastAPI):
    """
    Register all API routes with the application.
    
    This function:
    1. Registers the health check router (with special handling)
    2. Maps all domain routers to their OpenAPI tags
    3. Registers each domain router with the application
    4. Sets up the root endpoint for basic API information
    
    Args:
        app: The FastAPI application to register routes with
    """
    # Register health router with special prefix
    app.include_router(
        health_router,
        prefix=f"{settings.API_PREFIX}",
        tags=["Health"]
    )

    # Define a list of tuples with (router, tag) pairs instead of using a dictionary
    router_tags = [
        (admin_router, "Admin"),
        (candidate_router, "Candidates"),
        (management_unit_router, "Management Units"),
        (school_router, "Schools"),
        (major_router, "Majors"),
        (subject_router, "Subjects"),
        (degree_router, "Degrees"),
        (education_history_router, "Education Histories"),
        (education_level_router, "Education Levels"),
        (recognition_router, "Recognitions"),
        (award_router, "Awards"),
        (achievement_router, "Achievements"),
        (exam_type_router, "Exam Types"),
        (school_major_router, "School Majors"),
        (exam_router, "Exams"),
        (exam_location_router, "Exam Locations"),
        (exam_room_router, "Exam Rooms"),
        (exam_location_mapping_router, "Exam Location Mappings"),
        (exam_subject_router, "Exam Subjects"),
        (exam_schedule_router, "Exam Schedules"),
        (candidate_exam_router, "Candidate Exams"),
        (candidate_exam_subject_router, "Candidate Exam Subjects"),
        (candidate_credential_router, "Candidate Credentials"),
        (exam_score_router, "Exam Scores"),
        (score_review_router, "Score Reviews"),
        (exam_score_history_router, "Exam Score Histories"),
        (certificate_router, "Certificates"),
        (exam_attempt_history_router, "Attempt Histories"),
        (knowledge_graph_router, "Knowledge Graph")
    ]

    # Register all routers using the list of tuples
    for router, tag in router_tags:
        register_router(app, router, tag)
        
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint that provides basic API information."""
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": f"{settings.API_PREFIX}/docs"
        } 