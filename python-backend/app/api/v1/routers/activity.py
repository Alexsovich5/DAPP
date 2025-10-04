"""
Activity Tracking API Endpoints - Sprint 4
Real-time user activity tracking and presence management
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.error_handlers import (
    ActivityTrackingError,
    DinnerAppException,
    ValidationError,
    create_error_response,
)
from app.core.logging_config import get_logger, log_error, log_performance
from app.models.user import User
from app.models.user_activity_tracking import (
    ActivityContext,
    ActivityInsights,
    ActivityType,
    DeviceCapabilities,
)
from app.services.activity_tracking_service import activity_tracker
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

logger = get_logger("app.api.v1.routers.activity")

router = APIRouter()


# Pydantic models for request/response
class StartSessionRequest(BaseModel):
    session_id: str
    device_type: Optional[str] = "unknown"
    browser_info: Optional[Dict] = {}
    screen_resolution: Optional[str] = None
    device_capabilities: Optional[List[str]] = []
    timezone: Optional[str] = None
    network_type: Optional[str] = "unknown"

    @validator("session_id")
    def validate_session_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Session ID cannot be empty")
        if len(v) > 255:
            raise ValueError("Session ID too long (max 255 characters)")
        return v.strip()

    @validator("device_capabilities")
    def validate_device_capabilities(cls, v):
        if not v:
            return []
        valid_capabilities = [cap.value for cap in DeviceCapabilities]
        invalid_caps = [cap for cap in v if cap not in valid_capabilities]
        if invalid_caps:
            raise ValueError(f"Invalid device capabilities: {invalid_caps}")
        return v


class LogActivityRequest(BaseModel):
    session_id: str
    activity_type: str
    context: Optional[str] = None
    activity_data: Optional[Dict] = None
    target_user_id: Optional[int] = None
    connection_id: Optional[int] = None

    @validator("session_id")
    def validate_session_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Session ID cannot be empty")
        return v.strip()

    @validator("activity_type")
    def validate_activity_type(cls, v):
        try:
            ActivityType(v)
        except ValueError:
            valid_types = [t.value for t in ActivityType]
            raise ValueError(f"Invalid activity type. Valid options: {valid_types}")
        return v

    @validator("context")
    def validate_context(cls, v):
        if v is None:
            return v
        try:
            ActivityContext(v)
        except ValueError:
            valid_contexts = [c.value for c in ActivityContext]
            raise ValueError(
                f"Invalid activity context. Valid options: {valid_contexts}"
            )
        return v

    @validator("target_user_id", "connection_id")
    def validate_positive_ids(cls, v):
        if v is not None and v <= 0:
            raise ValueError("IDs must be positive integers")
        return v


class ActivityResponse(BaseModel):
    status: str
    activity: str
    context: Optional[str]
    display_status: str
    status_emoji: Optional[str]
    activity_started_at: Optional[str]
    activity_duration: Optional[float]
    active_connection_id: Optional[int]
    connection_activity: Optional[str]
    recent_activities: List[Dict]
    interactions_last_hour: int


@router.post(
    "/sessions/start",
    summary="Start Activity Tracking Session",
    description="Initialize a new user activity tracking session with device information",
    response_description="Activity session confirmation with tracking details",
    tags=["Activity Tracking"],
)
async def start_activity_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    http_request: Request = None,
):
    """
    Start a new activity tracking session for the current user.

    Initializes comprehensive user activity tracking with device capabilities,
    session management, and real-time presence monitoring.

    **Request Body:**
    - `session_id`: Unique identifier for this activity session
    - `device_type`: Device type (mobile, desktop, tablet, etc.)
    - `browser_info`: Browser and version information
    - `screen_resolution`: Display resolution for UI optimization
    - `device_capabilities`: Array of device capabilities (camera, microphone, etc.)
    - `timezone`: User's timezone for activity timing

    **Features Enabled:**
    - Real-time presence tracking
    - Activity pattern analysis
    - Device-optimized experience
    - Session continuity management
    - Performance monitoring
    - Engagement analytics

    **Response:**
    - `session_id`: Confirmed session identifier
    - `tracking_enabled`: Whether tracking is active
    - `capabilities_detected`: Detected device capabilities
    - `presence_status`: Initial presence status
    - `recommendations`: Personalized activity suggestions

    **Use Cases:**
    - User login activity tracking
    - Device capability detection
    - Personalized experience initialization
    - Real-time presence management
    - Session continuity across devices
    """
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())

    # Enhanced logging context
    context = {
        "request_id": request_id,
        "user_id": current_user.id,
        "session_id": request.session_id,
        "endpoint": "start_activity_session",
    }

    logger.info("Starting activity session request", extra=context)

    try:
        # Validate device capabilities (already validated by Pydantic, but double-check)
        valid_capabilities = [cap.value for cap in DeviceCapabilities]
        filtered_capabilities = [
            cap
            for cap in (request.device_capabilities or [])
            if cap in valid_capabilities
        ]

        device_info = {
            "device_type": request.device_type,
            "browser_info": request.browser_info or {},
            "screen_resolution": request.screen_resolution,
            "capabilities": filtered_capabilities,
            "timezone": request.timezone,
            "network_type": request.network_type,
        }

        # Start activity session with enhanced error handling
        success = await activity_tracker.start_activity_session(
            user_id=current_user.id,
            session_id=request.session_id,
            device_info=device_info,
            db=db,
        )

        # Calculate and log performance
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        log_performance(logger, "start_activity_session", duration_ms, context=context)

        if success:
            logger.info(
                "Activity session started successfully",
                extra={**context, "duration_ms": duration_ms},
            )

            return {
                "success": True,
                "message": "Activity session started successfully",
                "session_id": request.session_id,
                "request_id": request_id,
            }
        else:
            raise ActivityTrackingError(
                "Activity session creation failed",
                details=context,
                user_message="Unable to start activity session. Please try again.",
            )

    except DinnerAppException as e:
        # Our custom exceptions - log and return structured response
        log_error(
            logger,
            e,
            context=context,
            error_type="activity_session_start_error",
        )
        return await create_error_response(e, request_id)

    except ValueError as e:
        # Validation errors
        validation_error = ValidationError(
            f"Invalid request data: {str(e)}",
            details=context,
            user_message="Please check your input and try again.",
        )
        log_error(
            logger,
            validation_error,
            context=context,
            error_type="validation_error",
        )
        return await create_error_response(validation_error, request_id)

    except Exception as e:
        # Unexpected errors
        unexpected_error = ActivityTrackingError(
            f"Unexpected error starting activity session: {str(e)}",
            details=context,
            user_message="An unexpected error occurred. Please try again later.",
        )
        log_error(
            logger,
            unexpected_error,
            context=context,
            error_type="unexpected_error",
        )
        return await create_error_response(unexpected_error, request_id)


@router.post("/log")
async def log_user_activity(
    request: LogActivityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log a specific user activity"""
    try:
        # Validate activity type
        try:
            activity_type = ActivityType(request.activity_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid activity type: {request.activity_type}",
            )

        # Validate context if provided
        context = None
        if request.context:
            try:
                context = ActivityContext(request.context)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid activity context: {request.context}",
                )

        success = await activity_tracker.log_activity(
            user_id=current_user.id,
            session_id=request.session_id,
            activity_type=activity_type,
            context=context,
            activity_data=request.activity_data,
            target_user_id=request.target_user_id,
            connection_id=request.connection_id,
            db=db,
        )

        if success:
            return {
                "success": True,
                "message": "Activity logged successfully",
                "activity_type": request.activity_type,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to log activity",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/end")
