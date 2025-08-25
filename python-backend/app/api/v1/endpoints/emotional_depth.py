"""
Emotional Depth API Endpoints
Advanced psychological profiling and depth compatibility analysis
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.api.deps import get_current_user, get_db
from app.models.soul_connection import SoulConnection
from app.models.user import User
from app.services.emotional_depth_service import (
    EmotionalDepthLevel,
    EmotionalDepthMetrics,
    emotional_depth_service,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/analyze/{user_id}", response_model=Dict[str, Any])
async def analyze_user_emotional_depth(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze emotional depth for a specific user.
    Requires authentication and authorization.
    """
    try:
        # Check if user exists
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Authorization check - can only analyze own profile or matched users
        if current_user.id != user_id:
            # Check if users are matched/connected
            connection = (
                db.query(SoulConnection)
                .filter(
                    (
                        (SoulConnection.user1_id == current_user.id)
                        & (SoulConnection.user2_id == user_id)
                    )
                    | (
                        (SoulConnection.user1_id == user_id)
                        & (SoulConnection.user2_id == current_user.id)
                    )
                )
                .first()
            )

            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to analyze this user's emotional depth",
                )

        # Perform emotional depth analysis
        depth_metrics = emotional_depth_service.analyze_emotional_depth(target_user, db)

        # Convert to response format
        return {
            "user_id": user_id,
            "emotional_depth": {
                "overall_depth": depth_metrics.overall_depth,
                "depth_level": depth_metrics.depth_level.value,
                "emotional_vocabulary_count": depth_metrics.emotional_vocabulary,
                "vulnerability_score": depth_metrics.vulnerability_score,
                "authenticity_score": depth_metrics.authenticity_score,
                "empathy_indicators": depth_metrics.empathy_indicators,
                "growth_mindset": depth_metrics.growth_mindset,
                "emotional_availability": depth_metrics.emotional_availability,
                "attachment_security": depth_metrics.attachment_security,
                "communication_depth": depth_metrics.communication_depth,
                "confidence": depth_metrics.confidence,
                "text_quality": depth_metrics.text_quality,
                "response_richness": depth_metrics.response_richness,
            },
            "insights": {
                "vulnerability_types": [
                    vt.value for vt in depth_metrics.vulnerability_types
                ],
                "depth_indicators": depth_metrics.depth_indicators,
                "maturity_signals": depth_metrics.maturity_signals,
                "authenticity_markers": depth_metrics.authenticity_markers,
            },
            "analysis_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "algorithm_version": "1.0",
                "confidence_level": depth_metrics.confidence,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing emotional depth for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing emotional depth",
        )


