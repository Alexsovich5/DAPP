from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from pydantic import ValidationError

from app.api.v1.routers import (
    auth,
    matches,
    profiles,
    users,
    soul_connections,
    revelations,
    onboarding,
    photo_reveal,
    messages,
    ai_matching,
    personalization,
    adaptive_revelations,
    ui_personalization,
    analytics_api,
    notifications,
    monitoring,
    websocket,
)
from app.api.v1.routers import chat as chat_router
from app.api.v1.routers import safety as safety_router
# from app.api.v1.routers import analytics as analytics_router  # Temporarily disabled due to missing clickhouse
from app.core.database import create_tables
from app.middleware.middleware import log_requests_middleware
from app.middleware.security_headers import security_headers_middleware, get_secure_cors_config
from app.utils.error_handler import validation_error_handler
from app.services.realtime import manager

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

# Security Headers Middleware - Apply first for all responses
app.middleware("http")(security_headers_middleware)

# Secure CORS Configuration - Environment-aware and production-ready
cors_config = get_secure_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# Try to create database tables
try:
    create_tables()
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Dinner First API is running"}


@app.get("/ready")
async def readiness_check():
    """Readiness probe for Kubernetes"""
    return {"status": "ready", "message": "Service is ready to accept traffic"}


@app.get("/alive")
async def liveness_check():  
    """Liveness probe for Kubernetes"""
    return {"status": "alive", "message": "Service is alive"}

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

# Soul Before Skin routers
v1_app.include_router(
    soul_connections.router,
    prefix="/soul-connections",
    tags=["soul-connections"],
)
v1_app.include_router(
    revelations.router,
    prefix="/revelations",
    tags=["revelations"],
)
v1_app.include_router(
    onboarding.router,
    prefix="/onboarding",
    tags=["onboarding"],
)

# Phase 4: Photo Reveal System
v1_app.include_router(
    photo_reveal.router,
    prefix="/photo-reveal",
    tags=["photo-reveal"],
)

# Phase 4: Real-time Messaging
v1_app.include_router(
    messages.router,
    prefix="/messages",
    tags=["messages"],
)

# Phase 5: AI-Enhanced Matching
v1_app.include_router(
    ai_matching.router,
    prefix="/ai-matching",
    tags=["ai-matching"],
)

# Phase 6: Advanced Personalization & Content Intelligence
v1_app.include_router(
    personalization.router,
    prefix="/personalization",
    tags=["personalization"],
)

# Phase 6: Adaptive Revelation Prompts
v1_app.include_router(
    adaptive_revelations.router,
    prefix="/adaptive-revelations",
    tags=["adaptive-revelations"],
)

# Phase 6: UI Personalization System
v1_app.include_router(
    ui_personalization.router,
    prefix="/ui-personalization",
    tags=["ui-personalization"],
)

# Phase 7: Hybrid Advanced Features - Reserved for future implementation
# enhanced_communication.router - Not yet implemented
# social_proof.router - Not yet implemented  
# advanced_ai_matching.router - Not yet implemented

# Real-time Chat and Safety
v1_app.include_router(chat_router.router, tags=["chat"])
v1_app.include_router(safety_router.router)
# v1_app.include_router(analytics_router.router)  # Temporarily disabled

# Phase 7: Additional System Features  
v1_app.include_router(
    analytics_api.router,
    prefix="/analytics",
    tags=["analytics-api"],
)
v1_app.include_router(
    notifications.router,
    prefix="/notifications", 
    tags=["notifications"],
)
v1_app.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"],
)
v1_app.include_router(
    websocket.router,
    prefix="/websocket",
    tags=["websocket"],
)

# Add profile aliases for Angular compatibility
v1_app.include_router(
    profiles.router, prefix="/profile", tags=["profile-alias"]
)

# Mount the v1 API with prefix
app.mount("/api/v1", v1_app)

# Create a second mount for the non-v1 path to support the Angular app
app.mount("/api", v1_app)

# Add logging middleware
app.middleware("http")(log_requests_middleware)

# Register validation error handlers
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

# Create uploads directory (but do NOT mount as static files for security)
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
# File access will be handled through authenticated endpoints in users router


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


@app.websocket("/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """Top-level WebSocket endpoint to match frontend `ws://.../chat`."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_to_all_except(
                {"type": "event", "data": data}, except_ws=websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
