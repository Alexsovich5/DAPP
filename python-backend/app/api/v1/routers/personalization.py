"""
Phase 6: Advanced Personalization & Content Intelligence API Routes
Expose AI-powered personalization and content generation functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.personalization_models import (
    UserPersonalizationProfile, PersonalizedContent, ContentFeedback,
    AlgorithmOptimization, ConversationFlowAnalytics, ContentType
)
from app.services.personalization_service import personalization_engine
from app.schemas.personalization_schemas import (
    PersonalizationProfileResponse, ConversationStarterRequest, ConversationStarterResponse,
    RevelationPromptRequest, RevelationPromptResponse, SmartReplyRequest, SmartReplyResponse,
    UIPersonalizationRequest, UIPersonalizationResponse, ContentFeedbackRequest,
    ContentFeedbackResponse, AlgorithmOptimizationRequest, AlgorithmOptimizationResponse
)

router = APIRouter(prefix="/personalization", tags=["personalization"])
logger = logging.getLogger(__name__)

@router.get("/profile", response_model=PersonalizationProfileResponse)
async def get_personalization_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get or create user's personalization profile"""
    try:
        profile = await personalization_engine.get_or_create_personalization_profile(
            current_user.id, db
        )
        return PersonalizationProfileResponse.from_orm(profile)
    except Exception as e:
        logger.error(f"Error retrieving personalization profile for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve personalization profile"
        )

