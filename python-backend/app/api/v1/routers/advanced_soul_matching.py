"""
Advanced Soul Matching API Endpoints
Provides comprehensive compatibility analysis with emotional depth assessment
"""

import logging
from datetime import datetime
from enum import Enum
from typing import List

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.soul_connection import SoulConnection
from app.models.user import User
from app.services.advanced_soul_matching import advanced_matching_service
from app.services.emotional_depth_service import emotional_depth_service
from app.services.enhanced_match_quality_service import enhanced_match_quality_service
from app.services.soul_compatibility_service import compatibility_service
from fastapi import APIRouter, Depends, HTTPException, status

# Pydantic schemas for API responses
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class MatchQualityTier(str, Enum):
    """Enhanced match quality tiers"""

    TRANSCENDENT = "transcendent"
    EXCEPTIONAL = "exceptional"
    HIGH = "high"
    GOOD = "good"
    MODERATE = "moderate"
    EXPLORATORY = "exploratory"
    LIMITED = "limited"
    INCOMPATIBLE = "incompatible"


class ConnectionPrediction(str, Enum):
    """Relationship development predictions"""

    SOULMATE_POTENTIAL = "soulmate_potential"
    TRANSFORMATIONAL = "transformational"
    DYNAMIC_GROWTH = "dynamic_growth"
    STABLE_COMPANIONSHIP = "stable_companionship"
    EMOTIONAL_JOURNEY = "emotional_journey"
    COMPLEMENTARY_BALANCE = "complementary_balance"
    EXPLORATORY_CONNECTION = "exploratory_connection"
    FRIENDSHIP_FOUNDATION = "friendship_foundation"


class EmotionalDepthLevel(str, Enum):
    """Emotional depth classification levels"""

    SURFACE = "surface"
    EMERGING = "emerging"
    MODERATE = "moderate"
    DEEP = "deep"
    PROFOUND = "profound"


class VulnerabilityIndicator(str, Enum):
    """Types of vulnerability expression"""

    INTELLECTUAL = "intellectual"
    EMOTIONAL = "emotional"
    RELATIONAL = "relational"
    SPIRITUAL = "spiritual"
    PERSONAL = "personal"


# Response models
class CompatibilityBreakdown(BaseModel):
    """Detailed compatibility score breakdown"""

    total_score: float = Field(
        ..., ge=0, le=100, description="Overall compatibility score"
    )
    confidence: float = Field(..., ge=0, le=100, description="Confidence in assessment")

    # Component scores
    interests_score: float = Field(..., ge=0, le=100)
    values_score: float = Field(..., ge=0, le=100)
    personality_score: float = Field(..., ge=0, le=100)
    communication_score: float = Field(..., ge=0, le=100)
    demographic_score: float = Field(..., ge=0, le=100)
    emotional_resonance: float = Field(..., ge=0, le=100)

    # Qualitative assessment
    match_quality: str
    energy_level: str
    strengths: List[str]
    growth_areas: List[str]
    compatibility_summary: str


class AdvancedCompatibilityResponse(BaseModel):
    """Advanced compatibility analysis response"""

    # Base compatibility
    base_compatibility: CompatibilityBreakdown

    # Advanced metrics
    emotional_intelligence_compatibility: float = Field(..., ge=0, le=100)
    temporal_compatibility: float = Field(..., ge=0, le=100)
    communication_rhythm_match: float = Field(..., ge=0, le=100)
    growth_potential: float = Field(..., ge=0, le=100)
    conflict_resolution_compatibility: float = Field(..., ge=0, le=100)

    # Enhanced insights
    relationship_prediction: str
    growth_timeline: str
    recommended_first_date: str
    conversation_starters: List[str]


class EmotionalDepthMetricsResponse(BaseModel):
    """Emotional depth assessment response"""

    overall_depth: float = Field(..., ge=0, le=100)
    emotional_vocabulary: int = Field(..., ge=0)
    vulnerability_score: float = Field(..., ge=0, le=100)
    authenticity_score: float = Field(..., ge=0, le=100)
    empathy_indicators: float = Field(..., ge=0, le=100)
    growth_mindset: float = Field(..., ge=0, le=100)

    depth_level: EmotionalDepthLevel
    vulnerability_types: List[VulnerabilityIndicator]
    depth_indicators: List[str]
    maturity_signals: List[str]
    authenticity_markers: List[str]

    emotional_availability: float = Field(..., ge=0, le=100)
    attachment_security: float = Field(..., ge=0, le=100)
    communication_depth: float = Field(..., ge=0, le=100)

    confidence: float = Field(..., ge=0, le=100)
    text_quality: str
    response_richness: int


