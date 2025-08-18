"""
Emotional Depth Router - Soul Before Skin Advanced Matching
Router for emotional depth analysis and compatibility endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints.emotional_depth import router as emotional_depth_router

# Create the router
router = APIRouter()

# Include the emotional depth endpoints
router.include_router(
    emotional_depth_router,
    prefix="/emotional-depth",
    tags=["emotional-depth"]
)