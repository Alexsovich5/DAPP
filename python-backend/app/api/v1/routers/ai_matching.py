"""
AI Matching API Router - Phase 5 Revolutionary AI-Powered Matching
Advanced machine learning endpoints for soul-based compatibility and personalization
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.ai_models import UserProfile, CompatibilityPrediction, PersonalizedRecommendation
from app.services.ai_matching_service import ai_matching_service, MatchRecommendation

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ai_matching"])


# Pydantic models for request/response

class PersonalityInsightResponse(BaseModel):
    trait_name: str
    score: float
    confidence: float
    description: str
    percentile: Optional[float] = None
    improvement_suggestions: List[str] = []


class AIProfileResponse(BaseModel):
    user_id: int
    personality_summary: Dict[str, Any]
    ai_confidence_level: float
    profile_completeness_score: float
    last_updated: str
    insights: List[PersonalityInsightResponse]


class CompatibilityBreakdownResponse(BaseModel):
    overall_score: float
    confidence: float
    strengths: List[str]
    potential_challenges: List[str]
    conversation_starters: List[str]
    breakdown: Dict[str, float]
    predictions: Dict[str, float]


class MatchRecommendationResponse(BaseModel):
    user_id: int
    compatibility_score: float
    confidence_level: float
    match_reasons: List[str]
    conversation_starters: List[str]
    predicted_success_rate: float
    recommendation_strength: str
    user_profile: Dict[str, Any]


# AI Profile Management

@router.get("/profile/generate", response_model=AIProfileResponse)
async def generate_ai_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive AI profile with personality analysis and embeddings
    """
    try:
        profile = await ai_matching_service.generate_user_profile_embeddings(
            current_user.id, db
        )
        
        # Generate personality insights
        personality_summary = profile.get_personality_summary()
        
        insights = []
        # Big Five insights
        big_five_descriptions = {
            "openness": "Your openness to new experiences and creative thinking",
            "conscientiousness": "Your level of organization and goal-directed behavior", 
            "extraversion": "Your tendency toward social interaction and energy",
            "agreeableness": "Your cooperative and trusting nature",
            "neuroticism": "Your emotional stability and stress resilience"
        }
        
        for trait, description in big_five_descriptions.items():
            score = getattr(profile, f"{trait}_score", 0.5)
            if score is not None:
                insight = PersonalityInsightResponse(
                    trait_name=trait.title(),
                    score=score,
                    confidence=profile.ai_confidence_level,
                    description=description,
                    percentile=score * 100,  # Convert to percentile
                    improvement_suggestions=_get_trait_suggestions(trait, score)
                )
                insights.append(insight)
        
        return AIProfileResponse(
            user_id=current_user.id,
            personality_summary=personality_summary,
            ai_confidence_level=profile.ai_confidence_level,
            profile_completeness_score=profile.profile_completeness_score,
            last_updated=profile.last_updated_by_ai.isoformat() if profile.last_updated_by_ai else datetime.utcnow().isoformat(),
            insights=insights
        )
        
    except Exception as e:
        logger.error(f"Error generating AI profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI profile: {str(e)}"
        )