class DepthCompatibilityResponse(BaseModel):
    """Emotional depth compatibility response"""

    compatibility_score: float = Field(..., ge=0, le=100)
    depth_harmony: float = Field(..., ge=0, le=100)
    vulnerability_match: float = Field(..., ge=0, le=100)
    growth_alignment: float = Field(..., ge=0, le=100)

    user1_depth: EmotionalDepthMetricsResponse
    user2_depth: EmotionalDepthMetricsResponse

    connection_potential: str
    recommended_approach: str
    depth_growth_timeline: str


class EnhancedMatchQualityResponse(BaseModel):
    """Comprehensive match quality assessment response"""

    total_compatibility: float = Field(..., ge=0, le=100)
    match_quality_tier: MatchQualityTier
    connection_prediction: ConnectionPrediction

    # Component analyses
    soul_compatibility: CompatibilityBreakdown
    advanced_compatibility: AdvancedCompatibilityResponse
    emotional_depth_compatibility: DepthCompatibilityResponse

    # Enhanced insights
    relationship_timeline: str
    connection_strengths: List[str]
    growth_opportunities: List[str]
    potential_challenges: List[str]
    recommended_approach: str
    first_date_suggestion: str
    conversation_starters: List[str]

    # Metadata
    assessment_confidence: float = Field(..., ge=0, le=100)
    algorithm_version: str
    analysis_timestamp: datetime


# API Endpoints


@router.get("/compatibility/{user_id}", response_model=CompatibilityBreakdown)
async def get_soul_compatibility(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get soul compatibility score between current user and specified user
    Uses the foundational soul compatibility algorithm
    """
    try:
        # Get target user
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found",
            )

        # Prevent self-compatibility calculation
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot calculate compatibility with yourself",
            )

        # Calculate compatibility
        compatibility = compatibility_service.calculate_compatibility(
            current_user, target_user, db
        )

        # Convert to response model
        return CompatibilityBreakdown(
            total_score=compatibility.total_score,
            confidence=compatibility.confidence,
            interests_score=compatibility.interests_score,
            values_score=compatibility.values_score,
            personality_score=compatibility.personality_score,
            communication_score=compatibility.communication_score,
            demographic_score=compatibility.demographic_score,
            emotional_resonance=compatibility.emotional_resonance,
            match_quality=compatibility.match_quality,
            energy_level=compatibility.energy_level.value,
            strengths=compatibility.strengths,
            growth_areas=compatibility.growth_areas,
            compatibility_summary=compatibility.compatibility_summary,
        )

    except Exception as e:
        logger.error(f"Error calculating soul compatibility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate compatibility",
        )


@router.get(
    "/advanced-compatibility/{user_id}",
    response_model=AdvancedCompatibilityResponse,
)
async def get_advanced_compatibility(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get advanced compatibility analysis with enhanced algorithms
    Includes emotional intelligence, temporal compatibility, and growth potential
    """
    try:
        # Get target user
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found",
            )

        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot calculate compatibility with yourself",
            )

        # Calculate advanced compatibility
        advanced_compat = advanced_matching_service.calculate_advanced_compatibility(
            current_user, target_user, db
        )

        # Convert base compatibility to response model
        base_compat = CompatibilityBreakdown(
            total_score=advanced_compat.total_score,
            confidence=advanced_compat.confidence,
            interests_score=advanced_compat.interests_score,
            values_score=advanced_compat.values_score,
            personality_score=advanced_compat.personality_score,
            communication_score=advanced_compat.communication_score,
            demographic_score=advanced_compat.demographic_score,
            emotional_resonance=advanced_compat.emotional_resonance,
            match_quality=advanced_compat.match_quality,
            energy_level=advanced_compat.energy_level.value,
            strengths=advanced_compat.strengths,
            growth_areas=advanced_compat.growth_areas,
            compatibility_summary=advanced_compat.compatibility_summary,
        )

        return AdvancedCompatibilityResponse(
            base_compatibility=base_compat,
            emotional_intelligence_compatibility=advanced_compat.emotional_intelligence_compatibility,
            temporal_compatibility=advanced_compat.temporal_compatibility,
            communication_rhythm_match=advanced_compat.communication_rhythm_match,
            growth_potential=advanced_compat.growth_potential,
            conflict_resolution_compatibility=advanced_compat.conflict_resolution_compatibility,
            relationship_prediction=advanced_compat.relationship_prediction,
            growth_timeline=advanced_compat.growth_timeline,
            recommended_first_date=advanced_compat.recommended_first_date,
            conversation_starters=advanced_compat.conversation_starters,
        )

    except Exception as e:
        logger.error(f"Error calculating advanced compatibility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate advanced compatibility",
        )


