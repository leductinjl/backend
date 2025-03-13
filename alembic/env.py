"""
Alembic environment configuration file.

This module configures the Alembic environment for database migrations.
It connects to the database, loads the SQLAlchemy models, and provides
functions to run migrations in both online and offline modes.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers based on the config file.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import the SQLAlchemy metadata and models for 'autogenerate' support
from app.infrastructure.database.connection import Base
from app.domain.models import *

# Target metadata is the SQLAlchemy metadata object for schema generation
target_metadata = Base.metadata

# Read database URL from environment variables if available
from app.config import settings
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection.
    
    This function configures the migration context with the provided connection
    and runs the migrations within a transaction.
    
    Args:
        connection: An active database connection
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations asynchronously.
    
    This function creates an async engine, establishes a connection,
    and runs the migrations. It handles proper disposal of resources afterward.
    """
    # Create an async engine based on the config
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Run migrations within a connection
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    # Dispose of the engine
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    This function is the entry point for running migrations in online mode,
    which uses the asyncio event loop to run async migrations.
    """
    asyncio.run(run_async_migrations())


# Determine whether to run migrations in online or offline mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 