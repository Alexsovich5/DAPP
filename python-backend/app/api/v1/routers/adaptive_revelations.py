"""
Phase 6: Adaptive Revelation Prompts API
API endpoints for intelligent, context-aware revelation prompt generation
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Dict, Any, Optional
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.services.adaptive_revelation_service import adaptive_revelation_engine
from app.services.personalization_service import personalization_engine
from app.schemas.adaptive_revelation_schemas import (
    AdaptiveRevelationRequest, AdaptiveRevelationResponse,
    RevelationFeedbackRequest, RevelationAnalyticsResponse,
    RevelationTimingResponse, RevelationThemeResponse
)

router = APIRouter(prefix="/adaptive-revelations", tags=["adaptive-revelations"])
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=List[AdaptiveRevelationResponse])
async def generate_adaptive_revelation_prompts(
    request: AdaptiveRevelationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate adaptive revelation prompts based on user behavior and connection context
    """
    try:
        # Validate connection exists and user has access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == request.connection_id,
            or_(
                SoulConnection.user1_id == current_user.id,
                SoulConnection.user2_id == current_user.id
            )
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied"
            )
        
        # Validate revelation day
        if request.revelation_day < 1 or request.revelation_day > 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Revelation day must be between 1 and 7"
            )
        
        # Generate adaptive prompts
        prompts = await adaptive_revelation_engine.generate_adaptive_revelation_prompts(
            user_id=current_user.id,
            connection_id=request.connection_id,
            revelation_day=request.revelation_day,
            count=request.count,
            db=db
        )
        
        return [AdaptiveRevelationResponse(**prompt) for prompt in prompts]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating adaptive revelation prompts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate adaptive revelation prompts"
        )

@router.get("/themes/{revelation_day}", response_model=List[RevelationThemeResponse])
async def get_available_revelation_themes(
    revelation_day: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available revelation themes for a specific day
    """
    try:
        if revelation_day < 1 or revelation_day > 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Revelation day must be between 1 and 7"
            )
        
        # Get themes from the adaptive engine
        themes = adaptive_revelation_engine.revelation_themes.get(revelation_day, {})
        
        theme_responses = []
        for theme_name, theme_data in themes.items():
            theme_responses.append(RevelationThemeResponse(
                name=theme_name,
                description=theme_data.get("description", f"Theme focused on {theme_name.replace('_', ' ')}"),
                communication_style=theme_data.get("communication_style", "balanced"),
                requires_high_compatibility=theme_data.get("requires_high_compatibility", False),
                emotional_intensity=adaptive_revelation_engine.depth_progression[revelation_day]["emotional_intensity"],
                sample_templates=[
                    template.get("template", "")
                    for template in theme_data.get("templates", [])[:2]
                ]
            ))
        
        return theme_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving revelation themes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve revelation themes"
        )

@router.get("/timing-recommendations/{connection_id}", response_model=RevelationTimingResponse)
async def get_revelation_timing_recommendations(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized timing recommendations for revelations
    """
    try:
        # Validate connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            or_(
                SoulConnection.user1_id == current_user.id,
                SoulConnection.user2_id == current_user.id
            )
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied"
            )
        
        # Build context for timing analysis
        context = await adaptive_revelation_engine._build_revelation_context(
            current_user, connection, 1, db  # Day 1 as default for timing analysis
        )
        
        timing_recommendation = adaptive_revelation_engine._get_timing_recommendation(context)
        
        return RevelationTimingResponse(
            connection_id=connection_id,
            recommended_hours=timing_recommendation["recommended_hours"],
            optimal_day_time=timing_recommendation["optimal_day_time"],
            reasoning=timing_recommendation["reasoning"],
            urgency=timing_recommendation["urgency"],
            next_optimal_time=None  # Could calculate next optimal time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timing recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get timing recommendations"
        )