@router.get("/compatibility/{user1_id}/{user2_id}", response_model=Dict[str, Any])
async def analyze_depth_compatibility(
    user1_id: int,
    user2_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze emotional depth compatibility between two users.
    Requires authentication and that current user is one of the two users.
    """
    try:
        # Validate that current user is one of the two users
        if current_user.id not in [user1_id, user2_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to analyze compatibility between these users",
            )

        # Get both users
        user1 = db.query(User).filter(User.id == user1_id).first()
        user2 = db.query(User).filter(User.id == user2_id).first()

        if not user1 or not user2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both users not found",
            )

        # Calculate depth compatibility
        compatibility = emotional_depth_service.calculate_depth_compatibility(
            user1, user2, db
        )

        # Convert to response format
        return {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "depth_compatibility": {
                "overall_compatibility": compatibility.compatibility_score,
                "depth_harmony": compatibility.depth_harmony,
                "vulnerability_match": compatibility.vulnerability_match,
                "growth_alignment": compatibility.growth_alignment,
            },
            "individual_depths": {
                "user1": {
                    "overall_depth": compatibility.user1_depth.overall_depth,
                    "depth_level": compatibility.user1_depth.depth_level.value,
                    "vulnerability_score": compatibility.user1_depth.vulnerability_score,
                    "authenticity_score": compatibility.user1_depth.authenticity_score,
                    "growth_mindset": compatibility.user1_depth.growth_mindset,
                },
                "user2": {
                    "overall_depth": compatibility.user2_depth.overall_depth,
                    "depth_level": compatibility.user2_depth.depth_level.value,
                    "vulnerability_score": compatibility.user2_depth.vulnerability_score,
                    "authenticity_score": compatibility.user2_depth.authenticity_score,
                    "growth_mindset": compatibility.user2_depth.growth_mindset,
                },
            },
            "relationship_insights": {
                "connection_potential": compatibility.connection_potential,
                "recommended_approach": compatibility.recommended_approach,
                "depth_growth_timeline": compatibility.depth_growth_timeline,
            },
            "analysis_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "algorithm_version": "1.0",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing depth compatibility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing emotional depth compatibility",
        )


@router.get("/summary/me", response_model=Dict[str, Any])
async def get_my_emotional_depth_summary(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get a summary of the current user's emotional depth profile.
    """
    try:
        # Analyze current user's emotional depth
        depth_metrics = emotional_depth_service.analyze_emotional_depth(
            current_user, db
        )

        # Generate personalized insights
        insights = _generate_personal_insights(depth_metrics)

        # Generate recommendations
        recommendations = _generate_depth_recommendations(depth_metrics)

        return {
            "emotional_depth_summary": {
                "overall_depth": depth_metrics.overall_depth,
                "depth_level": depth_metrics.depth_level.value,
                "depth_level_description": _get_depth_level_description(
                    depth_metrics.depth_level
                ),
                "key_strengths": depth_metrics.depth_indicators[:3],
                "growth_areas": _identify_growth_areas(depth_metrics),
                "emotional_vocabulary_richness": _classify_vocabulary_richness(
                    depth_metrics.emotional_vocabulary
                ),
                "vulnerability_comfort": _classify_vulnerability_level(
                    depth_metrics.vulnerability_score
                ),
                "authenticity_level": _classify_authenticity_level(
                    depth_metrics.authenticity_score
                ),
            },
            "personal_insights": insights,
            "recommendations": recommendations,
            "profile_completeness": {
                "confidence": depth_metrics.confidence,
                "text_quality": depth_metrics.text_quality,
                "suggestions": _get_profile_improvement_suggestions(depth_metrics),
            },
        }

    except Exception as e:
        logger.error(f"Error getting emotional depth summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving emotional depth summary",
        )


# Helper functions for response formatting


def _generate_personal_insights(depth_metrics: EmotionalDepthMetrics) -> List[str]:
    """Generate personalized insights based on depth analysis"""
    insights = []

    if depth_metrics.vulnerability_score >= 70:
        insights.append(
            "You show remarkable openness and vulnerability in your communication"
        )
    elif depth_metrics.vulnerability_score >= 50:
        insights.append(
            "You demonstrate healthy emotional openness with room for deeper sharing"
        )
    else:
        insights.append(
            "Consider sharing more personal experiences to deepen connections"
        )

    if depth_metrics.growth_mindset >= 70:
        insights.append(
            "Your growth mindset indicates strong potential for relationship development"
        )

    if depth_metrics.empathy_indicators >= 70:
        insights.append(
            "You show strong empathy and consideration for others' perspectives"
        )

    return insights[:3]  # Return top 3 insights


def _generate_depth_recommendations(depth_metrics: EmotionalDepthMetrics) -> List[str]:
    """Generate recommendations for emotional depth development"""
    recommendations = []

    if depth_metrics.emotional_vocabulary < 10:
        recommendations.append(
            "Expand your emotional vocabulary by exploring feeling words and expressions"
        )

    if depth_metrics.vulnerability_score < 50:
        recommendations.append(
            "Practice sharing personal experiences and feelings to deepen connections"
        )

    if depth_metrics.growth_mindset < 60:
        recommendations.append(
            "Focus on self-reflection and personal development activities"
        )

    if not recommendations:
        recommendations.append(
            "Continue developing your emotional intelligence through meaningful conversations"
        )

    return recommendations


def _get_depth_level_description(depth_level: EmotionalDepthLevel) -> str:
    """Get human-readable description of depth level"""
    descriptions = {
        EmotionalDepthLevel.SURFACE: "You're developing your emotional expression and awareness",
        EmotionalDepthLevel.EMERGING: "You show growing emotional intelligence and self-awareness",
        EmotionalDepthLevel.MODERATE: "You demonstrate good emotional depth and understanding",
        EmotionalDepthLevel.DEEP: "You exhibit high emotional sophistication and depth",
        EmotionalDepthLevel.PROFOUND: "You show exceptional emotional depth and wisdom",
    }
    return descriptions.get(depth_level, "Developing emotional awareness")


def _classify_vocabulary_richness(vocab_count: int) -> str:
    """Classify emotional vocabulary richness"""
    if vocab_count >= 15:
        return "Rich and sophisticated"
    elif vocab_count >= 10:
        return "Well-developed"
    elif vocab_count >= 5:
        return "Developing"
    else:
        return "Limited"


def _classify_vulnerability_level(vuln_score: float) -> str:
    """Classify vulnerability comfort level"""
    if vuln_score >= 80:
        return "Very comfortable with emotional openness"
    elif vuln_score >= 60:
        return "Moderately comfortable sharing personal experiences"
    elif vuln_score >= 40:
        return "Developing comfort with vulnerability"
    else:
        return "Prefers to keep things more private"


def _classify_authenticity_level(auth_score: float) -> str:
    """Classify authenticity level"""
    if auth_score >= 80:
        return "Highly authentic and genuine"
    elif auth_score >= 60:
        return "Generally authentic in expression"
    elif auth_score >= 40:
        return "Moderately authentic"
    else:
        return "May benefit from more genuine self-expression"


def _identify_growth_areas(depth_metrics: EmotionalDepthMetrics) -> List[str]:
    """Identify specific growth areas"""
    growth_areas = []

    if depth_metrics.emotional_vocabulary < 8:
        growth_areas.append("Emotional vocabulary expansion")

    if depth_metrics.vulnerability_score < 60:
        growth_areas.append("Comfort with vulnerability")

    if depth_metrics.empathy_indicators < 60:
        growth_areas.append("Empathy and perspective-taking")

    if depth_metrics.growth_mindset < 60:
        growth_areas.append("Growth mindset development")

    return growth_areas[:3]  # Top 3 growth areas


def _get_profile_improvement_suggestions(
    depth_metrics: EmotionalDepthMetrics,
) -> List[str]:
    """Get suggestions for improving profile completeness"""
    suggestions = []

    if depth_metrics.confidence < 60:
        suggestions.append(
            "Share more detailed responses to increase analysis accuracy"
        )

    if depth_metrics.text_quality == "insufficient":
        suggestions.append("Provide richer, more detailed answers to profile questions")

    if depth_metrics.response_richness < 100:
        suggestions.append("Consider adding more personal examples and experiences")

    return suggestions