async def end_current_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    activity_id: Optional[int] = None,
):
    """End the current or specified activity"""
    try:
        success = await activity_tracker.end_activity(
            user_id=current_user.id, activity_id=activity_id, db=db
        )

        if success:
            return {"success": True, "message": "Activity ended successfully"}
        else:
            return {
                "success": False,
                "message": "No active activity found to end",
            }

    except Exception as e:
        logger.error(f"Error ending activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/current", response_model=ActivityResponse)
async def get_current_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current activity information for the user"""
    try:
        activity_info = await activity_tracker.get_user_current_activity(
            user_id=current_user.id, db=db
        )

        return ActivityResponse(**activity_info)

    except Exception as e:
        logger.error(f"Error getting current activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/user/{user_id}", response_model=ActivityResponse)
async def get_user_activity(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current activity information for a specific user (for connections/matches)"""
    try:
        # In a production app, you'd want to check if the current user
        # has permission to view this user's activity (e.g., they're connected)
        activity_info = await activity_tracker.get_user_current_activity(
            user_id=user_id, db=db
        )

        return ActivityResponse(**activity_info)

    except Exception as e:
        logger.error(f"Error getting user activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/connection/{connection_id}/summary")
async def get_connection_activity_summary(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get activity summary for users in a specific connection"""
    try:
        # TODO: Add permission check to ensure user is part of this connection

        summary = await activity_tracker.get_connection_activity_summary(
            connection_id=connection_id, db=db
        )

        return summary

    except Exception as e:
        logger.error(f"Error getting connection activity summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/insights/generate")
async def generate_daily_insights(
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate daily activity insights for the current user"""
    try:
        # Parse date or use today
        if date:
            insight_date = datetime.fromisoformat(date)
        else:
            insight_date = datetime.now()

        success = await activity_tracker.generate_daily_insights(
            user_id=current_user.id, date=insight_date, db=db
        )

        if success:
            return {
                "success": True,
                "message": "Daily insights generated",
                "date": insight_date.isoformat(),
            }
        else:
            return {
                "success": False,
                "message": "No activities found for the specified date",
            }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error generating daily insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/insights")
async def get_activity_insights(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get activity insights for the specified number of days"""
    try:
        start_date = datetime.now() - timedelta(days=days)

        insights = (
            db.query(ActivityInsights)
            .filter(
                ActivityInsights.user_id == current_user.id,
                ActivityInsights.insight_date >= start_date,
            )
            .order_by(ActivityInsights.insight_date.desc())
            .all()
        )

        return {
            "insights": [
                {
                    "date": insight.insight_date.isoformat(),
                    "total_session_time": insight.total_session_time,
                    "unique_connections_viewed": insight.unique_connections_viewed,
                    "revelations_shared": insight.revelations_shared,
                    "revelations_read": insight.revelations_read,
                    "average_interaction_time": insight.average_interaction_time,
                    "deep_engagement_count": insight.deep_engagement_count,
                    "quick_browse_count": insight.quick_browse_count,
                    "most_active_hour": insight.most_active_hour,
                }
                for insight in insights
            ]
        }

    except Exception as e:
        logger.error(f"Error getting activity insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/activity-types")
async def get_activity_types():
    """Get list of available activity types and contexts"""
    return {
        "activity_types": [
            {
                "value": activity.value,
                "name": activity.value.replace("_", " ").title(),
            }
            for activity in ActivityType
        ],
        "activity_contexts": [
            {
                "value": context.value,
                "name": context.value.replace("_", " ").title(),
            }
            for context in ActivityContext
        ],
        "device_capabilities": [
            {
                "value": capability.value,
                "name": capability.value.replace("_", " ").title(),
            }
            for capability in DeviceCapabilities
        ],
    }
