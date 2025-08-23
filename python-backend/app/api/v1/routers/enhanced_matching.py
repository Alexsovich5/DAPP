"""
Enhanced Matching Router - Advanced Soul Matching System
Router for comprehensive match quality analysis endpoints
"""

from app.api.v1.endpoints.enhanced_matching import router as enhanced_matching_router
from fastapi import APIRouter

# Create the router
router = APIRouter()

# Include the enhanced matching endpoints
router.include_router(
    enhanced_matching_router, prefix="/enhanced-matching", tags=["enhanced-matching"]
)
