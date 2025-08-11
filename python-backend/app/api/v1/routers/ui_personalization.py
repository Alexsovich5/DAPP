"""
Phase 6: User Behavior-Based UI Personalization API
API endpoints for dynamic UI adaptation based on user interaction patterns
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.ui_personalization_models import (
    UserUIProfile, UIInteractionLog, UIPersonalizationEvent, UIPersonalizationInsight
)
from app.services.ui_personalization_service import ui_personalization_engine
from app.schemas.ui_personalization_schemas import (
    UIPersonalizationResponse, InteractionTrackingRequest,
    UIProfileResponse, PersonalizationInsightResponse,
    UIAdaptationRequest, UIAnalyticsResponse
)

router = APIRouter(prefix="/ui-personalization", tags=["ui-personalization"])
logger = logging.getLogger(__name__)

@router.get("/profile", response_model=UIProfileResponse)
async def get_ui_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's UI personalization profile"""
    try:
        ui_profile = await ui_personalization_engine.get_or_create_ui_profile(
            current_user.id, db
        )
        
        return UIProfileResponse(
            id=ui_profile.id,
            user_id=ui_profile.user_id,
            primary_device_type=ui_profile.primary_device_type,
            preferred_theme=ui_profile.preferred_theme,
            font_size_preference=ui_profile.font_size_preference,
            animation_preference=ui_profile.animation_preference,
            layout_density=ui_profile.layout_density,
            interaction_speed=ui_profile.interaction_speed,
            navigation_pattern=ui_profile.navigation_pattern,
            personalization_score=ui_profile.personalization_score,
            accessibility_settings={
                "screen_reader_enabled": ui_profile.screen_reader_enabled,
                "keyboard_navigation_primary": ui_profile.keyboard_navigation_primary,
                "high_contrast_enabled": ui_profile.high_contrast_enabled,
                "reduce_motion_enabled": ui_profile.reduce_motion_enabled
            },
            current_preferences=ui_profile.get_current_preferences(),
            last_updated=ui_profile.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error retrieving UI profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve UI profile"
        )

@router.post("/track-interaction")
async def track_user_interaction(
    request: InteractionTrackingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track user interaction for behavioral analysis"""
    try:
        # Process interaction tracking in background for better performance
        background_tasks.add_task(
            ui_personalization_engine.track_user_interaction,
            current_user.id,
            request.dict(),
            db
        )
        
        return {
            "success": True,
            "message": "Interaction tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Error tracking interaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track interaction"
        )

@router.post("/generate-adaptations", response_model=UIPersonalizationResponse)
async def generate_ui_personalizations(
    request: UIAdaptationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate UI personalizations based on user behavior"""
    try:
        personalizations = await ui_personalization_engine.generate_ui_personalizations(
            user_id=current_user.id,
            current_context=request.current_context,
            db=db
        )
        
        return UIPersonalizationResponse(
            user_id=current_user.id,
            personalizations=personalizations,
            generated_at=datetime.utcnow(),
            confidence_score=personalizations.get("confidence", 0.7),
            applied_strategies=list(personalizations.keys())
        )
        
    except Exception as e:
        logger.error(f"Error generating UI personalizations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate UI personalizations"
        )

@router.get("/insights", response_model=List[PersonalizationInsightResponse])
async def get_personalization_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, le=50)
):
    """Get AI-generated insights about user's UI preferences and behaviors"""
    try:
        ui_profile = await ui_personalization_engine.get_or_create_ui_profile(
            current_user.id, db
        )
        
        # Get recent insights
        insights = db.query(UIPersonalizationInsight).filter(
            UIPersonalizationInsight.ui_profile_id == ui_profile.id
        ).order_by(
            UIPersonalizationInsight.generated_at.desc()
        ).limit(limit).all()
        
        # If no insights exist, generate some basic ones
        if not insights:
            insights = await generate_initial_insights(ui_profile, db)
        
        return [
            PersonalizationInsightResponse(
                id=insight.id,
                insight_type=insight.insight_type,
                category=insight.insight_category,
                title=insight.title,
                description=insight.description,
                recommended_action=insight.recommended_action,
                priority=insight.implementation_priority,
                confidence=insight.confidence_score,
                impact_estimate=insight.expected_impact,
                generated_at=insight.generated_at,
                implemented=insight.acted_upon
            )
            for insight in insights
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving personalization insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve personalization insights"
        )