@router.get("/recommendations", response_model=List[MatchRecommendationResponse])
async def get_ai_match_recommendations(
    limit: int = Query(default=10, ge=1, le=25),
    refresh: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered personalized match recommendations
    """
    try:
        # Generate fresh recommendations
        recommendations = await ai_matching_service.generate_personalized_recommendations(
            current_user.id, limit, db
        )
        
        # Format responses with user profile data
        formatted_recommendations = []
        for rec in recommendations:
            # Get recommended user's basic info
            recommended_user = db.query(User).filter(
                User.id == rec.recommended_user_id
            ).first()
            
            if recommended_user:
                user_profile_data = {
                    "id": recommended_user.id,
                    "first_name": recommended_user.first_name,
                    "last_name": recommended_user.last_name,
                    "age": _calculate_age(recommended_user.date_of_birth) if recommended_user.date_of_birth else None,
                    "bio": recommended_user.bio,
                    "interests": recommended_user.interests or [],
                    "location": recommended_user.location
                }
                
                formatted_rec = MatchRecommendationResponse(
                    user_id=rec.recommended_user_id,
                    compatibility_score=rec.compatibility_score,
                    confidence_level=rec.confidence_level,
                    match_reasons=rec.match_reasons,
                    conversation_starters=rec.conversation_starters,
                    predicted_success_rate=rec.predicted_success_rate,
                    recommendation_strength=rec.recommendation_strength,
                    user_profile=user_profile_data
                )
                
                formatted_recommendations.append(formatted_rec)
        
        return formatted_recommendations
        
    except Exception as e:
        logger.error(f"Error getting AI recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@router.get("/compatibility/{user_id}", response_model=CompatibilityBreakdownResponse)
async def get_compatibility_analysis(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed AI compatibility analysis with another user
    """
    try:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot calculate compatibility with yourself"
            )
        
        # Check if target user exists
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Calculate compatibility
        compatibility = await ai_matching_service.calculate_ai_compatibility(
            current_user.id, user_id, db
        )
        
        # Format response
        insights = compatibility.get_compatibility_insights()
        
        return CompatibilityBreakdownResponse(
            overall_score=insights["overall_score"],
            confidence=insights["confidence"],
            strengths=insights["strengths"],
            potential_challenges=insights["potential_challenges"],
            conversation_starters=insights["conversation_starters"],
            breakdown=insights["breakdown"],
            predictions=insights["predictions"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compatibility analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze compatibility"
        )


@router.get("/insights/personality")
async def get_personality_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed personality insights and recommendations
    """
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI profile not found. Please generate your profile first."
            )
        
        # Get behavioral analysis
        behavior_analysis = await ai_matching_service.analyze_user_behavior(
            current_user.id, db=db
        )
        
        return {
            "success": True,
            "personality": profile.get_personality_summary(),
            "behavior_analysis": {
                "patterns": behavior_analysis.patterns,
                "engagement_score": behavior_analysis.engagement_score,
                "communication_style": behavior_analysis.communication_style,
                "preferences": behavior_analysis.preferences,
                "recommendations": behavior_analysis.recommendations,
                "analysis_date": datetime.utcnow().isoformat(),
                "confidence": profile.ai_confidence_level
            },
            "profile_stats": {
                "ai_confidence": profile.ai_confidence_level,
                "completeness": profile.profile_completeness_score,
                "last_updated": profile.last_updated_by_ai.isoformat() if profile.last_updated_by_ai else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting personality insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personality insights"
        )


# Helper functions

def _get_trait_suggestions(trait: str, score: float) -> List[str]:
    """Get improvement suggestions based on personality trait scores"""
    suggestions = {
        "openness": {
            "low": ["Try exploring new hobbies", "Read books from different genres", "Visit museums or art galleries"],
            "high": ["Channel creativity into projects", "Share your ideas with others", "Embrace structured approaches sometimes"]
        },
        "conscientiousness": {
            "low": ["Use planning apps or calendars", "Set small, achievable goals", "Create daily routines"],
            "high": ["Allow for spontaneity", "Practice flexibility", "Don't over-plan everything"]
        },
        "extraversion": {
            "low": ["Practice small talk", "Join group activities", "Schedule social time"],
            "high": ["Make time for solitude", "Practice active listening", "Appreciate quiet moments"]
        },
        "agreeableness": {
            "low": ["Practice empathy exercises", "Consider others' perspectives", "Work on compromise skills"],
            "high": ["Practice assertiveness", "Set healthy boundaries", "Voice your own needs"]
        },
        "neuroticism": {
            "low": ["Continue stress management", "Help others with anxiety", "Maintain emotional balance"],
            "high": ["Try meditation or mindfulness", "Practice stress reduction techniques", "Consider professional support"]
        }
    }
    
    level = "low" if score < 0.4 else "high"
    return suggestions.get(trait, {}).get(level, ["Continue developing this trait"])


def _calculate_age(date_of_birth: str) -> Optional[int]:
    """Calculate age from date of birth string"""
    try:
        if not date_of_birth:
            return None
        
        # Parse date string (assuming YYYY-MM-DD format)
        birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        today = datetime.now().date()
        
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        return age
        
    except (ValueError, TypeError):
        return None