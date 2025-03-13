"""
Health service module.

This module provides service functions for checking the health of the application
and its connections to various databases and services.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from neo4j import AsyncDriver
import redis.asyncio as redis
import logging
from datetime import datetime

logger = logging.getLogger("api")

async def check_all_services(db: AsyncSession, neo4j_driver: AsyncDriver, redis_client: redis.Redis):
    """
    Check the health of all services.
    
    Args:
        db: PostgreSQL database session
        neo4j_driver: Neo4j driver instance
        redis_client: Redis client instance
        
    Returns:
        dict: Health information for all services
    """
    start_time = datetime.now()
    health_info = {
        "status": "healthy",
        "timestamp": start_time.isoformat(),
        "services": {
            "api": {
                "status": "up"
            },
            "postgres": {
                "status": "checking"
            },
            "neo4j": {
                "status": "checking"
            },
            "redis": {
                "status": "checking"
            }
        }
    }
    
    # Check PostgreSQL connection
    postgres_status = await check_postgres(db)
    health_info["services"]["postgres"] = postgres_status
    if postgres_status["status"] == "down":
        health_info["status"] = "degraded"
    
    # Check Neo4j connection
    neo4j_status = await check_neo4j(neo4j_driver)
    health_info["services"]["neo4j"] = neo4j_status
    if neo4j_status["status"] == "down":
        health_info["status"] = "degraded"
    
    # Check Redis connection
    redis_status = await check_redis(redis_client)
    health_info["services"]["redis"] = redis_status
    if redis_status["status"] == "down":
        health_info["status"] = "degraded"
    
    # Calculate response time
    end_time = datetime.now()
    health_info["response_time_ms"] = (end_time - start_time).total_seconds() * 1000
    
    return health_info

async def check_postgres(db: AsyncSession):
    """
    Check PostgreSQL database connection.
    
    Args:
        db: PostgreSQL database session
        
    Returns:
        dict: PostgreSQL connection status
    """
    result = {
        "status": "down"
    }
    
    try:
        query_result = await db.execute(text("SELECT 1"))
        await query_result.fetchone()
        result["status"] = "up"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        result["error"] = str(e)
    
    return result

async def check_neo4j(neo4j_driver: AsyncDriver):
    """
    Check Neo4j database connection.
    
    Args:
        neo4j_driver: Neo4j driver instance
        
    Returns:
        dict: Neo4j connection status
    """
    result = {
        "status": "down"
    }
    
    try:
        async with neo4j_driver.session() as session:
            query_result = await session.run("RETURN 1 AS num")
            record = await query_result.single()
            if record and record["num"] == 1:
                result["status"] = "up"
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        result["error"] = str(e)
    
    return result

async def check_redis(redis_client: redis.Redis):
    """
    Check Redis cache connection.
    
    Args:
        redis_client: Redis client instance
        
    Returns:
        dict: Redis connection status
    """
    result = {
        "status": "down"
    }
    
    try:
        await redis_client.ping()
        result["status"] = "up"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        result["error"] = str(e)
    
    return result 