@router.get("/analytics", response_model=UIAnalyticsResponse)
async def get_ui_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=90)
):
    """Get UI interaction analytics and behavioral patterns"""
    try:
        ui_profile = await ui_personalization_engine.get_or_create_ui_profile(
            current_user.id, db
        )
        
        # Get interaction logs for the specified period
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        interactions = db.query(UIInteractionLog).filter(
            and_(
                UIInteractionLog.ui_profile_id == ui_profile.id,
                UIInteractionLog.interaction_timestamp >= start_date
            )
        ).all()
        
        # Analyze behavior patterns
        behavior_analysis = await ui_personalization_engine._analyze_user_behavior(
            ui_profile, db
        )
        
        # Calculate analytics metrics
        total_interactions = len(interactions)
        unique_sessions = len(set(i.session_id for i in interactions if i.session_id))
        error_rate = sum(1 for i in interactions if i.error_occurred) / max(total_interactions, 1)
        
        # Device usage distribution
        device_usage = {}
        for interaction in interactions:
            device = interaction.device_type or "unknown"
            device_usage[device] = device_usage.get(device, 0) + 1
        
        # Page visit distribution
        page_visits = {}
        for interaction in interactions:
            page = interaction.page_route or "unknown"
            page_visits[page] = page_visits.get(page, 0) + 1
        
        return UIAnalyticsResponse(
            user_id=current_user.id,
            analysis_period_days=days,
            total_interactions=total_interactions,
            unique_sessions=unique_sessions,
            error_rate=error_rate,
            personalization_score=ui_profile.personalization_score,
            behavior_patterns=behavior_analysis,
            device_usage_distribution=device_usage,
            page_interaction_distribution=page_visits,
            interaction_efficiency=behavior_analysis.get("efficiency_metrics", {}),
            recommendations=await generate_analytics_recommendations(behavior_analysis)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving UI analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve UI analytics"
        )

@router.put("/preferences")
async def update_ui_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's UI preferences manually"""
    try:
        ui_profile = await ui_personalization_engine.get_or_create_ui_profile(
            current_user.id, db
        )
        
        # Update allowed preference fields
        allowed_fields = {
            'preferred_theme', 'font_size_preference', 'animation_preference',
            'layout_density', 'color_contrast_preference', 'haptic_feedback_intensity',
            'screen_reader_enabled', 'keyboard_navigation_primary',
            'high_contrast_enabled', 'reduce_motion_enabled'
        }
        
        updated_fields = []
        for field, value in preferences.items():
            if field in allowed_fields and hasattr(ui_profile, field):
                old_value = getattr(ui_profile, field)
                setattr(ui_profile, field, value)
                updated_fields.append({
                    "field": field,
                    "old_value": old_value,
                    "new_value": value
                })
        
        # Record the preference change as a personalization event
        if updated_fields:
            personalization_event = UIPersonalizationEvent(
                ui_profile_id=ui_profile.id,
                personalization_type="manual_preference_update",
                strategy_used="user_request",
                previous_settings={f["field"]: f["old_value"] for f in updated_fields},
                new_settings={f["field"]: f["new_value"] for f in updated_fields},
                change_reason="user_manual_update",
                trigger_event="preference_update_request"
            )
            db.add(personalization_event)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Updated {len(updated_fields)} preferences",
            "updated_fields": updated_fields
        }
        
    except Exception as e:
        logger.error(f"Error updating UI preferences: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update UI preferences"
        )

