import logging

import uvicorn
from app.core.database import create_tables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        # Create all database tables first
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully")

        # Skip database initialization during startup to avoid hanging
        # Test data can be created via API endpoints instead
        logger.info("Starting FastAPI server...")

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,  # Using port 8000 to avoid conflict with macOS AirPlay Receiver
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
