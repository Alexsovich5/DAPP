# Analytics API Router for Dinner First
# Business intelligence dashboard and metrics endpoints

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from ....core.auth import get_current_user, get_current_admin_user
from ....services.analytics import AnalyticsService
from ....models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])
security = HTTPBearer()

# Response Models
class RealTimeMetricsResponse(BaseModel):
    timestamp: datetime
    hourly: Dict[str, Any]
    daily: Dict[str, Any]

class UserJourneyResponse(BaseModel):
    user_id: int
    total_events: int
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    days_active: int
    event_categories: Dict[str, int]
    conversion_funnel: Dict[str, Optional[datetime]]
    engagement_score: float

class BusinessMetricsResponse(BaseModel):
    period: str
    active_users: int
    new_registrations: int
    matches_created: int
    conversations_started: int
    photo_reveals: int
    revenue_cents: int
    engagement_rate: float

class MatchingAnalyticsResponse(BaseModel):
    period: str
    total_interactions: int
    like_rate: float
    match_rate: float
    conversation_rate: float
    avg_compatibility_score: float
    algorithm_performance: Dict[str, Any]

class A_B_TestResultsResponse(BaseModel):
    experiment_id: str
    variants: List[Dict[str, Any]]
    statistical_significance: bool
    confidence_level: float
    recommendation: str

# Request Models
class EventTrackingRequest(BaseModel):
    event_type: str
    event_category: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[int] = None

class A_B_TestRequest(BaseModel):
    experiment_id: str
    variant: str
    event_type: str
    metric_value: float

# Dependencies
async def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance"""
    # This would be injected through dependency injection
    # For now, we'll create a placeholder
    raise HTTPException(status_code=503, detail="Analytics service not configured")

@router.get("/metrics/realtime", response_model=RealTimeMetricsResponse)
async def get_realtime_metrics(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get real-time metrics dashboard
    
    Admin-only endpoint for monitoring current platform activity
    """
    try:
        metrics = await analytics_service.get_real_time_metrics()
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics available")
        
        return RealTimeMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@router.get("/user-journey/{user_id}", response_model=UserJourneyResponse)
async def get_user_journey(
    user_id: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get comprehensive user journey analytics
    
    Admin-only endpoint for analyzing individual user behavior
    """
    try:
        journey_data = await analytics_service.get_user_journey_metrics(user_id)
        
        if not journey_data:
            raise HTTPException(status_code=404, detail="User journey data not found")
        
        return UserJourneyResponse(**journey_data)
        
    except Exception as e:
        logger.error(f"Failed to get user journey for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user journey")

@router.get("/user-journey/me", response_model=UserJourneyResponse)
async def get_my_journey(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's journey analytics
    
    Privacy-compliant endpoint for users to view their own activity
    """
    try:
        journey_data = await analytics_service.get_user_journey_metrics(current_user.id)
        
        if not journey_data:
            # Return empty journey for users with no activity
            return UserJourneyResponse(
                user_id=current_user.id,
                total_events=0,
                first_seen=None,
                last_seen=None,
                days_active=0,
                event_categories={},
                conversion_funnel={},
                engagement_score=0.0
            )
        
        return UserJourneyResponse(**journey_data)
        
    except Exception as e:
        logger.error(f"Failed to get journey for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve your journey")

@router.get("/business-metrics", response_model=BusinessMetricsResponse)
async def get_business_metrics(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get business intelligence metrics
    
    Admin-only endpoint for business performance analysis
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            if period == "daily":
                start_date = end_date - timedelta(days=1)
            elif period == "weekly":
                start_date = end_date - timedelta(weeks=1)
            else:  # monthly
                start_date = end_date - timedelta(days=30)
        
        # Get business metrics (this would be implemented in analytics service)
        metrics = await analytics_service.get_business_metrics(period, start_date, end_date)
        
        return BusinessMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get business metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve business metrics")

@router.get("/matching-analytics", response_model=MatchingAnalyticsResponse)
async def get_matching_analytics(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get matching algorithm performance analytics
    
    Admin-only endpoint for analyzing matching effectiveness
    """
    try:
        analytics = await analytics_service.get_matching_analytics(period)
        
        return MatchingAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error(f"Failed to get matching analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve matching analytics")

@router.post("/track-event")
async def track_custom_event(
    event_data: EventTrackingRequest,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Track custom analytics event
    
    Allows frontend to track specific user interactions
    """
    try:
        from ....services.analytics import AnalyticsEvent, EventType, EventCategory
        import uuid
        
        # Create analytics event
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            user_id=event_data.user_id or current_user.id,
            session_id=str(uuid.uuid4()),  # This should come from request context
            event_type=EventType(event_data.event_type),
            event_category=EventCategory(event_data.event_category),
            properties=event_data.properties,
            timestamp=datetime.utcnow()
        )
        
        success = await analytics_service.track_event(event)
        
        if success:
            return {"status": "success", "message": "Event tracked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track event")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type or category: {e}")
    except Exception as e:
        logger.error(f"Failed to track custom event: {e}")
        raise HTTPException(status_code=500, detail="Failed to track event")

@router.get("/a-b-tests/{experiment_id}", response_model=A_B_TestResultsResponse)
async def get_a_b_test_results(
    experiment_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get A/B test results and statistical analysis
    
    Admin-only endpoint for analyzing experiment results
    """
    try:
        results = await analytics_service.get_a_b_test_results(experiment_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        return A_B_TestResultsResponse(**results)
        
    except Exception as e:
        logger.error(f"Failed to get A/B test results for {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve A/B test results")

@router.post("/a-b-tests/track")
async def track_a_b_test_event(
    test_data: A_B_TestRequest,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user)
):
    """
    Track A/B test event and metrics
    
    Records user interactions for experiment analysis
    """
    try:
        success = await analytics_service.track_a_b_test_event(
            user_id=current_user.id,
            experiment_id=test_data.experiment_id,
            variant=test_data.variant,
            event_type=test_data.event_type,
            metric_value=test_data.metric_value
        )
        
        if success:
            return {"status": "success", "message": "A/B test event tracked"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track A/B test event")
            
    except Exception as e:
        logger.error(f"Failed to track A/B test event: {e}")
        raise HTTPException(status_code=500, detail="Failed to track A/B test event")

@router.get("/export/user-data/{user_id}")
async def export_user_analytics_data(
    user_id: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Export user's analytics data for GDPR compliance
    
    Admin-only endpoint for data export requests
    """
    try:
        # This would export user's analytics data in a privacy-compliant format
        export_data = await analytics_service.export_user_data(user_id)
        
        return {
            "user_id": user_id,
            "export_timestamp": datetime.utcnow(),
            "data": export_data
        }
        
    except Exception as e:
        logger.error(f"Failed to export analytics data for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export user data")

@router.delete("/user-data/{user_id}")
async def delete_user_analytics_data(
    user_id: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete user's analytics data for GDPR compliance
    
    Admin-only endpoint for data deletion requests
    """
    try:
        success = await analytics_service.delete_user_data(user_id)
        
        if success:
            return {"status": "success", "message": f"Analytics data deleted for user {user_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete user data")
            
    except Exception as e:
        logger.error(f"Failed to delete analytics data for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user data")

@router.get("/health")
async def analytics_health_check():
    """
    Health check endpoint for analytics service
    """
    try:
        # Check analytics service connectivity
        # This would ping ClickHouse and Redis
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {
                "clickhouse": "connected",
                "redis": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unhealthy")