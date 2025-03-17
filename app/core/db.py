"""
Database connection module.

This module handles initialization of connections to various data stores
including PostgreSQL, Neo4j graph database, and Redis cache.
"""

import logging
from app.infrastructure.database.connection import init_db
from app.infrastructure.ontology.neo4j_connection import init_neo4j
from app.infrastructure.cache.redis_connection import init_redis

async def connect_to_db():
    """
    Initialize all database connections.
    
    This function asynchronously connects to:
    1. PostgreSQL database (main data storage)
    2. Neo4j graph database (for ontology and relationships)
    3. Redis cache (for performance optimization)
    
    It should be called during application startup.
    """
    try:
        # Initialize each database connection
        await init_db()  # Initialize PostgreSQL
        logging.info("Connected to PostgreSQL database")
        
        await init_neo4j()  # Initialize Neo4j
        logging.info("Connected to Neo4j graph database")
        
        await init_redis()  # Initialize Redis
        logging.info("Connected to Redis cache")
        
        # Log overall success
        logging.info("All database connections established successfully")
    except Exception as e:
        # Log critical error if database connections fail
        logging.critical(f"Failed to initialize database connections: {str(e)}")
        logging.exception(e)
        raise  # Re-raise to prevent app startup with broken connections 