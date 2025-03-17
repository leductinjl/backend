"""
Health check router module.

This module provides endpoints for checking the health of the application 
and its connections to various services (PostgreSQL, Neo4j, Redis).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from neo4j import AsyncDriver
import redis.asyncio as redis
import logging
from datetime import datetime
import asyncio

from app.infrastructure.database.connection import get_db
from app.infrastructure.ontology.neo4j_connection import get_neo4j
from app.infrastructure.cache.redis_connection import get_redis
from app.services.health_service import (
    check_all_services, 
    check_postgres, 
    check_neo4j, 
    check_redis
)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
    responses={404: {"description": "Not found"}}
)
logger = logging.getLogger("api")

@router.get("/", summary="Health Check")
async def health_check(
    db: AsyncSession = Depends(get_db),
    neo4j_driver = Depends(get_neo4j),
    redis_client = Depends(get_redis)
):
    """
    Check the health of the application and its connections.
    
    This endpoint checks if the application can connect to:
    - PostgreSQL database
    - Neo4j graph database
    - Redis cache
    
    Returns:
        dict: Health status of all services
    """
    return await check_all_services(db, neo4j_driver, redis_client)

@router.get("/postgres", summary="PostgreSQL Health Check")
async def postgres_health(db: AsyncSession = Depends(get_db)):
    """
    Check only the PostgreSQL database connection.
    
    Returns:
        dict: PostgreSQL connection health status
    """
    result = await check_postgres(db)
    
    if result["status"] == "down":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PostgreSQL connection failed: {result.get('error', 'Unknown error')}"
        )
    
    return {
        "status": "up",
        "timestamp": datetime.now().isoformat(),
        "message": "PostgreSQL connection is healthy"
    }

@router.get("/neo4j", summary="Neo4j Health Check")
async def neo4j_health(neo4j_driver = Depends(get_neo4j)):
    """
    Check only the Neo4j database connection.
    
    Returns:
        dict: Neo4j connection health status
    """
    result = await check_neo4j(neo4j_driver)
    
    if result["status"] == "down":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Neo4j connection failed: {result.get('error', 'Unknown error')}"
        )
    
    return {
        "status": "up",
        "timestamp": datetime.now().isoformat(),
        "message": "Neo4j connection is healthy"
    }

@router.get("/redis", summary="Redis Health Check")
async def redis_health(redis_client = Depends(get_redis)):
    """
    Check only the Redis cache connection.
    
    Returns:
        dict: Redis connection health status
    """
    result = await check_redis(redis_client)
    
    if result["status"] == "down":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection failed: {result.get('error', 'Unknown error')}"
        )
    
    return {
        "status": "up",
        "timestamp": datetime.now().isoformat(),
        "message": "Redis connection is healthy"
    } 