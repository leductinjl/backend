"""
Main application module.

This is the entry point for the FastAPI application. It initializes the 
application, sets up middleware, connects to databases, and registers API routes
by calling specialized modules from the core package.
"""

from app.core.logging import setup_logging
from app.core.app_setup import create_application
from app.core.db import connect_to_db
from app.core.routes import setup_routes
import uvicorn
from app.config import settings
# Configure logging
setup_logging()

# Create the FastAPI application
app = create_application()

# Initialize database connections on application startup
@app.on_event("startup")
async def startup_db_client():
    """
    Initialize database connections when the application starts.
    
    This function is called when the FastAPI application starts up.
    """
    await connect_to_db()

# Set up all routes
setup_routes(app)

if __name__ == "__main__":
    # Run the application directly when this file is executed
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True) 