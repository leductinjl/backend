"""
Redis cache connection module.

This module provides connection handling for Redis cache, including:
- Connection setup and configuration
- Cache operations (get, set, delete)
- JSON serialization/deserialization for complex data types
- FastAPI dependency for Redis cache injection
"""

import redis.asyncio as redis
from app.config import settings
import logging
import json

class RedisCache:
    """
    Redis cache handler for data caching operations.
    
    This class manages the connection to Redis and provides
    methods for storing, retrieving, and deleting cached data.
    """
    
    def __init__(self):
        """Initialize Redis connection parameters from settings."""
        self._client = None
        self._host = settings.REDIS_HOST
        self._port = settings.REDIS_PORT
        self._db = settings.REDIS_DB
        self._password = settings.REDIS_PASSWORD

    async def connect(self):
        """
        Connect to Redis cache.
        
        Establishes a connection to the Redis cache using
        the configuration parameters.
        
        Returns:
            Redis: The Redis client instance
            
        Raises:
            Exception: If connection to Redis fails
        """
        try:
            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password or None,
                decode_responses=True  # Automatically decode responses to strings
            )
            # Verify connection is working
            await self._client.ping()
            logging.info("Connected to Redis cache successfully")
            return self._client
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """
        Close the Redis connection.
        
        Properly closes the connection to the Redis cache.
        """
        if self._client:
            await self._client.close()
            logging.info("Redis connection closed")

    async def get(self, key):
        """
        Retrieve data from cache.
        
        Attempts to retrieve data from Redis by key and automatically
        deserializes JSON data if applicable.
        
        Args:
            key (str): The cache key to retrieve
            
        Returns:
            Any: The cached data, or None if not found
            
        Note:
            JSON objects are automatically deserialized to Python objects
        """
        try:
            data = await self._client.get(key)
            if data:
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data
            return None
        except Exception as e:
            logging.error(f"Error getting data from Redis: {e}")
            return None

    async def set(self, key, value, expires=None):
        """
        Store data in cache.
        
        Stores data in Redis with the specified key and optional expiration.
        Automatically serializes complex data types to JSON.
        
        Args:
            key (str): The cache key to store under
            value (Any): The data to cache
            expires (int, optional): Expiration time in seconds. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise
            
        Note:
            Dictionaries, lists, and tuples are automatically serialized to JSON
        """
        try:
            if isinstance(value, (dict, list, tuple)):
                value = json.dumps(value)
            await self._client.set(key, value, ex=expires)
            return True
        except Exception as e:
            logging.error(f"Error setting data to Redis: {e}")
            return False

    async def delete(self, key):
        """
        Delete data from cache.
        
        Removes data with the specified key from Redis.
        
        Args:
            key (str): The cache key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logging.error(f"Error deleting key from Redis: {e}")
            return False

    async def ttl(self, key):
        """
        Get the time-to-live for a key.
        
        Args:
            key (str): The cache key to check
            
        Returns:
            int: Time-to-live in seconds, or -1 if the key has no expiry,
                 or -2 if the key doesn't exist
        """
        try:
            return await self._client.ttl(key)
        except Exception as e:
            logging.error(f"Error getting TTL from Redis: {e}")
            return -2

# Initialize Redis cache
redis_cache = RedisCache()

async def init_redis():
    """
    Initialize Redis connection when application starts.
    
    This function is called during application startup to
    establish the Redis connection.
    """
    await redis_cache.connect()

async def get_redis():
    """
    FastAPI dependency for Redis cache injection.
    
    Provides the Redis cache handler to API endpoints.
    
    Returns:
        RedisCache: The Redis cache handler
        
    Example:
        ```
        @router.get("/cached-data")
        async def get_cached_data(cache = Depends(get_redis)):
            # Use cache here
            data = await cache.get("my_key")
            ...
        ```
    """
    return redis_cache 