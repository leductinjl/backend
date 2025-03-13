"""
Neo4j database connection module.

This module provides connection handling for Neo4j graph database, including:
- Connection setup and configuration
- Query execution utilities
- Connection management
- FastAPI dependency for Neo4j connection injection
"""

from neo4j import AsyncGraphDatabase
from app.config import settings
import logging

class Neo4jConnection:
    """
    Neo4j connection handler for graph database operations.
    
    This class manages the connection to Neo4j and provides
    methods for executing Cypher queries.
    """
    
    def __init__(self):
        """Initialize Neo4j connection parameters from settings."""
        self._driver = None
        self._uri = settings.NEO4J_URI
        self._user = settings.NEO4J_USER
        self._password = settings.NEO4J_PASSWORD
        self._database = settings.NEO4J_DATABASE

    async def connect(self):
        """
        Connect to Neo4j database.
        
        Establishes a connection to the Neo4j database using
        the configuration parameters.
        
        Returns:
            AsyncDriver: The Neo4j driver instance
            
        Raises:
            Exception: If connection to Neo4j fails
        """
        try:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password)
            )
            # Verify connection is working
            await self._driver.verify_connectivity()
            logging.info("Connected to Neo4j database successfully")
            return self._driver
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def close(self):
        """
        Close the Neo4j connection.
        
        Properly closes the connection to the Neo4j database.
        """
        if self._driver:
            await self._driver.close()
            logging.info("Neo4j connection closed")

    async def execute_query(self, query, params=None):
        """
        Execute a Cypher query in Neo4j.
        
        Args:
            query (str): The Cypher query to execute
            params (dict, optional): Parameters for the query. Defaults to None.
            
        Returns:
            list: The query results as a list of records
            
        Raises:
            Exception: If the query execution fails
        """
        try:
            if not self._driver:
                await self.connect()
            
            async with self._driver.session(database=self._database) as session:
                result = await session.run(query, params or {})
                records = await result.values()
                return records
        except Exception as e:
            logging.error(f"Error executing Neo4j query: {e}")
            raise

    async def run_health_check(self):
        """
        Run a simple health check query on Neo4j.
        
        This method is specifically designed for health checks.
        
        Returns:
            bool: True if the health check passes, False otherwise
        """
        try:
            if not self._driver:
                await self.connect()
            
            async with self._driver.session(database=self._database) as session:
                result = await session.run("RETURN 1 AS num")
                record = await result.single()
                return record and record["num"] == 1
        except Exception as e:
            logging.error(f"Neo4j health check failed: {e}")
            return False

# Initialize Neo4j connection
neo4j_connection = Neo4jConnection()

async def init_neo4j():
    """
    Initialize Neo4j connection when application starts.
    
    This function is called during application startup to
    establish the Neo4j connection.
    """
    await neo4j_connection.connect()

async def get_neo4j():
    """
    FastAPI dependency for Neo4j connection injection.
    
    Provides the Neo4j connection to API endpoints.
    
    Returns:
        Neo4jConnection: The Neo4j connection handler
        
    Example:
        ```
        @router.get("/graph-data")
        async def get_graph_data(neo4j = Depends(get_neo4j)):
            # Use neo4j connection here
            ...
        ```
    """
    return neo4j_connection 