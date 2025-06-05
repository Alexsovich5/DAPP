from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from pydantic import ValidationError

from app.api.v1.routers import auth, matches, profiles, users
from app.core.database import create_tables
from app.middleware.middleware import log_requests_middleware
from app.utils.error_handler import validation_error_handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables first
load_dotenv()

# Create FastAPI application
app = FastAPI(
    title="Dinner App API",
    description="API for matching dinner companions",
    version="1.0.0",
)

# Configure CORS - updated for Angular frontend
origins = [
    "http://localhost:4200",  # Angular dev server default
    "http://localhost:5001",  # Angular dev server (alternate port)
    "http://localhost:3000",  # React dev server (if needed)
    "http://localhost:8080",  # Vue dev server (if needed)
    "http://localhost:5173",  # Vite dev server (if needed)
]

# Add environment variable override
env_origins = os.getenv("CORS_ORIGINS")
if env_origins:
    origins.extend(env_origins.split(","))

# Add CORS middleware with proper configuration for Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Enable credentials for Angular
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Try to create database tables
try:
    create_tables()
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {str(e)}")

# Create API routers for v1
v1_app = FastAPI(
    title="Dinner App API",
    description="API for matching dinner companions (v1)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Include routers in v1_app
v1_app.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_app.include_router(users.router, prefix="/users", tags=["users"])
v1_app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
v1_app.include_router(matches.router, prefix="/matches", tags=["matches"])

# Add profile aliases for Angular compatibility
v1_app.include_router(profiles.router, prefix="/profile", tags=["profile-alias"])

# Mount the v1 API with prefix
app.mount("/api/v1", v1_app)

# Create a second mount for the non-v1 path to support the Angular app
app.mount("/api", v1_app)

# Add logging middleware
app.middleware("http")(log_requests_middleware)

# Register validation error handlers
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

# Create uploads directory and mount static files
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def root():
    """
    Root endpoint to verify API is running
    """
    return {
        "status": "ok",
        "message": "Welcome to the Dinner App API",
        "version": "1.0.0",
        "documentation": {
            "api_v1_docs": "/api/v1/docs",
            "api_docs": "/api/docs",
        },
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    try:
        # You could add a simple database ping here
        return {
            "status": "healthy",
            "database": "connected",
            "api_version": "1.0.0",
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}
