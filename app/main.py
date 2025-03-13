"""
Main application module.

This is the entry point for the FastAPI application. It initializes the 
application, sets up middleware, connects to databases, and registers API routes.

The module creates and configures the FastAPI application instance with:
- Middleware (CORS, logging, admin authentication)
- Database connections (PostgreSQL, Neo4j, Redis)
- API routers for different domains
- Documentation endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.middleware import register_middleware
from app.infrastructure.database.connection import init_db
from app.infrastructure.ontology.neo4j_connection import init_neo4j
from app.infrastructure.cache.redis_connection import init_redis
import logging
import os

# Ensure logs directory exists
os.makedirs(os.path.dirname(settings.LOG_FILE_PATH), exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for candidate information retrieval system",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import Redis cache for middleware
from app.infrastructure.cache.redis_connection import redis_cache

# Register all middleware
register_middleware(app, redis_cache)

# Initialize database connections on application startup
@app.on_event("startup")
async def startup_db_client():
    """
    Initialize database connections when the application starts.
    
    This function is called when the FastAPI application starts up,
    connecting to PostgreSQL, Neo4j, and Redis.
    """
    await init_db()  # Initialize PostgreSQL
    await init_neo4j()  # Initialize Neo4j
    await init_redis()  # Initialize Redis
    
    logging.info("Connected to databases and cache")


# Import API router - currently only health router is implemented
from app.api.controllers import health_router

# Register API router
app.include_router(
    health_router.router,
    prefix=f"{settings.API_PREFIX}/health",
    tags=["Health"]
)

@app.get("/")
async def root():
    """Root endpoint that provides basic API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_PREFIX}/docs"
    }

if __name__ == "__main__":
    # Run the application directly when this file is executed
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 