@router.post("/conversation-starters", response_model=List[ConversationStarterResponse])
async def generate_conversation_starters(
    request: ConversationStarterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI-powered conversation starters for a specific user"""
    try:
        # Validate target user exists
        target_user = db.query(User).filter(User.id == request.target_user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        
        # Generate personalized conversation starters
        starters = await personalization_engine.generate_conversation_starters(
            user_id=current_user.id,
            target_user_id=request.target_user_id,
            count=request.count,
            db=db
        )
        
        return [ConversationStarterResponse(**starter) for starter in starters]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating conversation starters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate conversation starters"
        )

@router.post("/revelation-prompts", response_model=List[RevelationPromptResponse])
async def generate_revelation_prompts(
    request: RevelationPromptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate adaptive revelation prompts based on user behavior and connection progress"""
    try:
        prompts = await personalization_engine.generate_revelation_prompts(
            user_id=current_user.id,
            revelation_day=request.revelation_day,
            connection_context=request.connection_context,
            db=db
        )
        
        return [RevelationPromptResponse(**prompt) for prompt in prompts]
        
    except Exception as e:
        logger.error(f"Error generating revelation prompts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate revelation prompts"
        )

@router.post("/smart-replies", response_model=List[SmartReplyResponse])
async def generate_smart_replies(
    request: SmartReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate intelligent reply suggestions based on conversation context"""
    try:
        replies = await personalization_engine.generate_smart_replies(
            user_id=current_user.id,
            conversation_context=request.conversation_context,
            last_message=request.last_message,
            db=db
        )
        
        return [SmartReplyResponse(**reply) for reply in replies]
        
    except Exception as e:
        logger.error(f"Error generating smart replies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate smart replies"
        )

@router.post("/ui-personalization", response_model=UIPersonalizationResponse)
async def generate_ui_personalization(
    request: UIPersonalizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate UI/UX personalizations based on user behavior patterns"""
    try:
        personalizations = await personalization_engine.personalize_ui_experience(
            user_id=current_user.id,
            current_context=request.current_context,
            db=db
        )
        
        return UIPersonalizationResponse(**personalizations)
        
    except Exception as e:
        logger.error(f"Error generating UI personalization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate UI personalization"
        )

@router.post("/feedback", response_model=ContentFeedbackResponse)
async def submit_content_feedback(
    request: ContentFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit user feedback on personalized content for optimization"""
    try:
        success = await personalization_engine.record_content_feedback(
            user_id=current_user.id,
            content_id=request.content_id,
            feedback_data=request.feedback_data,
            db=db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record feedback"
            )
        
        return ContentFeedbackResponse(
            success=True,
            message="Feedback recorded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording content feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback"
        )

@router.post("/optimize-algorithm", response_model=AlgorithmOptimizationResponse)
async def optimize_algorithm_performance(
    request: AlgorithmOptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger real-time algorithm optimization (admin/premium feature)"""
    try:
        # Note: In production, this would be restricted to admin users or premium features
        optimization_result = await personalization_engine.optimize_algorithm_performance(
            optimization_type=request.optimization_type,
            target_metrics=request.target_metrics,
            db=db
        )
        
        if "error" in optimization_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=optimization_result["error"]
            )
        
        return AlgorithmOptimizationResponse(**optimization_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing algorithm: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize algorithm"
        )

@router.get("/content/{content_id}/performance")
async def get_content_performance(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics for specific personalized content"""
    try:
        content = db.query(PersonalizedContent).filter(
            PersonalizedContent.id == content_id,
            PersonalizedContent.user_profile_id == current_user.personalization_profile.id
        ).first()
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        return {
            "content_id": content.id,
            "content_type": content.content_type,
            "presentation_count": content.presentation_count,
            "engagement_count": content.engagement_count,
            "success_count": content.success_count,
            "feedback_score": content.feedback_score,
            "effectiveness_score": content.calculate_effectiveness_score(),
            "should_retire": content.should_retire_content(),
            "ai_confidence_score": content.ai_confidence_score,
            "optimization_version": content.optimization_version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving content performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content performance"
        )

@router.get("/analytics/conversation-flow")
async def get_conversation_flow_analytics(
    connection_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation flow analytics for optimization insights"""
    try:
        query = db.query(ConversationFlowAnalytics).filter(
            ConversationFlowAnalytics.user_id == current_user.id
        )
        
        if connection_id:
            query = query.filter(ConversationFlowAnalytics.connection_id == connection_id)
        
        analytics = query.order_by(ConversationFlowAnalytics.analysis_date.desc()).limit(10).all()
        
        return {
            "analytics": [
                {
                    "id": a.id,
                    "connection_id": a.connection_id,
                    "conversation_stage": a.conversation_stage,
                    "message_count": a.message_count,
                    "average_response_time": a.average_response_time,
                    "engagement_score": a.engagement_score,
                    "emotional_connection_score": a.emotional_connection_score,
                    "analysis_date": a.analysis_date.isoformat(),
                    "successful_starters": a.successful_starters,
                    "optimal_timing_patterns": a.optimal_timing_patterns
                }
                for a in analytics
            ]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conversation flow analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation flow analytics"
        )

@router.get("/preferences")
async def get_personalization_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's personalization preferences for settings"""
    try:
        profile = await personalization_engine.get_or_create_personalization_profile(
            current_user.id, db
        )
        
        return {
            "communication_style": profile.preferred_communication_style,
            "conversation_pace": profile.conversation_pace_preference,
            "revelation_timing": profile.revelation_timing_preference,
            "content_depth": profile.content_depth_preference,
            "ui_complexity": profile.preferred_ui_complexity,
            "animation_preferences": profile.animation_preferences,
            "color_theme_preferences": profile.color_theme_preferences,
            "accessibility_preferences": profile.accessibility_preferences,
            "learning_rate": profile.adaptation_learning_rate,
            "personalization_effectiveness": profile.personalization_effectiveness
        }
        
    except Exception as e:
        logger.error(f"Error retrieving personalization preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve personalization preferences"
        )

@router.put("/preferences")
async def update_personalization_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's personalization preferences"""
    try:
        profile = await personalization_engine.get_or_create_personalization_profile(
            current_user.id, db
        )
        
        # Update allowed preference fields
        allowed_fields = {
            'preferred_communication_style', 'conversation_pace_preference',
            'revelation_timing_preference', 'content_depth_preference',
            'preferred_ui_complexity', 'animation_preferences',
            'color_theme_preferences', 'accessibility_preferences',
            'adaptation_learning_rate'
        }
        
        for field, value in preferences.items():
            if field in allowed_fields and hasattr(profile, field):
                setattr(profile, field, value)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Personalization preferences updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating personalization preferences: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update personalization preferences"
        )

@router.get("/optimization-history")
async def get_optimization_history(
    optimization_type: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get algorithm optimization history for analytics"""
    try:
        query = db.query(AlgorithmOptimization).filter(
            AlgorithmOptimization.is_active == True
        )
        
        if optimization_type:
            query = query.filter(AlgorithmOptimization.optimization_type == optimization_type)
        
        optimizations = query.order_by(
            AlgorithmOptimization.created_at.desc()
        ).limit(limit).all()
        
        return {
            "optimizations": [
                {
                    "id": opt.id,
                    "optimization_type": opt.optimization_type,
                    "algorithm_version": opt.algorithm_version,
                    "improvement_percentage": opt.improvement_percentage,
                    "statistical_significance": opt.statistical_significance,
                    "is_deployed": opt.is_deployed,
                    "deployment_percentage": opt.deployment_percentage,
                    "created_at": opt.created_at.isoformat(),
                    "target_metrics": opt.target_metrics,
                    "current_metrics": opt.current_metrics
                }
                for opt in optimizations
            ]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving optimization history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve optimization history"
        )