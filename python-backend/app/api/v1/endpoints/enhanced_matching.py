"""
Enhanced Matching API Endpoints
Comprehensive match quality assessment with advanced algorithms
"""

import logging
from typing import Any, Dict, List

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.enhanced_match_quality_service import (
    ConnectionPrediction,
    EnhancedMatchQuality,
    MatchQualityTier,
    enhanced_match_quality_service,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
USERS_NOT_FOUND_ERROR = "One or both users not found"



@router.get(
    "/comprehensive-analysis/{user1_id}/{user2_id}",
    response_model=Dict[str, Any],
)
async def get_comprehensive_match_analysis(
    user1_id: int,
    user2_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive match quality analysis between two users.
    Combines soul compatibility, advanced algorithms, and emotional depth analysis.
    """
    try:
        # Validate authorization - current user must be one of the two users
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
                detail=USERS_NOT_FOUND_ERROR,
            )

        # Perform comprehensive match quality assessment
        match_quality = (
            enhanced_match_quality_service.assess_comprehensive_match_quality(
                user1, user2, db
            )
        )

        # Format response
        return {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "comprehensive_analysis": {
                "total_compatibility": match_quality.total_compatibility,
                "match_quality_tier": match_quality.match_quality_tier.value,
                "connection_prediction": match_quality.connection_prediction.value,
                "assessment_confidence": match_quality.assessment_confidence,
                "relationship_timeline": match_quality.relationship_timeline,
            },
            "component_scores": {
                "soul_compatibility": {
                    "total_score": match_quality.soul_compatibility.total_score,
                    "values_score": match_quality.soul_compatibility.values_score,
                    "interests_score": match_quality.soul_compatibility.interests_score,
                    "personality_score": match_quality.soul_compatibility.personality_score,
                    "communication_score": match_quality.soul_compatibility.communication_score,
                    "emotional_resonance": match_quality.soul_compatibility.emotional_resonance,
                },
                "advanced_compatibility": {
                    "total_score": match_quality.advanced_compatibility.total_score,
                    "emotional_intelligence": match_quality.advanced_compatibility.emotional_intelligence_compatibility,
                    "temporal_compatibility": match_quality.advanced_compatibility.temporal_compatibility,
                    "growth_potential": match_quality.advanced_compatibility.growth_potential,
                    "communication_rhythm": match_quality.advanced_compatibility.communication_rhythm_match,
                },
                "emotional_depth": {
                    "compatibility_score": match_quality.emotional_depth_compatibility.compatibility_score,
                    "depth_harmony": match_quality.emotional_depth_compatibility.depth_harmony,
                    "vulnerability_match": match_quality.emotional_depth_compatibility.vulnerability_match,
                    "growth_alignment": match_quality.emotional_depth_compatibility.growth_alignment,
                },
            },
            "relationship_insights": {
                "connection_strengths": match_quality.connection_strengths,
                "growth_opportunities": match_quality.growth_opportunities,
                "potential_challenges": match_quality.potential_challenges,
                "recommended_approach": match_quality.recommended_approach,
            },
            "interaction_guidance": {
                "first_date_suggestion": match_quality.first_date_suggestion,
                "conversation_starters": match_quality.conversation_starters,
            },
            "analysis_metadata": {
                "algorithm_version": match_quality.algorithm_version,
                "analysis_timestamp": match_quality.analysis_timestamp.isoformat(),
                "assessment_confidence": match_quality.assessment_confidence,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive match analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing comprehensive match analysis",
        )


@router.get("/quality-summary/{user1_id}/{user2_id}", response_model=Dict[str, Any])
async def get_match_quality_summary(
    user1_id: int,
    user2_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a summary of match quality between two users.
    Provides key insights without detailed breakdowns.
    """
    try:
        # Validate authorization
        if current_user.id not in [user1_id, user2_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view match quality for these users",
            )

        # Get users
        user1 = db.query(User).filter(User.id == user1_id).first()
        user2 = db.query(User).filter(User.id == user2_id).first()

        if not user1 or not user2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both users not found",
            )

        # Get comprehensive analysis
        match_quality = (
            enhanced_match_quality_service.assess_comprehensive_match_quality(
                user1, user2, db
            )
        )

        # Return summary format
        return {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "match_summary": {
                "compatibility_percentage": match_quality.total_compatibility,
                "quality_tier": match_quality.match_quality_tier.value,
                "quality_description": _get_quality_description(
                    match_quality.match_quality_tier
                ),
                "connection_type": match_quality.connection_prediction.value,
                "connection_description": _get_connection_description(
                    match_quality.connection_prediction
                ),
                "confidence": match_quality.assessment_confidence,
            },
            "key_insights": {
                "top_strengths": match_quality.connection_strengths[:2],
                "primary_opportunity": (
                    match_quality.growth_opportunities[0]
                    if match_quality.growth_opportunities
                    else None
                ),
                "main_challenge": (
                    match_quality.potential_challenges[0]
                    if match_quality.potential_challenges
                    else None
                ),
                "recommended_approach": match_quality.recommended_approach,
            },
            "interaction_preview": {
                "suggested_first_date": match_quality.first_date_suggestion,
                "conversation_starter": (
                    match_quality.conversation_starters[0]
                    if match_quality.conversation_starters
                    else None
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting match quality summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving match quality summary",
        )


@router.get("/connection-guidance/{user1_id}/{user2_id}", response_model=Dict[str, Any])
async def get_connection_guidance(
    user1_id: int,
    user2_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get specific guidance for how to approach and build this connection.
    Focus on actionable insights and recommendations.
    """
    try:
        # Validate authorization
        if current_user.id not in [user1_id, user2_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view connection guidance for these users",
            )

        # Get users
        user1 = db.query(User).filter(User.id == user1_id).first()
        user2 = db.query(User).filter(User.id == user2_id).first()

        if not user1 or not user2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both users not found",
            )

        # Get analysis
        match_quality = (
            enhanced_match_quality_service.assess_comprehensive_match_quality(
                user1, user2, db
            )
        )

        return {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "connection_guidance": {
                "overall_approach": match_quality.recommended_approach,
                "relationship_timeline": match_quality.relationship_timeline,
                "confidence_level": _get_confidence_description(
                    match_quality.assessment_confidence
                ),
            },
            "strengths_to_leverage": match_quality.connection_strengths,
            "growth_opportunities": match_quality.growth_opportunities,
            "challenges_to_navigate": match_quality.potential_challenges,
            "first_interaction": {
                "date_suggestion": match_quality.first_date_suggestion,
                "conversation_starters": match_quality.conversation_starters,
                "interaction_style": _get_interaction_style_recommendation(
                    match_quality
                ),
            },
            "long_term_potential": {
                "connection_prediction": match_quality.connection_prediction.value,
                "development_timeline": match_quality.relationship_timeline,
                "success_factors": _identify_success_factors(match_quality),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection guidance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving connection guidance",
        )


@router.get(
    "/compatibility-breakdown/{user1_id}/{user2_id}",
    response_model=Dict[str, Any],
)
async def get_compatibility_breakdown(
    user1_id: int,
    user2_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed breakdown of compatibility scores across all dimensions.
    """
    try:
        # Validate authorization
        if current_user.id not in [user1_id, user2_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view detailed compatibility breakdown",
            )

        # Get users
        user1 = db.query(User).filter(User.id == user1_id).first()
        user2 = db.query(User).filter(User.id == user2_id).first()

        if not user1 or not user2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both users not found",
            )

        # Get analysis
        match_quality = (
            enhanced_match_quality_service.assess_comprehensive_match_quality(
                user1, user2, db
            )
        )

        return {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "overall_compatibility": match_quality.total_compatibility,
            "detailed_breakdown": {
                "soul_connection": {
                    "total_score": match_quality.soul_compatibility.total_score,
                    "components": {
                        "values_alignment": match_quality.soul_compatibility.values_score,
                        "shared_interests": match_quality.soul_compatibility.interests_score,
                        "personality_compatibility": match_quality.soul_compatibility.personality_score,
                        "communication_style": match_quality.soul_compatibility.communication_score,
                        "demographic_fit": match_quality.soul_compatibility.demographic_score,
                        "emotional_resonance": match_quality.soul_compatibility.emotional_resonance,
                    },
                    "strengths": match_quality.soul_compatibility.strengths,
                    "growth_areas": match_quality.soul_compatibility.growth_areas,
                },
                "advanced_algorithms": {
                    "total_score": match_quality.advanced_compatibility.total_score,
                    "components": {
                        "emotional_intelligence": match_quality.advanced_compatibility.emotional_intelligence_compatibility,
                        "temporal_alignment": match_quality.advanced_compatibility.temporal_compatibility,
                        "communication_rhythm": match_quality.advanced_compatibility.communication_rhythm_match,
                        "growth_potential": match_quality.advanced_compatibility.growth_potential,
                        "conflict_resolution": match_quality.advanced_compatibility.conflict_resolution_compatibility,
                    },
                },
                "emotional_depth": {
                    "total_score": match_quality.emotional_depth_compatibility.compatibility_score,
                    "components": {
                        "depth_harmony": match_quality.emotional_depth_compatibility.depth_harmony,
                        "vulnerability_match": match_quality.emotional_depth_compatibility.vulnerability_match,
                        "growth_alignment": match_quality.emotional_depth_compatibility.growth_alignment,
                    },
                    "individual_depths": {
                        "user1_depth": match_quality.emotional_depth_compatibility.user1_depth.overall_depth,
                        "user2_depth": match_quality.emotional_depth_compatibility.user2_depth.overall_depth,
                    },
                },
            },
            "score_interpretations": {
                "excellent": "90-100: Exceptional compatibility",
                "very_good": "80-89: Strong compatibility",
                "good": "70-79: Good compatibility",
                "moderate": "60-69: Moderate compatibility",
                "limited": "50-59: Limited compatibility",
                "challenging": "0-49: Significant challenges",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compatibility breakdown: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving compatibility breakdown",
        )


# Helper functions for response formatting


def _get_quality_description(tier: MatchQualityTier) -> str:
    """Get human-readable description of match quality tier"""
    descriptions = {
        MatchQualityTier.TRANSCENDENT: "Transcendent soul connection with soulmate potential",
        MatchQualityTier.EXCEPTIONAL: "Exceptional compatibility with outstanding potential",
        MatchQualityTier.HIGH: "High compatibility with strong relationship potential",
        MatchQualityTier.GOOD: "Good compatibility with solid foundation",
        MatchQualityTier.MODERATE: "Moderate compatibility worth exploring",
        MatchQualityTier.EXPLORATORY: "Exploratory connection requiring patience",
        MatchQualityTier.LIMITED: "Limited compatibility with significant challenges",
        MatchQualityTier.INCOMPATIBLE: "Significant incompatibilities present",
    }
    return descriptions.get(tier, "Unknown compatibility level")


def _get_connection_description(prediction: ConnectionPrediction) -> str:
    """Get description of connection prediction"""
    descriptions = {
        ConnectionPrediction.SOULMATE_POTENTIAL: "Deep soulmate connection potential",
        ConnectionPrediction.TRANSFORMATIONAL: "Transformational partnership for growth",
        ConnectionPrediction.DYNAMIC_GROWTH: "Dynamic relationship with mutual development",
        ConnectionPrediction.STABLE_COMPANIONSHIP: "Stable, supportive companionship",
        ConnectionPrediction.EMOTIONAL_JOURNEY: "Rich emotional connection journey",
        ConnectionPrediction.COMPLEMENTARY_BALANCE: "Complementary balance of differences",
        ConnectionPrediction.EXPLORATORY_CONNECTION: "Exploratory connection worth pursuing",
        ConnectionPrediction.FRIENDSHIP_FOUNDATION: "Strong foundation for friendship first",
    }
    return descriptions.get(prediction, "Connection with potential")


def _get_confidence_description(confidence: float) -> str:
    """Get description of assessment confidence"""
    if confidence >= 85:
        return "Very high confidence in assessment"
    elif confidence >= 70:
        return "High confidence in assessment"
    elif confidence >= 55:
        return "Moderate confidence in assessment"
    else:
        return "Lower confidence - more data would improve accuracy"


def _get_interaction_style_recommendation(
    match_quality: EnhancedMatchQuality,
) -> str:
    """Recommend interaction style based on match analysis"""
    if match_quality.match_quality_tier in [
        MatchQualityTier.TRANSCENDENT,
        MatchQualityTier.EXCEPTIONAL,
    ]:
        return "Be authentic and open - natural flow is likely"
    elif match_quality.emotional_depth_compatibility.vulnerability_match >= 75:
        return "Comfortable with meaningful conversation and emotional sharing"
    elif match_quality.soul_compatibility.communication_score >= 75:
        return "Focus on good communication and shared interests"
    else:
        return "Start with light conversation and build trust gradually"


def _identify_success_factors(
    match_quality: EnhancedMatchQuality,
) -> List[str]:
    """Identify key factors for relationship success"""
    factors = []

    if match_quality.advanced_compatibility.growth_potential >= 80:
        factors.append("Mutual commitment to personal growth")

    if match_quality.soul_compatibility.values_score >= 80:
        factors.append("Alignment on core values and life goals")

    if match_quality.emotional_depth_compatibility.vulnerability_match >= 75:
        factors.append("Comfort with emotional vulnerability and authenticity")

    if match_quality.soul_compatibility.communication_score >= 75:
        factors.append("Strong communication foundation")

    # Default factors if none identified
    if not factors:
        factors = [
            "Open communication",
            "Mutual respect",
            "Patience with differences",
        ]

    return factors[:4]  # Return top 4 factors