@router.get("/emotional-depth", response_model=EmotionalDepthMetricsResponse)
async def get_emotional_depth_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user's emotional depth analysis
    Analyzes emotional intelligence, vulnerability, and authenticity
    """
    try:
        depth_metrics = emotional_depth_service.analyze_emotional_depth(
            current_user, db
        )

        return EmotionalDepthMetricsResponse(
            overall_depth=depth_metrics.overall_depth,
            emotional_vocabulary=depth_metrics.emotional_vocabulary,
            vulnerability_score=depth_metrics.vulnerability_score,
            authenticity_score=depth_metrics.authenticity_score,
            empathy_indicators=depth_metrics.empathy_indicators,
            growth_mindset=depth_metrics.growth_mindset,
            depth_level=EmotionalDepthLevel(depth_metrics.depth_level.value),
            vulnerability_types=[
                VulnerabilityIndicator(vt.value)
                for vt in depth_metrics.vulnerability_types
            ],
            depth_indicators=depth_metrics.depth_indicators,
            maturity_signals=depth_metrics.maturity_signals,
            authenticity_markers=depth_metrics.authenticity_markers,
            emotional_availability=depth_metrics.emotional_availability,
            attachment_security=depth_metrics.attachment_security,
            communication_depth=depth_metrics.communication_depth,
            confidence=depth_metrics.confidence,
            text_quality=depth_metrics.text_quality,
            response_richness=depth_metrics.response_richness,
        )

    except Exception as e:
        logger.error(f"Error analyzing emotional depth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze emotional depth",
        )


@router.get("/emotional-depth/{user_id}", response_model=EmotionalDepthMetricsResponse)
async def get_user_emotional_depth_analysis(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get specified user's emotional depth analysis
    Only accessible if users have an active connection
    """
    try:
        # Check if users have an active connection
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
                detail="Can only view emotional depth of connected users",
            )

        # Get target user
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        depth_metrics = emotional_depth_service.analyze_emotional_depth(target_user, db)

        return EmotionalDepthMetricsResponse(
            overall_depth=depth_metrics.overall_depth,
            emotional_vocabulary=depth_metrics.emotional_vocabulary,
            vulnerability_score=depth_metrics.vulnerability_score,
            authenticity_score=depth_metrics.authenticity_score,
            empathy_indicators=depth_metrics.empathy_indicators,
            growth_mindset=depth_metrics.growth_mindset,
            depth_level=EmotionalDepthLevel(depth_metrics.depth_level.value),
            vulnerability_types=[
                VulnerabilityIndicator(vt.value)
                for vt in depth_metrics.vulnerability_types
            ],
            depth_indicators=depth_metrics.depth_indicators,
            maturity_signals=depth_metrics.maturity_signals,
            authenticity_markers=depth_metrics.authenticity_markers,
            emotional_availability=depth_metrics.emotional_availability,
            attachment_security=depth_metrics.attachment_security,
            communication_depth=depth_metrics.communication_depth,
            confidence=depth_metrics.confidence,
            text_quality=depth_metrics.text_quality,
            response_richness=depth_metrics.response_richness,
        )

    except Exception as e:
        logger.error(f"Error analyzing user emotional depth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze emotional depth",
        )