@router.post("/feedback")
async def submit_personalization_feedback(
    feedback: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback on UI personalization effectiveness"""
    try:
        ui_profile = await ui_personalization_engine.get_or_create_ui_profile(
            current_user.id, db
        )
        
        # Record feedback
        satisfaction_score = feedback.get("satisfaction_score", 0.5)  # 0.0 to 1.0
        feedback_text = feedback.get("comments", "")
        specific_feature = feedback.get("feature", "general")
        
        # Update personalization score based on feedback
        ui_profile.update_personalization_score(1, satisfaction_score)
        
        # Create insight if feedback indicates issues
        if satisfaction_score < 0.6:
            insight = UIPersonalizationInsight(
                ui_profile_id=ui_profile.id,
                insight_type="feedback_driven",
                insight_category="usability",
                title="User Satisfaction Below Threshold",
                description=f"User provided feedback indicating dissatisfaction with {specific_feature}",
                recommended_action="Review and adjust personalization strategies",
                implementation_priority="medium",
                confidence_score=0.8,
                expected_impact=0.3,
                supporting_data={
                    "satisfaction_score": satisfaction_score,
                    "feedback_text": feedback_text,
                    "feature": specific_feature
                }
            )
            db.add(insight)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Feedback recorded successfully",
            "new_personalization_score": ui_profile.personalization_score
        }
        
    except Exception as e:
        logger.error(f"Error recording personalization feedback: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback"
        )

@router.get("/ab-tests")
async def get_active_ab_tests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active A/B tests for UI personalization"""
    try:
        ui_profile = await ui_personalization_engine.get_or_create_ui_profile(
            current_user.id, db
        )
        
        # Get active A/B test participations
        from app.models.ui_personalization_models import UIABTestParticipation
        active_tests = db.query(UIABTestParticipation).filter(
            and_(
                UIABTestParticipation.ui_profile_id == ui_profile.id,
                UIABTestParticipation.is_active == True
            )
        ).all()
        
        return {
            "active_tests": [
                {
                    "id": test.id,
                    "test_name": test.test_name,
                    "variant": test.test_variant,
                    "category": test.test_category,
                    "enrolled_at": test.enrolled_at,
                    "session_count": test.session_count
                }
                for test in active_tests
            ]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving A/B tests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B tests"
        )

@router.post("/real-time-adaptation")
async def trigger_real_time_adaptation(
    context: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger real-time UI adaptation based on current context"""
    try:
        ui_profile = await ui_personalization_engine.get_or_create_ui_profile(
            current_user.id, db
        )
        
        # Generate immediate adaptations
        adaptations = await ui_personalization_engine.generate_ui_personalizations(
            user_id=current_user.id,
            current_context=context,
            db=db
        )
        
        # Filter for high-confidence, immediate adaptations
        immediate_adaptations = {}
        for category, adaptation_data in adaptations.items():
            if isinstance(adaptation_data, dict):
                confidence = adaptation_data.get("confidence", 0.0)
                if confidence >= ui_personalization_engine.adaptation_thresholds["confidence_threshold"]:
                    immediate_adaptations[category] = adaptation_data
        
        return {
            "success": True,
            "adaptations": immediate_adaptations,
            "adaptation_count": len(immediate_adaptations),
            "message": "Real-time adaptations generated"
        }
        
    except Exception as e:
        logger.error(f"Error triggering real-time adaptation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger real-time adaptation"
        )

# Helper functions

async def generate_initial_insights(ui_profile: UserUIProfile, db: Session) -> List[UIPersonalizationInsight]:
    """Generate initial insights for new users"""
    insights = []
    
    # Welcome insight
    welcome_insight = UIPersonalizationInsight(
        ui_profile_id=ui_profile.id,
        insight_type="welcome",
        insight_category="onboarding",
        title="Welcome to Personalized UI",
        description="Your interface will adapt based on how you interact with the app",
        recommended_action="Use the app naturally and provide feedback",
        implementation_priority="low",
        confidence_score=1.0,
        expected_impact=0.2
    )
    insights.append(welcome_insight)
    db.add(welcome_insight)
    
    # Device-specific insight
    if ui_profile.primary_device_type == "mobile":
        mobile_insight = UIPersonalizationInsight(
            ui_profile_id=ui_profile.id,
            insight_type="device_optimization",
            insight_category="usability",
            title="Mobile-Optimized Experience",
            description="Your interface is optimized for mobile interactions",
            recommended_action="Try swipe gestures and thumb-friendly navigation",
            implementation_priority="medium",
            confidence_score=0.8,
            expected_impact=0.3
        )
        insights.append(mobile_insight)
        db.add(mobile_insight)
    
    db.commit()
    return insights

async def generate_analytics_recommendations(behavior_analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on behavior analysis"""
    recommendations = []
    
    # Performance recommendations
    if behavior_analysis.get("performance_sensitivity", {}).get("sensitive_to_slow_loading"):
        recommendations.append("Enable performance optimizations to improve loading times")
    
    # Accessibility recommendations
    accessibility = behavior_analysis.get("accessibility_needs", {})
    if accessibility.get("needs_high_contrast"):
        recommendations.append("Consider enabling high contrast mode for better visibility")
    
    # Interaction recommendations
    interaction_types = behavior_analysis.get("interaction_types", {})
    if interaction_types.get("primary_style") == "keyboard_heavy":
        recommendations.append("Enable keyboard shortcuts for faster navigation")
    
    # Engagement recommendations
    if behavior_analysis.get("engagement_patterns", {}).get("low_engagement"):
        recommendations.append("Try enabling micro-interactions to improve engagement")
    
    return recommendations

# Import required modules
from datetime import datetime
from sqlalchemy import and_