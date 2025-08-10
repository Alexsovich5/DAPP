"""
Analytics API Router - Phase 4 User Analytics and Engagement Tracking
Comprehensive analytics endpoints for user insights, system metrics, and engagement tracking
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.soul_analytics import AnalyticsEventType
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analytics"])


@router.post("/events/track")
async def track_user_event(
    event_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track a user engagement event"""
    try:
        event_type = AnalyticsEventType(event_data.get("eventType"))
        
        success = await analytics_service.track_user_event(
            user_id=current_user.id,
            event_type=event_type,
            event_data=event_data.get("data", {}),
            db=db,
            session_id=event_data.get("sessionId"),
            connection_id=event_data.get("connectionId")
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to track event")
        
        return {"success": True, "message": "Event tracked successfully"}
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event type")
    except Exception as e:
        logger.error(f"Error tracking user event: {str(e)}")
        raise HTTPException(status_code=500, detail="Error tracking event")


@router.get("/user/engagement-score")
async def get_user_engagement_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's engagement score"""
    try:
        engagement_score = await analytics_service.calculate_user_engagement_score(
            current_user.id, db
        )
        
        return {
            "userId": current_user.id,
            "engagementScore": engagement_score,
            "level": analytics_service._get_engagement_level(engagement_score),
            "calculatedAt": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error calculating engagement score: {str(e)}")
        raise HTTPException(status_code=500, detail="Error calculating engagement score")


@router.get("/user/insights")
async def get_user_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized insights for current user"""
    try:
        insights = await analytics_service.generate_user_insights(current_user.id, db)
        
        return {
            "userId": current_user.id,
            "insights": insights,
            "generatedAt": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error generating user insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating insights")


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard summary"""
    try:
        # Get user-specific insights
        user_insights = await analytics_service.generate_user_insights(current_user.id, db)
        user_engagement = await analytics_service.calculate_user_engagement_score(current_user.id, db)
        
        # Get system metrics
        engagement_metrics = await analytics_service.get_engagement_metrics(db)
        connection_metrics = await analytics_service.get_connection_metrics(db)
        
        return {
            "period": f"Last {days} days",
            "user": {
                "engagementScore": user_engagement,
                "insights": user_insights
            },
            "system": {
                "activeUsers": {
                    "daily": engagement_metrics.daily_active_users,
                    "weekly": engagement_metrics.weekly_active_users,
                    "monthly": engagement_metrics.monthly_active_users
                },
                "connections": {
                    "total": connection_metrics.total_connections,
                    "active": connection_metrics.active_connections,
                    "successRate": connection_metrics.connection_success_rate
                }
            },
            "generatedAt": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting dashboard summary")


@router.get("/metrics/engagement")
async def get_engagement_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall engagement metrics"""
    try:
        metrics = await analytics_service.get_engagement_metrics(db)
        
        return {
            "activeUsers": {
                "daily": metrics.daily_active_users,
                "weekly": metrics.weekly_active_users,
                "monthly": metrics.monthly_active_users
            },
            "sessions": {
                "total": metrics.total_sessions,
                "averageDuration": metrics.average_session_duration,
                "bounceRate": metrics.bounce_rate
            },
            "retention": metrics.retention_rates,
            "calculatedAt": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting engagement metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting engagement metrics")


@router.get("/metrics/connections")
async def get_connection_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get soul connection metrics"""
    try:
        metrics = await analytics_service.get_connection_metrics(db)
        
        return {
            "connections": {
                "total": metrics.total_connections,
                "active": metrics.active_connections,
                "successRate": metrics.connection_success_rate
            },
            "revelations": {
                "completed": metrics.completed_revelations,
                "photoReveals": metrics.photo_reveals
            },
            "quality": {
                "averageCompatibility": metrics.average_compatibility_score,
                "averageTimeToFirstMessage": metrics.average_time_to_first_message
            },
            "calculatedAt": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting connection metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting connection metrics")


@router.get("/metrics/system-health")
async def get_system_health_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system health and performance metrics"""
    try:
        health_metrics = await analytics_service.get_system_health_metrics(db)
        
        return {
            "performance": {
                "apiResponseTimes": health_metrics.api_response_times,
                "databasePerformance": health_metrics.database_performance,
                "websocketConnections": health_metrics.websocket_connections
            },
            "reliability": {
                "errorRates": health_metrics.error_rates
            },
            "satisfaction": health_metrics.user_satisfaction_scores,
            "calculatedAt": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting system health metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting system health metrics")


@router.post("/events/batch")
async def track_batch_events(
    events_data: Dict[str, List[Dict[str, Any]]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track multiple events in batch for performance"""
    try:
        events = events_data.get("events", [])
        successful_tracks = 0
        
        for event_data in events[:100]:  # Limit to 100 events per batch
            try:
                event_type = AnalyticsEventType(event_data.get("eventType"))
                
                success = await analytics_service.track_user_event(
                    user_id=current_user.id,
                    event_type=event_type,
                    event_data=event_data.get("data", {}),
                    db=db,
                    session_id=event_data.get("sessionId"),
                    connection_id=event_data.get("connectionId")
                )
                
                if success:
                    successful_tracks += 1
                    
            except Exception as e:
                logger.warning(f"Failed to track individual event: {str(e)}")
                continue
        
        return {
            "success": True,
            "totalEvents": len(events),
            "successfulTracks": successful_tracks,
            "message": f"Successfully tracked {successful_tracks} out of {len(events)} events"
        }
    
    except Exception as e:
        logger.error(f"Error tracking batch events: {str(e)}")
        raise HTTPException(status_code=500, detail="Error tracking batch events")


@router.get("/realtime/active-users")
async def get_realtime_active_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time active user count"""
    try:
        # Get users active in the last 5 minutes
        recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
        
        active_count = db.query(UserEngagementAnalytics.user_id).filter(
            UserEngagementAnalytics.created_at >= recent_cutoff
        ).distinct().count()
        
        return {
            "activeUsers": active_count,
            "timestamp": datetime.utcnow().isoformat(),
            "period": "Last 5 minutes"
        }
    
    except Exception as e:
        logger.error(f"Error getting real-time active users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting active users")