@router.get("/depth-compatibility/{user_id}", response_model=DepthCompatibilityResponse)
async def get_depth_compatibility(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get emotional depth compatibility between users
    Analyzes vulnerability matching, depth harmony, and growth alignment
    """
    try:
        # Get target user
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found",
            )

        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot calculate compatibility with yourself",
            )

        # Calculate depth compatibility
        depth_compat = emotional_depth_service.calculate_depth_compatibility(
            current_user, target_user, db
        )

        # Convert user depth metrics to response models
        user1_depth = EmotionalDepthMetricsResponse(
            overall_depth=depth_compat.user1_depth.overall_depth,
            emotional_vocabulary=depth_compat.user1_depth.emotional_vocabulary,
            vulnerability_score=depth_compat.user1_depth.vulnerability_score,
            authenticity_score=depth_compat.user1_depth.authenticity_score,
            empathy_indicators=depth_compat.user1_depth.empathy_indicators,
            growth_mindset=depth_compat.user1_depth.growth_mindset,
            depth_level=EmotionalDepthLevel(depth_compat.user1_depth.depth_level.value),
            vulnerability_types=[
                VulnerabilityIndicator(vt.value)
                for vt in depth_compat.user1_depth.vulnerability_types
            ],
            depth_indicators=depth_compat.user1_depth.depth_indicators,
            maturity_signals=depth_compat.user1_depth.maturity_signals,
            authenticity_markers=depth_compat.user1_depth.authenticity_markers,
            emotional_availability=depth_compat.user1_depth.emotional_availability,
            attachment_security=depth_compat.user1_depth.attachment_security,
            communication_depth=depth_compat.user1_depth.communication_depth,
            confidence=depth_compat.user1_depth.confidence,
            text_quality=depth_compat.user1_depth.text_quality,
            response_richness=depth_compat.user1_depth.response_richness,
        )

        user2_depth = EmotionalDepthMetricsResponse(
            overall_depth=depth_compat.user2_depth.overall_depth,
            emotional_vocabulary=depth_compat.user2_depth.emotional_vocabulary,
            vulnerability_score=depth_compat.user2_depth.vulnerability_score,
            authenticity_score=depth_compat.user2_depth.authenticity_score,
            empathy_indicators=depth_compat.user2_depth.empathy_indicators,
            growth_mindset=depth_compat.user2_depth.growth_mindset,
            depth_level=EmotionalDepthLevel(depth_compat.user2_depth.depth_level.value),
            vulnerability_types=[
                VulnerabilityIndicator(vt.value)
                for vt in depth_compat.user2_depth.vulnerability_types
            ],
            depth_indicators=depth_compat.user2_depth.depth_indicators,
            maturity_signals=depth_compat.user2_depth.maturity_signals,
            authenticity_markers=depth_compat.user2_depth.authenticity_markers,
            emotional_availability=depth_compat.user2_depth.emotional_availability,
            attachment_security=depth_compat.user2_depth.attachment_security,
            communication_depth=depth_compat.user2_depth.communication_depth,
            confidence=depth_compat.user2_depth.confidence,
            text_quality=depth_compat.user2_depth.text_quality,
            response_richness=depth_compat.user2_depth.response_richness,
        )

        return DepthCompatibilityResponse(
            compatibility_score=depth_compat.compatibility_score,
            depth_harmony=depth_compat.depth_harmony,
            vulnerability_match=depth_compat.vulnerability_match,
            growth_alignment=depth_compat.growth_alignment,
            user1_depth=user1_depth,
            user2_depth=user2_depth,
            connection_potential=depth_compat.connection_potential,
            recommended_approach=depth_compat.recommended_approach,
            depth_growth_timeline=depth_compat.depth_growth_timeline,
        )

    except Exception as e:
        logger.error(f"Error calculating depth compatibility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate depth compatibility",
        )


@router.get(
    "/comprehensive-match-quality/{user_id}",
    response_model=EnhancedMatchQualityResponse,
)
async def get_comprehensive_match_quality(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive match quality assessment combining all algorithms
    The ultimate compatibility analysis using soul, advanced, and emotional depth algorithms
    """
    try:
        # Get target user
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found",
            )

        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot calculate compatibility with yourself",
            )

        # Calculate comprehensive match quality
        enhanced_quality = (
            enhanced_match_quality_service.assess_comprehensive_match_quality(
                current_user, target_user, db
            )
        )

        # Convert component analyses to response models
        soul_compat = CompatibilityBreakdown(
            total_score=enhanced_quality.soul_compatibility.total_score,
            confidence=enhanced_quality.soul_compatibility.confidence,
            interests_score=enhanced_quality.soul_compatibility.interests_score,
            values_score=enhanced_quality.soul_compatibility.values_score,
            personality_score=enhanced_quality.soul_compatibility.personality_score,
            communication_score=enhanced_quality.soul_compatibility.communication_score,
            demographic_score=enhanced_quality.soul_compatibility.demographic_score,
            emotional_resonance=enhanced_quality.soul_compatibility.emotional_resonance,
            match_quality=enhanced_quality.soul_compatibility.match_quality,
            energy_level=enhanced_quality.soul_compatibility.energy_level.value,
            strengths=enhanced_quality.soul_compatibility.strengths,
            growth_areas=enhanced_quality.soul_compatibility.growth_areas,
            compatibility_summary=enhanced_quality.soul_compatibility.compatibility_summary,
        )

        # Note: For brevity, I'm creating simplified response models here
        # In a full implementation, you would fully convert all nested objects

        return EnhancedMatchQualityResponse(
            total_compatibility=enhanced_quality.total_compatibility,
            match_quality_tier=MatchQualityTier(
                enhanced_quality.match_quality_tier.value
            ),
            connection_prediction=ConnectionPrediction(
                enhanced_quality.connection_prediction.value
            ),
            soul_compatibility=soul_compat,
            # Note: The advanced_compatibility and emotional_depth_compatibility would need
            # full conversion in a complete implementation
            advanced_compatibility=AdvancedCompatibilityResponse(
                base_compatibility=soul_compat,
                emotional_intelligence_compatibility=enhanced_quality.advanced_compatibility.emotional_intelligence_compatibility,
                temporal_compatibility=enhanced_quality.advanced_compatibility.temporal_compatibility,
                communication_rhythm_match=enhanced_quality.advanced_compatibility.communication_rhythm_match,
                growth_potential=enhanced_quality.advanced_compatibility.growth_potential,
                conflict_resolution_compatibility=enhanced_quality.advanced_compatibility.conflict_resolution_compatibility,
                relationship_prediction=enhanced_quality.advanced_compatibility.relationship_prediction,
                growth_timeline=enhanced_quality.advanced_compatibility.growth_timeline,
                recommended_first_date=enhanced_quality.advanced_compatibility.recommended_first_date,
                conversation_starters=enhanced_quality.advanced_compatibility.conversation_starters,
            ),
            emotional_depth_compatibility=DepthCompatibilityResponse(
                compatibility_score=enhanced_quality.emotional_depth_compatibility.compatibility_score,
                depth_harmony=enhanced_quality.emotional_depth_compatibility.depth_harmony,
                vulnerability_match=enhanced_quality.emotional_depth_compatibility.vulnerability_match,
                growth_alignment=enhanced_quality.emotional_depth_compatibility.growth_alignment,
                user1_depth=EmotionalDepthMetricsResponse(
                    overall_depth=enhanced_quality.emotional_depth_compatibility.user1_depth.overall_depth,
                    emotional_vocabulary=enhanced_quality.emotional_depth_compatibility.user1_depth.emotional_vocabulary,
                    vulnerability_score=enhanced_quality.emotional_depth_compatibility.user1_depth.vulnerability_score,
                    authenticity_score=enhanced_quality.emotional_depth_compatibility.user1_depth.authenticity_score,
                    empathy_indicators=enhanced_quality.emotional_depth_compatibility.user1_depth.empathy_indicators,
                    growth_mindset=enhanced_quality.emotional_depth_compatibility.user1_depth.growth_mindset,
                    depth_level=EmotionalDepthLevel(
                        enhanced_quality.emotional_depth_compatibility.user1_depth.depth_level.value
                    ),
                    vulnerability_types=[
                        VulnerabilityIndicator(vt.value)
                        for vt in enhanced_quality.emotional_depth_compatibility.user1_depth.vulnerability_types
                    ],
                    depth_indicators=enhanced_quality.emotional_depth_compatibility.user1_depth.depth_indicators,
                    maturity_signals=enhanced_quality.emotional_depth_compatibility.user1_depth.maturity_signals,
                    authenticity_markers=enhanced_quality.emotional_depth_compatibility.user1_depth.authenticity_markers,
                    emotional_availability=enhanced_quality.emotional_depth_compatibility.user1_depth.emotional_availability,
                    attachment_security=enhanced_quality.emotional_depth_compatibility.user1_depth.attachment_security,
                    communication_depth=enhanced_quality.emotional_depth_compatibility.user1_depth.communication_depth,
                    confidence=enhanced_quality.emotional_depth_compatibility.user1_depth.confidence,
                    text_quality=enhanced_quality.emotional_depth_compatibility.user1_depth.text_quality,
                    response_richness=enhanced_quality.emotional_depth_compatibility.user1_depth.response_richness,
                ),
                user2_depth=EmotionalDepthMetricsResponse(
                    overall_depth=enhanced_quality.emotional_depth_compatibility.user2_depth.overall_depth,
                    emotional_vocabulary=enhanced_quality.emotional_depth_compatibility.user2_depth.emotional_vocabulary,
                    vulnerability_score=enhanced_quality.emotional_depth_compatibility.user2_depth.vulnerability_score,
                    authenticity_score=enhanced_quality.emotional_depth_compatibility.user2_depth.authenticity_score,
                    empathy_indicators=enhanced_quality.emotional_depth_compatibility.user2_depth.empathy_indicators,
                    growth_mindset=enhanced_quality.emotional_depth_compatibility.user2_depth.growth_mindset,
                    depth_level=EmotionalDepthLevel(
                        enhanced_quality.emotional_depth_compatibility.user2_depth.depth_level.value
                    ),
                    vulnerability_types=[
                        VulnerabilityIndicator(vt.value)
                        for vt in enhanced_quality.emotional_depth_compatibility.user2_depth.vulnerability_types
                    ],
                    depth_indicators=enhanced_quality.emotional_depth_compatibility.user2_depth.depth_indicators,
                    maturity_signals=enhanced_quality.emotional_depth_compatibility.user2_depth.maturity_signals,
                    authenticity_markers=enhanced_quality.emotional_depth_compatibility.user2_depth.authenticity_markers,
                    emotional_availability=enhanced_quality.emotional_depth_compatibility.user2_depth.emotional_availability,
                    attachment_security=enhanced_quality.emotional_depth_compatibility.user2_depth.attachment_security,
                    communication_depth=enhanced_quality.emotional_depth_compatibility.user2_depth.communication_depth,
                    confidence=enhanced_quality.emotional_depth_compatibility.user2_depth.confidence,
                    text_quality=enhanced_quality.emotional_depth_compatibility.user2_depth.text_quality,
                    response_richness=enhanced_quality.emotional_depth_compatibility.user2_depth.response_richness,
                ),
                connection_potential=enhanced_quality.emotional_depth_compatibility.connection_potential,
                recommended_approach=enhanced_quality.emotional_depth_compatibility.recommended_approach,
                depth_growth_timeline=enhanced_quality.emotional_depth_compatibility.depth_growth_timeline,
            ),
            relationship_timeline=enhanced_quality.relationship_timeline,
            connection_strengths=enhanced_quality.connection_strengths,
            growth_opportunities=enhanced_quality.growth_opportunities,
            potential_challenges=enhanced_quality.potential_challenges,
            recommended_approach=enhanced_quality.recommended_approach,
            first_date_suggestion=enhanced_quality.first_date_suggestion,
            conversation_starters=enhanced_quality.conversation_starters,
            assessment_confidence=enhanced_quality.assessment_confidence,
            algorithm_version=enhanced_quality.algorithm_version,
            analysis_timestamp=enhanced_quality.analysis_timestamp,
        )

    except Exception as e:
        logger.error(f"Error calculating comprehensive match quality: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate comprehensive match quality",
        )


