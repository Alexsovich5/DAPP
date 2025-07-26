# AI-Enhanced Matching API Router
# Dinner First Dating Platform - Advanced Features & Scale

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import logging
from datetime import datetime, timedelta

from ....core.database import get_db
from ....core.auth import get_current_user
from ....models.user import User
from ....models.profile import Profile
from ....services.ai_matching import get_ai_matching_service, PrivacyFirstMatchingAI
from ....schemas.ai_matching import (
    AICompatibilityAnalysis,
    ConversationStartersResponse,
    MatchingRequest,
    BatchMatchingRequest,
    BatchMatchingResponse,
    DeepCompatibilityAnalysis,
    AIModelStatus,
    AIMatchingConfig,
    MatchingMetrics,
    MatchResult,
    ConversationStarter
)
from ....core.config import settings
from ....core.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-matching", tags=["AI Matching"])

# Rate limiters for AI endpoints
compatibility_limiter = RateLimiter(times=10, seconds=300)  # 10 analyses per 5 minutes
batch_limiter = RateLimiter(times=3, seconds=3600)  # 3 batch analyses per hour
conversation_limiter = RateLimiter(times=20, seconds=3600)  # 20 conversation generations per hour

@router.post("/analyze-compatibility", response_model=AICompatibilityAnalysis)
async def analyze_compatibility(
    request: MatchingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: PrivacyFirstMatchingAI = Depends(get_ai_matching_service)
):
    """
    Analyze compatibility between two users using AI-enhanced algorithms.
    
    This endpoint provides comprehensive compatibility analysis including:
    - Semantic similarity of profiles
    - Communication style compatibility  
    - Emotional depth analysis
    - Life goals alignment
    - Personality matching
    - Interest overlap calculation
    """
    
    # Rate limiting
    await compatibility_limiter.check_rate_limit(f"user:{current_user.id}")
    
    start_time = time.time()
    
    try:
        # Validate users exist and are not the same
        if request.user1_id == request.user2_id:
            raise HTTPException(status_code=400, detail="Cannot analyze compatibility with self")
        
        # Get users with profiles
        user1 = db.query(User).filter(User.id == request.user1_id).first()
        user2 = db.query(User).filter(User.id == request.user2_id).first()
        
        if not user1 or not user2:
            raise HTTPException(status_code=404, detail="One or both users not found")
        
        if not user1.profile or not user2.profile:
            raise HTTPException(status_code=400, detail="Both users must have completed profiles")
        
        # Privacy check - ensure current user is authorized to see this analysis
        if current_user.id != request.user1_id and current_user.id != request.user2_id:
            raise HTTPException(status_code=403, detail="Not authorized to analyze these users")
        
        # Initialize AI models if needed
        if not ai_service.is_initialized:
            await ai_service.initialize_models(db)
        
        # Perform compatibility analysis
        compatibility_result = await ai_service.calculate_comprehensive_compatibility(user1, user2)
        
        # Add processing time
        processing_time = (time.time() - start_time) * 1000
        compatibility_result["processing_time_ms"] = round(processing_time, 2)
        
        # Log analytics in background
        background_tasks.add_task(
            log_compatibility_analysis,
            current_user.id,
            request.user1_id,
            request.user2_id,
            compatibility_result["ai_compatibility_score"],
            processing_time
        )
        
        return AICompatibilityAnalysis(**compatibility_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in compatibility analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Compatibility analysis failed")

@router.post("/batch-analyze", response_model=BatchMatchingResponse)
async def batch_analyze_compatibility(
    request: BatchMatchingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: PrivacyFirstMatchingAI = Depends(get_ai_matching_service)
):
    """
    Perform batch compatibility analysis for multiple candidate users.
    
    This endpoint analyzes compatibility between a target user and multiple candidates,
    returning results sorted by compatibility score above the specified threshold.
    """
    
    # Rate limiting
    await batch_limiter.check_rate_limit(f"user:{current_user.id}")
    
    start_time = time.time()
    
    try:
        # Privacy check
        if current_user.id != request.target_user_id:
            raise HTTPException(status_code=403, detail="Can only analyze your own compatibility")
        
        # Get target user
        target_user = db.query(User).filter(User.id == request.target_user_id).first()
        if not target_user or not target_user.profile:
            raise HTTPException(status_code=404, detail="Target user not found or profile incomplete")
        
        # Get candidate users
        candidate_users = db.query(User).filter(
            User.id.in_(request.candidate_user_ids),
            User.profile_id.isnot(None)
        ).all()
        
        if len(candidate_users) != len(request.candidate_user_ids):
            raise HTTPException(status_code=400, detail="Some candidate users not found or have incomplete profiles")
        
        # Initialize AI models if needed
        if not ai_service.is_initialized:
            await ai_service.initialize_models(db)
        
        # Perform batch analysis
        matches = []
        successful_analyses = 0
        
        for candidate in candidate_users:
            try:
                compatibility_result = await ai_service.calculate_comprehensive_compatibility(target_user, candidate)
                
                # Check if above threshold
                if compatibility_result["ai_compatibility_score"] >= request.min_compatibility_score:
                    match_result = MatchResult(
                        user_id=candidate.id,
                        compatibility_analysis=AICompatibilityAnalysis(**compatibility_result)
                    )
                    
                    # Add conversation starters if requested
                    if request.include_conversation_starters:
                        starters_text = await ai_service.generate_conversation_starters(target_user, candidate)
                        starters = [
                            ConversationStarter(
                                message=starter,
                                category="ai_generated",
                                confidence_score=0.8,
                                personalization_factors=["compatibility_analysis"]
                            )
                            for starter in starters_text
                        ]
                        match_result.conversation_starters = starters
                    
                    matches.append(match_result)
                    successful_analyses += 1
                    
            except Exception as e:
                logger.error(f"Error analyzing compatibility with user {candidate.id}: {str(e)}")
                continue
        
        # Sort by compatibility score (descending) and add ranks
        matches.sort(key=lambda x: x.compatibility_analysis.ai_compatibility_score, reverse=True)
        for i, match in enumerate(matches):
            match.match_rank = i + 1
        
        processing_time = (time.time() - start_time) * 1000
        
        response = BatchMatchingResponse(
            target_user_id=request.target_user_id,
            matches=matches,
            total_candidates_analyzed=len(candidate_users),
            matches_above_threshold=len(matches),
            processing_time_ms=round(processing_time, 2)
        )
        
        # Log analytics in background
        background_tasks.add_task(
            log_batch_analysis,
            current_user.id,
            len(candidate_users),
            len(matches),
            processing_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch compatibility analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch analysis failed")

@router.post("/conversation-starters", response_model=ConversationStartersResponse)
async def generate_conversation_starters(
    user1_id: int,
    user2_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: PrivacyFirstMatchingAI = Depends(get_ai_matching_service)
):
    """
    Generate AI-powered conversation starters for two matched users.
    
    Creates personalized conversation starters based on compatibility analysis
    and shared interests, values, and personality traits.
    """
    
    # Rate limiting
    await conversation_limiter.check_rate_limit(f"user:{current_user.id}")
    
    try:
        # Privacy check
        if current_user.id != user1_id and current_user.id != user2_id:
            raise HTTPException(status_code=403, detail="Not authorized to generate starters for these users")
        
        # Get users
        user1 = db.query(User).filter(User.id == user1_id).first()
        user2 = db.query(User).filter(User.id == user2_id).first()
        
        if not user1 or not user2:
            raise HTTPException(status_code=404, detail="One or both users not found")
        
        if not user1.profile or not user2.profile:
            raise HTTPException(status_code=400, detail="Both users must have completed profiles")
        
        # Initialize AI models if needed
        if not ai_service.is_initialized:
            await ai_service.initialize_models(db)
        
        # Generate conversation starters
        starters_text = await ai_service.generate_conversation_starters(user1, user2)
        
        # Get compatibility score for context
        compatibility_result = await ai_service.calculate_comprehensive_compatibility(user1, user2)
        
        # Convert to ConversationStarter objects
        starters = []
        categories = ["interests", "values", "personality", "goals", "general"]
        
        for i, starter_text in enumerate(starters_text):
            category = categories[i % len(categories)]
            confidence = min(0.9, compatibility_result["ai_compatibility_score"] / 100)
            
            starter = ConversationStarter(
                message=starter_text,
                category=category,
                confidence_score=confidence,
                personalization_factors=["ai_analysis", "compatibility_score", "shared_interests"]
            )
            starters.append(starter)
        
        return ConversationStartersResponse(
            starters=starters,
            user_compatibility_score=compatibility_result["ai_compatibility_score"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating conversation starters: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate conversation starters")

@router.get("/model-status", response_model=AIModelStatus)
async def get_ai_model_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: PrivacyFirstMatchingAI = Depends(get_ai_matching_service)
):
    """
    Get the current status of AI models and their capabilities.
    """
    try:
        # Get training data size
        profile_count = db.query(Profile).filter(
            Profile.life_philosophy.isnot(None),
            Profile.core_values.isnot(None)
        ).count()
        
        return AIModelStatus(
            is_initialized=ai_service.is_initialized,
            training_data_size=profile_count,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get model status")

@router.get("/config", response_model=AIMatchingConfig)
async def get_ai_matching_config(
    current_user: User = Depends(get_current_user),
    ai_service: PrivacyFirstMatchingAI = Depends(get_ai_matching_service)
):
    """
    Get the current AI matching configuration and weights.
    """
    return AIMatchingConfig(
        compatibility_weights=ai_service.compatibility_weights
    )

@router.post("/deep-analysis", response_model=DeepCompatibilityAnalysis)
async def perform_deep_compatibility_analysis(
    user1_id: int,
    user2_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: PrivacyFirstMatchingAI = Depends(get_ai_matching_service)
):
    """
    Perform deep compatibility analysis with personality insights and relationship potential.
    
    This premium feature provides comprehensive analysis including:
    - Detailed personality insights
    - Relationship potential assessment
    - Growth opportunities identification
    - Potential challenges analysis
    - Recommended activities for connection
    """
    
    # Rate limiting (stricter for deep analysis)
    await compatibility_limiter.check_rate_limit(f"user:{current_user.id}:deep")
    
    try:
        # Privacy check
        if current_user.id != user1_id and current_user.id != user2_id:
            raise HTTPException(status_code=403, detail="Not authorized for deep analysis of these users")
        
        # Get users
        user1 = db.query(User).filter(User.id == user1_id).first()
        user2 = db.query(User).filter(User.id == user2_id).first()
        
        if not user1 or not user2:
            raise HTTPException(status_code=404, detail="One or both users not found")
        
        if not user1.profile or not user2.profile:
            raise HTTPException(status_code=400, detail="Both users must have completed profiles")
        
        # Initialize AI models if needed
        if not ai_service.is_initialized:
            await ai_service.initialize_models(db)
        
        # Perform basic compatibility analysis
        basic_analysis = await ai_service.calculate_comprehensive_compatibility(user1, user2)
        
        # Generate personality insights
        personality_insights = await generate_personality_insights(user1, user2, ai_service)
        
        # Assess relationship potential
        relationship_potential = assess_relationship_potential(basic_analysis["ai_compatibility_score"])
        
        # Identify growth opportunities and challenges
        growth_opportunities = await identify_growth_opportunities(user1, user2, ai_service)
        potential_challenges = await identify_potential_challenges(user1, user2, ai_service)
        
        # Recommend activities
        recommended_activities = await recommend_connection_activities(user1, user2, ai_service)
        
        deep_analysis = DeepCompatibilityAnalysis(
            basic_analysis=AICompatibilityAnalysis(**basic_analysis),
            personality_insights=personality_insights,
            relationship_potential=relationship_potential,
            growth_opportunities=growth_opportunities,
            potential_challenges=potential_challenges,
            recommended_activities=recommended_activities
        )
        
        # Log premium feature usage
        background_tasks.add_task(
            log_deep_analysis_usage,
            current_user.id,
            user1_id,
            user2_id,
            basic_analysis["ai_compatibility_score"]
        )
        
        return deep_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in deep compatibility analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Deep analysis failed")

@router.get("/metrics", response_model=MatchingMetrics)
async def get_matching_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze")
):
    """
    Get AI matching system performance metrics (admin only).
    """
    # Check if user is admin (implement admin check)
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # This would typically query a metrics database
        # For now, return mock metrics
        return MatchingMetrics(
            total_comparisons=1000,
            successful_analyses=950,
            failed_analyses=50,
            average_processing_time_ms=250.5,
            average_compatibility_score=67.8,
            high_compatibility_matches=120,
            model_confidence_average=0.82
        )
        
    except Exception as e:
        logger.error(f"Error getting matching metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

# Helper functions

async def generate_personality_insights(user1: User, user2: User, ai_service: PrivacyFirstMatchingAI):
    """Generate personality insights for deep analysis"""
    insights = []
    
    # Communication style insight
    comm_score = await ai_service.analyze_communication_compatibility(user1, user2)
    insights.append({
        "aspect": "Communication Style",
        "description": f"Your communication styles are {get_compatibility_description(comm_score * 100)} compatible",
        "compatibility_impact": "This affects how well you'll understand each other's communication preferences",
        "score": round(comm_score * 100, 1)
    })
    
    # Emotional compatibility insight
    emotional_score = await ai_service.analyze_emotional_compatibility(user1, user2)
    insights.append({
        "aspect": "Emotional Depth",
        "description": f"Your emotional expression styles show {get_compatibility_description(emotional_score * 100)} alignment",
        "compatibility_impact": "This influences emotional intimacy and understanding",
        "score": round(emotional_score * 100, 1)
    })
    
    return insights

def get_compatibility_description(score: float) -> str:
    """Get descriptive text for compatibility scores"""
    if score >= 80:
        return "excellent"
    elif score >= 70:
        return "very good"
    elif score >= 60:
        return "good"
    elif score >= 50:
        return "moderate"
    else:
        return "challenging"

def assess_relationship_potential(compatibility_score: float) -> str:
    """Assess overall relationship potential"""
    if compatibility_score >= 85:
        return "Exceptional potential for a deep, lasting connection"
    elif compatibility_score >= 75:
        return "Strong potential for a meaningful relationship"
    elif compatibility_score >= 65:
        return "Good potential with effort and understanding"
    elif compatibility_score >= 50:
        return "Moderate potential, may require significant compromise"
    else:
        return "Limited compatibility, significant challenges likely"

async def identify_growth_opportunities(user1: User, user2: User, ai_service: PrivacyFirstMatchingAI) -> List[str]:
    """Identify mutual growth opportunities"""
    opportunities = [
        "Exploring shared values and life philosophies together",
        "Learning from each other's different perspectives",
        "Supporting each other's personal development goals"
    ]
    
    # Add specific opportunities based on profiles
    interests1 = set(user1.profile.interests or [])
    interests2 = set(user2.profile.interests or [])
    common_interests = interests1.intersection(interests2)
    
    if common_interests:
        opportunities.append(f"Deepening connection through shared interest in {list(common_interests)[0]}")
    
    return opportunities

async def identify_potential_challenges(user1: User, user2: User, ai_service: PrivacyFirstMatchingAI) -> List[str]:
    """Identify potential relationship challenges"""
    challenges = []
    
    # Analyze personality differences
    traits1 = user1.profile.personality_traits or {}
    traits2 = user2.profile.personality_traits or {}
    
    if 'introverted' in str(traits1).lower() and 'extroverted' in str(traits2).lower():
        challenges.append("Balancing social energy needs (introvert/extrovert dynamic)")
    
    if 'spontaneous' in str(traits1).lower() and 'organized' in str(traits2).lower():
        challenges.append("Coordinating different approaches to planning and spontaneity")
    
    # Generic challenges based on compatibility
    challenges.extend([
        "Maintaining individual identity while building connection",
        "Navigating different communication styles during conflicts"
    ])
    
    return challenges[:3]  # Return top 3 challenges

async def recommend_connection_activities(user1: User, user2: User, ai_service: PrivacyFirstMatchingAI) -> List[str]:
    """Recommend activities for building connection"""
    activities = []
    
    # Based on common interests
    interests1 = set(user1.profile.interests or [])
    interests2 = set(user2.profile.interests or [])
    common_interests = interests1.intersection(interests2)
    
    interest_activities = {
        'cooking': 'Try cooking a new cuisine together',
        'reading': 'Start a two-person book club',
        'hiking': 'Explore new hiking trails together',
        'art': 'Visit art galleries or create art together',
        'music': 'Attend concerts or learn an instrument together',
        'travel': 'Plan a weekend getaway to a new place'
    }
    
    for interest in common_interests:
        for activity_interest, activity in interest_activities.items():
            if activity_interest in interest.lower():
                activities.append(activity)
                break
    
    # Generic connection activities
    activities.extend([
        "Share your life stories over a long dinner",
        "Take turns teaching each other something new",
        "Volunteer together for a cause you both care about"
    ])
    
    return activities[:3]  # Return top 3 activities

# Background task functions

async def log_compatibility_analysis(user_id: int, user1_id: int, user2_id: int, score: float, processing_time: float):
    """Log compatibility analysis for analytics"""
    # Implementation would log to analytics database
    logger.info(f"Compatibility analysis: user {user_id} analyzed {user1_id}-{user2_id}, score: {score}, time: {processing_time}ms")

async def log_batch_analysis(user_id: int, candidates_count: int, matches_count: int, processing_time: float):
    """Log batch analysis for analytics"""
    logger.info(f"Batch analysis: user {user_id} analyzed {candidates_count} candidates, {matches_count} matches, time: {processing_time}ms")

async def log_deep_analysis_usage(user_id: int, user1_id: int, user2_id: int, score: float):
    """Log deep analysis usage for premium features tracking"""
    logger.info(f"Deep analysis: user {user_id} performed deep analysis {user1_id}-{user2_id}, score: {score}")