"""
User Activity Tracking Models - Sprint 4
Enhanced presence system with detailed activity tracking and context
"""

import enum
from datetime import datetime

from app.core.database import Base
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class ActivityType(str, enum.Enum):
    """Types of user activities for detailed tracking"""

    # Navigation activities
    VIEWING_DISCOVERY = "viewing_discovery"
    BROWSING_CONNECTIONS = "browsing_connections"
    READING_REVELATIONS = "reading_revelations"
    VIEWING_MESSAGES = "viewing_messages"
    EDITING_PROFILE = "editing_profile"

    # Interaction activities
    SWIPING_PROFILES = "swiping_profiles"
    READING_PROFILE = "reading_profile"
    TYPING_MESSAGE = "typing_message"
    SENDING_MESSAGE = "sending_message"
    SHARING_REVELATION = "sharing_revelation"
    READING_REVELATION = "reading_revelation"

    # Soul connection activities
    ENERGY_INTERACTION = "energy_interaction"
    COMPATIBILITY_VIEWING = "compatibility_viewing"
    CONNECTION_CELEBRATION = "connection_celebration"

    # System activities
    IDLE = "idle"
    AWAY = "away"
    BACKGROUND = "background"


class ActivityContext(str, enum.Enum):
    """Context/location where activity is happening"""

    DISCOVERY_PAGE = "discovery_page"
    CONNECTION_DETAIL = "connection_detail"
    REVELATION_TIMELINE = "revelation_timeline"
    MESSAGE_THREAD = "message_thread"
    PROFILE_VIEW = "profile_view"
    PROFILE_EDIT = "profile_edit"
    SOUL_ORB_INTERACTION = "soul_orb_interaction"
    COMPATIBILITY_RADAR = "compatibility_radar"
    SETTINGS = "settings"
    UNKNOWN = "unknown"


class DeviceCapabilities(str, enum.Enum):
    """Device capabilities that affect user experience"""

    HAPTIC_FEEDBACK = "haptic_feedback"
    PUSH_NOTIFICATIONS = "push_notifications"
    BACKGROUND_SYNC = "background_sync"
    HIGH_PERFORMANCE = "high_performance"
    REDUCED_MOTION = "reduced_motion"
    SCREEN_READER = "screen_reader"


class UserActivitySession(Base):
    """Track detailed user activity sessions"""

    __tablename__ = "user_activity_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, nullable=False, unique=True, index=True)

    # Session details
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Device and browser info
    device_type = Column(String, nullable=True)  # mobile, tablet, desktop
    browser_info = Column(JSON, nullable=True)
    screen_resolution = Column(String, nullable=True)
    device_capabilities = Column(JSON, nullable=True)  # List of DeviceCapabilities

    # Location and network
    timezone = Column(String, nullable=True)
    network_type = Column(String, nullable=True)  # wifi, cellular, unknown

    # Session quality metrics
    connection_quality = Column(String, nullable=True)  # excellent, good, poor
    interactions_count = Column(Integer, default=0)
    pages_visited = Column(Integer, default=0)
    websocket_reconnects = Column(Integer, default=0)

    # Relationships
    user = relationship("User")
    activities = relationship("UserActivityLog", back_populates="session")


class UserActivityLog(Base):
    """Log individual user activities within sessions"""

    __tablename__ = "user_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        String, ForeignKey("user_activity_sessions.session_id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Activity details
    activity_type = Column(String, nullable=False)  # ActivityType enum value
    activity_context = Column(String, nullable=True)  # ActivityContext enum value
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Context-specific data
    target_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # User being viewed/interacted with
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=True)
    revelation_day = Column(Integer, nullable=True)
    message_count = Column(Integer, nullable=True)

    # Activity metadata
    activity_data = Column(JSON, nullable=True)  # Additional context data
    interaction_intensity = Column(Float, nullable=True)  # 0.0 to 1.0 scale
    emotional_context = Column(
        String, nullable=True
    )  # happy, contemplative, excited, etc.

    # Performance metrics
    page_load_time = Column(Float, nullable=True)
    interaction_delay = Column(
        Float, nullable=True
    )  # Time between user action and system response

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    connection = relationship("SoulConnection")
    session = relationship("UserActivitySession", back_populates="activities")


class PresenceActivitySummary(Base):
    """Aggregated activity summary for real-time presence"""

    __tablename__ = "presence_activity_summary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Current activity context
    current_activity = Column(String, nullable=True)  # Most recent ActivityType
    current_context = Column(String, nullable=True)  # Most recent ActivityContext
    activity_started_at = Column(DateTime, nullable=True)

    # Activity in the last hour
    recent_activities = Column(JSON, nullable=True)  # List of recent activity types
    interactions_last_hour = Column(Integer, default=0)
    pages_visited_last_hour = Column(Integer, default=0)

    # Connection-specific activity
    active_connection_id = Column(
        Integer, ForeignKey("soul_connections.id"), nullable=True
    )
    connection_activity_type = Column(
        String, nullable=True
    )  # typing, reading, viewing_profile
    connection_activity_started = Column(DateTime, nullable=True)

    # Engagement patterns
    typical_session_duration = Column(
        Integer, nullable=True
    )  # Average session length in minutes
    most_active_times = Column(JSON, nullable=True)  # Hours when user is most active
    preferred_activities = Column(JSON, nullable=True)  # Most frequent activity types

    # Real-time status for display
    display_status = Column(
        String, nullable=True
    )  # Human-readable status like "Discovering souls"
    status_emoji = Column(
        String, nullable=True
    )  # Emoji representation of current activity

    # Updated automatically
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    active_connection = relationship("SoulConnection")


class ActivityInsights(Base):
    """Analytics and insights about user activity patterns"""

    __tablename__ = "activity_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    insight_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Daily insights
    total_session_time = Column(Integer, nullable=True)  # Minutes
    unique_connections_viewed = Column(Integer, nullable=True)
    revelations_shared = Column(Integer, nullable=True)
    revelations_read = Column(Integer, nullable=True)
    messages_sent = Column(Integer, nullable=True)

    # Engagement quality
    average_interaction_time = Column(Float, nullable=True)  # Seconds per interaction
    deep_engagement_count = Column(Integer, nullable=True)  # Long-duration activities
    quick_browse_count = Column(Integer, nullable=True)  # Short-duration activities

    # Soul connection insights
    compatibility_views = Column(Integer, nullable=True)
    energy_interactions = Column(Integer, nullable=True)
    celebration_triggers = Column(Integer, nullable=True)

    # Behavioral patterns
    most_active_hour = Column(Integer, nullable=True)  # 0-23
    preferred_activity_contexts = Column(JSON, nullable=True)
    activity_flow_patterns = Column(
        JSON, nullable=True
    )  # Common sequences of activities

    # Relationships
    user = relationship("User")
