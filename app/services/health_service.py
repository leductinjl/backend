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
        # Add a timeout to avoid hanging
        query_result = await db.execute(text("SELECT 1"))
        row = query_result.fetchone()
        if row and row[0] == 1:
            result["status"] = "up"
        else:
            logger.error("PostgreSQL health check failed: Unexpected response")
            result["error"] = "Unexpected response from database"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        result["error"] = str(e)
    
    return result

async def check_neo4j(neo4j_driver):
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
        # Check if our driver has the run_health_check method
        if hasattr(neo4j_driver, 'run_health_check'):
            # Use our custom health check method
            if await neo4j_driver.run_health_check():
                result["status"] = "up"
                return result
                
        # Try the execute_query method next
        elif hasattr(neo4j_driver, 'execute_query'):
            records = await neo4j_driver.execute_query("RETURN 1 AS num")
            if records and len(records) > 0 and records[0][0] == 1:
                result["status"] = "up"
                return result
                
        # If direct methods fail, log detailed error
        logger.error("Neo4j health check failed: Unable to query Neo4j. Object type: " + str(type(neo4j_driver)))
        result["error"] = "Could not execute Neo4j query"
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        result["error"] = str(e)
    
    return result

async def check_redis(redis_client):
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
        # Handle both direct Redis client and our RedisCache wrapper
        if hasattr(redis_client, 'ping'):
            ping_result = await redis_client.ping()
            if ping_result:
                result["status"] = "up"
        else:
            logger.error("Redis health check failed: Redis client has no ping method")
            result["error"] = "Incompatible Redis client object"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        result["error"] = str(e)
    
    return result 