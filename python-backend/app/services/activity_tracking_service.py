"""
Activity Tracking Service - Sprint 4
Enhanced presence system with detailed user activity tracking and real-time updates
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.core.error_handlers import (
    ActivityTrackingError,
    DatabaseError,
    ErrorCategory,
    error_handler_decorator,
    safe_execute,
)
from app.core.logging_config import get_logger, log_performance
from app.models.user_activity_tracking import (
    ActivityContext,
    ActivityInsights,
    ActivityType,
    PresenceActivitySummary,
    UserActivityLog,
    UserActivitySession,
)
from app.services.realtime_integration_service import realtime_integration
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = get_logger("app.services.activity_tracking_service")


class ActivityTrackingService:
    """Enhanced activity tracking with real-time presence integration"""

    def __init__(self):
        self.activity_display_map = {
            ActivityType.VIEWING_DISCOVERY: (
                "🔍 Discovering souls",
                "discovering souls",
            ),
            ActivityType.BROWSING_CONNECTIONS: (
                "💫 Viewing connections",
                "browsing connections",
            ),
            ActivityType.READING_REVELATIONS: (
                "📖 Reading revelations",
                "reading revelations",
            ),
            ActivityType.VIEWING_MESSAGES: ("💬 In conversation", "messaging"),
            ActivityType.EDITING_PROFILE: (
                "✏️ Updating profile",
                "updating profile",
            ),
            ActivityType.SWIPING_PROFILES: (
                "👆 Swiping profiles",
                "swiping profiles",
            ),
            ActivityType.READING_PROFILE: (
                "👤 Reading profile",
                "viewing profile",
            ),
            ActivityType.TYPING_MESSAGE: ("⌨️ Typing message", "typing"),
            ActivityType.SHARING_REVELATION: (
                "✨ Sharing revelation",
                "sharing revelation",
            ),
            ActivityType.READING_REVELATION: (
                "💝 Reading revelation",
                "reading revelation",
            ),
            ActivityType.ENERGY_INTERACTION: (
                "⚡ Soul energy sync",
                "energy sync",
            ),
            ActivityType.COMPATIBILITY_VIEWING: (
                "🎯 Viewing compatibility",
                "checking compatibility",
            ),
            ActivityType.CONNECTION_CELEBRATION: (
                "🎉 Celebrating connection",
                "celebrating",
            ),
            ActivityType.IDLE: ("💭 Contemplating", "idle"),
            ActivityType.AWAY: ("🌙 Away", "away"),
        }

    @error_handler_decorator(
        operation_name="start_activity_session",
        category=ErrorCategory.ACTIVITY_SESSION,
        user_message="Unable to start activity session. Please try again.",
        fallback_value=False,
    )
    async def start_activity_session(
        self,
        user_id: int,
        session_id: str,
        device_info: Dict[str, Any],
        db: Session,
    ) -> bool:
        """Start a new activity session for a user"""
        start_time = datetime.utcnow()

        # Validate inputs
        if not session_id or not user_id:
            raise ActivityTrackingError(
                "Missing required parameters: user_id or session_id",
                details={"user_id": user_id, "session_id": session_id},
            )

        try:
            # Create new session with validation
            session = UserActivitySession(
                user_id=user_id,
                session_id=session_id,
                device_type=device_info.get("device_type", "unknown"),
                browser_info=device_info.get("browser_info", {}),
                screen_resolution=device_info.get("screen_resolution"),
                device_capabilities=device_info.get("capabilities", []),
                timezone=device_info.get("timezone"),
                network_type=device_info.get("network_type", "unknown"),
                connection_quality="good",  # Default, can be updated
            )

            db.add(session)
            db.commit()

            # Initialize or update presence activity summary
            logging_context = {"user_id": user_id, "session_id": session_id}
            await safe_execute(
                "update_presence_summary",
                self._update_presence_summary,
                user_id,
                ActivityType.VIEWING_DISCOVERY,
                ActivityContext.DISCOVERY_PAGE,
                db,
                logger=logger,
                context=logging_context,
            )

            # Broadcast user activity start
            await safe_execute(
                "notify_user_activity",
                realtime_integration.notify_user_activity,
                user_id,
                "session_started",
                "platform",
                db,
                logger=logger,
                context=logging_context,
            )

            # Log performance
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            log_performance(
                logger,
                "start_activity_session",
                duration,
                context=logging_context,
            )

            logger.info(
                "Activity session started successfully",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "duration_ms": duration,
                },
            )
            return True

        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(
                f"Failed to create activity session: {str(e)}",
                original_error=e,
                details={"user_id": user_id, "session_id": session_id},
            )
        except Exception as e:
            db.rollback()
            raise ActivityTrackingError(
                f"Unexpected error starting activity session: {str(e)}",
                details={"user_id": user_id, "session_id": session_id},
            )

    @error_handler_decorator(
        operation_name="log_activity",
        category=ErrorCategory.ACTIVITY_LOGGING,
        user_message="Unable to log activity. This won't affect your experience.",
        fallback_value=False,
    )
    async def log_activity(
        self,
        user_id: int,
        session_id: str,
        activity_type: ActivityType,
        context: Optional[ActivityContext] = None,
        activity_data: Optional[Dict] = None,
        target_user_id: Optional[int] = None,
        connection_id: Optional[int] = None,
        db: Session = None,
    ) -> bool:
        """Log a specific user activity"""
        try:
            # End any previous ongoing activity for this user
            previous_activity = (
                db.query(UserActivityLog)
                .filter(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.ended_at.is_(None),
                )
                .first()
            )

            if previous_activity:
                previous_activity.ended_at = datetime.utcnow()
                previous_activity.duration_seconds = (
                    previous_activity.ended_at - previous_activity.started_at
                ).total_seconds()

            # Create new activity log
            activity_log = UserActivityLog(
                session_id=session_id,
                user_id=user_id,
                activity_type=activity_type.value,
                activity_context=context.value if context else None,
                target_user_id=target_user_id,
                connection_id=connection_id,
                activity_data=activity_data or {},
            )

            # Add context-specific data
            if activity_type == ActivityType.READING_REVELATION:
                activity_log.revelation_day = (
                    activity_data.get("day") if activity_data else None
                )
                activity_log.interaction_intensity = (
                    0.8  # High engagement for revelations
                )

            elif activity_type == ActivityType.TYPING_MESSAGE:
                activity_log.interaction_intensity = 0.9  # Very high for typing
                activity_log.emotional_context = (
                    activity_data.get("emotional_tone") if activity_data else None
                )

            elif activity_type == ActivityType.SWIPING_PROFILES:
                activity_log.interaction_intensity = 0.4  # Medium for browsing

            elif activity_type == ActivityType.ENERGY_INTERACTION:
                activity_log.interaction_intensity = 0.7  # High for soul connections

            db.add(activity_log)
            db.commit()

            # Update presence summary and broadcast
            await self._update_presence_summary(user_id, activity_type, context, db)
            await self._broadcast_activity_update(
                user_id, activity_type, context, activity_data
            )

            # Update session metrics
            await self._update_session_metrics(session_id, db)

            logger.debug(f"Activity logged: user {user_id} - {activity_type.value}")
            return True

        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
            return False

    async def end_activity(
        self,
        user_id: int,
        activity_id: Optional[int] = None,
        db: Session = None,
    ) -> bool:
        """End the current or specified activity"""
        try:
            if activity_id:
                activity = (
                    db.query(UserActivityLog)
                    .filter(UserActivityLog.id == activity_id)
                    .first()
                )
            else:
                # End most recent ongoing activity
                activity = (
                    db.query(UserActivityLog)
                    .filter(
                        UserActivityLog.user_id == user_id,
                        UserActivityLog.ended_at.is_(None),
                    )
                    .order_by(desc(UserActivityLog.started_at))
                    .first()
                )

            if activity:
                activity.ended_at = datetime.utcnow()
                activity.duration_seconds = (
                    activity.ended_at - activity.started_at
                ).total_seconds()
                db.commit()

                # Update activity to idle
                await self._update_presence_summary(
                    user_id, ActivityType.IDLE, ActivityContext.UNKNOWN, db
                )

                logger.debug(
                    f"Activity ended: user {user_id}, duration {activity.duration_seconds}s"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error ending activity: {str(e)}")
            return False

    async def get_user_current_activity(
        self, user_id: int, db: Session
    ) -> Dict[str, Any]:
        """Get detailed current activity information for a user"""
        try:
            # Get presence summary
            summary = (
                db.query(PresenceActivitySummary)
                .filter(PresenceActivitySummary.user_id == user_id)
                .first()
            )

            if not summary:
                return {
                    "status": "offline",
                    "activity": "unknown",
                    "display_status": "Offline",
                    "context": None,
                }

            # Get current activity log
            current_activity = (
                db.query(UserActivityLog)
                .filter(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.ended_at.is_(None),
                )
                .order_by(desc(UserActivityLog.started_at))
                .first()
            )

            activity_duration = None
            if current_activity:
                activity_duration = (
                    datetime.utcnow() - current_activity.started_at
                ).total_seconds()

            return {
                "status": "online",
                "activity": summary.current_activity,
                "context": summary.current_context,
                "display_status": summary.display_status,
                "status_emoji": summary.status_emoji,
                "activity_started_at": (
                    summary.activity_started_at.isoformat()
                    if summary.activity_started_at
                    else None
                ),
                "activity_duration": activity_duration,
                "active_connection_id": summary.active_connection_id,
                "connection_activity": summary.connection_activity_type,
                "recent_activities": summary.recent_activities or [],
                "interactions_last_hour": summary.interactions_last_hour,
            }

        except Exception as e:
            logger.error(f"Error getting user activity: {str(e)}")
            return {"status": "error", "activity": "unknown"}

    async def get_connection_activity_summary(
        self, connection_id: int, db: Session
    ) -> Dict[str, Any]:
        """Get activity summary for users in a specific connection"""
        try:
            from app.models.soul_connection import SoulConnection

            connection = (
                db.query(SoulConnection)
                .filter(SoulConnection.id == connection_id)
                .first()
            )
            if not connection:
                return {"error": "Connection not found"}

            user1_activity = await self.get_user_current_activity(
                connection.user1_id, db
            )
            user2_activity = await self.get_user_current_activity(
                connection.user2_id, db
            )

            # Check if they're both actively engaged in this connection
            both_active = (
                user1_activity.get("active_connection_id") == connection_id
                and user2_activity.get("active_connection_id") == connection_id
            )

            return {
                "connection_id": connection_id,
                "both_users_active": both_active,
                "user1_activity": user1_activity,
                "user2_activity": user2_activity,
                "connection_energy": "high" if both_active else "medium",
            }

        except Exception as e:
            logger.error(f"Error getting connection activity: {str(e)}")
            return {"error": str(e)}

    async def generate_daily_insights(
        self, user_id: int, date: datetime, db: Session
    ) -> bool:
        """Generate daily activity insights for a user"""
        try:
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)

            # Get daily activities
            daily_activities = (
                db.query(UserActivityLog)
                .filter(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.started_at >= start_date,
                    UserActivityLog.started_at < end_date,
                )
                .all()
            )

            if not daily_activities:
                return False

            # Calculate insights
            total_session_time = (
                sum((activity.duration_seconds or 0) for activity in daily_activities)
                // 60
            )  # Convert to minutes

            unique_connections = len(
                set(
                    activity.connection_id
                    for activity in daily_activities
                    if activity.connection_id
                )
            )

            revelations_shared = len(
                [
                    a
                    for a in daily_activities
                    if a.activity_type == ActivityType.SHARING_REVELATION.value
                ]
            )

            revelations_read = len(
                [
                    a
                    for a in daily_activities
                    if a.activity_type == ActivityType.READING_REVELATION.value
                ]
            )

            # Create insights record
            insights = ActivityInsights(
                user_id=user_id,
                insight_date=date,
                total_session_time=total_session_time,
                unique_connections_viewed=unique_connections,
                revelations_shared=revelations_shared,
                revelations_read=revelations_read,
                average_interaction_time=total_session_time
                / max(len(daily_activities), 1)
                * 60,  # Seconds
                deep_engagement_count=len(
                    [a for a in daily_activities if (a.duration_seconds or 0) > 120]
                ),
                quick_browse_count=len(
                    [a for a in daily_activities if (a.duration_seconds or 0) < 30]
                ),
            )

            db.add(insights)
            db.commit()

            logger.info(
                f"Daily insights generated for user {user_id}: {total_session_time}min session time"
            )
            return True

        except Exception as e:
            logger.error(f"Error generating daily insights: {str(e)}")
            return False

    async def _update_presence_summary(
        self,
        user_id: int,
        activity_type: ActivityType,
        context: Optional[ActivityContext],
        db: Session,
    ):
        """Update the presence activity summary for real-time display"""
        try:
            summary = (
                db.query(PresenceActivitySummary)
                .filter(PresenceActivitySummary.user_id == user_id)
                .first()
            )

            if not summary:
                summary = PresenceActivitySummary(user_id=user_id)
                db.add(summary)

            # Update current activity
            summary.current_activity = activity_type.value
            summary.current_context = context.value if context else None
            summary.activity_started_at = datetime.utcnow()

            # Set display status and emoji
            display_info = self.activity_display_map.get(
                activity_type, ("🔮 Active", "active")
            )
            summary.display_status = display_info[1]
            summary.status_emoji = display_info[0].split()[0]  # Extract emoji

            # Update recent activities
            recent = summary.recent_activities or []
            recent.append(
                {
                    "activity": activity_type.value,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            # Keep only last 10 activities
            summary.recent_activities = recent[-10:]

            # Increment hourly interaction count
            summary.interactions_last_hour = (summary.interactions_last_hour or 0) + 1

            db.commit()

        except Exception as e:
            logger.error(f"Error updating presence summary: {str(e)}")

    async def _broadcast_activity_update(
        self,
        user_id: int,
        activity_type: ActivityType,
        context: Optional[ActivityContext],
        activity_data: Optional[Dict],
    ):
        """Broadcast activity update via real-time system"""
        try:
            display_info = self.activity_display_map.get(
                activity_type, ("🔮 Active", "active")
            )

            await realtime_integration.notify_user_activity(
                user_id=user_id,
                activity=display_info[1],
                location=context.value if context else "unknown",
                db=None,  # We'll pass this through if needed
            )

        except Exception as e:
            logger.warning(f"Failed to broadcast activity update: {str(e)}")

    async def _update_session_metrics(self, session_id: str, db: Session):
        """Update session-level metrics"""
        try:
            session = (
                db.query(UserActivitySession)
                .filter(UserActivitySession.session_id == session_id)
                .first()
            )

            if session:
                session.interactions_count = (session.interactions_count or 0) + 1

                # Count unique pages/contexts visited
                unique_contexts = (
                    db.query(UserActivityLog.activity_context)
                    .filter(UserActivityLog.session_id == session_id)
                    .distinct()
                    .count()
                )
                session.pages_visited = unique_contexts

                db.commit()

        except Exception as e:
            logger.warning(f"Failed to update session metrics: {str(e)}")


# Global instance
activity_tracker = ActivityTrackingService()