@router.get("/discovery/enhanced", response_model=List[EnhancedMatchQualityResponse])
async def get_enhanced_discovery_matches(
    limit: int = 10,
    min_compatibility: float = 50.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Discover potential matches using enhanced compatibility algorithms
    Returns comprehensive match quality assessments for discovery
    """
    try:
        # Get potential matches (users not already connected)
        existing_connections = (
            db.query(SoulConnection)
            .filter(
                (SoulConnection.user1_id == current_user.id)
                | (SoulConnection.user2_id == current_user.id)
            )
            .all()
        )

        connected_user_ids = set()
        for conn in existing_connections:
            connected_user_ids.add(conn.user1_id)
            connected_user_ids.add(conn.user2_id)
        connected_user_ids.discard(current_user.id)  # Remove self

        # Get potential matches
        potential_matches = (
            db.query(User)
            .filter(
                User.id != current_user.id,
                ~User.id.in_(connected_user_ids),
                User.emotional_onboarding_completed,
            )
            .limit(limit * 2)
            .all()
        )  # Get more than needed for filtering

        enhanced_matches = []

        for potential_match in potential_matches:
            try:
                # Calculate comprehensive match quality
                enhanced_quality = (
                    enhanced_match_quality_service.assess_comprehensive_match_quality(
                        current_user, potential_match, db
                    )
                )

                # Filter by minimum compatibility
                if enhanced_quality.total_compatibility >= min_compatibility:
                    # Convert to response model (simplified for brevity)
                    soul_compat = CompatibilityBreakdown(
                        total_score=enhanced_quality.soul_compatibility.total_score,
                        confidence=enhanced_quality.soul_compatibility.confidence,
                        interests_score=enhanced_quality.soul_compatibility.interests_score,
                        values_score=enhanced_quality.soul_compatibility.values_score,
                        personality_score=enhanced_quality.soul_compatibility.personality_score,
                        communication_score=enhanced_quality.soul_compatibility.communication_score,
                        demographic_score=enhanced_quality.soul_compatibility.demographic_score,
                        emotional_resonance=enhanced_quality.soul_compatibility.emotional_resonance,
                        match_quality=enhanced_quality.soul_compatibility.match_quality,
                        energy_level=enhanced_quality.soul_compatibility.energy_level.value,
                        strengths=enhanced_quality.soul_compatibility.strengths,
                        growth_areas=enhanced_quality.soul_compatibility.growth_areas,
                        compatibility_summary=enhanced_quality.soul_compatibility.compatibility_summary,
                    )

                    enhanced_match_response = EnhancedMatchQualityResponse(
                        total_compatibility=enhanced_quality.total_compatibility,
                        match_quality_tier=MatchQualityTier(
                            enhanced_quality.match_quality_tier.value
                        ),
                        connection_prediction=ConnectionPrediction(
                            enhanced_quality.connection_prediction.value
                        ),
                        soul_compatibility=soul_compat,
                        advanced_compatibility=AdvancedCompatibilityResponse(
                            base_compatibility=soul_compat,
                            emotional_intelligence_compatibility=enhanced_quality.advanced_compatibility.emotional_intelligence_compatibility,
                            temporal_compatibility=enhanced_quality.advanced_compatibility.temporal_compatibility,
                            communication_rhythm_match=enhanced_quality.advanced_compatibility.communication_rhythm_match,
                            growth_potential=enhanced_quality.advanced_compatibility.growth_potential,
                            conflict_resolution_compatibility=enhanced_quality.advanced_compatibility.conflict_resolution_compatibility,
                            relationship_prediction=enhanced_quality.advanced_compatibility.relationship_prediction,
                            growth_timeline=enhanced_quality.advanced_compatibility.growth_timeline,
                            recommended_first_date=enhanced_quality.advanced_compatibility.recommended_first_date,
                            conversation_starters=enhanced_quality.advanced_compatibility.conversation_starters,
                        ),
                        emotional_depth_compatibility=DepthCompatibilityResponse(
                            compatibility_score=enhanced_quality.emotional_depth_compatibility.compatibility_score,
                            depth_harmony=enhanced_quality.emotional_depth_compatibility.depth_harmony,
                            vulnerability_match=enhanced_quality.emotional_depth_compatibility.vulnerability_match,
                            growth_alignment=enhanced_quality.emotional_depth_compatibility.growth_alignment,
                            user1_depth=EmotionalDepthMetricsResponse(
                                overall_depth=enhanced_quality.emotional_depth_compatibility.user1_depth.overall_depth,
                                emotional_vocabulary=enhanced_quality.emotional_depth_compatibility.user1_depth.emotional_vocabulary,
                                vulnerability_score=enhanced_quality.emotional_depth_compatibility.user1_depth.vulnerability_score,
                                authenticity_score=enhanced_quality.emotional_depth_compatibility.user1_depth.authenticity_score,
                                empathy_indicators=enhanced_quality.emotional_depth_compatibility.user1_depth.empathy_indicators,
                                growth_mindset=enhanced_quality.emotional_depth_compatibility.user1_depth.growth_mindset,
                                depth_level=EmotionalDepthLevel(
                                    enhanced_quality.emotional_depth_compatibility.user1_depth.depth_level.value
                                ),
                                vulnerability_types=[
                                    VulnerabilityIndicator(vt.value)
                                    for vt in enhanced_quality.emotional_depth_compatibility.user1_depth.vulnerability_types
                                ],
                                depth_indicators=enhanced_quality.emotional_depth_compatibility.user1_depth.depth_indicators,
                                maturity_signals=enhanced_quality.emotional_depth_compatibility.user1_depth.maturity_signals,
                                authenticity_markers=enhanced_quality.emotional_depth_compatibility.user1_depth.authenticity_markers,
                                emotional_availability=enhanced_quality.emotional_depth_compatibility.user1_depth.emotional_availability,
                                attachment_security=enhanced_quality.emotional_depth_compatibility.user1_depth.attachment_security,
                                communication_depth=enhanced_quality.emotional_depth_compatibility.user1_depth.communication_depth,
                                confidence=enhanced_quality.emotional_depth_compatibility.user1_depth.confidence,
                                text_quality=enhanced_quality.emotional_depth_compatibility.user1_depth.text_quality,
                                response_richness=enhanced_quality.emotional_depth_compatibility.user1_depth.response_richness,
                            ),
                            user2_depth=EmotionalDepthMetricsResponse(
                                overall_depth=enhanced_quality.emotional_depth_compatibility.user2_depth.overall_depth,
                                emotional_vocabulary=enhanced_quality.emotional_depth_compatibility.user2_depth.emotional_vocabulary,
                                vulnerability_score=enhanced_quality.emotional_depth_compatibility.user2_depth.vulnerability_score,
                                authenticity_score=enhanced_quality.emotional_depth_compatibility.user2_depth.authenticity_score,
                                empathy_indicators=enhanced_quality.emotional_depth_compatibility.user2_depth.empathy_indicators,
                                growth_mindset=enhanced_quality.emotional_depth_compatibility.user2_depth.growth_mindset,
                                depth_level=EmotionalDepthLevel(
                                    enhanced_quality.emotional_depth_compatibility.user2_depth.depth_level.value
                                ),
                                vulnerability_types=[
                                    VulnerabilityIndicator(vt.value)
                                    for vt in enhanced_quality.emotional_depth_compatibility.user2_depth.vulnerability_types
                                ],
                                depth_indicators=enhanced_quality.emotional_depth_compatibility.user2_depth.depth_indicators,
                                maturity_signals=enhanced_quality.emotional_depth_compatibility.user2_depth.maturity_signals,
                                authenticity_markers=enhanced_quality.emotional_depth_compatibility.user2_depth.authenticity_markers,
                                emotional_availability=enhanced_quality.emotional_depth_compatibility.user2_depth.emotional_availability,
                                attachment_security=enhanced_quality.emotional_depth_compatibility.user2_depth.attachment_security,
                                communication_depth=enhanced_quality.emotional_depth_compatibility.user2_depth.communication_depth,
                                confidence=enhanced_quality.emotional_depth_compatibility.user2_depth.confidence,
                                text_quality=enhanced_quality.emotional_depth_compatibility.user2_depth.text_quality,
                                response_richness=enhanced_quality.emotional_depth_compatibility.user2_depth.response_richness,
                            ),
                            connection_potential=enhanced_quality.emotional_depth_compatibility.connection_potential,
                            recommended_approach=enhanced_quality.emotional_depth_compatibility.recommended_approach,
                            depth_growth_timeline=enhanced_quality.emotional_depth_compatibility.depth_growth_timeline,
                        ),
                        relationship_timeline=enhanced_quality.relationship_timeline,
                        connection_strengths=enhanced_quality.connection_strengths,
                        growth_opportunities=enhanced_quality.growth_opportunities,
                        potential_challenges=enhanced_quality.potential_challenges,
                        recommended_approach=enhanced_quality.recommended_approach,
                        first_date_suggestion=enhanced_quality.first_date_suggestion,
                        conversation_starters=enhanced_quality.conversation_starters,
                        assessment_confidence=enhanced_quality.assessment_confidence,
                        algorithm_version=enhanced_quality.algorithm_version,
                        analysis_timestamp=enhanced_quality.analysis_timestamp,
                    )

                    enhanced_matches.append(enhanced_match_response)

                    # Stop when we have enough high-quality matches
                    if len(enhanced_matches) >= limit:
                        break

            except Exception as e:
                logger.warning(
                    f"Error calculating compatibility for user {potential_match.id}: {str(e)}"
                )
                continue

        # Sort by total compatibility score (descending)
        enhanced_matches.sort(key=lambda x: x.total_compatibility, reverse=True)

        return enhanced_matches[:limit]

    except Exception as e:
        logger.error(f"Error in enhanced discovery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover enhanced matches",
        )