@router.post("/feedback")
async def submit_revelation_feedback(
    request: RevelationFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on adaptive revelation prompts for optimization
    """
    try:
        # Validate the revelation exists and belongs to user
        revelation = db.query(DailyRevelation).filter(
            DailyRevelation.id == request.revelation_id,
            DailyRevelation.user_id == current_user.id
        ).first()
        
        if not revelation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revelation not found or access denied"
            )
        
        # Record feedback using personalization engine
        success = await personalization_engine.record_content_feedback(
            user_id=current_user.id,
            content_id=request.content_id,
            feedback_data={
                "type": "revelation_feedback",
                "helpful_score": request.helpful_score,
                "engagement_score": request.engagement_score,
                "emotional_resonance": request.emotional_resonance,
                "timing_appropriateness": request.timing_appropriateness,
                "comments": request.comments,
                "revelation_id": request.revelation_id
            },
            db=db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record feedback"
            )
        
        return {
            "success": True,
            "message": "Feedback recorded successfully. This will help improve future revelation prompts."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording revelation feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback"
        )

@router.get("/analytics/{connection_id}", response_model=RevelationAnalyticsResponse)
async def get_revelation_analytics(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get revelation analytics and insights for a connection
    """
    try:
        # Validate connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            or_(
                SoulConnection.user1_id == current_user.id,
                SoulConnection.user2_id == current_user.id
            )
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied"
            )
        
        # Get user's revelations for this connection
        revelations = db.query(DailyRevelation).filter(
            DailyRevelation.user_id == current_user.id,
            DailyRevelation.connection_id == connection_id
        ).order_by(DailyRevelation.day_number).all()
        
        # Analyze revelation patterns
        revelation_patterns = await adaptive_revelation_engine._analyze_user_revelation_patterns(
            current_user.id, db
        )
        
        # Calculate analytics
        completed_days = len(revelations)
        total_word_count = sum(len((rev.content or "").split()) for rev in revelations)
        avg_word_count = total_word_count / max(completed_days, 1)
        
        theme_distribution = {}
        for rev in revelations:
            theme = rev.revelation_type or "general"
            theme_distribution[theme] = theme_distribution.get(theme, 0) + 1
        
        return RevelationAnalyticsResponse(
            connection_id=connection_id,
            completed_revelation_days=completed_days,
            total_revelations_shared=len(revelations),
            average_words_per_revelation=round(avg_word_count, 1),
            theme_distribution=theme_distribution,
            engagement_trend=revelation_patterns.get("engagement_trend", "developing"),
            most_successful_themes=revelation_patterns.get("preferred_types", [])[:3],
            overall_depth_score=sum(rev.day_number for rev in revelations) / max(completed_days, 1),
            personalization_effectiveness=0.8,  # Would calculate from feedback
            next_recommended_theme=None  # Would calculate based on patterns
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving revelation analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve revelation analytics"
        )

@router.get("/progress/{connection_id}")
async def get_revelation_progress(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get revelation progress for a connection
    """
    try:
        # Validate connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            or_(
                SoulConnection.user1_id == current_user.id,
                SoulConnection.user2_id == current_user.id
            )
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied"
            )
        
        # Get revelations for both users
        user_revelations = db.query(DailyRevelation).filter(
            DailyRevelation.user_id == current_user.id,
            DailyRevelation.connection_id == connection_id
        ).all()
        
        partner_id = connection.user2_id if connection.user1_id == current_user.id else connection.user1_id
        partner_revelations = db.query(DailyRevelation).filter(
            DailyRevelation.user_id == partner_id,
            DailyRevelation.connection_id == connection_id
        ).all()
        
        # Calculate progress
        user_completed_days = set(rev.day_number for rev in user_revelations)
        partner_completed_days = set(rev.day_number for rev in partner_revelations)
        
        progress = {
            "connection_id": connection_id,
            "current_revelation_day": max(
                max(user_completed_days, default=0),
                max(partner_completed_days, default=0)
            ) + 1,
            "user_progress": {
                "completed_days": sorted(list(user_completed_days)),
                "total_completed": len(user_completed_days),
                "next_day": max(user_completed_days, default=0) + 1 if len(user_completed_days) < 7 else None
            },
            "partner_progress": {
                "completed_days": sorted(list(partner_completed_days)),
                "total_completed": len(partner_completed_days),
                "next_day": max(partner_completed_days, default=0) + 1 if len(partner_completed_days) < 7 else None
            },
            "mutual_completion": {
                "completed_together": sorted(list(user_completed_days.intersection(partner_completed_days))),
                "waiting_for_partner": sorted(list(user_completed_days - partner_completed_days)),
                "waiting_for_user": sorted(list(partner_completed_days - user_completed_days))
            },
            "can_proceed_to_photo_reveal": len(user_completed_days) >= 7 and len(partner_completed_days) >= 7,
            "days_until_photo_reveal": max(0, 7 - min(len(user_completed_days), len(partner_completed_days)))
        }
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving revelation progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve revelation progress"
        )