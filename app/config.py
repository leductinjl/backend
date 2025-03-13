"""
Configuration module for the application.

This module defines the application settings loaded from environment variables.
It uses Pydantic for validation and provides default values for all settings.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import PostgresDsn, AnyHttpUrl, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if we're running in Docker environment
IS_DOCKER = os.getenv("DOCKER_ENV", "false").lower() == "true"

# Set appropriate host values based on environment
DB_HOST = "postgres" if IS_DOCKER else "localhost"
CACHE_HOST = "redis" if IS_DOCKER else "localhost"
GRAPH_HOST = "neo4j" if IS_DOCKER else "localhost"

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables with validation.
    
    This class defines all configuration settings for the application, including
    database connections, API settings, and other environment-specific values.
    """
    # Application settings
    APP_NAME: str = os.getenv("APP_NAME", "Candidate Information API")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    # Docker environment flag
    DOCKER_ENV: bool = IS_DOCKER
    
    # PostgreSQL settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", DB_HOST)
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "candidate_db")
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """
        Dynamically build the database connection URL if not provided.
        
        Args:
            v: The existing value, if any
            values: The current values dictionary
            
        Returns:
            str: A complete PostgreSQL connection URL
        """
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Neo4j settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", f"bolt://{GRAPH_HOST}:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", CACHE_HOST)
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", "")
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/app.log")
    
    class Config:
        """Pydantic configuration class."""
        case_sensitive = True


# Create settings instance
settings = Settings() 