"""
PostgreSQL database connection module.

This module provides the SQLAlchemy connection setup for PostgreSQL, including:
- Database connection engine configuration
- Session factory for handling database transactions
- Base class for SQLAlchemy ORM models
- Initialization function for database setup
- Dependency function for FastAPI endpoints
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text, inspect
from app.config import settings
import logging
import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Configure database connection URL for asyncpg
DATABASE_URL = str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")

# Create async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL statements when in debug mode
    future=True,  # Use SQLAlchemy 2.0 features
    pool_pre_ping=True,  # Verify connections before using them
)

# Create async session factory
async_session = sessionmaker(
    engine, 
    expire_on_commit=False,  # Don't expire objects after commit
    class_=AsyncSession  # Use async session class
)

# Create base model class for SQLAlchemy models
Base = declarative_base()

async def check_database_exists():
    """
    Check if the target database exists, and create it if it doesn't.
    
    Returns:
        bool: True if database exists or was created, False if creation failed
    """
    db_name = settings.POSTGRES_DB
    # Connect to postgres database to be able to create a new database if needed
    temp_url = str(settings.DATABASE_URL).replace(f"/{db_name}", "/postgres")
    temp_url = temp_url.replace("postgresql://", "postgresql+asyncpg://")
    
    temp_engine = create_async_engine(
        temp_url,
        isolation_level="AUTOCOMMIT"
    )
    
    try:
        # Check if database exists
        async with temp_engine.connect() as conn:
            result = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            exists = result.scalar() == 1
            
            if not exists:
                logging.info(f"Database '{db_name}' does not exist. Creating...")
                # Create database
                await conn.execute(text(f"CREATE DATABASE {db_name}"))
                logging.info(f"Database '{db_name}' created successfully.")
                return True
            return True
    except Exception as e:
        logging.error(f"Failed to check/create database: {e}")
        return False
    finally:
        await temp_engine.dispose()

async def check_if_tables_exist():
    """
    Check if any tables exist in the database.
    
    Returns:
        bool: True if tables exist, False otherwise
    """
    try:
        async with engine.connect() as conn:
            # Get all table names from our models
            model_tables = set(Base.metadata.tables.keys())
            
            # Check if any tables exist in the database using inspector
            # Create inspector within the run_sync lambda for synchronous execution
            existing_tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
            
            # Check if all model tables exist
            return all(table in existing_tables for table in model_tables)
    except Exception as e:
        logging.error(f"Error checking for existing tables: {e}")
        return False

def compare_models_with_db():
    """
    Compare model metadata with database to check for differences.
    
    Returns:
        bool: True if changes are detected, False otherwise
    """
    try:
        # Get project root path
        project_root = Path(__file__).parents[3]  # Go up 3 levels from this file
        
        # Create a temporary autogenerate script to detect changes
        temp_migration_name = f"temp_check_{int(os.path.getctime(__file__))}"
        
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", temp_migration_name],
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logging.error(f"Failed to create temporary migration: {result.stderr}")
            return False
        
        # Check generated migration files in versions directory
        versions_dir = os.path.join(project_root, "alembic", "versions")
        
        # Find the temp migration file
        temp_migration_file = None
        for filename in os.listdir(versions_dir):
            if temp_migration_name in filename and filename.endswith('.py'):
                temp_migration_file = os.path.join(versions_dir, filename)
                break
        
        if not temp_migration_file:
            logging.error("Could not find generated migration file")
            return False
        
        # Read the file content to check if it contains any actual changes
        with open(temp_migration_file, 'r') as f:
            content = f.read()
        
        # Delete the temporary file after checking
        os.remove(temp_migration_file)
        
        # If the migration only contains pass in the upgrade/downgrade functions,
        # it means there are no changes
        return "pass" not in content or "op.create_" in content or "op.drop_" in content or "op.alter_" in content
    except Exception as e:
        logging.error(f"Error comparing models with database: {e}")
        return False

def create_alembic_migration():
    """
    Create a new Alembic migration based on model changes.
    
    Returns:
        bool: True if migration was created successfully, False otherwise
    """
    try:
        # Get project root path
        project_root = Path(__file__).parents[3]  # Go up 3 levels from this file
        
        # Create migration name with timestamp
        migration_name = f"auto_migration_{int(os.path.getctime(__file__))}"
        
        # Run alembic revision command
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", migration_name],
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info(f"Alembic migration created: {migration_name}")
            return True
        else:
            logging.error(f"Failed to create Alembic migration: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error creating Alembic migration: {e}")
        return False

def run_alembic_migrations():
    """
    Run all pending Alembic migrations.
    
    Returns:
        bool: True if migrations were applied successfully, False otherwise
    """
    try:
        # Get project root path
        project_root = Path(__file__).parents[3]  # Go up 3 levels from this file
        
        # Run alembic upgrade command
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Alembic migrations applied successfully")
            return True
        else:
            logging.error(f"Failed to apply Alembic migrations: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running Alembic migrations: {e}")
        return False

async def init_db():
    """
    Initialize PostgreSQL database connection.
    
    This function:
    1. Checks if the database exists and creates it if not
    2. Checks if tables exist and creates them if not
    3. If tables exist, checks for model changes and creates migrations
    4. Runs any pending migrations
    
    This function is called during application startup.
    
    Raises:
        Exception: If database connection or schema creation fails
    """
    try:
        # First check/create database
        db_exists = await check_database_exists()
        if not db_exists:
            raise Exception("Failed to create database")
        
        # Check if tables exist
        tables_exist = await check_if_tables_exist()
        
        if not tables_exist:
            # Create tables directly from models if no tables exist yet
            async with engine.begin() as conn:
                logging.info("Creating database tables from models...")
                await conn.run_sync(Base.metadata.create_all)
            logging.info("Database tables created successfully")
        else:
            # Check for model changes and create migrations if needed
            has_changes = compare_models_with_db()
            
            if has_changes:
                logging.info("Model changes detected, creating migration...")
                if create_alembic_migration():
                    logging.info("Running migrations...")
                    run_alembic_migrations()
            else:
                logging.info("No model changes detected")
        
        logging.info("PostgreSQL database connection initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database connection: {e}")
        raise

async def get_db():
    """
    FastAPI dependency for database session injection.
    
    Provides a database session to API endpoints and ensures
    proper handling of commits and rollbacks. 
    
    Yields:
        AsyncSession: An async SQLAlchemy session
        
    Example:
        ```
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            # Use db session here
            ...
        ```
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close() 